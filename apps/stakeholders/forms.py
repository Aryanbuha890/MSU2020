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
            if c not in held and c != UserProfile.StakeholderType.FOUNDATION_ADMIN
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


class NewUserRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": _INPUT}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": _INPUT}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": _INPUT}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": _INPUT}))
    batch_year = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={"class": _INPUT}))
    phone = forms.CharField(max_length=32, required=False, widget=forms.TextInput(attrs={"class": _INPUT}))
    linkedin_url = forms.URLField(required=True, label="LinkedIn profile URL", widget=forms.URLInput(attrs={"class": _INPUT}))
    desired_role_codes = forms.MultipleChoiceField(
        label="Roles desired",
        choices=UserProfile.StakeholderType.choices,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "space-y-2"}),
        required=True,
        help_text="Select roles you are interested in. You will be able to request them from your dashboard.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["desired_role_codes"].choices = [
            (c, label)
            for c, label in UserProfile.StakeholderType.choices
            if c != UserProfile.StakeholderType.FOUNDATION_ADMIN
        ]

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "An account with this email already exists. Please sign in instead."
            )
        return email

    def save(self):
        # We handle user creation in the view to log them in, 
        # or we can do it here and return the user.
        cd = self.cleaned_data
        user = User.objects.create_user(
            username=cd["email"],
            email=cd["email"],
            password=cd["password"],
            first_name=cd["first_name"],
            last_name=cd["last_name"],
        )
        
        # UserProfile is created via signal, so we just update it
        profile = user.profile
        profile.batch_year = cd.get("batch_year")
        profile.phone = cd.get("phone", "")
        profile.linkedin_url = cd["linkedin_url"]
        profile.needs_persona_assignment = True
        profile.save()

        # Create role requests for the desired roles or auto-grant them
        auto_grant_roles = []
        for role in cd["desired_role_codes"]:
            if role in (UserProfile.StakeholderType.HOD, UserProfile.StakeholderType.GOVERNANCE):
                UserRoleRequest.objects.create(
                    user=user,
                    requested_persona=role,
                    reason="Requested during registration."
                )
            else:
                auto_grant_roles.append(role)

        if auto_grant_roles:
            from apps.stakeholders.models import UserStakeholderPersona
            for role in auto_grant_roles:
                UserStakeholderPersona.objects.create(user=user, persona_type=role)
            profile.needs_persona_assignment = False
            profile.save()

        return user
