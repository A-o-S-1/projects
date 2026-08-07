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


class AboutPage(models.Model):
    """
    Singleton content for the About page: history, mission, vision.

    Design decision: the live site repeated its "administrator's welcome"
    message verbatim on both Home and About. Here it's stored once
    (administrator_message) and each page decides for itself whether to
    show it — no copy-paste duplication to keep in sync by hand.
    """

    history = models.TextField(
        blank=True,
        help_text="The school's founding story and background.",
    )
    mission = models.TextField(blank=True)
    vision = models.TextField(blank=True)

    administrator_name = models.CharField(max_length=150, blank=True)
    administrator_title = models.CharField(max_length=150, blank=True, default="School Administrator")
    administrator_message = models.TextField(blank=True)
    administrator_photo = models.ImageField(upload_to="about/", blank=True, null=True)

    class Meta:
        verbose_name = "About Page"
        verbose_name_plural = "About Page"

    def clean(self):
        if not self.pk and AboutPage.objects.exists():
            raise ValidationError("About Page content already exists — edit the existing entry instead.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "About Page content"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class CoreValue(models.Model):
    """
    One item in the school's list of core values (shown on the About page).

    Modeled as its own table rather than a fixed set of fields on AboutPage
    so staff can add/reorder/remove values from the admin without a
    developer changing the schema every time the list changes.
    """

    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first.")

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title


class AdmissionsPage(models.Model):
    """Singleton content for the Admissions page: intro copy and requirements."""

    intro = models.TextField(blank=True)
    requirements = models.TextField(
        blank=True,
        help_text="Documents/requirements needed to apply, one per line.",
    )

    class Meta:
        verbose_name = "Admissions Page"
        verbose_name_plural = "Admissions Page"

    def clean(self):
        if not self.pk and AdmissionsPage.objects.exists():
            raise ValidationError("Admissions Page content already exists — edit the existing entry instead.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "Admissions Page content"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def requirements_list(self):
        """Split the free-text requirements field into a clean list for template rendering."""
        return [line.strip() for line in self.requirements.splitlines() if line.strip()]


class AdmissionStep(models.Model):
    """One step in the admissions process (e.g. '1. Submit inquiry', '2. School visit')."""

    title = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class AdmissionInquiry(models.Model):
    """
    A parent/guardian's admission inquiry submitted through the public form.

    This replaces the original site's dead "Enroll Now" link (which pointed
    to '#') with an actual working inquiry pipeline that staff can review
    from the admin.
    """

    LEVEL_CHOICES = [
        ("creche", "Creche"),
        ("nursery", "Nursery"),
        ("primary", "Primary"),
        ("jss", "Junior Secondary"),
        ("sss", "Senior Secondary"),
    ]

    parent_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    child_name = models.CharField(max_length=150)
    level_applying_for = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    message = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False, help_text="Marked once office staff have followed up.")

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name_plural = "Admission Inquiries"

    def __str__(self):
        return f"{self.child_name} ({self.get_level_applying_for_display()}) — {self.parent_name}"
