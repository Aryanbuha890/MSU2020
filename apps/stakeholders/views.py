from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, FormView, TemplateView, UpdateView

from apps.core.permissions import has_stakeholder_type, user_stakeholder_codes
from apps.stakeholders.activity import recent_activity_for_user
from apps.stakeholders.forms import NewUserRegistrationForm, RoleRequestForm, UserNameForm, UserProfileForm
from apps.stakeholders.models import UserProfile, UserRoleRequest
from apps.stakeholders.persona_utils import replace_user_personas


class NewUserRegistrationView(FormView):
    template_name = "stakeholders/new_user_register.html"
    form_class = NewUserRegistrationForm
    success_url = reverse_lazy("stakeholders:new_user_register_done")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            "Thank you. Your registration request was submitted. Our team will review it and contact you at the email you provided.",
        )
        return super().form_valid(form)


class NewUserRegistrationDoneView(TemplateView):
    template_name = "stakeholders/new_user_register_done.html"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "stakeholders/profile_form.html"
    success_url = reverse_lazy("stakeholders:profile")

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        prof = u.profile
        ctx["user_form"] = UserNameForm(instance=u)
        ctx["persona_codes"] = sorted(prof.persona_codes())
        ctx["persona_labels"] = [
            dict(UserProfile.StakeholderType.choices).get(c, c) for c in ctx["persona_codes"]
        ]
        ctx["member_since"] = u.date_joined
        ctx["recent_activity"] = recent_activity_for_user(u, limit=10)
        ctx["pending_role_requests"] = UserRoleRequest.objects.filter(
            user=u, status=UserRoleRequest.Status.PENDING
        )
        ctx["held_personas"] = prof.persona_codes()
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        profile_form = UserProfileForm(request.POST, request.FILES, instance=self.object)
        user_form = UserNameForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, "Profile updated.")
            return redirect(self.success_url)
        return self.render_to_response(
            self.get_context_data(form=profile_form, user_form=user_form)
        )


class RoleRequestListView(LoginRequiredMixin, TemplateView):
    template_name = "stakeholders/role_request_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_requests"] = UserRoleRequest.objects.filter(user=self.request.user).select_related(
            "reviewed_by"
        )
        return ctx


class RoleRequestCreateView(LoginRequiredMixin, CreateView):
    model = UserRoleRequest
    form_class = RoleRequestForm
    template_name = "stakeholders/role_request_form.html"
    success_url = reverse_lazy("stakeholders:profile")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(
            self.request,
            "Request submitted. You'll be notified when reviewed.",
        )
        return super().form_valid(form)


def _can_review_role_requests(user):
    return user.is_superuser or has_stakeholder_type(
        user,
        UserProfile.StakeholderType.GOVERNANCE,
        UserProfile.StakeholderType.FOUNDATION_ADMIN,
    )


def role_request_approve(request, pk):
    if not request.user.is_authenticated or not _can_review_role_requests(request.user):
        messages.error(request, "Not allowed.")
        return redirect("dashboard:governance_queue")
    if request.method != "POST":
        return redirect("dashboard:governance_queue")
    req = get_object_or_404(UserRoleRequest, pk=pk, status=UserRoleRequest.Status.PENDING)
    if req.requested_persona == UserProfile.StakeholderType.FOUNDATION_ADMIN:
        codes = user_stakeholder_codes(request.user)
        if not request.user.is_superuser and UserProfile.StakeholderType.FOUNDATION_ADMIN not in codes:
            messages.error(request, "Only Foundation Admin can approve that role.")
            return redirect("dashboard:governance_queue")
    personas = list(req.user.profile.persona_codes())
    if req.requested_persona not in personas:
        personas.append(req.requested_persona)
    replace_user_personas(req.user, personas)
    req.status = UserRoleRequest.Status.APPROVED
    req.reviewed_by = request.user
    req.reviewed_at = timezone.now()
    req.save()
    messages.success(request, f"Approved {req.get_requested_persona_display()} for {req.user.username}.")
    return redirect("dashboard:governance_queue")


def role_request_reject(request, pk):
    if not request.user.is_authenticated or not _can_review_role_requests(request.user):
        messages.error(request, "Not allowed.")
        return redirect("dashboard:governance_queue")
    if request.method != "POST":
        return redirect("dashboard:governance_queue")
    req = get_object_or_404(UserRoleRequest, pk=pk, status=UserRoleRequest.Status.PENDING)
    req.status = UserRoleRequest.Status.REJECTED
    req.reviewed_by = request.user
    req.reviewed_at = timezone.now()
    req.review_notes = (request.POST.get("reason") or "").strip()
    req.save()
    messages.success(request, f"Rejected role request for {req.user.username}.")
    return redirect("dashboard:governance_queue")
