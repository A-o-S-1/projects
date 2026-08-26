"""
Recalculates per-subject positions/class-averages and per-class overall
position for one term (or every term, if none is specified). Same logic
used by the admin action and the CSV upload — see apps/results/services.py.

Usage:
    python manage.py recalculate_positions              # every term
    python manage.py recalculate_positions --term-id 3  # one term only
"""
from django.core.management.base import BaseCommand

from apps.results import services
from apps.results.models import Term


class Command(BaseCommand):
    help = "Recalculate result positions and class averages for one term or all terms."

    def add_arguments(self, parser):
        parser.add_argument(
            "--term-id", type=int, default=None,
            help="Only recalculate this Term's ID. Omit to recalculate every term.",
        )

    def handle(self, *args, **options):
        terms = Term.objects.filter(pk=options["term_id"]) if options["term_id"] else Term.objects.all()

        if not terms.exists():
            self.stdout.write(self.style.WARNING("No matching term(s) found."))
            return

        for term in terms:
            entries_updated, term_results_updated = services.recalculate_positions_for_term(term)
            self.stdout.write(
                f"{term}: {entries_updated} subject entries, {term_results_updated} student summaries updated."
            )

        self.stdout.write(self.style.SUCCESS("Done."))
