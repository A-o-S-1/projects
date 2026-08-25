from django.contrib import admin

from .models import GalleryAlbum, GalleryPhoto


class GalleryPhotoInline(admin.TabularInline):
    model = GalleryPhoto
    extra = 3
    fields = ("image", "caption", "order")


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "photo_count", "order")
    list_filter = ("category",)
    list_editable = ("order",)
    search_fields = ("title", "caption")
    inlines = [GalleryPhotoInline]
