from django.views.generic import ListView

from .models import GalleryAlbum


class GalleryView(ListView):
    """
    Gallery grid of albums (title blocks), each with optional server-side
    category filtering via ?category=. The slideshow WITHIN each album is
    plain client-side JS — no page reload needed to page through photos.
    """
    model = GalleryAlbum
    template_name = "gallery/gallery.html"
    context_object_name = "albums"
    paginate_by = 24

    def get_queryset(self):
        qs = GalleryAlbum.objects.prefetch_related("photos")
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = GalleryAlbum.CATEGORY_CHOICES
        context["active_category"] = self.request.GET.get("category", "")
        return context
