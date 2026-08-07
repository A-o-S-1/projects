from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "department", "submitted_at", "is_read")
    list_filter = ("department", "is_read")
    search_fields = ("name", "email", "message")
    readonly_fields = ("submitted_at",)
    list_editable = ("is_read",)
