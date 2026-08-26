"""
Shared result-calculation logic.

Pulled into its own module because it's called from three places that must
stay consistent: the CSV bulk upload, the TermResult admin action, and the
`recalculate_positions` management command. Keeping the ranking rules in
one place means a future change to how ties are handled, for example,
only has to happen once.
"""
from .models import ClassRoom, ResultEntry, TermResult


def ordinal(n):
    """1 -> '1st', 2 -> '2nd', 3 -> '3rd', 11 -> '11th', ..."""
    if 11 <= n % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def recalculate_term_result_totals(student, term):
    """
    Recomputes one student's overall_total/average for a term from their
    ResultEntry rows. Does NOT touch is_published/is_blocked — those are
    staff decisions, never something a data-entry action should silently
    reset.
    """
    entries = ResultEntry.objects.filter(student=student, term=term)
    total = sum(e.total_score for e in entries)
    average = round(total / entries.count(), 1) if entries.count() else None

    term_result, _ = TermResult.objects.get_or_create(student=student, term=term)
    term_result.overall_total = total
    term_result.average = average
    term_result.save(update_fields=["overall_total", "average"])
    return term_result


def recalculate_positions_for_term(term):
    """
    Recomputes, PER CLASS (never across the whole school — a JSS1A student
    should never be ranked against SS3 students):
      - each ResultEntry's position_in_subject and subject_class_average
      - each TermResult's position_in_class

    Uses competition ranking (equal scores share a rank; the next distinct
    score skips ahead accordingly — e.g. two students tied for 1st means
    the next student is 3rd, not 2nd).

    Returns (entries_updated, term_results_updated) for reporting back to
    whoever triggered this (admin action, CSV upload summary, management
    command output).
    """
    entries_updated = 0
    term_results_updated = 0

    for classroom in ClassRoom.objects.all():
        student_ids = list(classroom.students.filter(is_active=True).values_list("id", flat=True))
        if not student_ids:
            continue

        subject_ids = (
            ResultEntry.objects.filter(term=term, student_id__in=student_ids)
            .values_list("subject_id", flat=True).distinct()
        )
        for subject_id in subject_ids:
            entries = list(
                ResultEntry.objects.filter(term=term, subject_id=subject_id, student_id__in=student_ids)
            )
            if not entries:
                continue
            entries.sort(key=lambda e: e.total_score, reverse=True)
            average = round(sum(e.total_score for e in entries) / len(entries), 1)

            rank, previous_score = 0, None
            for i, entry in enumerate(entries):
                if entry.total_score != previous_score:
                    rank = i + 1
                    previous_score = entry.total_score
                entry.position_in_subject = ordinal(rank)
                entry.subject_class_average = average
                entry.save(update_fields=["position_in_subject", "subject_class_average"])
                entries_updated += 1

        term_results = list(TermResult.objects.filter(term=term, student_id__in=student_ids))
        term_results.sort(key=lambda tr: (tr.average if tr.average is not None else -1), reverse=True)
        total_in_class = len(term_results)

        rank, previous_average = 0, None
        for i, term_result in enumerate(term_results):
            if term_result.average != previous_average:
                rank = i + 1
                previous_average = term_result.average
            term_result.position_in_class = f"{ordinal(rank)} out of {total_in_class}"
            term_result.save(update_fields=["position_in_class"])
            term_results_updated += 1

    return entries_updated, term_results_updated
