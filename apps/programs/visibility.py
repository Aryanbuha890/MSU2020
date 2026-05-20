from apps.stakeholders.models import UserProfile

def can_manage_program(user, program=None):
    if not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    if not hasattr(user, "profile"):
        return False
    
    codes = user.profile.persona_codes()
    # Governance + Foundation Admin only can create/manage everything
    if UserProfile.StakeholderType.GOVERNANCE in codes or UserProfile.StakeholderType.FOUNDATION_ADMIN in codes:
        return True
    
    # Program Manager persona: full edit on assigned programs only
    if UserProfile.StakeholderType.PROGRAM_MANAGER in codes:
        if program and program.owners.filter(id=user.id).exists():
            return True
        
    return False

def filter_programs_for_user(qs, user):
    """Full for Gov/Admin, read-only for others."""
    # Since read-only for others, everyone can *see* all programs in the list.
    # We will just return the full queryset here. The view can use can_manage_program to toggle buttons.
    return qs
