from django import forms


class ScoreCSVUploadForm(forms.Form):
    """
    Bulk score upload. Expected CSV columns (header row required):
        admission_number, subject, ca_score, exam_score
    One term is chosen for the whole file — every row in one upload
    belongs to the same term, since that's how a teacher/admin naturally
    works (marking one term's scores in one sitting).
    """
    term = forms.ChoiceField(label="Term")
    csv_file = forms.FileField(label="CSV File")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Term
        self.fields["term"].choices = [
            (t.id, str(t)) for t in Term.objects.select_related("session").all()
        ]

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        return f


class MasterSheetForm(forms.Form):
    term = forms.ChoiceField(label="Term")
    classroom = forms.ChoiceField(label="Class")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import ClassRoom, Term
        self.fields["term"].choices = [
            (t.id, str(t)) for t in Term.objects.select_related("session").all()
        ]
        self.fields["classroom"].choices = [
            (c.id, c.name) for c in ClassRoom.objects.all()
        ]


class ResultLookupForm(forms.Form):
    """
    Public result lookup form. Deliberately a plain Form, not a ModelForm —
    none of these fields map to a single model; validation logic lives in
    the view since it needs to check three models together (Student,
    ScratchCard, TermResult), not just field-level rules.
    """

    admission_number = forms.CharField(label="Admission Number", max_length=20)
    term = forms.ChoiceField(label="Term")
    pin = forms.CharField(label="Scratch Card PIN", max_length=12, widget=forms.PasswordInput(render_value=True))
    serial_number = forms.CharField(label="Serial Number", max_length=20)

    # Honeypot — same spam-mitigation pattern as the admissions/contact forms.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Term
        self.fields["term"].choices = [
            (t.id, str(t)) for t in Term.objects.select_related("session").all()
        ]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Submission rejected.")
        # Normalize for consistent, case-insensitive matching in the view.
        if cleaned.get("admission_number"):
            cleaned["admission_number"] = cleaned["admission_number"].strip().upper()
        if cleaned.get("serial_number"):
            cleaned["serial_number"] = cleaned["serial_number"].strip().upper()
        if cleaned.get("pin"):
            cleaned["pin"] = cleaned["pin"].strip()
        return cleaned
