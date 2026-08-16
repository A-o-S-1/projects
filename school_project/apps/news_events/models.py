from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class PublishedManager(models.Manager):
    """Returns only is_published=True rows — used by every public-facing view
    so a draft post/event can never accidentally leak onto the live site."""
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class NewsPost(models.Model):
    """A news article shown on the News page and previewed on the homepage."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.CharField(
        max_length=300,
        help_text="Short summary shown in listings and the homepage preview.",
    )
    body = models.TextField()
    cover_image = models.ImageField(upload_to="news/", blank=True, null=True)
    published_date = models.DateField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()       # default manager — admin sees everything, drafts included
    published = PublishedManager()   # public views use this one

    class Meta:
        ordering = ["-published_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news_events:news_detail", kwargs={"slug": self.slug})


class Event(models.Model):
    """A school event shown on the Events page, split into upcoming/past by start_datetime."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    cover_image = models.ImageField(upload_to="events/", blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:220]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news_events:event_detail", kwargs={"slug": self.slug})

    @property
    def is_past(self):
        return self.start_datetime < timezone.now()
