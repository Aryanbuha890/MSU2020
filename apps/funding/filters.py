import django_filters
from django.db.models import Q

from apps.funding.models import Contribution, Expense, FundPool


class ContributionFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_search", label="Search")
    status = django_filters.ChoiceFilter(choices=Contribution.Status.choices)
    fund_pool = django_filters.ModelChoiceFilter(queryset=FundPool.objects.all())

    order_by = django_filters.OrderingFilter(
        fields=(
            ("donor__username", "donor"),
            ("amount_usd", "amount"),
            ("status", "status"),
            ("pledge_date", "pledge"),
            ("received_date", "received"),
            ("created_at", "created"),
        ),
        field_labels={
            "donor": "Donor",
            "amount": "USD amount",
            "status": "Status",
            "pledge": "Pledge date",
            "received": "Received date",
            "created": "Created",
        },
    )

    class Meta:
        model = Contribution
        fields = ["status", "fund_pool"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        term = value.strip()
        return queryset.filter(
            Q(donor__username__icontains=term)
            | Q(donor__first_name__icontains=term)
            | Q(donor__last_name__icontains=term)
            | Q(project__title__icontains=term)
            | Q(event__title__icontains=term)
        )


class ExpenseFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_search", label="Search")
    status = django_filters.ChoiceFilter(choices=Expense.Status.choices)
    fund_pool = django_filters.ModelChoiceFilter(queryset=FundPool.objects.all())
    project = django_filters.NumberFilter(field_name="project_id")

    order_by = django_filters.OrderingFilter(
        fields=(
            ("project__title", "project"),
            ("amount", "amount"),
            ("status", "status"),
            ("expense_date", "date"),
            ("created_at", "created"),
        ),
    )

    class Meta:
        model = Expense
        fields = ["status", "fund_pool", "project"]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        term = value.strip()
        return queryset.filter(
            Q(project__title__icontains=term)
            | Q(requested_by__username__icontains=term)
            | Q(description__icontains=term)
        )
