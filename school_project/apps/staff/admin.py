from django.contrib import admin

from .models import StaffMember


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role_title", "category", "department", "order", "is_published")
    list_filter = ("category", "department", "is_published")
    list_editable = ("order", "is_published")
    search_fields = ("full_name", "role_title")
