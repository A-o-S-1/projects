import csv
import io
from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView

from . import services
from .forms import MasterSheetForm, ResultLookupForm, ScoreCSVUploadForm
from .models import ClassRoom, ResultCheckLog, ResultEntry, PsychomotorRating, ScratchCard, Student, Term, TermResult
from apps.academics.models import Subject

# How many failed attempts from one IP within the window before we block
# further tries. Deliberately generous enough not to lock out a parent who
# fat-fingers a PIN twice, strict enough to make brute-forcing impractical.
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_MINUTES = 15

# How long a successful lookup stays viewable before the parent has to
# check again with the (now-used-up) card. Short enough that a result
# left open on a shared/library computer doesn't stay exposed for long.
SESSION_UNLOCK_MINUTES = 15

SESSION_KEY = "unlocked_term_result_id"
SESSION_KEY_EXPIRES = "unlocked_term_result_expires"


def _client_ip(request):
    """
    Best-effort real client IP behind a reverse proxy. Checked against
    X-Forwarded-For first (set by Nginx/the hosting platform in production),
    falling back to REMOTE_ADDR for local development.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _is_rate_limited(ip_address):
    window_start = timezone.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    recent_failed = ResultCheckLog.objects.filter(
        ip_address=ip_address, was_successful=False, attempted_at__gte=window_start
    ).count()
    return recent_failed >= RATE_LIMIT_MAX_ATTEMPTS


class ResultLookupView(FormView):
    """
    Public result lookup: Admission Number + Term + Scratch Card PIN + Serial.

    Security properties (see also the module-level constants above):
    - Every attempt is logged (ResultCheckLog), success or failure.
    - Failures never reveal WHICH field was wrong — same generic message
      whether the admission number doesn't exist, the PIN is wrong, the
      card was already used, or the result simply isn't published yet.
      Distinguishing these would let an attacker enumerate valid admission
      numbers or valid-but-unused PINs one field at a time.
    - IP-based rate limiting via the same log table — no new dependency.
    - On success, the card is immediately marked used (single-use) and the
      result becomes viewable only through a time-limited session flag,
      not a bookmarkable/guessable URL.
    """
    template_name = "results/lookup.html"
    form_class = ResultLookupForm

    def form_valid(self, form):
        ip_address = _client_ip(self.request)
        admission_number = form.cleaned_data["admission_number"]

        if _is_rate_limited(ip_address):
            form.add_error(None, "Too many attempts. Please wait 15 minutes before trying again.")
            return self.render_to_response(self.get_context_data(form=form))

        term = Term.objects.filter(pk=form.cleaned_data["term"]).first()
        student = Student.objects.filter(admission_number__iexact=admission_number, is_active=True).first()
        card = ScratchCard.objects.filter(
            serial_number__iexact=form.cleaned_data["serial_number"],
            pin=form.cleaned_data["pin"],
            is_used=False,
        ).first()

        term_result = None
        if student and term:
            term_result = TermResult.objects.filter(student=student, term=term).first()

        success = bool(student and term and card and term_result and term_result.is_publicly_visible)

        ResultCheckLog.objects.create(
            admission_number_attempted=admission_number, ip_address=ip_address, was_successful=success
        )

        if not success:
            form.add_error(
                None,
                "We couldn't find a result matching those details. Please double-check your admission "
                "number, term, PIN, and serial number, or confirm the result has been published.",
            )
            return self.render_to_response(self.get_context_data(form=form))

        card.mark_used(student)
        self.request.session[SESSION_KEY] = term_result.id
        self.request.session[SESSION_KEY_EXPIRES] = (
            timezone.now() + timedelta(minutes=SESSION_UNLOCK_MINUTES)
        ).isoformat()
        return redirect(reverse("results:view_result"))


class ResultDetailView(View):
    """
    Displays the unlocked result — reachable only via a valid session flag
    set by ResultLookupView, never by a direct/guessable URL. Session flag
    is time-limited and single-use per successful card check.
    """
    template_name = "results/result_detail.html"

    def get(self, request):
        term_result_id = request.session.get(SESSION_KEY)
        expires_at = request.session.get(SESSION_KEY_EXPIRES)

        if not term_result_id or not expires_at or timezone.now().isoformat() > expires_at:
            request.session.pop(SESSION_KEY, None)
            request.session.pop(SESSION_KEY_EXPIRES, None)
            return redirect(reverse("results:check"))

        term_result = TermResult.objects.filter(pk=term_result_id, is_published=True, is_blocked=False).first()
        if not term_result:
            return redirect(reverse("results:check"))

        result_entries = ResultEntry.objects.filter(
            student=term_result.student, term=term_result.term
        ).select_related("subject")
        psychomotor_ratings = PsychomotorRating.objects.filter(
            student=term_result.student, term=term_result.term
        ).select_related("skill")

        return render(request, self.template_name, {
            "term_result": term_result,
            "student": term_result.student,
            "result_entries": result_entries,
            "psychomotor_ratings": psychomotor_ratings,
        })


class ResultLogoutView(View):
    """Lets the parent explicitly clear the unlocked result before the
    session naturally expires — e.g. on a shared computer."""

    def get(self, request):
        request.session.pop(SESSION_KEY, None)
        request.session.pop(SESSION_KEY_EXPIRES, None)
        return redirect(reverse("results:check"))


# ==============================================================================
# Staff-only tools: CSV score upload, position recalculation, master sheets
# ==============================================================================
@method_decorator(staff_member_required, name="dispatch")
class ScoreUploadView(View):
    """
    Bulk score upload for a whole class/term at once from a CSV file,
    rather than entering each ResultEntry one at a time in the admin.

    Gated with @staff_member_required (Django's built-in admin-login check)
    rather than building separate authentication — this reuses the same
    login every other admin action already requires.
    """
    template_name = "results/staff/upload_scores.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ScoreCSVUploadForm()})

    def post(self, request):
        form = ScoreCSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        term = Term.objects.get(pk=form.cleaned_data["term"])
        csv_file = form.cleaned_data["csv_file"]

        decoded = csv_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        created, updated, errors = 0, 0, []
        touched_students = set()

        required_columns = {"admission_number", "subject", "ca_score", "exam_score"}
        if not required_columns.issubset(set(reader.fieldnames or [])):
            errors.append(
                f"CSV header must include: {', '.join(sorted(required_columns))}. "
                f"Found: {', '.join(reader.fieldnames or []) or '(empty file)'}"
            )
            return render(request, self.template_name, {"form": form, "errors": errors})

        for row_number, row in enumerate(reader, start=2):  # row 1 is the header
            admission_number = (row.get("admission_number") or "").strip()
            subject_name = (row.get("subject") or "").strip()

            student = Student.objects.filter(admission_number__iexact=admission_number).first()
            if not student:
                errors.append(f"Row {row_number}: no student with admission number '{admission_number}'.")
                continue

            # Subject names like "Mathematics" exist at BOTH junior and
            # senior level — resolve using the student's own class level so
            # a JSS1 student's "Mathematics" never gets attached to the
            # senior-level Subject record (or vice versa).
            subject_qs = Subject.objects.filter(name__iexact=subject_name)
            if student.current_class:
                subject = subject_qs.filter(level=student.current_class.subject_level).first()
                if not subject:
                    # Fall back to any match (e.g. the subject only exists
                    # at one level) rather than failing outright.
                    subject = subject_qs.first()
            else:
                subject = subject_qs.first()

            if not subject:
                errors.append(f"Row {row_number}: no subject named '{subject_name}'.")
                continue

            try:
                ca_score = float(row.get("ca_score") or 0)
                exam_score = float(row.get("exam_score") or 0)
            except ValueError:
                errors.append(f"Row {row_number}: CA/Exam score must be a number.")
                continue

            if ca_score > 30 or exam_score > 70 or ca_score < 0 or exam_score < 0:
                errors.append(
                    f"Row {row_number}: scores out of range (CA max 30, Exam max 70) for {admission_number}."
                )
                continue

            entry, was_created = ResultEntry.objects.update_or_create(
                student=student, term=term, subject=subject,
                defaults={"ca_score": ca_score, "exam_score": exam_score},
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1
            touched_students.add(student.id)

        for student_id in touched_students:
            services.recalculate_term_result_totals(Student.objects.get(pk=student_id), term)
        entries_updated, term_results_updated = services.recalculate_positions_for_term(term)

        return render(request, self.template_name, {
            "form": ScoreCSVUploadForm(),
            "summary": {
                "created": created,
                "updated": updated,
                "students_touched": len(touched_students),
                "entries_ranked": entries_updated,
                "term_results_ranked": term_results_updated,
            },
            "errors": errors,
        })


@method_decorator(staff_member_required, name="dispatch")
class MasterSheetView(View):
    """
    Printable class-wide broadsheet: every active student in a class, every
    subject as a column, for one term — for teachers/admin, not parents.
    Distinct from the individual result sheet parents see via the public
    lookup (results/result_detail.html).
    """
    template_name = "results/staff/master_sheet.html"

    def get(self, request):
        term_id = request.GET.get("term")
        classroom_id = request.GET.get("classroom")

        if not term_id or not classroom_id:
            return render(request, self.template_name, {"form": MasterSheetForm()})

        term = Term.objects.get(pk=term_id)
        classroom = ClassRoom.objects.get(pk=classroom_id)
        students = list(classroom.students.filter(is_active=True).order_by("last_name", "first_name"))

        subjects = list(
            Subject.objects.filter(
                result_entries__student__in=students, result_entries__term=term
            ).distinct().order_by("name")
        )

        entries_by_student = {}
        for student in students:
            entries = {
                e.subject_id: e
                for e in ResultEntry.objects.filter(student=student, term=term)
            }
            term_result = TermResult.objects.filter(student=student, term=term).first()
            entries_by_student[student.id] = {"entries": entries, "term_result": term_result}

        return render(request, self.template_name, {
            "form": MasterSheetForm(initial={"term": term_id, "classroom": classroom_id}),
            "term": term,
            "classroom": classroom,
            "students": students,
            "subjects": subjects,
            "entries_by_student": entries_by_student,
        })
