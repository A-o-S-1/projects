from django.db import models


class GalleryAlbum(models.Model):
    """
    One "title block" in the gallery, e.g. 'Cultural Day' — holds many
    GalleryPhoto entries shown as a slideshow.

    Design decision: split into Album (the title/category/caption) +
    Photo (the individual images) so a single event with many photos —
    e.g. Cultural Day — appears as ONE card the visitor pages through,
    instead of one card per photo cluttering the grid.
    """

    CATEGORY_CHOICES = [
        ("campus", "Campus"),
        ("academics", "Academics"),
        ("sports", "Sports & Activities"),
        ("events", "School Events"),
        ("spiritual", "Spiritual Life"),
    ]

    title = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="campus")
    caption = models.CharField(max_length=255, blank=True, help_text="Short description shown under the title.")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def cover_photo(self):
        return self.photos.first()

    @property
    def photo_count(self):
        return self.photos.count()


class GalleryPhoto(models.Model):
    """
    One photo within an album's slideshow. `image` is optional (blank=True)
    — same reasoning as before: lets us seed the slideshow layout with
    labeled placeholder slides before real photos exist, rather than a
    broken-image icon.
    """

    album = models.ForeignKey(GalleryAlbum, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="gallery/", blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.album.title} — photo {self.order + 1}"
