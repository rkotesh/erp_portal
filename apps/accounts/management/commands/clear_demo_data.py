from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.academics.models import Department, Subject
from apps.students.models import StudentProfile
from apps.placements.models import Company, PlacementDrive, StudentApplication
from apps.reports.models import GeneratedReport
from apps.core.models import College
from apps.admin_portal.models import AcademicYear, CollegeSetting

class Command(BaseCommand):
    help = 'Clears all demo data from the database'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all application data...")
        
        # Order matters for foreign key constraints
        StudentApplication.objects.all().delete()
        PlacementDrive.objects.all().delete()
        Company.objects.all().delete()
        GeneratedReport.objects.all().delete()
        StudentProfile.objects.all().delete()
        Subject.objects.all().delete()
        CollegeSetting.objects.all().delete()
        AcademicYear.objects.all().delete()
        Department.objects.all().delete()
        College.objects.all().delete()
        
        # Delete non-staff users
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS("✓ All demo data cleared. Only superusers remain."))
        self.stdout.write("You can now add real data via the Admin Panel or bulk upload scripts.")
