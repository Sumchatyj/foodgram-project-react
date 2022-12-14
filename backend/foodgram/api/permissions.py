from rest_framework import permissions


class IsAuthorOrStaffOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_staff
        )

    def has_permission(self, request, view):
        return (
            not request.user.is_anonymous
            or request.method in permissions.SAFE_METHODS
        )
