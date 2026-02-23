from django.contrib import admin
from apps.hr_portal.models import HRLink, HRSharedStudent

@admin.register(HRLink)
class HRLinkAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'expires_at', 'token')

@admin.register(HRSharedStudent)
class HRSharedStudentAdmin(admin.ModelAdmin):
    list_display = ('hr_user', 'student', 'shared_by', 'created_at')
    list_filter = ('hr_user', 'shared_by')
    search_fields = ('student__user__full_name', 'student__roll_no')
