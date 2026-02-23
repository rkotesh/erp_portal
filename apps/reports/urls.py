from apps.reports import views, public_views
from django.urls import path

urlpatterns = [
    path('share/<uuid:token>/', public_views.SharedReportView.as_view(), name='report-share'),
    path('chairman/summary/', views.ChairmanSummaryView.as_view(), name='chairman-summary'),
    path('chairman/students-by-dept/', views.StudentsByDepartmentView.as_view(), name='chairman-students-by-dept'),
    path('request/', views.RequestReportView.as_view(), name='report-request'),
    path('list/', views.GeneratedReportListView.as_view(), name='report-list'),
]
