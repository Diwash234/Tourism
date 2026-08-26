"""
Tourism/tourist/permissions.py

Reusable DRF permission classes.

Includes:
- Legacy permission classes (so existing imports continue to work)
- New role-based permission classes for the expanded role system
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission

# ---------------------------------------------------------------------
# ROLE SENIORITY
# ---------------------------------------------------------------------

ROLE_SENIORITY = [
    "tourist",
    "guide",
    "staff",
    "hotel_manager",
    "tourist_police",
    "police",
    "hospital_staff",
    "rescue_team",
    "emergency_operator",
    "content_moderator",
    "district_manager",
    "tourism_admin",
    "admin",
    "super_admin",
]


def _seniority_index(role):
    try:
        return ROLE_SENIORITY.index(role)
    except ValueError:
        return -1


# ---------------------------------------------------------------------
# NEW ROLE-BASED PERMISSIONS
# ---------------------------------------------------------------------

class IsRoleOrAbove(BasePermission):
    """
    Example:

    permission_classes = [IsRoleOrAbove(User.Role.TOURISM_ADMIN)]

    Allows the specified role and any role above it.
    """

    def __init__(self, minimum_role):
        self.minimum_role = minimum_role

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return (
            _seniority_index(getattr(request.user, "role", ""))
            >= _seniority_index(self.minimum_role)
        )


class IsEmergencyRole(BasePermission):
    """
    Emergency-related roles only.
    """

    ALLOWED = {
        "tourist_police",
        "police",
        "hospital_staff",
        "rescue_team",
        "emergency_operator",
        "admin",
        "super_admin",
    }

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in self.ALLOWED
        )


class IsDistrictManagerForOwnDistrict(BasePermission):
    """
    District Managers may manage only their district.
    Tourism Admin/Admin/Super Admin bypass this restriction.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if _seniority_index(user.role) >= _seniority_index("tourism_admin"):
            return True

        if user.role != "district_manager":
            return False

        obj_district = (
            getattr(obj, "district", None)
            or getattr(getattr(obj, "destination", None), "district", None)
        )

        return (
            bool(obj_district)
            and obj_district == user.managed_district
        )


class HasCapabilityOrReadOnly(BasePermission):
    """Public/authenticated reads remain compatible; writes require module capability."""
    message = "You do not have permission to modify this resource."
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}:
            return True
        module = getattr(view, "capability_module", None)
        action = {"POST":"add","PUT":"change","PATCH":"change","DELETE":"delete"}.get(request.method, "view")
        try:
            return bool(module and user.capability_profile.allows(module, action))
        except Exception:
            return False


class HasCapability(BasePermission):
    """Backend-enforced module/action permission for staff; admins bypass."""
    message = "You do not have the required staff capability."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}:
            return True
        module = getattr(view, "capability_module", None)
        action_map = {"GET": "view", "HEAD": "view", "OPTIONS": "view", "POST": "add", "PUT": "change", "PATCH": "change", "DELETE": "delete"}
        action = getattr(view, "capability_action", action_map.get(request.method, "view"))
        if not module:
            return False
        try:
            return user.capability_profile.allows(module, action)
        except Exception:
            return False


# ---------------------------------------------------------------------
# LEGACY PERMISSIONS
# ---------------------------------------------------------------------

class IsAdminOrStaff(BasePermission):
    """Allows Super Admins, Admins, Tourism Admins, and Staff/Sub-admins."""
    ALLOWED_ROLES = {
        "admin", "super_admin", "tourism_admin", "staff",
        "content_moderator", "district_manager", "guide",
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.role in self.ALLOWED_ROLES
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Anyone can read.
    Only staff/admin users can create/update/delete.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Anyone can read.
    Only the owner or staff may edit/delete.
    """

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        owner = getattr(obj, self.owner_field, None)

        return owner == request.user or request.user.is_staff


class IsOwner(permissions.BasePermission):
    """
    Only the owner or staff may access.
    """

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, self.owner_field, None)

        return owner == request.user or request.user.is_staff


class CanSubmitPlace(permissions.BasePermission):
    """
    Destination permissions:

    - Anyone can read.
    - Authenticated users can submit places.
    - Only the submitter (while pending) or staff can edit/delete.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(
            request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        return (
            obj.created_by == request.user
            and obj.status == obj.SubmissionStatus.PENDING
        )