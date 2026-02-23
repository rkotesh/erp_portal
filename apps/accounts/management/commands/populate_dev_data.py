from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.academics.models import Department, Subject
from apps.students.models import StudentProfile
from apps.core.models import College
from apps.admin_portal.models import AcademicYear, CollegeSetting
from apps.placements.models import Company, PlacementDrive, StudentApplication
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Populate development data'

    def handle(self, *args, **options):
        # 1. Create College
        college, _ = College.objects.get_or_create(
            code="ACET",
            defaults={
                "name": "Chalapathi Institute of Engineering & Technology",
                "address": "Orbit Layer 7, Silicon Valley",
                "contact_email": "admin@ciet.edu"
            }
        )

        # 2. Academic Year
        ay, _ = AcademicYear.objects.get_or_create(year="2023-2024", defaults={"is_current": True})
        CollegeSetting.objects.get_or_create(college=college, defaults={"current_academic_year": ay})

        # 3. Create Departments
        depts = [
            ("Computer Science", "CSE"),
            ("Electronics", "ECE"),
            ("Mechanical", "MECH"),
        ]
        dept_objs = []
        for name, code in depts:
            dept, _ = Department.objects.get_or_create(name=name, code=code)
            dept_objs.append(dept)

        # 4. Special Roles
        roles = [
            ("chairman@college.edu", "Chairman"),
            ("placement@college.edu", "Placement"),
            ("hr@college.edu", "HR"),
        ]
        for email, role in roles:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'role': role, 'phone': '+1000000000'}
            )
            if created:
                user.set_password('password123')
                user.save()

        # 5. Create Faculty
        faculty_users = []
        for i in range(10):
            email = f"faculty{i}@college.edu"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'role': 'Faculty',
                    'department': random.choice(dept_objs),
                    'phone': f'+123456789{i}'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            faculty_users.append(user)

        # 6. Subjects and Students
        for dept in dept_objs:
            # Subjects
            for sem in range(1, 9):
                Subject.objects.get_or_create(
                    code=f"{dept.code}{sem}01",
                    defaults={
                        "name": f"{dept.code} Core {sem}",
                        "department": dept,
                        "semester": sem,
                        "faculty": random.choice(faculty_users)
                    }
                )
            # Students
            for i in range(20):
                email = f"{dept.code.lower()}_student{i}@college.edu"
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={'role': 'Student', 'department': dept, 'phone': '+999888777'}
                )
                if created:
                    user.set_password('password123')
                    user.save()
                
                StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'roll_no': f"22{dept.code}{i:03}",
                        'batch': '2022-2026',
                        'department': dept,
                        'cgpa': round(random.uniform(6.5, 9.8), 2)
                    }
                )

        # 7. Companies and Placements
        companies = [("Google", "Tech"), ("Microsoft", "Software"), ("Tesla", "Auto"), ("TCS", "IT")]
        comp_objs = []
        for name, ind in companies:
            c, _ = Company.objects.get_or_create(name=name, defaults={"industry": ind})
            comp_objs.append(c)

        for comp in comp_objs:
            drive, _ = PlacementDrive.objects.get_or_create(
                company=comp,
                job_title="Software Engineer",
                defaults={
                    "job_description": "Full stack role...",
                    "eligibility_cgpa": 7.5,
                    "deadline": timezone.now() + timedelta(days=30),
                    "status": "Ongoing",
                    "ctc_package": random.randint(10, 45)
                }
            )
            # Create applications
            eligible = StudentProfile.objects.filter(cgpa__gte=7.5).order_by('?')[:15]
            for student in eligible:
                status = random.choice(['Applied', 'Shortlisted', 'Interviewed', 'Selected'])
                StudentApplication.objects.get_or_create(
                    drive=drive,
                    student=student,
                    defaults={
                        "status": status,
                        "offered_package": drive.ctc_package if status == 'Selected' else None
                    }
                )

        self.stdout.write(self.style.SUCCESS("✓ Demo data population complete!"))
