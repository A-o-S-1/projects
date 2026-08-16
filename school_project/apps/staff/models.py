from django.db import models


class StaffMember(models.Model):
    """
    A single staff member — teaching, non-teaching, or management.

    Design decision: one model with a `category` field, not separate
    Management/Teacher models. Staff Directory and Management Profiles
    (two distinct nav items per the project brief) are just two filtered
    views over this same table — same fields, same admin workflow, less
    duplication than maintaining parallel schemas for what is structurally
    the same kind of record.
    """

    CATEGORY_CHOICES = [
        ("management", "Management"),
        ("teaching", "Teaching Staff"),
        ("non_teaching", "Non-Teaching Staff"),
    ]

    full_name = models.CharField(max_length=150)
    role_title = models.CharField(max_length=150, help_text="e.g. 'Vice Principal (Academics)', 'Mathematics Teacher'.")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    department = models.ForeignKey(
        "academics.Department",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="staff_members",
        help_text="Optional — mainly relevant for teaching staff.",
    )
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="staff/", blank=True, null=True)
    email = models.EmailField(blank=True)

    order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first within their category.")
    is_published = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this profile from the public site without deleting it.",
    )

    class Meta:
        ordering = ["category", "order", "full_name"]

    def __str__(self):
        return f"{self.full_name} — {self.role_title}"

    @property
    def initials(self):
        """
        Initials shown in the placeholder avatar when no photo is set.
        Strips non-letter characters first (our seed data uses bracketed
        placeholder names like "[Placeholder Teacher]") and falls back to
        "?" if nothing usable is left, rather than surfacing punctuation.
        """
        letters_only = "".join(ch for ch in self.full_name if ch.isalpha() or ch.isspace())
        words = letters_only.split()
        if not words:
            return "?"
        if len(words) == 1:
            return words[0][:2].upper()
        return (words[0][0] + words[1][0]).upper()
