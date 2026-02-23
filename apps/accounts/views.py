from django.contrib.auth import logout, login, authenticate
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.core.cache import cache
from apps.accounts.models import User

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class LoginView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    """
    Unified login: accepts roll number (students) or email (all roles).
    All user accounts are pre-created by admin.
    Includes IP-based brute-force rate limiting.
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html', {})

    def post(self, request, *args, **kwargs):
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

        ip = get_client_ip(request)
        cache_key = f'login_attempts_{ip}'

        # ── Rate limit check ──
        attempts = cache.get(cache_key, 0)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            return render(request, 'login.html', {
                'error': 'Too many login attempts. Please wait 5 minutes before trying again.',
                'identifier': identifier,
                'selected_role': role,
            })

        if not identifier or not password or not role:
            return render(request, 'login.html', {
                'error': 'Please fill in all fields and select your role.',
                'identifier': identifier,
                'selected_role': role,
            })

        # ── Look up user by email or roll number ──
        user = None

        # Try email first
        try:
            user = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            pass

        # If not found by email, try roll number (students and parents)
        if user is None and role in ['Student', 'Parent']:
            from apps.students.models import StudentProfile
            try:
                profile = StudentProfile.objects.select_related('user').get(roll_no__iexact=identifier)
                user = profile.user
            except StudentProfile.DoesNotExist:
                pass

        # ── Validate ──
        if user is None:
            cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
            return render(request, 'login.html', {
                'error': 'No account found with this ID. Contact your admin.',
                'identifier': identifier,
                'selected_role': role,
            })

        if not user.is_active:
            return render(request, 'login.html', {
                'error': 'Your account is inactive. Contact your admin.',
                'identifier': identifier,
                'selected_role': role,
            })

        # ALLOW Parent role to log in as Student
        if user.role != role:
            if role == 'Parent' and user.role == 'Student':
                # Allow it, we'll handle the redirect in DashboardView or set a session flag
                request.session['is_parent_login'] = True
            else:
                cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
                return render(request, 'login.html', {
                    'error': f'This account is registered as {user.role}, not {role}.',
                    'identifier': identifier,
                    'selected_role': role,
                })

        # Check password
        if not user.check_password(password):
            cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
            remaining = MAX_LOGIN_ATTEMPTS - (attempts + 1)
            error_msg = 'Incorrect password. Try again or use Forgot Password.'
            if remaining <= 2 and remaining > 0:
                error_msg += f' ({remaining} attempts remaining)'
            return render(request, 'login.html', {
                'error': error_msg,
                'identifier': identifier,
                'selected_role': role,
            })

        # ── Success — log in and track IP ──
        cache.delete(cache_key)  # Reset attempts on success
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])
        login(request, user)
        return redirect('dashboard')


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('login'))

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('login'))

