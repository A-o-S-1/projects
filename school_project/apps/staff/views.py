from django.views.generic import ListView

from .models import StaffMember


class StaffDirectoryView(ListView):
    """Teaching + non-teaching staff — the general Staff Directory page."""
    template_name = "staff/directory.html"
    context_object_name = "staff_members"

    def get_queryset(self):
        return StaffMember.objects.filter(
            is_published=True,
            category__in=["teaching", "non_teaching"],
        ).select_related("department")


class ManagementView(ListView):
    """School leadership — the separate Management Profiles page."""
    template_name = "staff/management.html"
    context_object_name = "staff_members"

    def get_queryset(self):
        return StaffMember.objects.filter(is_published=True, category="management")
