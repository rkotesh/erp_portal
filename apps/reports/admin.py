from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from apps.reports.models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ("report_type", "format", "created_by", "created_at", "is_scheduled")
    list_filter = ("report_type", "format", "is_scheduled")
    search_fields = ("created_by__email",)
    ordering = ("-created_at",)
>>>>>>> bc40f1fa (update the latest changes)
