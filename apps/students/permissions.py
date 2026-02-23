from rest_framework import permissions


class IsStudentOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow students to edit their own profile.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
