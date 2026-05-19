"""Recent user activity for profile timeline."""

from django.contrib.auth import get_user_model

User = get_user_model()


def recent_activity_for_user(user, limit: int = 10) -> list[dict]:
    """Return [{when, label, url}, ...] newest first."""
    from apps.funding.models import Contribution
    from apps.needs.models import Need
    from apps.projects.models import Milestone

    items = []
    for n in Need.objects.filter(created_by=user).order_by("-created_at")[:limit]:
        items.append(
            {
                "when": n.created_at,
                "label": f'Created need "{n.title}"',
                "url": n.get_absolute_url(),
            }
        )
    for m in (
        Milestone.objects.filter(assigned_to=user)
        .select_related("project")
        .order_by("-updated_at")[:limit]
    ):
        items.append(
            {
                "when": m.updated_at,
                "label": f'Updated milestone "{m.title}" on {m.project.title}',
                "url": m.project.get_absolute_url(),
            }
        )
    for c in (
        Contribution.objects.filter(donor=user)
        .select_related("project", "event")
        .order_by("-created_at")[:limit]
    ):
        target = ""
        if c.project_id:
            target = f" for {c.project.title}"
        elif c.event_id:
            target = f" for {c.event.title}"
        items.append(
            {
                "when": c.created_at,
                "label": f"Contribution {c.amount} {c.currency}{target}",
                "url": c.project.get_absolute_url() if c.project_id else None,
            }
        )
    items.sort(key=lambda x: x["when"], reverse=True)
    return items[:limit]
