import csv

from django.contrib import admin, messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AcademicSession,
    ClassRoom,
    GradeBand,
    PsychomotorRating,
    PsychomotorSkill,
    ResultCheckLog,
    ResultEntry,
    ScratchCard,
    ScratchCardBatch,
    Student,
    Term,
    TermResult,
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("label", "start_date", "end_date", "is_current")
    list_editable = ("is_current",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_current", "next_term_begins", "next_term_fees")
    list_filter = ("session", "name")
    list_editable = ("is_current",)


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "arm", "class_teacher", "student_count")
    list_filter = ("level",)
    ordering = ("order", "name")

    def student_count(self, obj):
        return obj.students.count()


class ExportCsvMixin:
    """
    Shared "Export selected as CSV" admin action — used by Student and
    ClassRoom admins. Matches "View and/or Export Combined Population" and
    "View and Export Class-By-Class List" from the original admin panel,
    without needing a separate custom view for each.
    """
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = self.csv_fields
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta.model_name}_export.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field, "") for field in field_names])
        return response

    export_as_csv.short_description = "Export selected as CSV"


@admin.register(Student)
class StudentAdmin(ExportCsvMixin, admin.ModelAdmin):
    list_display = ("admission_number", "full_name", "current_class", "gender", "is_active")
    list_filter = ("current_class", "gender", "is_active")
    search_fields = ("admission_number", "first_name", "last_name")
    actions = ["export_as_csv"]
    csv_fields = ["admission_number", "first_name", "last_name", "current_class", "gender", "guardian_name", "guardian_phone", "is_active"]


@admin.register(GradeBand)
class GradeBandAdmin(admin.ModelAdmin):
    list_display = ("grade_code", "min_score", "max_score", "remark", "order")
    list_editable = ("min_score", "max_score", "remark", "order")
    ordering = ("order",)


@admin.register(PsychomotorSkill)
class PsychomotorSkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order")
    list_filter = ("category",)
    list_editable = ("order",)


@admin.register(PsychomotorRating)
class PsychomotorRatingAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "skill", "rating")
    list_filter = ("term", "skill__category")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")


@admin.register(ResultEntry)
class ResultEntryAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "term", "ca_score", "exam_score", "total_display", "grade_display")
    list_filter = ("term", "subject", "student__current_class")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")
    autocomplete_fields = ["student", "subject"]

    def total_display(self, obj):
        return obj.total_score
    total_display.short_description = "Total"

    def grade_display(self, obj):
        return f"{obj.grade_code} — {obj.remark}"
    grade_display.short_description = "Grade"


@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "average", "position_in_class", "is_published", "is_blocked")
    list_filter = ("term", "is_published", "is_blocked")
    search_fields = ("student__admission_number", "student__first_name", "student__last_name")
    list_editable = ("is_published", "is_blocked")
    actions = ["publish_results", "unpublish_results", "recalculate_summary"]

    def publish_results(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"Published {updated} result(s).", messages.SUCCESS)
    publish_results.short_description = "Publish selected results"

    def unpublish_results(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"Unpublished {updated} result(s).", messages.SUCCESS)
    unpublish_results.short_description = "Unpublish selected results"

    def recalculate_summary(self, request, queryset):
        """
        Recomputes overall_total/average from each student's ResultEntry rows.
        Position-in-class and per-subject positions/averages are handled by
        the separate `recalculate_positions` management command, since that
        needs to rank across the WHOLE class, not just the selected rows.
        """
        count = 0
        for term_result in queryset:
            entries = ResultEntry.objects.filter(student=term_result.student, term=term_result.term)
            total = sum(e.total_score for e in entries)
            term_result.overall_total = total
            term_result.average = round(total / entries.count(), 1) if entries.count() else None
            term_result.save(update_fields=["overall_total", "average"])
            count += 1
        self.message_user(request, f"Recalculated totals for {count} result(s).", messages.SUCCESS)
    recalculate_summary.short_description = "Recalculate totals from result entries"


@admin.register(ScratchCardBatch)
class ScratchCardBatchAdmin(admin.ModelAdmin):
    list_display = ("label", "quantity", "price", "created_at", "cards_link")

    def cards_link(self, obj):
        url = reverse("admin:results_scratchcard_changelist") + f"?batch__id__exact={obj.id}"
        return format_html('<a href="{}">View {} cards</a>', url, obj.quantity)
    cards_link.short_description = "Cards"


@admin.register(ScratchCard)
class ScratchCardAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "pin", "batch", "is_used", "used_at", "used_for_student")
    list_filter = ("is_used", "batch")
    search_fields = ("serial_number", "pin")
    actions = ["reactivate_cards"]

    def reactivate_cards(self, request, queryset):
        """Matches 'Activate Supplementary Scratch Card' — for a legitimate
        re-check (e.g. a parent needs to view the result again)."""
        updated = queryset.update(is_used=False, used_at=None, used_for_student=None)
        self.message_user(request, f"Reactivated {updated} card(s).", messages.SUCCESS)
    reactivate_cards.short_description = "Reactivate selected cards (allow re-use)"


@admin.register(ResultCheckLog)
class ResultCheckLogAdmin(admin.ModelAdmin):
    list_display = ("admission_number_attempted", "ip_address", "was_successful", "attempted_at")
    list_filter = ("was_successful",)
    search_fields = ("admission_number_attempted", "ip_address")
    date_hierarchy = "attempted_at"

    def has_add_permission(self, request):
        return False  # logs are system-generated only, never hand-created
