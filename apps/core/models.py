from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UploadAuditLog(TimeStampedModel):
    class ScanResult(models.TextChoices):
        CLEAN = "clean", "Clean"
        FLAGGED = "flagged", "Flagged"
        SKIPPED = "skipped", "Skipped"
        ERROR = "error", "Error"

    class UploadType(models.TextChoices):
        CSV = "csv", "CSV"
        DOCUMENT = "document", "Document"
        PHOTO = "photo", "Photo"
        PROOF = "proof", "Proof"

    class ActionTaken(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        QUARANTINED = "quarantined", "Quarantined"

    uploader = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, related_name="upload_audit_logs"
    )
    filename = models.CharField(max_length=512)
    file_size = models.PositiveIntegerField()
    declared_mime = models.CharField(max_length=255, blank=True)
    actual_mime = models.CharField(max_length=255, blank=True)
    scan_result = models.CharField(max_length=32, choices=ScanResult.choices, default=ScanResult.CLEAN)
    scan_detail = models.TextField(blank=True)
    upload_type = models.CharField(max_length=32, choices=UploadType.choices)
    action_taken = models.CharField(max_length=32, choices=ActionTaken.choices)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.get_scan_result_display()})"
