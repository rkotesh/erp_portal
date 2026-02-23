from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from apps.parents.models import ParentProfile
from apps.academics.models import Marks, Attendance
from django.db.models import Avg

class ParentDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Try to find ParentProfile if user is Parent
        # OR handle the case where student credentials are used for parent login
        is_parent_login = request.session.get('is_parent_login', False)
        
        if request.user.role == 'Student' and is_parent_login:
            # Shared credentials case: Get the student profile for this user
            student_profile = getattr(request.user, 'student_profile', None)
            if not student_profile:
                return render(request, 'parents/no_profile.html')
            
            # Simulate a list of students (just this one) to reuse the template logic
            profile_students = [student_profile]
        elif request.user.role == 'Parent':
            try:
                profile = request.user.parent_profile
                profile_students = profile.students.all()
            except ParentProfile.DoesNotExist:
                return render(request, 'parents/no_profile.html')
        else:
            return redirect('dashboard')

        students_data = []
        for student in profile_students:
            marks = Marks.objects.filter(student=student)
            
            # Logic for parent dashboard: usually they want simple summary
            avg_score = marks.aggregate(avg=Avg('total'))['avg'] or 0
            
            students_data.append({
                'student': student,
                'avg_score': round(float(avg_score)),
                'marks': marks.select_related('subject'),
            })

        return render(request, 'parents/dashboard.html', {
            'students_data': students_data,
        })
