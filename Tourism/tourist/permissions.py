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


class IsRoleOrAboveForWriteOnly(IsRoleOrAbove):
    """
    ADDED: same role gate as IsRoleOrAbove, but GET/HEAD/OPTIONS are
    always allowed through, for anyone (including anonymous visitors).

    Fixes a real bug: HotelViewSet's own docstring says "Public read;
    admin write", but it was using plain IsRoleOrAbove, which has no
    read/write distinction at all -- has_permission() rejects everyone
    below the minimum role regardless of HTTP method. That meant an
    anonymous tourist browsing hotels (the actual public-facing
    Hotels/HotelSearch pages) got a 401 trying to just list them,
    confirmed live against the real API. Kept as a separate class
    rather than changing IsRoleOrAbove itself, since the other two
    call sites (destination approval, emergency-role actions) are
    legitimately gated for both read and write by design.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_permission(request, view)


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


# ---------------------------------------------------------------------
# LEGACY PERMISSIONS
# ---------------------------------------------------------------------

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