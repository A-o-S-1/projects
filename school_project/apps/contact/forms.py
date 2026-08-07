from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Honeypot field, same spam-mitigation approach as the admissions form.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "department", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Submission rejected.")
        return cleaned
