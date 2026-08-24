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
