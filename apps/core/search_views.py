from rest_framework.views import APIView
from rest_framework.response import Response
from apps.students.models import StudentProfile
from apps.accounts.models import User
from apps.placements.models import PlacementDrive
from django.db.models import Q


class GlobalSearchView(APIView):
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return Response("")

        results = []

        # Search Students
        students = StudentProfile.objects.filter(
            Q(roll_no__icontains=query) | Q(user__email__icontains=query)
        )[:5]
        for s in students:
            results.append({"category": "Student", "title": f"{s.roll_no} - {s.user.email}", "url": f"/students/{s.id}/"})

        # Search Faculty
        faculty = User.objects.filter(role='Faculty', email__icontains=query)[:5]
        for f in faculty:
            results.append({"category": "Faculty", "title": f.email, "url": f"/faculty/{f.id}/"})

        # Search Drives
        drives = PlacementDrive.objects.filter(Q(job_title__icontains=query) | Q(company__name__icontains=query))[:5]
        for d in drives:
            results.append({"category": "Placement", "title": f"{d.company.name} - {d.job_title}", "url": f"/placements/drives/{d.id}/"})

        # Render HTML for HTMX
        if results:
            html = '<div class="list-group shadow position-absolute w-50 z-index-1000" style="z-index: 1050;">'
            for r in results:
                html += f'<a href="{r["url"]}" class="list-group-item list-group-item-action"><strong>[{r["category"]}]</strong> {r["title"]}</a>'
            html += '</div>'
            return Response(html)
        
        return Response('<div class="list-group position-absolute w-50"><div class="list-group-item">No results found</div></div>')
