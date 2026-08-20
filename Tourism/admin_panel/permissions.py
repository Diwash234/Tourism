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
        user = request.user
        if not user or not user.is_authenticated or not user.is_staff: return False
        if user.is_superuser or getattr(user,"role",None) in {"admin","super_admin","tourism_admin"}: return True
        module = "hotels" if "hotel" in getattr(view,"basename","") else "dashboard"
        try: return user.capability_profile.allows(module,"view")
        except Exception: return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        owner = getattr(obj, "admin", None) or getattr(obj, "assigned_to", None)
        return owner == request.user