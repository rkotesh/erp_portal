from django.contrib import admin
from apps.academics.models import Department, Subject, Marks


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'hod')
    search_fields = ('name', 'code')
    ordering = ('code',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'semester', 'type', 'credits', 'faculty')
    list_filter = ('department', 'semester', 'type')
    search_fields = ('name', 'code')
    ordering = ('department', 'semester', 'code')


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'internal', 'external', 'total', 'grade')
    list_filter = ('subject__department', 'subject')
    search_fields = ('student__roll_no', 'student__user__full_name')
    ordering = ('student',)
