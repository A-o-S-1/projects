from django.core.exceptions import ValidationError
from django.db import models


class SchoolInfo(models.Model):
    """
    Site-wide school information (name, contact numbers, address, social
    links) used in the navbar, footer, and About page.

    Design decision: this is a *singleton* model — there is only ever one
    row — enforced in clean(). Storing this in the DB (instead of hardcoding
    it in templates/settings) lets school staff update contact details or
    social links from the Django admin without a developer touching code.
    """

    school_name = models.CharField(max_length=200, default="Mater Domini Schools")
    tagline = models.CharField(
        max_length=255,
        blank=True,
        help_text="Short phrase shown under the school name, e.g. on the homepage hero.",
    )
    address = models.CharField(max_length=255, blank=True)

    main_office_phone = models.CharField(max_length=30, blank=True)
    admissions_phone = models.CharField(max_length=30, blank=True)
    emergency_phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)

    result_portal_url = models.URLField(
        blank=True,
        help_text="Link to the Student Result Portal (Phase 2). Kept as a URL field "
        "so it can point at the new built-in portal once Phase 2 ships.",
    )

    class Meta:
        verbose_name = "School Information"
        verbose_name_plural = "School Information"

    def clean(self):
        # Enforce singleton: block saving a second row.
        if not self.pk and SchoolInfo.objects.exists():
            raise ValidationError("School Information already exists — edit the existing entry instead of creating a new one.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.school_name

    @classmethod
    def load(cls):
        """Fetch the singleton row, creating a sensible default the first time."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
