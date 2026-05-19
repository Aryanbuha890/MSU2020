from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django_filters.views import FilterView

from apps.events.models import Event
from apps.funding.filters import ContributionFilter, ExpenseFilter
from apps.funding.forms import ContributionForm, ExpenseForm
from apps.funding.models import Contribution, Expense, FundPool
from apps.funding.visibility import (
    can_approve_expense,
    can_manage_expense,
    can_record_contribution,
    filter_contributions,
    filter_expenses,
)
from apps.core.currency_utils import exchange_rate_context
from apps.core.permissions import has_stakeholder_type
from apps.needs.visibility import filter_projects_for_user
from apps.projects.models import Project
from apps.stakeholders.models import UserProfile


def _fund_pool_for_project(project):
    dept = getattr(project.need, "department", None)
    if not dept:
        return None
    jmap = {
        "india": FundPool.Jurisdiction.INDIA,
        "us": FundPool.Jurisdiction.US,
    }
    fj = jmap.get(dept.jurisdiction)
    if not fj:
        return None
    return FundPool.objects.filter(jurisdiction=fj).first()


_COLLECTED_STATUSES = (
    Contribution.Status.RECEIVED,
    Contribution.Status.ALLOCATED,
    Contribution.Status.UTILIZED,
)
_ALLOCATED_EXPENSE_STATUSES = (
    Expense.Status.APPROVED,
    Expense.Status.DISBURSED,
)


def _annotate_pool_balances(pools):
    rows = []
    for pool in pools:
        collected = (
            Contribution.objects.filter(fund_pool=pool, status__in=_COLLECTED_STATUSES).aggregate(
                t=Sum("amount_usd")
            )["t"]
            or Decimal("0")
        )
        allocated = (
            Expense.objects.filter(fund_pool=pool, status__in=_ALLOCATED_EXPENSE_STATUSES).aggregate(
                t=Sum("amount_usd")
            )["t"]
            or Decimal("0")
        )
        remaining = collected - allocated
        util_pct = 0
        if collected > 0:
            util_pct = min(100, int((allocated / collected) * 100))
        if util_pct < 50:
            util_class = "progress-low"
        elif util_pct <= 80:
            util_class = "progress-mid"
        else:
            util_class = "progress-full"
        rows.append(
            {
                "pool": pool,
                "total_collected": collected,
                "total_allocated": allocated,
                "total_remaining": remaining,
                "utilization_pct": util_pct,
                "util_class": util_class,
            }
        )
    return rows


class FundPoolListView(LoginRequiredMixin, ListView):
    model = FundPool
    template_name = "funding/pool_list.html"
    context_object_name = "pool_rows"

    def get_queryset(self):
        return FundPool.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pool_rows"] = _annotate_pool_balances(self.object_list)
        return ctx


class ContributionListView(LoginRequiredMixin, FilterView):
    model = Contribution
    template_name = "funding/contribution_list.html"
    context_object_name = "contributions"
    filterset_class = ContributionFilter
    paginate_by = 25

    def get_queryset(self):
        return filter_contributions(
            Contribution.objects.select_related(
                "donor", "project", "fund_pool", "event", "volunteer_lead"
            ),
            self.request.user,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter"] = self.filterset
        params = self.request.GET.copy()
        ctx["active_filters"] = []
        if params.get("q"):
            ctx["active_filters"].append({"key": "q", "label": f'Search: "{params["q"]}"'})
        if params.get("status"):
            label = dict(Contribution.Status.choices).get(params["status"], params["status"])
            ctx["active_filters"].append({"key": "status", "label": f"Status: {label}"})
        if params.get("fund_pool"):
            pool = FundPool.objects.filter(pk=params["fund_pool"]).first()
            if pool:
                ctx["active_filters"].append({"key": "fund_pool", "label": f"Pool: {pool.name}"})
        ctx["current_order"] = params.get("order_by", "")
        return ctx


class ContributionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Contribution
    form_class = ContributionForm
    template_name = "funding/contribution_form.html"
    success_url = reverse_lazy("funding:contributions")

    def test_func(self):
        return can_record_contribution(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(exchange_rate_context())
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        pid = self.request.GET.get("project")
        if pid and str(pid).isdigit():
            proj = filter_projects_for_user(
                Project.objects.select_related("need__department"), self.request.user
            ).filter(pk=int(pid)).first()
            if proj:
                initial["project"] = proj.pk
                initial["currency"] = proj.budget_currency or "INR"
                if proj.lead_id:
                    initial["volunteer_lead"] = proj.lead_id
                dept = getattr(proj.need, "department", None)
                if dept:
                    jo = {
                        "india": Contribution.JurisdictionOrigin.INDIA,
                        "us": Contribution.JurisdictionOrigin.US,
                    }
                    initial["jurisdiction_origin"] = jo.get(
                        dept.jurisdiction, Contribution.JurisdictionOrigin.OTHER
                    )
                pool = _fund_pool_for_project(proj)
                if pool:
                    initial["fund_pool"] = pool.pk
        eid = self.request.GET.get("event")
        if eid and str(eid).isdigit() and Event.objects.filter(pk=int(eid)).exists():
            initial["event"] = int(eid)
        return initial

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        messages.success(self.request, "Contribution recorded.")
        return super().form_valid(form)


class ExpenseListView(LoginRequiredMixin, FilterView):
    model = Expense
    template_name = "funding/expense_list.html"
    context_object_name = "expenses"
    filterset_class = ExpenseFilter
    paginate_by = 25

    def get_queryset(self):
        return filter_expenses(
            Expense.objects.select_related("project", "fund_pool", "requested_by").prefetch_related(
                "owners"
            ),
            self.request.user,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter"] = self.filterset
        params = self.request.GET.copy()
        ctx["active_filters"] = []
        if params.get("q"):
            ctx["active_filters"].append({"key": "q", "label": f'Search: "{params["q"]}"'})
        if params.get("status"):
            label = dict(Expense.Status.choices).get(params["status"], params["status"])
            ctx["active_filters"].append({"key": "status", "label": f"Status: {label}"})
        if params.get("fund_pool"):
            pool = FundPool.objects.filter(pk=params["fund_pool"]).first()
            if pool:
                ctx["active_filters"].append({"key": "fund_pool", "label": f"Pool: {pool.name}"})
        ctx["current_order"] = params.get("order_by", "")
        return ctx


class ExpenseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "funding/expense_form.html"
    success_url = reverse_lazy("funding:expenses")

    def test_func(self):
        return can_manage_expense(self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        initial["expense_date"] = date.today()
        initial["owners"] = [self.request.user.pk]
        pid = self.request.GET.get("project")
        if pid and str(pid).isdigit():
            proj = filter_projects_for_user(
                Project.objects.select_related("need__department"), self.request.user
            ).filter(pk=int(pid)).first()
            if proj:
                initial["project"] = proj.pk
                initial["currency"] = proj.budget_currency or "INR"
                pool = _fund_pool_for_project(proj)
                if pool:
                    initial["fund_pool"] = pool.pk
        return initial

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["user"] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, "Expense submitted.")
        return super().form_valid(form)


def expense_approve(request, pk):
    ex = get_object_or_404(Expense, pk=pk)
    if not can_approve_expense(request.user):
        messages.error(request, "Not allowed.")
        return redirect("funding:expenses")
    if request.method != "POST":
        return redirect("funding:expenses")
    if ex.status not in ("pending", "pending_governance"):
        messages.error(request, "Invalid state.")
        return redirect("funding:expenses")
    if ex.status == "pending_governance" and not (
        request.user.is_superuser
        or has_stakeholder_type(
            request.user,
            UserProfile.StakeholderType.GOVERNANCE,
            UserProfile.StakeholderType.FOUNDATION_ADMIN,
        )
    ):
        if not request.user.is_superuser:
            messages.error(request, "Governance approval required.")
            return redirect("funding:expenses")
    ex.status = Expense.Status.APPROVED
    ex.approved_by = request.user
    ex.save()
    messages.success(request, "Expense approved.")
    return redirect("funding:expenses")


def expense_disburse(request, pk):
    ex = get_object_or_404(Expense, pk=pk)
    if not (
        request.user.is_superuser
        or has_stakeholder_type(
            request.user,
            UserProfile.StakeholderType.FOUNDATION_ADMIN,
            UserProfile.StakeholderType.FINANCE_CONTROLLER,
        )
    ):
        messages.error(request, "Not allowed.")
        return redirect("funding:expenses")
    if request.method != "POST":
        return redirect("funding:expenses")
    if ex.status != Expense.Status.APPROVED:
        messages.error(request, "Must be approved first.")
        return redirect("funding:expenses")
    ex.status = Expense.Status.DISBURSED
    ex.save()
    messages.success(request, "Marked disbursed.")
    return redirect("funding:expenses")
