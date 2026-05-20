from django.contrib import admin
from .models import Program, ProgramMilestone

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "budget", "budget_currency", "start_date"]
    list_filter = ["status"]
    search_fields = ["title", "description"]

@admin.register(ProgramMilestone)
class ProgramMilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "program", "due_date", "completed", "tranche_percent"]
    list_filter = ["completed", "tranche_governance_status"]
    search_fields = ["title", "program__title"]
