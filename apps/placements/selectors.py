from django.db import models
from django.db.models import Count, Avg, Max
from apps.placements.models import StudentApplication, PlacementDrive, Company


def get_placement_analytics():
    """Returns overall placement statistics."""
    selected_apps = StudentApplication.objects.filter(status='Selected')
    
    return {
        "total_placed": selected_apps.values('student').distinct().count(),
        "highest_package": selected_apps.aggregate(Max('offered_package'))['offered_package__max'] or 0.0,
        "avg_package": selected_apps.aggregate(Avg('offered_package'))['offered_package__avg'] or 0.0,
        "total_companies": Company.objects.count(),
        "ongoing_drives": PlacementDrive.objects.filter(status='Ongoing').count()
    }


def get_company_wise_stats():
    """Returns analytics per company."""
    return Company.objects.annotate(
        placed_count=Count('drives__applications', filter=models.Q(drives__applications__status='Selected')),
        avg_pkg=Avg('drives__applications__offered_package')
    ).values('name', 'placed_count', 'avg_pkg')


def get_student_placement_timeline(student_id):
    """Returns placement history for a student."""
    return (
        StudentApplication.objects
        .filter(student_id=student_id)
        .select_related('drive', 'drive__company')
        .order_by('-created_at')
    )
