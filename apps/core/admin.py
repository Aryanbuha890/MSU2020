from django.contrib import admin

from apps.core.models import UploadAuditLog

@admin.register(UploadAuditLog)
class UploadAuditLogAdmin(admin.ModelAdmin):
    list_display = ("filename", "uploader", "scan_result", "upload_type", "created_at")
    list_filter = ("scan_result", "upload_type")
    search_fields = ("filename", "uploader__username")
