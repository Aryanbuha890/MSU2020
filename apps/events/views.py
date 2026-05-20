from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.permissions import user_stakeholder_codes
from apps.events.forms import EventForm, EventMilestoneForm
from apps.events.models import Event, EventMilestone
from apps.events.permissions import can_manage_events, can_view_event_milestones
from apps.events.state_machine import allowed_event_next, transition_label
from apps.funding.visibility import can_record_contribution
from apps.stakeholders.models import UserProfile

User = get_user_model()


class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        qs = Event.objects.select_related(
            "organized_by", "linked_project", "linked_need", "fund_pool"
        ).prefetch_related("media_items")
        codes = user_stakeholder_codes(self.request.user)
        if self.request.user.is_superuser or codes & {
            UserProfile.StakeholderType.FOUNDATION_ADMIN,
            UserProfile.StakeholderType.FINANCE_CONTROLLER,
            UserProfile.StakeholderType.GOVERNANCE,
            UserProfile.StakeholderType.AUDITOR,
        }:
            return qs
        return qs.filter(
            status__in=[
                Event.Status.PUBLISHED,
                Event.Status.REGISTRATION_OPEN,
                Event.Status.ONGOING,
                Event.Status.COMPLETED,
                Event.Status.ARCHIVED,
                Event.Status.GOVERNANCE_APPROVED,
            ]
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_create_event"] = can_manage_events(self.request.user)
        return ctx


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.select_related(
            "organized_by", "linked_project", "linked_need", "fund_pool"
        ).prefetch_related(
            "media_items__uploaded_by",
            "registrations__user",
            "milestones__owner",
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        codes = user_stakeholder_codes(self.request.user)
        if self.request.user.is_superuser or codes & {
            UserProfile.StakeholderType.FOUNDATION_ADMIN,
            UserProfile.StakeholderType.FINANCE_CONTROLLER,
            UserProfile.StakeholderType.GOVERNANCE,
            UserProfile.StakeholderType.AUDITOR,
        }:
            return obj
        if obj.status == Event.Status.DRAFT:
            raise Http404()
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        event = self.object
        ctx["can_prefill_contribution"] = can_record_contribution(self.request.user)
        ctx["can_manage_event"] = can_manage_events(self.request.user)
        ctx["can_view_milestones"] = can_view_event_milestones(self.request.user)
        ctx["can_manage_milestones"] = can_manage_events(self.request.user)
        milestones = list(event.milestones.all())
        ctx["event_milestones"] = milestones
        total = len(milestones)
        done = sum(1 for m in milestones if m.completed)
        ctx["milestone_done_count"] = done
        ctx["milestone_total_count"] = total
        ctx["milestone_progress_pct"] = int((done / total) * 100) if total else 0
        nxt = allowed_event_next(event.status)
        ctx["allowed_transitions"] = [
            {"status": s, "label": transition_label(event.status, s)} for s in sorted(nxt)
        ]
        ctx["workflow_steps"] = [
            Event.Status.DRAFT,
            Event.Status.GOVERNANCE_APPROVED,
            Event.Status.PUBLISHED,
            Event.Status.COMPLETED,
        ]
        return ctx


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        return can_manage_events(self.request.user)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def get_success_url(self):
        return reverse("events:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Event created.")
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        return can_manage_events(self.request.user)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def get_success_url(self):
        return reverse("events:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Event updated.")
        return super().form_valid(form)


def event_transition(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_manage_events(request.user):
        messages.error(request, "Not allowed.")
        return redirect("events:detail", pk=pk)
    if request.method != "POST":
        return redirect("events:detail", pk=pk)
    nxt = request.POST.get("next_status")
    if nxt not in allowed_event_next(event.status):
        messages.error(request, "Invalid transition.")
        return redirect("events:detail", pk=pk)
    event.status = nxt
    event.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Event status updated to {event.get_status_display()}.")
    return redirect("events:detail", pk=pk)


class EventMilestoneCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = EventMilestone
    form_class = EventMilestoneForm
    template_name = "events/event_milestone_form.html"

    def test_func(self):
        return can_manage_events(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs["event_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["event"] = self.event
        return kw

    def form_valid(self, form):
        form.instance.event = self.event
        messages.success(self.request, "Milestone added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("events:detail", kwargs={"pk": self.event.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["event"] = self.event
        return ctx


class EventMilestoneUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EventMilestone
    form_class = EventMilestoneForm
    template_name = "events/event_milestone_form.html"
    pk_url_kwarg = "milestone_id"

    def test_func(self):
        return can_manage_events(self.request.user)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["event"] = self.object.event
        return kw

    def get_success_url(self):
        return reverse("events:detail", kwargs={"pk": self.object.event_id})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["event"] = self.object.event
        return ctx


def event_milestone_complete(request, event_id, milestone_id):
    event = get_object_or_404(Event, pk=event_id)
    ms = get_object_or_404(EventMilestone, pk=milestone_id, event=event)
    if not can_manage_events(request.user):
        messages.error(request, "Not allowed.")
        return redirect("events:detail", pk=event_id)
    if request.method != "POST":
        return redirect("events:detail", pk=event_id)
    proof = request.FILES.get("proof")
    if proof:
        from apps.core.upload_security import process_upload
        from django.core.exceptions import ValidationError
        try:
            process_upload(proof, request.user, "event_milestone_proof")
        except ValidationError as e:
            messages.error(request, str(e.message) if hasattr(e, 'message') else str(e))
            return redirect("events:detail", pk=event_id)
        ms.proof = proof
        ms.proof_original_filename = proof.name
    ms.completed = True
    ms.completed_date = timezone.localdate()
    ms.save()
    messages.success(request, "Milestone marked complete.")
    return redirect("events:detail", pk=event_id)
