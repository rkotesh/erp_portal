from django.contrib import admin
from django.utils.html import format_html
from apps.students.models import (
    StudentProfile, EducationBackground, Certification,
    Project, Internship, Event, Course, Research, SemesterResult
)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'get_name', 'get_email', 'department', 'batch', 'cgpa', 'is_public', 'get_public_link')
    list_filter = ('department', 'batch', 'is_public')
    search_fields = ('roll_no', 'user__full_name', 'user__email')
    ordering = ('roll_no',)
    list_per_page = 30
    readonly_fields = ('slug', 'get_public_link')

    def get_name(self, obj): return obj.user.full_name
    get_name.short_description = 'Full Name'

    def get_email(self, obj): return obj.user.email
    get_email.short_description = 'Email'

    def get_public_link(self, obj):
        if obj.is_public and obj.slug:
            url = f"/student/p/{obj.slug}/"
            return format_html(
                '<a href="{}" target="_blank" title="Open public profile">🔗 View Profile</a>',
                url
            )
        return '🔒 Private'
    get_public_link.short_description = 'Public Link'


@admin.register(EducationBackground)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('student', 'edu_type', 'institution', 'year_of_passing', 'score', 'is_verified')
    list_filter = ('edu_type', 'is_verified')
    search_fields = ('student__roll_no', 'student__user__full_name', 'institution')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'issuer', 'issued_date', 'cert_type', 'is_verified')
    list_filter = ('cert_type', 'is_verified', 'issued_date')
    search_fields = ('student__roll_no', 'student__user__full_name', 'title', 'issuer')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'project_type', 'tech_stack', 'is_group', 'is_verified')
    list_filter = ('project_type', 'is_verified', 'is_group')
    search_fields = ('student__roll_no', 'student__user__full_name', 'title')


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('student', 'organization', 'role', 'start_date', 'end_date')
    list_filter = ('start_date',)
    search_fields = ('student__roll_no', 'student__user__full_name', 'organization')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('student', 'name', 'scope', 'role', 'position', 'organizer', 'event_date')
    list_filter = ('scope', 'role', 'event_date')
    search_fields = ('student__roll_no', 'name', 'organizer')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'source', 'platform', 'completion_percentage', 'is_verified')
    list_filter = ('source', 'is_verified')
    search_fields = ('student__roll_no', 'title', 'platform')


@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'research_type', 'outcome', 'publisher', 'published_date', 'is_verified')
    list_filter = ('research_type', 'outcome', 'is_verified')
    search_fields = ('student__roll_no', 'student__user__full_name', 'title')


@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'semester', 'exam_name', 'subject_code', 'subject_name',
        'score', 'max_score', 'grade', 'is_verified'
    )
    list_filter = ('semester', 'is_verified', 'exam_name')
    search_fields = ('student__roll_no', 'student__user__full_name', 'subject_name', 'subject_code')
