from django.db.models import QuerySet
from apps.students.models import StudentProfile


def get_students_by_department(department_id: str) -> QuerySet:
    """Return active students for a department, ordered by roll number."""
    return (
        StudentProfile.objects
        .filter(department_id=department_id, is_deleted=False)
        .select_related('user', 'department')
        .order_by('roll_no')
    )


def get_student_by_roll_no(roll_no: str) -> StudentProfile:
    """Return student profile by roll number."""
    return StudentProfile.objects.select_related('user', 'department').get(roll_no=roll_no)
