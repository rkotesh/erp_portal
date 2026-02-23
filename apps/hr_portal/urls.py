from django.urls import path
from apps.hr_portal.views import HRStudentListView, HRDashboardView, HRStudentDetailView, AdminShareStudentView

urlpatterns = [
    path('view/<str:token>/', HRStudentListView.as_view(), name='hr-view'),
    path('dashboard/', HRDashboardView.as_view(), name='hr-dashboard'),
    path('student/<uuid:student_id>/', HRStudentDetailView.as_view(), name='hr-student-detail'),
    path('admin/share/', AdminShareStudentView.as_view(), name='admin-share-student'),
]
