from django.contrib import admin

from .models import (
    AboutPage,
    AdmissionInquiry,
    AdmissionsPage,
    AdmissionStep,
    CoreValue,
    HeroSlide,
    SchoolInfo,
)


class SingletonAdminMixin:
    """Shared behaviour for our singleton content models (About, Admissions, SchoolInfo):
    block creating a second row and block deleting the only one, since either
    action would break the corresponding public page."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SchoolInfo)
class SchoolInfoAdmin(SingletonAdminMixin, admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("school_name", "tagline", "address")}),
        ("Contact", {"fields": ("main_office_phone", "admissions_phone", "emergency_phone", "email")}),
        ("Social Links", {"fields": ("facebook_url", "twitter_url", "instagram_url", "youtube_url")}),
        ("Result Portal", {"fields": ("result_portal_url",)}),
    )


class CoreValueInline(admin.TabularInline):
    model = CoreValue
    extra = 1


@admin.register(AboutPage)
class AboutPageAdmin(SingletonAdminMixin, admin.ModelAdmin):
    fieldsets = (
        ("Story", {"fields": ("history", "mission", "vision")}),
        ("Administrator's Message", {"fields": ("administrator_name", "administrator_title", "administrator_message", "administrator_photo")}),
    )


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)


class AdmissionStepInline(admin.TabularInline):
    model = AdmissionStep
    extra = 1


@admin.register(AdmissionsPage)
class AdmissionsPageAdmin(SingletonAdminMixin, admin.ModelAdmin):
    fieldsets = (("Content", {"fields": ("intro", "requirements")}),)


@admin.register(AdmissionStep)
class AdmissionStepAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)


@admin.register(AdmissionInquiry)
class AdmissionInquiryAdmin(admin.ModelAdmin):
    list_display = ("child_name", "parent_name", "phone", "level_applying_for", "submitted_at", "reviewed")
    list_filter = ("level_applying_for", "reviewed")
    search_fields = ("child_name", "parent_name", "phone", "email")
    readonly_fields = ("submitted_at",)
    list_editable = ("reviewed",)


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_editable = ("order", "is_active")
