from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.hr_portal.services import get_students_for_hr_token
from apps.students.serializers import StudentProfileSerializer
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from apps.hr_portal.models import HRSharedStudent
from apps.accounts.models import User
from apps.students.models import StudentProfile


class HRStudentListView(APIView):
    """
    View for HR to see students via a secure token.
    No authentication required as the token is the credential (Section 10.3).
    """
    permission_classes = [] # Public with token

    def get(self, request, token):
        try:
            students = get_students_for_hr_token(token)
            serializer = StudentProfileSerializer(students, many=True)
            return Response(serializer.data)
        except Exception:
            return Response(
                {"error": "Invalid or expired token"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class HRDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'HR':
            return redirect('dashboard')
        
        shared_students = HRSharedStudent.objects.filter(hr_user=request.user).select_related('student__user', 'student__department')
        return render(request, 'hr_portal/dashboard.html', {'shared_students': shared_students})


class HRStudentDetailView(LoginRequiredMixin, View):
    def get(self, request, student_id):
        if request.user.role != 'HR':
            return redirect('dashboard')
            
        # Verify student is shared with this HR
        is_shared = HRSharedStudent.objects.filter(hr_user=request.user, student_id=student_id).exists()
        if not is_shared:
            return redirect('hr-dashboard')
            
        student = get_object_or_404(StudentProfile, id=student_id)
        return render(request, 'hr_portal/student_detail.html', {'student': student})


class AdminShareStudentView(LoginRequiredMixin, View):
    """View for admins to share students with HR users."""
    def get(self, request):
        if request.user.role not in ['Chairman', 'Director', 'Principal']:
            return redirect('dashboard')
            
        students = StudentProfile.objects.all().select_related('user')
        hr_users = User.objects.filter(role='HR')
        return render(request, 'hr_portal/admin_share.html', {
            'students': students,
            'hr_users': hr_users
        })

    def post(self, request):
        student_id = request.POST.get('student_id')
        hr_user_id = request.POST.get('hr_user_id')
        
        if student_id and hr_user_id:
            HRSharedStudent.objects.get_or_create(
                hr_user_id=hr_user_id,
                student_id=student_id,
                defaults={'shared_by': request.user}
            )
        return redirect('admin-share-student')
