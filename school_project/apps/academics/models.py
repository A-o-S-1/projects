from django.core.exceptions import ValidationError
from django.db import models


class AcademicsPage(models.Model):
    """
    Singleton intro copy for the Academics page — explains the school's
    overall academic structure before listing departments/subjects.
    The live site had no Academics content at all; this replaces that gap.
    """

    intro = models.TextField(blank=True)
    junior_secondary_overview = models.TextField(
        blank=True,
        help_text="Explains the JSS1–JSS3 curriculum structure to prospective parents.",
    )
    senior_secondary_overview = models.TextField(
        blank=True,
        help_text="Explains SS1–SS3 and the subject tracks (Science/Arts/Commercial).",
    )

    class Meta:
        verbose_name = "Academics Page"
        verbose_name_plural = "Academics Page"

    def clean(self):
        if not self.pk and AcademicsPage.objects.exists():
            raise ValidationError("Academics Page content already exists — edit the existing entry instead.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "Academics Page content"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Department(models.Model):
    """
    An academic department (e.g. Sciences, Languages). Subjects belong to
    a department so the Academics page can group them meaningfully instead
    of showing one long flat subject list.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    """
    A single subject taught at the school.

    `level` and `track` together capture how Nigerian secondary curricula
    actually work: every subject is taught at Junior Secondary (JSS1–3) or
    Senior Secondary (SS1–3); senior subjects are further split into a
    shared "core" (compulsory for everyone) plus elective subjects specific
    to a student's chosen track (Science, Arts, or Commercial).
    """

    LEVEL_CHOICES = [
        ("junior", "Junior Secondary (JSS1–JSS3)"),
        ("senior", "Senior Secondary (SS1–SS3)"),
    ]
    TRACK_CHOICES = [
        ("", "— Not applicable —"),
        ("core", "Core (all senior students)"),
        ("science", "Science Track"),
        ("arts", "Arts Track"),
        ("commercial", "Commercial Track"),
    ]

    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subjects")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    track = models.CharField(
        max_length=12,
        choices=TRACK_CHOICES,
        blank=True,
        help_text="Only relevant for Senior Secondary subjects.",
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["department__order", "level", "track", "name"]

    def clean(self):
        if self.level == "junior" and self.track:
            raise ValidationError("Junior Secondary subjects shouldn't have a track — tracks only apply to Senior Secondary.")
        if self.level == "senior" and not self.track:
            raise ValidationError("Senior Secondary subjects need a track (Core, Science, Arts, or Commercial).")

    def __str__(self):
        return self.name
