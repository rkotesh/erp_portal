from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.placements.views import CompanyViewSet, PlacementDriveViewSet, PlacementApplicationViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'drives', PlacementDriveViewSet)
router.register(r'applications', PlacementApplicationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
