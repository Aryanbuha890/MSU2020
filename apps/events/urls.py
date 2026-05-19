from django.urls import path

from apps.events import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="list"),
    path("create/", views.EventCreateView.as_view(), name="create"),
    path("<int:pk>/", views.EventDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.EventUpdateView.as_view(), name="edit"),
    path("<int:pk>/transition/", views.event_transition, name="transition"),
    path("<int:event_id>/milestones/create/", views.EventMilestoneCreateView.as_view(), name="milestone_create"),
    path(
        "<int:event_id>/milestones/<int:milestone_id>/edit/",
        views.EventMilestoneUpdateView.as_view(),
        name="milestone_edit",
    ),
    path(
        "<int:event_id>/milestones/<int:milestone_id>/complete/",
        views.event_milestone_complete,
        name="milestone_complete",
    ),
]
