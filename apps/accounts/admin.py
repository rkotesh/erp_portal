from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from apps.accounts.models import User, OTPRecord


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'department', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'department')
    search_fields = ('email', 'full_name', 'role')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'last_login_ip')
    change_list_template = 'admin/accounts/user_changelist.html'

    fieldsets = (
        ('🔐 Credentials', {'fields': ('email', 'password')}),
        ('👤 Personal Info', {'fields': ('full_name', 'role', 'department', 'phone')}),
        ('✅ Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('📅 Timestamps', {'fields': ('last_login', 'created_at', 'updated_at', 'last_login_ip'), 'classes': ('collapse',)}),
    )
    add_fieldsets = (
        ('Create New User', {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'department', 'phone', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'purpose', 'expires_at', 'is_used', 'attempt_count', 'created_at')
    list_filter = ('purpose', 'is_used')
    search_fields = ('user__email',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

