from django.contrib import admin

from .models import GalleryImage


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "order", "uploaded_at")
    list_filter = ("category",)
    list_editable = ("order",)
    search_fields = ("title", "caption")
