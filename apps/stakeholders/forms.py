from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.stakeholders.models import PendingUserRegistration, UserProfile, UserRoleRequest

User = get_user_model()

_INPUT = "mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"


class UserNameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": _INPUT}),
            "last_name": forms.TextInput(attrs={"class": _INPUT}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "photo",
            "batch_year",
            "department",
            "phone",
            "linkedin_url",
            "bio",
            "organization",
            "jurisdiction",
            "email_opt_in",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"class": _INPUT, "rows": 4}),
            "department": forms.TextInput(attrs={"class": _INPUT}),
            "phone": forms.TextInput(attrs={"class": _INPUT}),
            "linkedin_url": forms.URLInput(attrs={"class": _INPUT}),
            "batch_year": forms.NumberInput(attrs={"class": _INPUT}),
            "email_opt_in": forms.CheckboxInput(attrs={"class": "rounded border-slate-300"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        y = date.today().year
        self.fields["batch_year"].required = False
        if self.fields.get("organization"):
            self.fields["organization"].widget.attrs["class"] = _INPUT
        if self.fields.get("jurisdiction"):
            self.fields["jurisdiction"].widget.attrs["class"] = _INPUT


class RoleRequestForm(forms.ModelForm):
    class Meta:
        model = UserRoleRequest
        fields = ["requested_persona", "reason"]
        widgets = {
            "requested_persona": forms.Select(attrs={"class": _INPUT}),
            "reason": forms.Textarea(attrs={"class": _INPUT, "rows": 4, "placeholder": "Why do you need this role?"}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        held = user.profile.persona_codes() if hasattr(user, "profile") else set()
        choices = [
            (c, label)
            for c, label in UserProfile.StakeholderType.choices
            if c not in held
        ]
        self.fields["requested_persona"].choices = [("", "Select a role…"), *choices]
        self.user = user

    def clean_requested_persona(self):
        persona = self.cleaned_data.get("requested_persona")
        if not persona:
            raise ValidationError("Select a role to request.")
        if persona in self.user.profile.persona_codes():
            raise ValidationError("You already have this role.")
        if UserRoleRequest.objects.filter(
            user=self.user,
            requested_persona=persona,
            status=UserRoleRequest.Status.PENDING,
        ).exists():
            raise ValidationError("You already have a pending request for this role.")
        return persona


class NewUserRegistrationForm(forms.ModelForm):
    desired_role_codes = forms.MultipleChoiceField(
        label="Roles desired",
        choices=UserProfile.StakeholderType.choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select all that apply. The team will review and assign appropriate access.",
    )

    class Meta:
        model = PendingUserRegistration
        fields = ["full_name", "email", "batch_year", "phone", "address", "linkedin_url"]
        labels = {
            "full_name": "Full name",
            "email": "Email",
            "batch_year": "Batch (year passed out)",
            "phone": "Contact phone",
            "address": "Address",
            "linkedin_url": "LinkedIn profile URL (optional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        y = date.today().year
        self.fields["batch_year"].min_value = 1950
        self.fields["batch_year"].max_value = y + 6
        self.fields["batch_year"].widget.attrs.setdefault("placeholder", str(y - 10))
        self.fields["address"].widget.attrs.setdefault("rows", 3)
        self.fields["desired_role_codes"].widget.attrs.setdefault("class", "space-y-2")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "An account with this email already exists. Please sign in instead."
            )
        if PendingUserRegistration.objects.filter(
            email__iexact=email, status=PendingUserRegistration.Status.PENDING
        ).exists():
            raise ValidationError(
                "We already have a pending application for this email. We will contact you soon."
            )
        return email

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.desired_roles = list(self.cleaned_data["desired_role_codes"])
        obj.status = PendingUserRegistration.Status.PENDING
        if commit:
            obj.save()
        return obj
