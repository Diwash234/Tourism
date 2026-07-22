from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Only Django superusers can assign hotels/create tasks for others."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsSuperAdminOrAssignedAdmin(permissions.BasePermission):
    """
    Super admins can do anything. A regular staff admin can only see/act on
    objects (tasks, hotel assignments) that belong to them.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        owner = getattr(obj, "admin", None) or getattr(obj, "assigned_to", None)
        return owner == request.user