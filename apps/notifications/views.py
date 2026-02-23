from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from django.db.models import Q
from .models import Notification, NotificationRecipient
from apps.academics.models import Department

class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # Filters: Global OR (targeted role AND targeted/null department)
        notifications = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                (Q(target_department__isnull=True) | Q(target_department=user.department))
            )
        ).distinct().order_by('-created_at')

        return render(request, 'notifications/list.html', {
            'notifications': notifications,
            'departments': Department.objects.all()
        })

class MarkAsReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        NotificationRecipient.objects.get_or_create(
            user=request.user, 
            notification=notification,
            defaults={'is_read': True}
        )
        return redirect('notification-list')

class CreateNotificationView(LoginRequiredMixin, View):
    def post(self, request):
        # Strict permission check: Admin can post anything, HOD can post to their department
        if request.user.role not in ['Admin', 'HOD', 'Principal', 'Chairman', 'Director']:
            messages.error(request, "Unauthorized to post notifications.")
            return redirect('dashboard')
            
        title = request.POST.get('title')
        message = request.POST.get('message')
        target_role = request.POST.get('target_role', 'All')
        is_global = request.POST.get('is_global') == 'on'
        
        # HOD restriction: can only post to their own department if not global
        dept_id = request.POST.get('department')
        if request.user.role == 'HOD' and not is_global:
            target_dept = request.user.department
        elif dept_id:
            target_dept = Department.objects.filter(id=dept_id).first()
        else:
            target_dept = None

        Notification.objects.create(
            sender=request.user,
            title=title,
            message=message,
            target_role=target_role,
            target_department=target_dept,
            is_global=is_global if request.user.role == 'Admin' else False # Only Admin can post global
        )
        
        messages.success(request, "Notification sent successfully.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
