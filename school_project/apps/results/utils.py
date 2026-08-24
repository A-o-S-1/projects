from datetime import timedelta

from django.utils import timezone

from .models import ResultCheckLog

# Deliberately conservative: a genuine parent needs at most a couple of
# tries (typo in the PIN, wrong serial digit). Anything beyond this in a
# short window looks like automated guessing against admission numbers.
MAX_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


def get_client_ip(request):
    """
    Returns the real client IP, accounting for a reverse proxy (Nginx in
    our deployment) setting X-Forwarded-For. Takes the first address in
    that header when present — the original client — falling back to
    REMOTE_ADDR for local/dev requests with no proxy in front.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def is_rate_limited(ip_address):
    """
    True if this IP has made MAX_ATTEMPTS or more *failed* lookups within
    the lockout window. Only failed attempts count — a parent legitimately
    checking a not-yet-published result repeatedly shouldn't get locked
    out for it (see ResultLookupView.form_valid).
    """
    window_start = timezone.now() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    recent_failures = ResultCheckLog.objects.filter(
        ip_address=ip_address, was_successful=False, attempted_at__gte=window_start
    ).count()
    return recent_failures >= MAX_ATTEMPTS
