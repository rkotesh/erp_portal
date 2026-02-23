from django.http import HttpResponseForbidden


class RoleMiddleware:
    ROLE_URL_MAP = {
        '/admin-portal/': ['Chairman', 'Director', 'Principal'],
        '/faculty/':       ['HOD', 'Mentor', 'Faculty', 'Chairman', 'Director', 'Principal'],
        '/students/':      ['Student', 'Chairman', 'Director', 'Principal', 'Placement'],
        '/student/':       ['Student', 'Chairman', 'Director', 'Principal', 'HOD', 'Mentor', 'Faculty'],
        '/reports/':       ['Chairman', 'Director', 'Placement'],
        '/hr/':            ['HR', 'Chairman'],
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            for prefix, roles in self.ROLE_URL_MAP.items():
                if request.path.startswith(prefix):
                    if request.user.role not in roles:
                        return HttpResponseForbidden('Access Denied')
        return self.get_response(request)
