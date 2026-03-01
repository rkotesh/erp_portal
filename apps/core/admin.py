from django.contrib import admin
from apps.core.models import College, Event

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_email')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'created_by', 'is_active')
    list_filter = ('is_active', 'date')
    search_fields = ('title', 'location')
