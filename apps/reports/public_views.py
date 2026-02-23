from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from apps.reports.models import GeneratedReport
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class SharedReportView(APIView):
    """Access a report via a secure share token."""
    permission_classes = [AllowAny]

    def get(self, request, token):
        report = get_object_or_404(GeneratedReport, share_token=token)
        return FileResponse(report.file.open(), as_attachment=True)
