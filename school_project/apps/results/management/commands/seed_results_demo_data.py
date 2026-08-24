"""
Seeds the Result Portal with a working academic calendar, the grading
scale read off the school's real report card, standard psychomotor/social
behaviour skills, a handful of clearly-fictional demo students, and one
active scratch card per demo student so the public lookup flow can be
tested end-to-end.

Design decision: demo student names are entirely fictional — the actual
report card sample we were given showed a real student's name, and that
is never reused here, even as placeholder data.

Usage:
    python manage.py seed_results_demo_data
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.academics.models import Subject
from apps.results.models import (
    AcademicSession,
    ClassRoom,
    GradeBand,
    PsychomotorRating,
    PsychomotorSkill,
    ResultEntry,
    ScratchCard,
    ScratchCardBatch,
    Student,
    Term,
    TermResult,
)
from apps.staff.models import StaffMember


class Command(BaseCommand):
    help = "Seed the Result Portal with calendar, grading scale, classes, and demo students/results."

    def handle(self, *args, **options):
        self.seed_calendar()
        self.seed_grade_bands()
        self.seed_psychomotor_skills()
        self.seed_classrooms()
        students = self.seed_students()
        self.seed_results(students)
        self.seed_scratch_cards(students)
        self.stdout.write(self.style.SUCCESS("Result Portal demo data seeded successfully."))

    # ----------------------------------------------------------------
    def seed_calendar(self):
        session, _ = AcademicSession.objects.get_or_create(
            label="2025/2026",
            defaults={
                "start_date": datetime.date(2025, 9, 8),
                "end_date": datetime.date(2026, 7, 24),
                "is_current": True,
            },
        )
        terms = [
            ("first", datetime.date(2026, 1, 12), 45000),
            ("second", datetime.date(2026, 4, 20), 45000),
            ("third", None, 45000),
        ]
        for i, (name, next_begins, fees) in enumerate(terms):
            Term.objects.get_or_create(
                session=session,
                name=name,
                defaults={
                    "is_current": i == 0,
                    "next_term_begins": next_begins,
                    "next_term_fees": fees,
                    "vacation_date": datetime.date(2025, 12, 19) if name == "first" else None,
                },
            )

    def seed_grade_bands(self):
        # Read directly off the school's real report card image. Editable
        # any time from /admin/results/gradeband/ without touching code.
        bands = [
            (70, 100, "A1", "Excellent", 0),
            (65, 69, "A2", "Very Good", 1),
            (60, 64, "A3", "Good", 2),
            (55, 59, "C4", "Credit", 3),
            (50, 54, "C5", "Merit", 4),
            (45, 49, "C6", "Pass", 5),
            (40, 44, "P7", "Strong Pass", 6),
            (35, 39, "P8", "Weak Pass", 7),
            (0, 34, "F", "Fail", 8),
        ]
        for min_score, max_score, code, remark, order in bands:
            GradeBand.objects.get_or_create(
                grade_code=code,
                defaults={"min_score": min_score, "max_score": max_score, "remark": remark, "order": order},
            )

    def seed_psychomotor_skills(self):
        psychomotor = [
            "Handwriting", "Fluency", "Games", "Sports", "Drawing", "Craft", "Music",
        ]
        social = [
            "Attitude to School", "Punctuality", "Reliability", "Attendance", "Neatness",
            "Sense of Responsibility", "Attentiveness", "Initiative", "Organisation", "Perseverance",
        ]
        for i, name in enumerate(psychomotor):
            PsychomotorSkill.objects.get_or_create(name=name, category="psychomotor", defaults={"order": i})
        for i, name in enumerate(social):
            PsychomotorSkill.objects.get_or_create(name=name, category="social", defaults={"order": i})

    def seed_classrooms(self):
        teachers = list(StaffMember.objects.filter(category="teaching"))
        classes = [
            ("JSS1A", "jss1", "A", 0), ("JSS1B", "jss1", "B", 1),
            ("JSS2A", "jss2", "A", 2), ("JSS3A", "jss3", "A", 3),
            ("SS1A", "ss1", "A", 4), ("SS2A", "ss2", "A", 5), ("SS3A", "ss3", "A", 6),
        ]
        for i, (name, level, arm, order) in enumerate(classes):
            teacher = teachers[i % len(teachers)] if teachers else None
            ClassRoom.objects.get_or_create(
                name=name, defaults={"level": level, "arm": arm, "order": order, "class_teacher": teacher}
            )

    def seed_students(self):
        # Entirely fictional — never reuse a real student's name/details, even as demo data.
        jss1a = ClassRoom.objects.get(name="JSS1A")
        demo_students = [
            ("MDS/2025/0001", "Adaeze", "Nwosu", "F"),
            ("MDS/2025/0002", "Emeka", "Okafor", "M"),
            ("MDS/2025/0003", "Chiamaka", "Eze", "F"),
        ]
        students = []
        for admission_number, first, last, gender in demo_students:
            student, _ = Student.objects.get_or_create(
                admission_number=admission_number,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "gender": gender,
                    "current_class": jss1a,
                    "guardian_name": f"[Demo Guardian for {first}]",
                    "guardian_phone": "08000000000",
                    "admitted_date": datetime.date(2025, 9, 8),
                },
            )
            students.append(student)
        return students

    def seed_results(self, students):
        term = Term.objects.get(is_current=True)
        junior_subjects = list(Subject.objects.filter(level="junior"))

        # Slightly different score profiles per student so the demo shows
        # a range of grades, not three identical "perfect student" results.
        score_profiles = [
            (20, 46),  # strong student — spans A1 down to A2/A3, not a flat sweep
            (18, 40),  # average student
            (22, 55),  # good student
        ]

        for student, (ca_base, exam_base) in zip(students, score_profiles):
            for i, subject in enumerate(junior_subjects):
                # Deterministic +/- swing per subject (not real randomness,
                # but enough spread that demo grades vary realistically
                # instead of being identical across every subject).
                variation = ((i * 5) % 11) - 5
                ca = min(30, ca_base + variation // 2)
                exam = min(70, exam_base + variation)
                ResultEntry.objects.get_or_create(
                    student=student, term=term, subject=subject,
                    defaults={"ca_score": max(0, ca), "exam_score": max(0, exam)},
                )

            entries = ResultEntry.objects.filter(student=student, term=term)
            total = sum(e.total_score for e in entries)
            average = round(total / entries.count(), 1) if entries.count() else 0

            term_result, _ = TermResult.objects.get_or_create(
                student=student, term=term,
                defaults={
                    "overall_total": total,
                    "average": average,
                    "position_in_class": "—",
                    "overall_performance": "Excellent" if average >= 65 else "Good" if average >= 50 else "Fair",
                    "class_teacher_remark": "[Demo remark] A pleasure to teach — keep up the good work.",
                    "administrator_remark": "[Demo remark] Well done this term.",
                    "is_published": True,
                },
            )

            # Psychomotor ratings — deterministic-but-varied 3-5 range.
            for i, skill in enumerate(PsychomotorSkill.objects.all()):
                rating = 3 + ((i + students.index(student)) % 3)
                PsychomotorRating.objects.get_or_create(
                    student=student, term=term, skill=skill, defaults={"rating": rating}
                )

        # Recalculate class positions now that every demo student has a TermResult.
        ranked = TermResult.objects.filter(term=term, student__in=students).order_by("-average")
        for i, tr in enumerate(ranked):
            suffix = "th" if 11 <= (i + 1) % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get((i + 1) % 10, "th")
            tr.position_in_class = f"{i + 1}{suffix} out of {len(students)}"
            tr.save(update_fields=["position_in_class"])

    def seed_scratch_cards(self, students):
        batch, _ = ScratchCardBatch.objects.get_or_create(
            label="Demo Batch — First Term 2025/2026",
            defaults={"quantity": len(students), "price": 200},
        )
        self.stdout.write(self.style.WARNING("Demo scratch card PINs (for testing the public lookup only):"))
        for student in students:
            # Deterministic serial (derived from admission number) rather than
            # the model's random default — this is the only way to reliably
            # find "this demo student's card" on a second run without adding
            # a field just for seed-script bookkeeping. Real cards generated
            # via the admin still get fully random serials as normal.
            demo_serial = "MDS-DEMO-" + student.admission_number.replace("/", "")
            card, _ = ScratchCard.objects.get_or_create(
                serial_number=demo_serial, defaults={"batch": batch}
            )
            self.stdout.write(f"  {student.admission_number} ({student.full_name}) -> PIN {card.pin} / Serial {card.serial_number}")
