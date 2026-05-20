from django.urls import path
from . import views

app_name = "programs"

urlpatterns = [
    path("", views.ProgramListView.as_view(), name="list"),
    path("new/", views.ProgramCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ProgramDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ProgramUpdateView.as_view(), name="update"),
    path("<int:program_id>/milestones/new/", views.ProgramMilestoneCreateView.as_view(), name="milestone_create"),
    path("milestones/<int:pk>/edit/", views.ProgramMilestoneUpdateView.as_view(), name="milestone_update"),
    path("milestones/<int:pk>/tranche-release/", views.program_milestone_tranche_release, name="milestone_tranche_release"),
]
