from django.contrib import admin

from .models import SchoolInfo


@admin.register(SchoolInfo)
class SchoolInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("school_name", "tagline", "address")}),
        ("Contact", {"fields": ("main_office_phone", "admissions_phone", "emergency_phone", "email")}),
        ("Social Links", {"fields": ("facebook_url", "twitter_url", "instagram_url", "youtube_url")}),
        ("Result Portal", {"fields": ("result_portal_url",)}),
    )

    def has_add_permission(self, request):
        # Singleton: never allow a second row from the admin UI.
        return not SchoolInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Deleting the only row would break every page's navbar/footer.
        return False
