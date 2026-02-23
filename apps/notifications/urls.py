from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('create/', views.CreateNotificationView.as_view(), name='notification-create'),
    path('read/<int:pk>/', views.MarkAsReadView.as_view(), name='notification-read'),
]
