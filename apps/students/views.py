from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.db.models import Avg
from apps.students.models import (
    StudentProfile, EducationBackground, Certification,
    Project, Internship, Event, Course, Research
)
from apps.academics.models import Subject, Marks, Attendance
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.students.serializers import StudentProfileSerializer
from apps.students.permissions import IsStudentOwnerOrReadOnly


# ── API ViewSet ────────────────────────────────────────────
class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.filter(is_deleted=False)
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentOwnerOrReadOnly]
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'Student':
            return self.queryset.filter(user=user)
        return self.queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except StudentProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)


# ── Student Portal UI Views ────────────────────────────────
def student_required(view_func):
    """Decorator: only logged-in students can access."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'Student':
            return redirect('dashboard')
        try:
            request.user.student_profile
        except StudentProfile.DoesNotExist:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


class StudentPortalView(LoginRequiredMixin, View):
    """Main student dashboard — overview."""
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        try:
            profile = request.user.student_profile
        except StudentProfile.DoesNotExist:
            return render(request, 'student_portal/no_profile.html')

        marks = Marks.objects.filter(student=profile).select_related('subject')
        attendance = Attendance.objects.filter(student=profile).select_related('subject')
        
        # Calculate overall attendance
        total_att = attendance.count()
        present_att = attendance.filter(is_present=True).count()
        att_pct = round((present_att / total_att * 100), 1) if total_att else 0

        # Calculate subject-wise attendance
        subject_stats = {}
        for sub in Subject.objects.filter(department=profile.department):
            sub_att = attendance.filter(subject=sub)
            sub_count = sub_att.count()
            sub_present = sub_att.filter(is_present=True).count()
            sub_pct = round((sub_present / sub_count * 100), 1) if sub_count else 0
            
            # Find marks if any
            sub_marks = marks.filter(subject=sub).first()
            
            subject_stats[sub.id] = {
                'subject': sub,
                'total': sub_count,
                'present': sub_present,
                'pct': sub_pct,
                'marks': sub_marks
            }

        return render(request, 'student_portal/dashboard.html', {
            'profile': profile,
            'att_pct': att_pct,
            'total_classes': total_att,
            'present': present_att,
            'absent': total_att - present_att,
            'subject_stats': subject_stats,
        })


class StudentProfileEditView(LoginRequiredMixin, View):
    """Edit personal info, photo, links."""
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        education = EducationBackground.objects.filter(student=profile)
        return render(request, 'student_portal/profile_edit.html', {
            'profile': profile,
            'education': education,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        # Personal info
        profile.user.full_name = request.POST.get('full_name', profile.user.full_name)
        profile.user.save()
        # Links
        for field in ['linkedin_url', 'github_url', 'leetcode_url',
                      'hackerrank_url', 'codechef_url', 'codeforces_url']:
            setattr(profile, field, request.POST.get(field, ''))
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        if 'resume' in request.FILES:
            profile.resume = request.FILES['resume']
        profile.save()
        return redirect('student-profile-edit')


class StudentAcademicsView(LoginRequiredMixin, View):
    """View-only marks and attendance."""
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        marks = Marks.objects.filter(student=profile).select_related('subject', 'subject__department')
        attendance = Attendance.objects.filter(student=profile).select_related('subject')
        
        # Subject-wise Summary
        subject_stats = {}
        for sub in Subject.objects.filter(department=profile.department):
            sub_att = attendance.filter(subject=sub)
            sub_count = sub_att.count()
            sub_present = sub_att.filter(is_present=True).count()
            sub_pct = round((sub_present / sub_count * 100), 1) if sub_count else 0
            
            sub_marks = marks.filter(subject=sub).first()
            
            subject_stats[sub.id] = {
                'subject': sub,
                'total': sub_count,
                'present': sub_present,
                'pct': sub_pct,
                'marks': sub_marks
            }

        return render(request, 'student_portal/academics.html', {
            'profile': profile,
            'marks': marks,
            'attendance': attendance,
            'subject_stats': subject_stats,
        })


class StudentCertificationsView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        certs = Certification.objects.filter(student=profile).order_by('-issued_date')
        return render(request, 'student_portal/certifications.html', {
            'profile': profile, 'certs': certs,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        cert = Certification(
            student=profile,
            title=request.POST.get('title', ''),
            issuer=request.POST.get('issuer', ''),
            issued_date=request.POST.get('issued_date'),
            cert_type=request.POST.get('cert_type', 'upload'),
            cert_url=request.POST.get('cert_url', ''),
        )
        if 'file' in request.FILES:
            cert.file = request.FILES['file']
        cert.save()
        return redirect('student-certifications')


class StudentProjectsView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        projects = Project.objects.filter(student=profile).order_by('-created_at')
        return render(request, 'student_portal/projects.html', {
            'profile': profile, 'projects': projects,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        Project.objects.create(
            student=profile,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            tech_stack=request.POST.get('tech_stack', ''),
            project_type=request.POST.get('project_type', 'external'),
            is_group=request.POST.get('is_group') == 'on',
            team_size=int(request.POST.get('team_size', 1)),
            repo_url=request.POST.get('repo_url', ''),
        )
        return redirect('student-projects')


class StudentInternshipsView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        internships = Internship.objects.filter(student=profile).order_by('-start_date')
        return render(request, 'student_portal/internships.html', {
            'profile': profile, 'internships': internships,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        intp = Internship(
            student=profile,
            organization=request.POST.get('organization', ''),
            role=request.POST.get('role', ''),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date') or None,
            technologies=request.POST.get('technologies', ''),
            description=request.POST.get('description', ''),
            supervisor_name=request.POST.get('supervisor_name', ''),
            supervisor_email=request.POST.get('supervisor_email', ''),
        )
        if 'certificate' in request.FILES:
            intp.certificate = request.FILES['certificate']
        intp.save()
        return redirect('student-internships')


class StudentEventsView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        events = Event.objects.filter(student=profile).order_by('-event_date')
        return render(request, 'student_portal/events.html', {
            'profile': profile, 'events': events,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        Event.objects.create(
            student=profile,
            name=request.POST.get('name', ''),
            scope=request.POST.get('scope', 'External'),
            role=request.POST.get('role', 'Participation'),
            position=request.POST.get('position', ''),
            organizer=request.POST.get('organizer', ''),
            location=request.POST.get('location', ''),
            event_date=request.POST.get('event_date'),
        )
        return redirect('student-events')


class StudentCoursesView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        courses = Course.objects.filter(student=profile).order_by('-created_at')
        return render(request, 'student_portal/courses.html', {
            'profile': profile, 'courses': courses,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        Course.objects.create(
            student=profile,
            title=request.POST.get('title', ''),
            source=request.POST.get('source', 'external'),
            platform=request.POST.get('platform', ''),
            completion_percentage=int(request.POST.get('completion_percentage', 100)),
            certificate_url=request.POST.get('certificate_url', ''),
        )
        return redirect('student-courses')


class StudentResearchView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        research_list = Research.objects.filter(student=profile).order_by('-created_at')
        return render(request, 'student_portal/research.html', {
            'profile': profile, 'research_list': research_list,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        Research.objects.create(
            student=profile,
            title=request.POST.get('title', ''),
            research_type=request.POST.get('research_type', 'external'),
            advisor_name=request.POST.get('advisor_name', ''),
            advisor_email=request.POST.get('advisor_email', ''),
            outcome=request.POST.get('outcome', 'paper'),
            publisher=request.POST.get('publisher', ''),
            publication_url=request.POST.get('publication_url', ''),
            published_date=request.POST.get('published_date') or None,
        )
        return redirect('student-research')


class StudentEducationView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        education = EducationBackground.objects.filter(student=profile)
        return render(request, 'student_portal/education.html', {
            'profile': profile, 'education': education,
            'edu_types': EducationBackground.EduType.choices,
        })

    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        edu_type = request.POST.get('edu_type')
        EducationBackground.objects.update_or_create(
            student=profile, edu_type=edu_type,
            defaults={
                'institution': request.POST.get('institution', ''),
                'board_university': request.POST.get('board_university', ''),
                'year_of_passing': request.POST.get('year_of_passing') or None,
                'score': request.POST.get('score', ''),
                'score_type': request.POST.get('score_type', '%'),
            }
        )
        return redirect('student-education')


class StudentManagementDetailView(LoginRequiredMixin, View):
    """Detailed view for management/faculty to see full student data."""
    def get(self, request, pk):
        if request.user.role not in ['Chairman', 'Director', 'Principal', 'HOD', 'Mentor', 'Faculty']:
            return redirect('dashboard')

        profile = get_object_or_404(StudentProfile, pk=pk)
        education = profile.education.all()
        certifications = profile.certifications.all()
        projects = profile.projects.all()
        internships = profile.internships.all()
        events = profile.events.all()
        courses = profile.courses.all()
        research = profile.research.all()
        marks = Marks.objects.filter(student=profile).select_related('subject')
        
        attendance = Attendance.objects.filter(student=profile)
        total_att = attendance.count()
        present_att = attendance.filter(is_present=True).count()
        absent_att = total_att - present_att
        att_pct = round((present_att / total_att * 100), 1) if total_att else 0

        return render(request, 'students/student_detail.html', {
            'profile': profile,
            'education': education,
            'certifications': certifications,
            'projects': projects,
            'internships': internships,
            'events': events,
            'courses': courses,
            'research': research,
            'marks': marks,
            'att_pct': att_pct,
            'total_classes': total_att,
            'present': present_att,
            'absent': absent_att,
        })


class PublicStudentProfileView(View):
    """Public shareable profile view — /student/p/<slug>/"""
    def get(self, request, slug):
        profile = get_object_or_404(StudentProfile, slug=slug, is_public=True)
        return render(request, 'student_portal/public_profile.html', {
            'profile': profile,
            'education': EducationBackground.objects.filter(student=profile),
            'certifications': Certification.objects.filter(student=profile, is_verified=True),
            'projects': Project.objects.filter(student=profile),
            'internships': Internship.objects.filter(student=profile),
            'events': Event.objects.filter(student=profile),
            'courses': Course.objects.filter(student=profile),
            'research': Research.objects.filter(student=profile),
        })


class TogglePublicProfileView(LoginRequiredMixin, View):
    def post(self, request):
        profile = get_object_or_404(StudentProfile, user=request.user)
        profile.is_public = not profile.is_public
        profile.save()
        return redirect('student-profile-edit')
