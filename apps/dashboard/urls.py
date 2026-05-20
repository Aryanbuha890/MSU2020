from django.urls import path

from apps.dashboard import views
from apps.core import views as core_views

app_name = "dashboard"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("projects/rollup/", views.ProjectRollupView.as_view(), name="project_rollup"),
    path("governance/queue/", views.GovernanceQueueView.as_view(), name="governance_queue"),
    path(
        "governance/profiles/upload/",
        views.governance_profile_bulk_upload,
        name="governance_profile_bulk_upload",
    ),
    path(
        "governance/profiles/sample.csv",
        views.governance_profile_sample_csv,
        name="governance_profile_sample_csv",
    ),
    path(
        "governance/profiles/confirm/",
        views.governance_csv_confirm,
        name="governance_csv_confirm",
    ),
    path("switch-role/", views.switch_role, name="switch_role"),
    path("toggle-currency/", views.toggle_currency, name="toggle_currency"),
    path("audit/uploads/", core_views.UploadAuditLogListView.as_view(), name="upload_audit_log"),
    path("audit/trail/", core_views.AuditTrailView.as_view(), name="audit_trail"),
    path("audit/trail/export/", core_views.export_audit_trail_csv, name="export_audit_trail_csv"),
]
