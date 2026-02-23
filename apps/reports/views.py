from rest_framework.views import APIView
from rest_framework.response import Response
from apps.reports import tasks, models, selectors
from rest_framework import permissions


class ChairmanSummaryView(APIView):
    def get(self, request):
        data = selectors.get_chairman_summary()
        return Response(data)


class StudentsByDepartmentView(APIView):
    def get(self, request):
        data = selectors.get_students_by_department_data()
        return Response(data)


class RequestReportView(APIView):
    """View to request an asynchronous report generation."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        report_type = request.data.get('report_type')
        report_format = request.data.get('format', 'PDF')
        
        # Role-based restriction
        if request.user.role not in ['Chairman', 'Director', 'Placement']:
            return Response({"error": "Unauthorized to generate reports"}, status=403)
        
        # In a real environment with Redis/Celery:
        # tasks.generate_async_report.delay(...)
        # For now, we follow the 'continue' flow.
        tasks.generate_async_report(
            report_type=report_type,
            format=report_format,
            user_id=str(request.user.id)
        )
        return Response({"message": "Report generation summary available."})


class GeneratedReportListView(APIView):
    """View to list reports available to the user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reports = models.GeneratedReport.objects.filter(created_by=request.user).order_by('-created_at')
        data = [{
            "id": r.id,
            "type": r.report_type,
            "format": r.format,
            "url": r.file.url,
            "date": r.created_at,
            "share_token": r.share_token
        } for r in reports]
        return Response(data)
