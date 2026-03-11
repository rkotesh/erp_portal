from django import template
from django.contrib.admin.models import LogEntry

from apps.accounts.models import User
from apps.faculty.models import Cohort, InstitutionCourse
from apps.reports.models import GeneratedReport

register = template.Library()


@register.simple_tag
def admin_stats():
    return {
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "total_courses": InstitutionCourse.objects.count(),
        "total_cohorts": Cohort.objects.count(),
        "total_reports": GeneratedReport.objects.count(),
    }


@register.simple_tag
def recent_admin_actions(limit=8):
    return LogEntry.objects.select_related("user").order_by("-action_time")[:limit]
