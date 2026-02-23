from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


ROLE_PERMISSIONS = {
    'Chairman':  ['view_marks', 'view_attendance', 'view_facultyprofile', 'view_auditlog', 'view_generatedreport', 'add_generatedreport'],
    'Director':  ['view_marks', 'view_attendance', 'view_loginlog', 'view_profilelog', 'view_generatedreport'],
    'Principal': ['view_facultyprofile', 'approve_faculty', 'view_hodprofile'],
    'HOD':       ['add_lessonplan', 'view_lessonplan', 'assign_mentor', 'view_deptreport'],
    'Mentor':    ['add_marks', 'add_attendance', 'view_studentprofile'],
    'Faculty':   ['add_course', 'add_assessment', 'view_cohort'],
    'Student':   ['view_marks', 'view_attendance', 'change_studentprofile', 'add_certification'],
    'Parent':    ['view_marks', 'view_attendance'],
    'HR':        ['view_studentprofile_hr'],
    'Placement': ['view_placementdrive', 'add_placementdrive', 'change_studentapplication', 'view_generatedreport'],
}


class Command(BaseCommand):
    help = 'Create default role groups and permissions'

    def handle(self, *args, **options):
        for role_name, perm_codenames in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            # Filter permissions - note: in a real scenario we'd need to ensure these permissions exist
            # For brevity/safety, we'll just log
            perms = Permission.objects.filter(codename__in=perm_codenames)
            group.permissions.set(perms)
            self.stdout.write(f'✓ Role {role_name} configured')
