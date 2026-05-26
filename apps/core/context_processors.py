from apps.core.nav_items import nav_items_for_user, persona_choices_for_user


def persona_nav(request):
    active = request.session.get("active_persona")
    choices = persona_choices_for_user(request.user)
    if choices:
        if not active:
            from apps.stakeholders.persona_utils import pick_primary_persona

            active = pick_primary_persona(c["code"] for c in choices)
        for c in choices:
            c["active"] = c["code"] == active

    primary, more = nav_items_for_user(request.user, request.path, active_persona=active)
    return {
        "nav_items": primary,
        "nav_more_items": more,
        "persona_choices": choices,
        "active_persona": active,
        "show_role_switcher": len(choices) > 1,
    }
