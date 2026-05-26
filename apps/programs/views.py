from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Program, ProgramMilestone
from .forms import ProgramForm, ProgramMilestoneForm
from .visibility import can_manage_program, filter_programs_for_user

class ProgramAccessMixin(UserPassesTestMixin):
    def test_func(self):
        program = None
        if hasattr(self, 'get_object'):
            try:
                program = self.get_object()
            except AttributeError:
                pass
        return can_manage_program(self.request.user, program)


class ProgramListView(LoginRequiredMixin, ListView):
    model = Program
    template_name = "programs/program_list.html"
    context_object_name = "programs"

    def get_queryset(self):
        qs = super().get_queryset()
        return filter_programs_for_user(qs, self.request.user)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_create"] = can_manage_program(self.request.user)
        return ctx


class ProgramDetailView(LoginRequiredMixin, DetailView):
    model = Program
    template_name = "programs/program_detail.html"
    context_object_name = "program"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_manage"] = can_manage_program(self.request.user, self.object)
        ctx["milestones"] = self.object.milestones.all()
        return ctx


class ProgramCreateView(LoginRequiredMixin, ProgramAccessMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = "programs/program_form.html"
    
    def form_valid(self, form):
        form.instance.originated_by = self.request.user
        messages.success(self.request, "Program created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("programs:detail", kwargs={"pk": self.object.pk})


class ProgramUpdateView(LoginRequiredMixin, ProgramAccessMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = "programs/program_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Program updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("programs:detail", kwargs={"pk": self.object.pk})


class ProgramMilestoneCreateView(LoginRequiredMixin, ProgramAccessMixin, CreateView):
    model = ProgramMilestone
    form_class = ProgramMilestoneForm
    template_name = "programs/program_milestone_form.html"

    def get_program(self):
        return get_object_or_404(Program, pk=self.kwargs["program_id"])

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def test_func(self):
        return can_manage_program(self.request.user, self.get_program())

    def form_valid(self, form):
        form.instance.program = self.get_program()
        messages.success(self.request, "Milestone added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("programs:detail", kwargs={"pk": self.kwargs["program_id"]})


class ProgramMilestoneUpdateView(LoginRequiredMixin, ProgramAccessMixin, UpdateView):
    model = ProgramMilestone
    form_class = ProgramMilestoneForm
    template_name = "programs/program_milestone_form.html"

    def test_func(self):
        milestone = self.get_object()
        return can_manage_program(self.request.user, milestone.program)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, "Milestone updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("programs:detail", kwargs={"pk": self.object.program_id})


@login_required
@require_POST
def program_milestone_tranche_release(request, pk):
    milestone = get_object_or_404(ProgramMilestone, pk=pk)
    if not can_manage_program(request.user, milestone.program):
        raise PermissionDenied

    milestone.tranche_governance_status = "released"
    milestone.save()
    messages.success(request, f"Tranche released for {milestone.title}.")
    return redirect("programs:detail", pk=milestone.program_id)
