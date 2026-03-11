from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from apps.faculty.models import Cohort, InstitutionCourse


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ("name", "cohort_type", "department", "created_by", "is_active")
    list_filter = ("cohort_type", "is_active", "department")
    search_fields = ("name", "created_by__email")
    ordering = ("-created_at",)


@admin.register(InstitutionCourse)
class InstitutionCourseAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "created_by", "is_published_to_profile")
    list_filter = ("category", "is_published_to_profile")
    search_fields = ("name", "created_by__email")
    ordering = ("-created_at",)
>>>>>>> bc40f1fa (update the latest changes)
