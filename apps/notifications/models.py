from django.db import models
from apps.core.models import BaseModel

class Notification(BaseModel):
    class TargetRole(models.TextChoices):
        ALL = 'All', 'All'
        STUDENT = 'Student', 'Student'
        FACULTY = 'Faculty', 'Faculty'
        HOD = 'HOD', 'HOD'
        MENTOR = 'Mentor', 'Mentor'

    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications_sent')
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    target_role = models.CharField(max_length=20, choices=TargetRole.choices, default=TargetRole.ALL)
    target_department = models.ForeignKey('academics.Department', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    is_global = models.BooleanField(default=False)  # If True, target_role and department are ignored (admin to everyone)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class NotificationRecipient(BaseModel):
    """Tracks if a specific user has seen a notification."""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notification_states')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='recipients')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'notification')
