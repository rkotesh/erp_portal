from django.core.exceptions import PermissionDenied


class RoleRequiredMixin:
    """Mixin for class-based views that enforces role access."""
    required_role = None  # Set in subclass: required_role = "HOD"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.required_role and request.user.role != self.required_role:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
