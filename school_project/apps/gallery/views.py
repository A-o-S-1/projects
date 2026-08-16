from django.views.generic import ListView

from .models import GalleryImage


class GalleryView(ListView):
    """
    Gallery grid with optional server-side category filtering via ?category=.
    No JS filtering — keeps the page working even with JS disabled/slow
    connections, which matters for a school site accessed on varied devices.
    """
    model = GalleryImage
    template_name = "gallery/gallery.html"
    context_object_name = "images"
    paginate_by = 24

    def get_queryset(self):
        qs = GalleryImage.objects.all()
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = GalleryImage.CATEGORY_CHOICES
        context["active_category"] = self.request.GET.get("category", "")
        return context
