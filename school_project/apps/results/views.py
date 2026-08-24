from datetime import timedelta

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from .forms import ResultLookupForm
from .models import ResultCheckLog, ResultEntry, PsychomotorRating, ScratchCard, Student, Term, TermResult

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
