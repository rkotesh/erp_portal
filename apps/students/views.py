from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.db.models import Avg
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from django.conf import settings
import random
import re
import os
from apps.students.models import (
    StudentProfile, EducationBackground, Certification,
    Project, Internship, Event, Course, Research, SemesterResult
)
from apps.accounts.models import OTPRecord
from apps.academics.models import Subject, Marks
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.students.serializers import StudentProfileSerializer
from apps.students.permissions import IsStudentOwnerOrReadOnly


EXAM_CELL_ROLES = ['Chairman', 'Director', 'Principal', 'HOD', 'Faculty']


def _extract_cert_metadata(cert_url):
    """Best-effort metadata extraction from cert URL."""
    derived = {}
    if not cert_url:
        return derived
    try:
        req = Request(cert_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=5) as resp:
            html = resp.read(250000).decode('utf-8', errors='ignore')

        og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        title_tag = re.search(r'<title>(.*?)</title>', html, re.I | re.S)
        date_meta = re.search(r'(\d{4}-\d{2}-\d{2})', html)

        if og_title:
            derived['title'] = og_title.group(1).strip()
        elif title_tag:
            derived['title'] = re.sub(r'\s+', ' ', title_tag.group(1)).strip()

        issuer = urlparse(cert_url).netloc.replace('www.', '')
        if issuer:
            derived['issuer'] = issuer
        if date_meta:
            derived['issued_date'] = date_meta.group(1)
    except Exception:
        pass
    return derived


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
        subject_stats = {}
        for sub in Subject.objects.filter(department=profile.department):
            sub_marks = marks.filter(subject=sub).first()
            internal = sub_marks.internal if sub_marks else '-'
            external = sub_marks.external if sub_marks else '-'
            subject_stats[sub.id] = {
                'subject_name': sub.name,
                'subject_code': sub.code,
                'semester': sub.semester,
                'credits': sub.credits,
                'internal': internal,
                'external': external,
            }

        def _cert_preview(c):
            if not c.file:
                return None
            ext = os.path.splitext(c.file.name.lower())[1]
            if ext in ['.png', '.jpg', '.jpeg', '.webp']:
                return c.file.url
            return None

        activity_posts = []
        for c in profile.certifications.all().order_by('-created_at')[:8]:
            activity_posts.append({
                'kind': 'Certification',
                'title': c.title,
                'subtitle': c.issuer,
                'created_at': c.created_at,
                'preview_image': _cert_preview(c),
                'file_url': c.file.url if c.file else '',
                'external_url': c.cert_url,
                'verified': c.is_verified,
            })
        for p in profile.projects.all().order_by('-created_at')[:8]:
            activity_posts.append({
                'kind': 'Project',
                'title': p.title,
                'subtitle': p.tech_stack,
                'created_at': p.created_at,
                'preview_image': p.cover_image.url if p.cover_image else None,
                'file_url': '',
                'external_url': p.repo_url,
                'verified': p.is_verified,
            })
        if profile.resume:
            activity_posts.append({
                'kind': 'Resume',
                'title': 'Updated Resume',
                'subtitle': 'Curriculum Vitae',
                'created_at': profile.updated_at,
                'preview_image': None,
                'file_url': profile.resume.url,
                'external_url': '',
                'verified': True,
            })
        activity_posts = sorted(activity_posts, key=lambda x: x['created_at'], reverse=True)[:12]

        return render(request, 'student_portal/dashboard.html', {
            'profile': profile,
            'subject_stats': subject_stats,
            'activity_posts': activity_posts,
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
        linkedin_url = request.POST.get('linkedin_url', '').strip()
        if not linkedin_url:
            messages.error(request, 'LinkedIn profile is required.')
            return redirect('student-profile-edit')

        personal_email = request.POST.get('personal_email', '').strip()
        personal_phone = request.POST.get('personal_phone', '').strip()
        if personal_email != profile.personal_email:
            profile.personal_email_verified = False
        if personal_phone != profile.personal_phone:
            profile.personal_phone_verified = False
        profile.personal_email = personal_email
        profile.personal_phone = personal_phone

        # Links
        for field in ['linkedin_url', 'github_url', 'leetcode_url',
                      'hackerrank_url', 'codechef_url', 'codeforces_url']:
            setattr(profile, field, request.POST.get(field, '').strip())
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        if 'resume' in request.FILES:
            profile.resume = request.FILES['resume']
        profile.save()
        return redirect('student-profile-edit')


class StudentAcademicsView(LoginRequiredMixin, View):
    """View-only semester marks published by institution staff."""
    def get(self, request):
        if request.user.role != 'Student':
            return redirect('dashboard')
        profile = get_object_or_404(StudentProfile, user=request.user)
        marks = Marks.objects.filter(student=profile).select_related('subject', 'subject__department')
        subject_stats = {}
        for sub in Subject.objects.filter(department=profile.department):
            sub_marks = marks.filter(subject=sub).first()
            internal = sub_marks.internal if sub_marks else '-'
            external = sub_marks.external if sub_marks else '-'
            total = sub_marks.total if sub_marks else '-'
            grade = sub_marks.grade if sub_marks and sub_marks.grade else '-'
            
            subject_stats[sub.id] = {
                'subject_name': sub.name,
                'subject_code': sub.code,
                'semester': sub.semester,
                'credits': sub.credits,
                'internal': internal,
                'external': external,
                'total': total,
                'grade': grade,
            }

        return render(request, 'student_portal/academics.html', {
            'profile': profile,
            'marks': marks,
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
        action = request.POST.get('action', 'create')
        if action == 'delete':
            cert_id = request.POST.get('cert_id')
            cert = get_object_or_404(Certification, id=cert_id, student=profile)
            cert.delete()
            messages.success(request, 'Certification removed.')
            return redirect('student-certifications')

        cert_type = request.POST.get('cert_type', 'upload')
        cert_url = request.POST.get('cert_url', '').strip()
        title = request.POST.get('title', '').strip()
        issuer = request.POST.get('issuer', '').strip()
        issued_date = request.POST.get('issued_date', '').strip()

        if cert_type == 'link':
            derived = _extract_cert_metadata(cert_url)
            title = title or derived.get('title', '')
            issuer = issuer or derived.get('issuer', '')
            issued_date = issued_date or derived.get('issued_date', '')

        if not title:
            title = 'External Certification'
        if not issuer:
            issuer = 'Self Reported'
        if not issued_date:
            issued_date = str(timezone.now().date())

        cert = Certification(
            student=profile,
            title=title,
            issuer=issuer,
            issued_date=issued_date,
            cert_type=cert_type,
            cert_url=cert_url,
            is_verified=False,
            verified_by=None,
            verified_at=None,
            rejection_reason='',
        )
        if 'file' in request.FILES:
            cert.file = request.FILES['file']
        cert.save()
        messages.success(request, 'Certification submitted for verification.')
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
        action = request.POST.get('action', 'create')
        if action == 'delete':
            project_id = request.POST.get('project_id')
            project = get_object_or_404(Project, id=project_id, student=profile)
            project.delete()
            messages.success(request, 'Project removed.')
            return redirect('student-projects')

        project = Project.objects.create(
            student=profile,
            title=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            tech_stack=request.POST.get('tech_stack', ''),
            project_type=request.POST.get('project_type', 'external'),
            is_group=request.POST.get('is_group') == 'on',
            team_size=int(request.POST.get('team_size', 1)),
            repo_url=request.POST.get('repo_url', ''),
        )
        if 'cover_image' in request.FILES:
            project.cover_image = request.FILES['cover_image']
            project.save(update_fields=['cover_image', 'updated_at'])
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
        semester_results = profile.semester_results.all()
        marks = Marks.objects.filter(student=profile).select_related('subject')

        return render(request, 'students/student_detail.html', {
            'profile': profile,
            'education': education,
            'certifications': certifications,
            'projects': projects,
            'internships': internships,
            'events': events,
            'courses': courses,
            'research': research,
            'semester_results': semester_results,
            'marks': marks,
        })

    def post(self, request, pk):
        if request.user.role not in EXAM_CELL_ROLES:
            return redirect('dashboard')
        action = request.POST.get('action')
        approve = request.POST.get('decision') == 'approve'
        reason = request.POST.get('reason', '').strip()

        if action == 'verify_education':
            edu = get_object_or_404(EducationBackground, id=request.POST.get('item_id'))
            edu.is_verified = approve
            edu.verified_by = request.user if approve else None
            edu.save(update_fields=['is_verified', 'verified_by', 'updated_at'])
        elif action == 'verify_certification':
            cert = get_object_or_404(Certification, id=request.POST.get('item_id'))
            cert.is_verified = approve
            cert.verified_by = request.user if approve else None
            cert.verified_at = timezone.now() if approve else None
            cert.rejection_reason = '' if approve else reason
            cert.save(update_fields=['is_verified', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])
        elif action == 'verify_semester_result':
            result = get_object_or_404(SemesterResult, id=request.POST.get('item_id'))
            result.is_verified = approve
            result.verified_by = request.user if approve else None
            result.verified_at = timezone.now() if approve else None
            result.rejection_reason = '' if approve else reason
            result.save(update_fields=['is_verified', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])
        return redirect('student-detail', pk=pk)


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


class StudentContactOtpView(LoginRequiredMixin, View):
    """Send/verify OTP for personal email and phone."""
    def post(self, request):
        if request.user.role != 'Student':
            return JsonResponse({'ok': False, 'error': 'Unauthorized'}, status=403)

        profile = get_object_or_404(StudentProfile, user=request.user)
        target = request.POST.get('target')
        action = request.POST.get('otp_action')
        if target not in ['email', 'phone']:
            return JsonResponse({'ok': False, 'error': 'Invalid target'}, status=400)

        purpose = f'student_{target}_verify'
        if action == 'send':
            destination = request.POST.get('destination', '').strip()
            if not destination:
                destination = profile.personal_email if target == 'email' else profile.personal_phone
            if not destination:
                return JsonResponse({'ok': False, 'error': f'Provide {target} first'}, status=400)

            if target == 'email':
                if destination != profile.personal_email:
                    profile.personal_email = destination
                    profile.personal_email_verified = False
                    profile.save(update_fields=['personal_email', 'personal_email_verified', 'updated_at'])
            else:
                if destination != profile.personal_phone:
                    profile.personal_phone = destination
                    profile.personal_phone_verified = False
                    profile.save(update_fields=['personal_phone', 'personal_phone_verified', 'updated_at'])

            code = f"{random.randint(100000, 999999)}"
            OTPRecord.objects.create(
                user=request.user,
                otp_code=code,
                purpose=purpose,
                expires_at=timezone.now() + timezone.timedelta(minutes=10)
            )
            if target == 'email':
                from apps.accounts.otp_services import send_otp_email
                ok, info = send_otp_email(request.user, code, purpose, destination_email=destination)
                if not ok:
                    return JsonResponse({'ok': False, 'error': f'Email OTP send failed: {info}'}, status=500)
                if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                    return JsonResponse({
                        'ok': True,
                        'message': f'OTP generated for email. Current backend is console, check runserver terminal output.'
                    })
            else:
                from apps.accounts.otp_services import send_otp_sms_to_phone
                ok, info = send_otp_sms_to_phone(destination, code, purpose, user_email=request.user.email)
                if not ok:
                    return JsonResponse({'ok': False, 'error': f'SMS OTP send failed: {info}'}, status=500)
            return JsonResponse({'ok': True, 'message': f'OTP sent to {target}'})

        if action == 'verify':
            otp = request.POST.get('otp', '').strip()
            otp_rec = OTPRecord.objects.filter(
                user=request.user,
                purpose=purpose,
                otp_code=otp,
                is_used=False,
                expires_at__gt=timezone.now()
            ).first()
            if not otp_rec:
                return JsonResponse({'ok': False, 'error': 'Invalid or expired OTP'}, status=400)
            otp_rec.is_used = True
            otp_rec.save(update_fields=['is_used', 'updated_at'])

            if target == 'email':
                profile.personal_email_verified = True
            else:
                profile.personal_phone_verified = True
            profile.save(update_fields=['personal_email_verified', 'personal_phone_verified', 'updated_at'])
            return JsonResponse({'ok': True, 'message': f'{target.capitalize()} verified'})

        return JsonResponse({'ok': False, 'error': 'Invalid OTP action'}, status=400)


class StudentVerificationQueueView(LoginRequiredMixin, View):
    """Exam cell verification queue for student-submitted data."""
    def get(self, request):
        if request.user.role not in EXAM_CELL_ROLES:
            return redirect('dashboard')
        pending_education = EducationBackground.objects.filter(is_verified=False).select_related('student__user')
        pending_certs = Certification.objects.filter(is_verified=False).select_related('student__user')
        pending_results = SemesterResult.objects.filter(is_verified=False).select_related('student__user')
        return render(request, 'students/verification_queue.html', {
            'pending_education': pending_education,
            'pending_certs': pending_certs,
            'pending_results': pending_results,
        })

    def post(self, request):
        if request.user.role not in EXAM_CELL_ROLES:
            return redirect('dashboard')
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        decision = request.POST.get('decision')
        approve = decision == 'approve'
        reason = request.POST.get('reason', '').strip()

        if item_type == 'education':
            edu = get_object_or_404(EducationBackground, id=item_id)
            edu.is_verified = approve
            edu.verified_by = request.user if approve else None
            edu.save(update_fields=['is_verified', 'verified_by', 'updated_at'])
        elif item_type == 'certification':
            cert = get_object_or_404(Certification, id=item_id)
            cert.is_verified = approve
            cert.verified_by = request.user if approve else None
            cert.verified_at = timezone.now() if approve else None
            cert.rejection_reason = '' if approve else reason
            cert.save(update_fields=['is_verified', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])
        elif item_type == 'semester_result':
            result = get_object_or_404(SemesterResult, id=item_id)
            result.is_verified = approve
            result.verified_by = request.user if approve else None
            result.verified_at = timezone.now() if approve else None
            result.rejection_reason = '' if approve else reason
            result.save(update_fields=['is_verified', 'verified_by', 'verified_at', 'rejection_reason', 'updated_at'])
        return redirect('student-verification-queue')
