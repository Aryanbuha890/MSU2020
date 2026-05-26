"""Per-persona navigation matrix (Doc 4 §2)."""

from django.urls import NoReverseMatch, reverse

from apps.core.permissions import user_stakeholder_codes
from apps.stakeholders.models import UserProfile

# Nav key -> (url_name, label, optional personas for "More" group)
_NAV_DEFS = {
    "needs": ("needs:list", "Needs"),
    "projects": ("projects:list", "Projects"),
    "my_projects": ("projects:list", "My Projects"),
    "programs": ("programs:list", "Programs"),
    "events": ("events:list", "Events"),
    "rollup": ("dashboard:project_rollup", "Rollup"),
    "funding": ("funding:contributions", "Funding"),
    "my_contributions": ("funding:contributions", "My Contributions"),
    "pools": ("funding:pools", "Pools"),
    "governance": ("dashboard:governance_queue", "Governance"),
    "audit_log": ("dashboard:upload_audit_log", "Upload Audit Log"),
    "role_requests": ("stakeholders:role_requests", "Role Requests"),
    "my_assignments": ("dashboard:home", "My Assignments"),
    "profile": ("stakeholders:profile", "Profile"),
}

_PERSONA_NAV_KEYS = {
    UserProfile.StakeholderType.FOUNDATION_ADMIN: [
        "needs",
        "projects",
        "programs",
        "events",
        "rollup",
        "funding",
        "pools",
        "governance",
        "audit_log",
        "profile",
    ],
    UserProfile.StakeholderType.HOD: [
        "needs",
        "projects",
        "events",
        "role_requests",
        "profile",
    ],
    UserProfile.StakeholderType.DONOR: [
        "my_contributions",
        "my_projects",
        "events",
        "role_requests",
        "profile",
    ],
    UserProfile.StakeholderType.PROJECT_LEAD: [
        "my_projects",
        "events",
        "rollup",
        "role_requests",
        "profile",
    ],
    UserProfile.StakeholderType.VOLUNTEER: [
        "my_assignments",
        "events",
        "role_requests",
        "profile",
    ],
    UserProfile.StakeholderType.FINANCE_CONTROLLER: [
        "funding",
        "pools",
        "projects",
        "rollup",
        "governance",
        "role_requests",
        "profile",
    ],
    UserProfile.StakeholderType.GOVERNANCE: [
        "needs",
        "projects",
        "programs",
        "events",
        "rollup",
        "governance",
        "role_requests",
        "audit_log",
        "profile",
    ],
    UserProfile.StakeholderType.AUDITOR: [
        "needs",
        "projects",
        "funding",
        "rollup",
        "audit_log",
        "profile",
    ],
}

# Secondary items grouped under "More" on desktop
_MORE_GROUP_KEYS = frozenset({"pools", "governance", "audit_log", "role_requests", "programs"})


def _resolve_url(url_name: str) -> str | None:
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return None


def nav_items_for_user(user, request_path: str = "", active_persona: str | None = None) -> tuple[list[dict], list[dict]]:
    """
    Return (primary_nav_items, more_nav_items) for the authenticated user.
    Each item: {url, label, active, key}
    """
    if not user.is_authenticated:
        return [], []

    codes = user_stakeholder_codes(user)
    if user.is_superuser:
        codes = codes | {UserProfile.StakeholderType.FOUNDATION_ADMIN}

    if active_persona and active_persona in codes:
        codes = {active_persona}

    ordered_keys: list[str] = []
    seen: set[str] = set()
    for persona in _PERSONA_NAV_KEYS:
        if persona not in codes:
            continue
        for key in _PERSONA_NAV_KEYS[persona]:
            if key not in seen:
                seen.add(key)
                ordered_keys.append(key)

    primary: list[dict] = []
    more: list[dict] = []
    for key in ordered_keys:
        url_name, label = _NAV_DEFS[key]
        url = _resolve_url(url_name)
        if not url:
            continue
        active = request_path.startswith(url.rstrip("/")) and url != "/"
        if key == "profile" and request_path.rstrip("/").endswith("/profile"):
            active = True
        item = {"key": key, "url": url, "label": label, "active": active}
        if key in _MORE_GROUP_KEYS:
            more.append(item)
        else:
            primary.append(item)

    return primary, more


def persona_choices_for_user(user) -> list[dict]:
    """Active personas for role switcher: {code, label, active}."""
    if not user.is_authenticated:
        return []
    prof = getattr(user, "profile", None)
    if not prof:
        return []
    choice_map = dict(UserProfile.StakeholderType.choices)
    codes = sorted(user_stakeholder_codes(user))
    if user.is_superuser and UserProfile.StakeholderType.FOUNDATION_ADMIN not in codes:
        codes = [UserProfile.StakeholderType.FOUNDATION_ADMIN, *codes]
    return [{"code": c, "label": choice_map.get(c, c)} for c in codes]
