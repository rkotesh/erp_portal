from apps.core.models import BaseModel
from django.db import models


class AcademicYear(BaseModel):
    year = models.CharField(max_length=20)   # e.g., "2023-2024"
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.year


class FacultyApproval(BaseModel):
    """Principal approves / rejects faculty assignments and profile changes."""
    class ActionType(models.TextChoices):
        NEW_ASSIGNMENT    = 'new_assignment',    'New Faculty Assignment'
        PROFILE_UPDATE    = 'profile_update',    'Faculty Profile Update'
        SUBJECT_CHANGE    = 'subject_change',    'Subject Assignment Change'

    class Status(models.TextChoices):
        PENDING  = 'Pending',  'Pending'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'

    faculty      = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                        related_name='approval_requests', limit_choices_to={'role__in': ['Faculty', 'HOD', 'Mentor']})
    submitted_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                        related_name='submitted_approvals', null=True, blank=True)
    action_type  = models.CharField(max_length=30, choices=ActionType.choices)
    description  = models.TextField(help_text='Details of what is being requested')
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewed_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                        related_name='reviewed_approvals')
    reviewed_at  = models.DateTimeField(null=True, blank=True)
    remarks      = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Faculty Approval'

    def __str__(self):
        return f"{self.faculty.full_name} — {self.action_type} ({self.status})"


class LoginActivity(BaseModel):
    """Tracks login events for Director dashboard."""
    user        = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='login_activity')
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.CharField(max_length=512, blank=True, default='')
    action      = models.CharField(max_length=20, default='login',
                    choices=[('login', 'Login'), ('logout', 'Logout'), ('profile_update', 'Profile Updated')])

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Login Activity'

    def __str__(self):
        return f"{self.user.email} — {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
