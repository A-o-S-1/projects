from django.db import models


class GalleryImage(models.Model):
    """
    A single photo in the public gallery.

    Design decision: `image` is optional (blank=True). This lets us seed
    the gallery's layout/filtering with placeholder entries before real
    photos exist — the template falls back to a labeled placeholder tile
    instead of a broken image icon (same pattern as staff placeholder
    avatars in Step 3).
    """

    CATEGORY_CHOICES = [
        ("campus", "Campus"),
        ("academics", "Academics"),
        ("sports", "Sports & Activities"),
        ("events", "School Events"),
        ("spiritual", "Spiritual Life"),
    ]

    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="gallery/", blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="campus")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-uploaded_at"]

    def __str__(self):
        return self.title
