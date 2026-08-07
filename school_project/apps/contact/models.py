from django.db import models


class ContactMessage(models.Model):
    """
    A message submitted through the public contact form.

    Design decision: the original site's contact form had a "Department"
    dropdown (Teaching, Billing, Financial Aid, Sports, Boarding,
    Conveyance) but there was no visible indication of where submissions
    actually went. Here every submission is stored and reviewable from
    the admin, and the department is kept so staff can filter/triage by
    who should handle it.
    """

    DEPARTMENT_CHOICES = [
        ("teaching", "Teaching"),
        ("billing", "Billing"),
        ("financial_aid", "Financial Aid"),
        ("sports", "Sports"),
        ("boarding", "Boarding"),
        ("conveyance", "Conveyance"),
        ("general", "General Inquiry"),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default="general")
    message = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.name} — {self.get_department_display()} ({self.submitted_at:%Y-%m-%d})"
