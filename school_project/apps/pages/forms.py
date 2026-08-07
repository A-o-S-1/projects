from django import forms

from .models import AdmissionInquiry


class AdmissionInquiryForm(forms.ModelForm):
    """
    Public admission inquiry form. Uses a ModelForm so validation rules
    stay defined once, on the model — the form doesn't duplicate them.
    """

    # Honeypot field: real visitors never see or fill this (hidden via CSS),
    # but simple spam bots that auto-fill every field will. If it's
    # non-empty on submit, we silently drop the submission. This is a
    # zero-dependency alternative to a CAPTCHA for a low-traffic school site.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = AdmissionInquiry
        fields = ["parent_name", "phone", "email", "child_name", "level_applying_for", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Submission rejected.")
        return cleaned
