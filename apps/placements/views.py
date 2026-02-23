from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.placements.models import Company, PlacementDrive, StudentApplication
from apps.placements.serializers import CompanySerializer, PlacementDriveSerializer, StudentApplicationSerializer
from apps.placements import services, selectors


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated] # Simplified


class PlacementDriveViewSet(viewsets.ModelViewSet):
    queryset = PlacementDrive.objects.all().select_related('company')
    serializer_class = PlacementDriveSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def auto_shortlist(self, request, pk=None):
        """Management action to auto-shortlist students."""
        count = services.auto_shortlist_students(pk)
        return Response({"message": f"Successfully shortlisted {count} students"})


class PlacementApplicationViewSet(viewsets.ModelViewSet):
    queryset = StudentApplication.objects.all().select_related('student', 'drive', 'drive__company')
    serializer_class = StudentApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'Student':
            return self.queryset.filter(student__user=user)
        return self.queryset

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Returns overall placement summary."""
        data = selectors.get_placement_analytics()
        return Response(data)
