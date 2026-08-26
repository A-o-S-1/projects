"""
Tests for the public result lookup flow. Covers the security properties
that matter most for this app: no enumeration via error messages, rate
limiting, single-use scratch cards, and no direct/guessable access to a
result without a valid lookup.

Run with: python manage.py test apps.results
"""
import datetime

from django.test import TestCase
from django.urls import reverse

from apps.academics.models import Department, Subject
from apps.results.models import (
    AcademicSession,
    ClassRoom,
    ResultCheckLog,
    ScratchCard,
    Student,
    Term,
)


class ResultLookupFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        session = AcademicSession.objects.create(
            label="2025/2026", start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2026, 7, 31), is_current=True,
        )
        cls.term = Term.objects.create(session=session, name="first", is_current=True)
        classroom = ClassRoom.objects.create(name="JSS1A", level="jss1", arm="A")
        cls.student = Student.objects.create(
            admission_number="TEST/0001", first_name="Test", last_name="Student", current_class=classroom,
        )
        cls.card = ScratchCard.objects.create()

        department = Department.objects.create(name="Test Dept")
        subject = Subject.objects.create(name="Test Subject", department=department, level="junior")
        from apps.results.models import ResultEntry, TermResult
        ResultEntry.objects.create(student=cls.student, term=cls.term, subject=subject, ca_score=25, exam_score=60)
        cls.term_result = TermResult.objects.create(
            student=cls.student, term=cls.term, overall_total=85, average=85, is_published=True,
        )

    def _post(self, admission_number, pin, serial_number):
        return self.client.post(reverse("results:check"), {
            "admission_number": admission_number,
            "term": self.term.id,
            "pin": pin,
            "serial_number": serial_number,
            "website": "",
        })

    def test_lookup_form_loads(self):
        response = self.client.get(reverse("results:check"))
        self.assertEqual(response.status_code, 200)

    def test_correct_credentials_succeed_and_show_result(self):
        response = self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.assertRedirects(response, reverse("results:view_result"))
        detail = self.client.get(reverse("results:view_result"))
        self.assertContains(detail, "Student Test")

    def test_card_is_marked_used_after_success(self):
        self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.card.refresh_from_db()
        self.assertTrue(self.card.is_used)

    def test_used_card_cannot_be_reused(self):
        self._post("TEST/0001", self.card.pin, self.card.serial_number)
        response = self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.assertContains(response, "couldn")

    def test_wrong_pin_and_wrong_admission_number_give_identical_error(self):
        """Critical anti-enumeration property: an attacker must not be able
        to tell WHICH field was wrong from the response."""
        resp_wrong_pin = self._post("TEST/0001", "000000000000", self.card.serial_number)
        resp_wrong_admission = self._post("NOPE/9999", self.card.pin, self.card.serial_number)

        def extract_alert(response):
            content = response.content.decode()
            start = content.find('alert--error')
            return content[start:start + 300] if start != -1 else None

        self.assertIsNotNone(extract_alert(resp_wrong_pin))
        self.assertEqual(extract_alert(resp_wrong_pin), extract_alert(resp_wrong_admission))

    def test_every_attempt_is_logged(self):
        self.assertEqual(ResultCheckLog.objects.count(), 0)
        self._post("TEST/0001", "000000000000", self.card.serial_number)
        self.assertEqual(ResultCheckLog.objects.count(), 1)
        self.assertFalse(ResultCheckLog.objects.first().was_successful)

    def test_unpublished_result_cannot_be_checked(self):
        self.term_result.is_published = False
        self.term_result.save()
        response = self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.assertContains(response, "couldn")

    def test_blocked_result_cannot_be_checked_even_if_published(self):
        self.term_result.is_blocked = True
        self.term_result.save()
        response = self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.assertContains(response, "couldn")

    def test_rate_limiting_kicks_in_after_repeated_failures(self):
        for _ in range(5):
            self._post("TEST/0001", "000000000000", self.card.serial_number)
        response = self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.assertContains(response, "Too many attempts")
        # The card must NOT be consumed by an attempt that was rate-limited,
        # even though the credentials on that 6th attempt were correct.
        self.card.refresh_from_db()
        self.assertFalse(self.card.is_used)

    def test_honeypot_blocks_submission(self):
        response = self.client.post(reverse("results:check"), {
            "admission_number": "TEST/0001",
            "term": self.term.id,
            "pin": self.card.pin,
            "serial_number": self.card.serial_number,
            "website": "http://spam.example.com",
        })
        self.card.refresh_from_db()
        self.assertFalse(self.card.is_used)

    def test_direct_access_to_result_view_without_lookup_redirects_away(self):
        response = self.client.get(reverse("results:view_result"), follow=True)
        self.assertRedirects(response, reverse("results:check"))

    def test_done_view_clears_session(self):
        self._post("TEST/0001", self.card.pin, self.card.serial_number)
        self.client.get(reverse("results:done"))
        response = self.client.get(reverse("results:view_result"), follow=True)
        self.assertRedirects(response, reverse("results:check"))


class StaffToolsTests(TestCase):
    """Covers CSV bulk upload, subject-level disambiguation, the master
    sheet, and the shared position/average calculation service."""

    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import User
        from apps.results.models import ResultEntry, TermResult

        cls.staff_user = User.objects.create_user(
            username="staffmember", password="testpass123", is_staff=True
        )

        session = AcademicSession.objects.create(
            label="2025/2026", start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2026, 7, 31), is_current=True,
        )
        cls.term = Term.objects.create(session=session, name="first", is_current=True)
        cls.classroom = ClassRoom.objects.create(name="JSS1A", level="jss1", arm="A")

        department = Department.objects.create(name="Core")
        # Deliberately create "Mathematics" at BOTH levels — the exact
        # ambiguity that caused a real bug during development.
        cls.junior_maths = Subject.objects.create(name="Mathematics", department=department, level="junior")
        cls.senior_maths = Subject.objects.create(name="Mathematics", department=department, level="senior")

        cls.student = Student.objects.create(
            admission_number="TEST/JSS1/0001", first_name="Jane", last_name="Doe",
            current_class=cls.classroom,
        )

    def _csv_upload(self, csv_bytes, filename="upload.csv"):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.login(username="staffmember", password="testpass123")
        upload = SimpleUploadedFile(filename, csv_bytes, content_type="text/csv")
        return self.client.post(reverse("results:upload_scores"), {
            "term": self.term.id, "csv_file": upload,
        })

    def test_anonymous_user_cannot_access_upload_page(self):
        response = self.client.get(reverse("results:upload_scores"))
        self.assertNotEqual(response.status_code, 200)

    def test_staff_can_access_upload_page(self):
        self.client.login(username="staffmember", password="testpass123")
        response = self.client.get(reverse("results:upload_scores"))
        self.assertEqual(response.status_code, 200)

    def test_csv_upload_resolves_ambiguous_subject_by_class_level(self):
        """The core bug this test suite exists to prevent regressing: a JSS1
        student's 'Mathematics' score must land on the JUNIOR Subject record,
        never the senior one, even though both share the exact same name."""
        csv_bytes = b"admission_number,subject,ca_score,exam_score\nTEST/JSS1/0001,Mathematics,25,60\n"
        response = self._csv_upload(csv_bytes)
        self.assertContains(response, "Upload complete")

        from apps.results.models import ResultEntry
        entry = ResultEntry.objects.get(student=self.student, term=self.term)
        self.assertEqual(entry.subject_id, self.junior_maths.id)
        self.assertNotEqual(entry.subject_id, self.senior_maths.id)

    def test_csv_upload_reports_unknown_admission_number_without_crashing(self):
        csv_bytes = b"admission_number,subject,ca_score,exam_score\nNOTREAL/0000,Mathematics,25,60\n"
        response = self._csv_upload(csv_bytes)
        self.assertContains(response, "no student with admission number")

    def test_csv_upload_rejects_out_of_range_scores(self):
        csv_bytes = b"admission_number,subject,ca_score,exam_score\nTEST/JSS1/0001,Mathematics,99,60\n"
        response = self._csv_upload(csv_bytes)
        self.assertContains(response, "out of range")

    def test_csv_upload_recalculates_totals_and_positions(self):
        csv_bytes = b"admission_number,subject,ca_score,exam_score\nTEST/JSS1/0001,Mathematics,25,60\n"
        self._csv_upload(csv_bytes)

        from apps.results.models import TermResult
        term_result = TermResult.objects.get(student=self.student, term=self.term)
        self.assertEqual(term_result.overall_total, 85)
        self.assertEqual(term_result.position_in_class, "1st out of 1")

    def test_master_sheet_requires_staff_login(self):
        response = self.client.get(reverse("results:master_sheet"))
        self.assertNotEqual(response.status_code, 200)

    def test_master_sheet_renders_with_class_and_term_selected(self):
        self._csv_upload(b"admission_number,subject,ca_score,exam_score\nTEST/JSS1/0001,Mathematics,25,60\n")
        self.client.login(username="staffmember", password="testpass123")
        response = self.client.get(reverse("results:master_sheet"), {
            "term": self.term.id, "classroom": self.classroom.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Doe Jane")
        self.assertContains(response, "85.0")  # the total we uploaded


class RecalculatePositionsServiceTests(TestCase):
    """Directly tests the shared ranking service in isolation from any view."""

    def test_positions_never_cross_class_boundaries(self):
        from apps.results import services
        from apps.results.models import ResultEntry, TermResult

        session = AcademicSession.objects.create(
            label="2025/2026", start_date=datetime.date(2025, 9, 1),
            end_date=datetime.date(2026, 7, 31), is_current=True,
        )
        term = Term.objects.create(session=session, name="first", is_current=True)
        department = Department.objects.create(name="Core")
        subject = Subject.objects.create(name="English", department=department, level="junior")

        class_a = ClassRoom.objects.create(name="JSS1A", level="jss1", arm="A")
        class_b = ClassRoom.objects.create(name="JSS1B", level="jss1", arm="B")

        # Weakest student in Class A scores higher than the strongest in Class B.
        weak_in_a = Student.objects.create(admission_number="A/1", first_name="Weak", last_name="InA", current_class=class_a)
        strong_in_a = Student.objects.create(admission_number="A/2", first_name="Strong", last_name="InA", current_class=class_a)
        strong_in_b = Student.objects.create(admission_number="B/1", first_name="Strong", last_name="InB", current_class=class_b)

        ResultEntry.objects.create(student=weak_in_a, term=term, subject=subject, ca_score=20, exam_score=40)
        ResultEntry.objects.create(student=strong_in_a, term=term, subject=subject, ca_score=30, exam_score=70)
        ResultEntry.objects.create(student=strong_in_b, term=term, subject=subject, ca_score=10, exam_score=20)

        for student in [weak_in_a, strong_in_a, strong_in_b]:
            services.recalculate_term_result_totals(student, term)
        services.recalculate_positions_for_term(term)

        weak_entry = ResultEntry.objects.get(student=weak_in_a, term=term, subject=subject)
        strong_entry = ResultEntry.objects.get(student=strong_in_a, term=term, subject=subject)

        # Within Class A, weak_in_a must be LAST (2nd out of 2 in that class),
        # never boosted by comparison against the lower-scoring Class B student.
        self.assertEqual(weak_entry.position_in_subject, "2nd")
        self.assertEqual(strong_entry.position_in_subject, "1st")

        # Class B's single student must be ranked only within Class B (1st
        # out of 1), not penalized for scoring lower than Class A students.
        b_term_result = TermResult.objects.get(student=strong_in_b, term=term)
        self.assertEqual(b_term_result.position_in_class, "1st out of 1")
