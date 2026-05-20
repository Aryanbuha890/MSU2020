from django import forms
from .models import Program, ProgramMilestone

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["title", "description", "fund_pool", "budget", "budget_currency", "start_date", "end_date", "owners"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "owners": forms.SelectMultiple(attrs={"class": "select2"}),
        }

class ProgramMilestoneForm(forms.ModelForm):
    class Meta:
        model = ProgramMilestone
        fields = ["phase", "title", "owner", "due_date", "tranche_percent", "proof"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)

    def clean_proof(self):
        f = self.cleaned_data.get("proof")
        if f and hasattr(f, 'file'):
            from apps.core.upload_security import process_upload
            from apps.projects.attachments import MAX_MILESTONE_PROOF_BYTES
            process_upload(f, self._user, "program_milestone_proof", max_bytes=MAX_MILESTONE_PROOF_BYTES)
        return f
