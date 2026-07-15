from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Anyone can read; only staff/admin users can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Anyone can read; only the object's owner can update/delete it."""

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, self.owner_field, None)
        return owner == request.user or request.user.is_staff


class IsOwner(permissions.BasePermission):
    """Only the owner (or staff) may access the object at all."""

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, self.owner_field, None)
        return owner == request.user or request.user.is_staff


class CanSubmitPlace(permissions.BasePermission):
    """
    Destination access rules:
      - Anyone can read (list/retrieve) approved, active destinations.
      - Any authenticated user can submit (POST) a new place.
      - Only the original submitter (while still pending) or staff can
        update/delete a destination.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        return obj.created_by == request.user and obj.status == obj.SubmissionStatus.PENDING