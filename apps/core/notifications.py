from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

def _get_emails_for_stakeholder(stakeholder_type):
    return list(User.objects.filter(
        stakeholder_personas__persona_type=stakeholder_type,
        stakeholder_personas__is_active=True,
        profile__email_opt_in=True
    ).values_list('email', flat=True))


def notify_need_status_change(need, old_status, new_status, actor):
    if old_status == new_status: return
    subject = f"Need Status Updated: {need.title}"
    actor_name = actor.get_full_name() if actor else "System"
    message = f"Need '{need.title}' status changed from {old_status} to {new_status} by {actor_name}."
    emails = []
    if need.department:
        emails = list(User.objects.filter(
            profile__department=need.department, 
            profile__email_opt_in=True
        ).values_list('email', flat=True))
    if emails:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)

def notify_project_status_change(project, old_status, new_status, actor):
    if old_status == new_status: return
    subject = f"Project Status Updated: {project.title}"
    actor_name = actor.get_full_name() if actor else "System"
    message = f"Project '{project.title}' status changed from {old_status} to {new_status} by {actor_name}."
    emails = list(project.owners.filter(profile__email_opt_in=True).values_list('email', flat=True))
    if emails:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)

def notify_expense_status_change(expense, old_status, new_status, actor):
    if old_status == new_status: return
    subject = f"Expense Status Updated"
    message = f"Expense for '{expense.project.title}' status changed to {new_status}."
    emails = [expense.requested_by.email]
    if emails:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)

def notify_milestone_completed(milestone, actor):
    subject = f"Milestone Completed: {milestone.title}"
    message = f"Milestone '{milestone.title}' was marked complete."
    emails = list(milestone.project.owners.filter(profile__email_opt_in=True).values_list('email', flat=True))
    if emails:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)

def notify_role_request(role_request):
    subject = f"New Role Request: {role_request.user.username}"
    message = f"User {role_request.user.username} requested role {role_request.requested_persona}."
    from apps.stakeholders.models import UserProfile
    emails = _get_emails_for_stakeholder(UserProfile.StakeholderType.GOVERNANCE)
    if emails:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)

def notify_role_decision(role_request):
    subject = f"Role Request {role_request.status.title()}"
    message = f"Your request for {role_request.requested_persona} has been {role_request.status}."
    if role_request.user.profile.email_opt_in:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [role_request.user.email])

def notify_upload_flagged(audit_log):
    subject = f"Upload Flagged: {audit_log.filename}"
    message = f"File {audit_log.filename} was flagged by security scanner."
    from apps.stakeholders.models import UserProfile
    emails = _get_emails_for_stakeholder(UserProfile.StakeholderType.FOUNDATION_ADMIN)
    if emails:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, emails)
