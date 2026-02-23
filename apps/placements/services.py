from apps.placements.models import StudentApplication, PlacementDrive
from apps.students.models import StudentProfile
from apps.audit.services import log_action
from django.db import transaction


def apply_to_drive(student, drive_id: str) -> StudentApplication:
    """Student applies to a placement drive."""
    drive = PlacementDrive.objects.get(id=drive_id)
    
    # Eligibility check
    if student.cgpa < drive.eligibility_cgpa:
        raise ValueError("CGPA requirement not met")
    
    if drive.eligibility_depts.exists() and student.department not in drive.eligibility_depts.all():
        raise ValueError("Department not eligible")

    application, created = StudentApplication.objects.get_or_create(
        student=student,
        drive=drive,
        defaults={'status': 'Applied'}
    )
    
    if created:
        log_action(actor=student.user, target=application, action='PLACEMENT_APPLIED')
    
    return application


@transaction.atomic
def auto_shortlist_students(drive_id: str) -> int:
    """Automatically shortlist students based on drive criteria."""
    drive = PlacementDrive.objects.get(id=drive_id)
    
    # Find eligible students who haven't applied or are already applied
    eligible_students = StudentProfile.objects.filter(
        cgpa__gte=drive.eligibility_cgpa,
        is_deleted=False
    )
    
    if drive.eligibility_depts.exists():
        eligible_students = eligible_students.filter(department__in=drive.eligibility_depts.all())

    shortlisted_count = 0
    for student in eligible_students:
        app, created = StudentApplication.objects.get_or_create(
            student=student,
            drive=drive,
            defaults={'status': 'Shortlisted'}
        )
        if not created and app.status == 'Applied':
            app.status = 'Shortlisted'
            app.save(update_fields=['status', 'updated_at'])
            shortlisted_count += 1
        elif created:
            shortlisted_count += 1
            
    return shortlisted_count


def update_application_status(application_id: str, new_status: str, verifier) -> StudentApplication:
    """Update placement application status."""
    app = StudentApplication.objects.get(id=application_id)
    app.status = new_status
    app.save(update_fields=['status', 'updated_at'])
    
    log_action(actor=verifier, target=app, action=f'PLACEMENT_STATUS_{new_status.upper()}')
    return app
