from django.db.models import Q
from .models import Notification, NotificationRecipient

def notification_context(request):
    if not request.user.is_authenticated:
        return {}
    
    user = request.user
    # Count notifications that are for this user but not marked as read in NotificationRecipient
    # A bit tricky for mass notifications.
    # Logic: Total matching notifications - count of NotificationRecipient where is_read=True
    
    total_relevant = Notification.objects.filter(
        Q(is_global=True) |
        (
            (Q(target_role='All') | Q(target_role=user.role)) &
            (Q(target_department__isnull=True) | Q(target_department=user.department))
        )
    ).count()
    
    read_count = NotificationRecipient.objects.filter(user=user, is_read=True).count()
    
    unread_count = max(0, total_relevant - read_count)
    
    return {
        'unread_notifications_count': unread_count
    }
