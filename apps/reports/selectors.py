from django.db.models import Count
from apps.students.models import StudentProfile
from apps.accounts.models import User
from apps.academics.models import Department


def get_chairman_summary():
    """
    Return summary data for the chairman dashboard.
    """
    return {
        "total_students": StudentProfile.objects.filter(is_deleted=False).count(),
        "total_faculty": User.objects.filter(role__in=['Faculty', 'Mentor', 'HOD'], is_active=True).count(),
        "active_departments": Department.objects.count(),
        "pass_rate_percentage": 85.5, # Placeholder for now
    }


def get_students_by_department_data():
    """
    Return data for students by department chart.
    """
    data = Department.objects.annotate(student_count=Count('students')).values('name', 'student_count')
    return list(data)
