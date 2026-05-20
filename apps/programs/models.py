from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.projects.models import Milestone


class Program(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    fund_pool = models.ForeignKey(
        "funding.FundPool", on_delete=models.SET_NULL, null=True, blank=True, related_name="programs"
    )
    originated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="programs_originated"
    )
    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    budget_currency = models.CharField(max_length=8, default="INR")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="owned_programs")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProgramMilestone(TimeStampedModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="milestones")
    phase = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="program_milestones"
    )
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    tranche_percent = models.PositiveSmallIntegerField(default=0)
    proof = models.FileField(upload_to="program_milestone_proof/%Y/", blank=True, null=True)
    completed = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=0)
    tranche_governance_status = models.CharField(
        max_length=32,
        choices=Milestone.TrancheGovernance.choices,
        default=Milestone.TrancheGovernance.NOT_APPLICABLE,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["sequence", "due_date"]

    def __str__(self):
        return f"{self.program.title} - {self.title}"
