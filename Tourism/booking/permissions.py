from rest_framework import permissions


class IsOwnerOrHotelAdminOrSuperAdmin(permissions.BasePermission):
    """
    A booking/review can be seen or modified by: the user who made it, an
    admin_panel staff admin assigned to that hotel, or a super admin.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user or request.user.is_superuser:
            return True
        from admin_panel.models import HotelAssignment

        return HotelAssignment.objects.filter(hotel=obj.hotel, admin=request.user).exists()

class IsHotelReviewOwnerOrReadOnly(permissions.BasePermission):
    """Public reads; only the review owner may edit or withdraw through traveler APIs."""
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.user_id == request.user.id
