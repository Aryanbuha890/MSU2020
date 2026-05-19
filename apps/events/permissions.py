from apps.core.permissions import has_stakeholder_type, user_stakeholder_codes
from apps.stakeholders.models import UserProfile

_EVENT_MANAGERS = {
    UserProfile.StakeholderType.FOUNDATION_ADMIN,
    UserProfile.StakeholderType.GOVERNANCE,
}

_MILESTONE_VIEWERS = _EVENT_MANAGERS | {UserProfile.StakeholderType.AUDITOR}


def can_manage_events(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(user_stakeholder_codes(user) & _EVENT_MANAGERS)


def can_view_event_milestones(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(user_stakeholder_codes(user) & _MILESTONE_VIEWERS)
