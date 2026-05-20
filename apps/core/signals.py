from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from apps.needs.models import Need
from apps.projects.models import Project, Milestone
from apps.funding.models import Expense
from apps.stakeholders.models import UserRoleRequest
from apps.core.models import UploadAuditLog
from allauth.account.signals import user_signed_up
from . import notifications

@receiver(pre_save, sender=Need)
def track_need_status(sender, instance, **kwargs):
    if instance.pk:
        old = Need.objects.get(pk=instance.pk)
        instance._old_status = old.status

@receiver(post_save, sender=Need)
def handle_need_status(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        notifications.notify_need_status_change(instance, instance._old_status, instance.status, getattr(instance, 'originated_by', instance.owners.first()))

@receiver(pre_save, sender=Project)
def track_project_status(sender, instance, **kwargs):
    if instance.pk:
        old = Project.objects.get(pk=instance.pk)
        instance._old_status = old.status

@receiver(post_save, sender=Project)
def handle_project_status(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        notifications.notify_project_status_change(instance, instance._old_status, instance.status, instance.lead or instance.owners.first())

@receiver(pre_save, sender=Expense)
def track_expense_status(sender, instance, **kwargs):
    if instance.pk:
        old = Expense.objects.get(pk=instance.pk)
        instance._old_status = old.status

@receiver(post_save, sender=Expense)
def handle_expense_status(sender, instance, created, **kwargs):
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        notifications.notify_expense_status_change(instance, instance._old_status, instance.status, instance.approved_by or instance.requested_by)

@receiver(post_save, sender=UserRoleRequest)
def handle_role_request(sender, instance, created, **kwargs):
    if created:
        notifications.notify_role_request(instance)
    elif instance.status in [UserRoleRequest.Status.APPROVED, UserRoleRequest.Status.REJECTED]:
        notifications.notify_role_decision(instance)

@receiver(post_save, sender=UploadAuditLog)
def handle_upload_audit(sender, instance, created, **kwargs):
    if created and instance.scan_result == UploadAuditLog.ScanResult.FLAGGED:
        notifications.notify_upload_flagged(instance)

@receiver(user_signed_up)
def handle_google_oauth_signup(sender, request, user, **kwargs):
    # This runs when a new user signs up (e.g. via Google OAuth)
    from apps.stakeholders.models import UserProfile, Organization
    from django.contrib.auth.models import Group
    # If the user doesn't have a profile, create one
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(
            user=user, 
            stakeholder_type=UserProfile.StakeholderType.VOLUNTEER, 
            needs_persona_assignment=True
        )
