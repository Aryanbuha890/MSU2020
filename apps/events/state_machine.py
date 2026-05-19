"""Event status transitions (Doc 1 §4a)."""

from apps.events.models import Event

_TRANSITIONS = {
    Event.Status.DRAFT: {Event.Status.GOVERNANCE_APPROVED},
    Event.Status.GOVERNANCE_APPROVED: {Event.Status.PUBLISHED},
    Event.Status.PUBLISHED: {Event.Status.COMPLETED},
    Event.Status.REGISTRATION_OPEN: {Event.Status.COMPLETED},
    Event.Status.ONGOING: {Event.Status.COMPLETED},
}


def allowed_event_next(current: str) -> set[str]:
    return _TRANSITIONS.get(current, set())


def transition_label(current: str, nxt: str) -> str:
    mapping = {
        (Event.Status.DRAFT, Event.Status.GOVERNANCE_APPROVED): "Submit for Governance Approval",
        (Event.Status.GOVERNANCE_APPROVED, Event.Status.PUBLISHED): "Publish",
        (Event.Status.PUBLISHED, Event.Status.COMPLETED): "Mark Completed",
        (Event.Status.REGISTRATION_OPEN, Event.Status.COMPLETED): "Mark Completed",
        (Event.Status.ONGOING, Event.Status.COMPLETED): "Mark Completed",
    }
    return mapping.get((current, nxt), f"Move to {nxt}")
