from django.db.models import QuerySet
from apps.academics.models import Subject
from apps.students.models import Certification


def get_subjects_by_faculty(faculty_id: str) -> QuerySet:
    """Return subjects taught by a specific faculty."""
    return Subject.objects.filter(faculty_id=faculty_id).select_related('department')


def get_pending_certifications_for_dept(department_id: str) -> QuerySet:
    """Return certifications pending verification for a department."""
    return (
        Certification.objects
        .filter(student__department_id=department_id, verified=False)
        .select_related('student__user')
    )
