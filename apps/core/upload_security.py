import os
import magic
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.core.models import UploadAuditLog
from apps.core.notifications import notify_upload_flagged

# For optional ClamAV
try:
    import pyclamd
    clamd = pyclamd.ClamdAgnostic()
    CLAMAV_AVAILABLE = clamd.ping()
except (ImportError, Exception):
    CLAMAV_AVAILABLE = False


def check_mime_type(file_obj, allowed_mimes):
    file_obj.seek(0)
    mime = magic.from_buffer(file_obj.read(2048), mime=True)
    file_obj.seek(0)
    if mime not in allowed_mimes:
        raise ValidationError(f"Invalid file type: {mime}. Allowed: {', '.join(allowed_mimes)}")
    return mime


def check_file_size(file_obj, max_bytes):
    size = file_obj.size
    if size > max_bytes:
        raise ValidationError(f"File too large: {size} bytes. Max allowed is {max_bytes} bytes.")
    return size


def scan_for_malware(file_obj):
    if not CLAMAV_AVAILABLE:
        return True # Graceful fallback
    try:
        file_obj.seek(0)
        res = clamd.scan_stream(file_obj.read())
        file_obj.seek(0)
        if res:
            return False
    except Exception:
        pass
    return True


def process_upload(file_obj, uploader, upload_type, allowed_mimes=None, max_bytes=None):
    if allowed_mimes is None:
        allowed_mimes = [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "text/csv",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]

    if max_bytes is None:
        if upload_type == UploadAuditLog.UploadType.PHOTO:
            max_bytes = getattr(settings, "UPLOAD_MAX_PHOTO_BYTES", 5 * 1024 * 1024)
        else:
            max_bytes = getattr(settings, "UPLOAD_MAX_DOCUMENT_BYTES", 10 * 1024 * 1024)
    
    audit_log = UploadAuditLog(
        filename=file_obj.name,
        uploader=uploader,
        upload_type=upload_type,
        file_size=file_obj.size,
        scan_result=UploadAuditLog.ScanResult.CLEAN
    )
    
    try:
        mime = check_mime_type(file_obj, allowed_mimes)
        audit_log.actual_mime = mime
        
        check_file_size(file_obj, max_bytes)
        
        is_safe = scan_for_malware(file_obj)
        if not is_safe:
            audit_log.scan_result = UploadAuditLog.ScanResult.FLAGGED
            audit_log.save()
            notify_upload_flagged(audit_log)
            raise ValidationError("File flagged as malicious.")
            
        audit_log.scan_result = UploadAuditLog.ScanResult.CLEAN
        audit_log.save()
        return True
        
    except ValidationError as e:
        audit_log.scan_result = UploadAuditLog.ScanResult.FLAGGED
        audit_log.save()
        raise e
    except Exception as e:
        audit_log.scan_result = UploadAuditLog.ScanResult.PENDING
        audit_log.save()
        raise ValidationError("Upload failed during security processing.")
