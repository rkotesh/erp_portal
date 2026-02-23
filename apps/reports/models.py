from apps.core.models import BaseModel
from django.db import models
import uuid


class GeneratedReport(BaseModel):
    class ReportType(models.TextChoices):
        DEPARTMENT = 'Department', 'Department'
        FACULTY = 'Faculty', 'Faculty'
        STUDENT = 'Student', 'Student'
        PLACEMENT = 'Placement', 'Placement'
        ATTENDANCE = 'Attendance', 'Attendance'

    class Format(models.TextChoices):
        PDF = 'PDF', 'PDF'
        EXCEL = 'Excel', 'Excel'

    report_type = models.CharField(max_length=50, choices=ReportType.choices)
    format = models.CharField(max_length=10, choices=Format.choices)
    file = models.FileField(upload_to='reports/generated/')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    is_scheduled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.report_type} ({self.format}) - {self.created_at}"
