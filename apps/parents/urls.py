from django.urls import path
from apps.parents import views

urlpatterns = [
    path('portal/', views.ParentDashboardView.as_view(), name='parent-portal'),
]
