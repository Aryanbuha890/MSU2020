from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.http import Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

User = get_user_model()


@require_POST
def demo_login(request):
    """One-click demo user — only when DEBUG (never expose in production)."""
    if not settings.DEBUG:
        raise Http404()
    user = User.objects.filter(username="demo").first()
    if not user:
        messages.error(
            request,
            'No demo user yet. Run: python manage.py load_demo_data',
        )
        return redirect("account_login")
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("dashboard:home")


import csv
from django.http import HttpResponse
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.permissions import has_stakeholder_type
from apps.stakeholders.models import UserProfile
from apps.projects.models import Project
from apps.core.models import UploadAuditLog


class AuditTrailView(LoginRequiredMixin, TemplateView):
    template_name = "core/audit_trail.html"

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or has_stakeholder_type(request.user, UserProfile.StakeholderType.FOUNDATION_ADMIN)):
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project_history"] = Project.history.all()[:50]
        return ctx


def export_audit_trail_csv(request):
    if not (request.user.is_superuser or has_stakeholder_type(request.user, UserProfile.StakeholderType.FOUNDATION_ADMIN)):
        return redirect("dashboard:home")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_trail.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'User', 'Action', 'Object'])
    for record in Project.history.all()[:500]:
        writer.writerow([record.history_date, getattr(record.history_user, 'username', 'System'), record.history_type, record.title])
    return response


class UploadAuditLogListView(LoginRequiredMixin, ListView):
    model = UploadAuditLog
    template_name = "core/upload_audit_log.html"
    context_object_name = "audit_entries"

    def dispatch(self, request, *args, **kwargs):
        if not (
            request.user.is_superuser
            or has_stakeholder_type(
                request.user,
                UserProfile.StakeholderType.FOUNDATION_ADMIN,
                UserProfile.StakeholderType.GOVERNANCE,
                UserProfile.StakeholderType.AUDITOR,
            )
        ):
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        u = self.request.user
        ctx["read_only"] = not (
            u.is_superuser or has_stakeholder_type(u, UserProfile.StakeholderType.FOUNDATION_ADMIN)
        )
        return ctx
