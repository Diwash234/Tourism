"""
Bulk operations mixin for DRF viewsets — bulk create, update, delete.
"""
import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer

logger = logging.getLogger(__name__)


class BulkOperationsMixin:
    """
    Adds bulk_create, bulk_update, and bulk_delete actions to a ViewSet.

    Usage:
        class MyViewSet(BulkOperationsMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer

    Endpoints:
        POST   /api/v1/mymodel/bulk-create/  — create multiple objects
        PUT    /api/v1/mymodel/bulk-update/  — update multiple objects
        POST   /api/v1/mymodel/bulk-delete/  — delete multiple objects by ID
    """

    def get_serializer(self, *args, **kwargs):
        """Return a ListSerializer when many=True for bulk operations."""
        if kwargs.get("many", False):
            kwargs.setdefault("child", self.serializer_class())
            return ListSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        """Create multiple objects in one request."""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request):
        """Update multiple objects in one request (each must include 'id')."""
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"error": {"code": "invalid_format", "message": "Expected a list of objects"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = []
        errors = []
        for item in data:
            obj_id = item.get("id")
            if not obj_id:
                errors.append({"id": None, "error": "Missing 'id' field"})
                continue
            try:
                instance = self.get_queryset().get(pk=obj_id)
            except self.get_queryset().model.DoesNotExist:
                errors.append({"id": obj_id, "error": "Object not found"})
                continue
            serializer = self.get_serializer(instance, data=item, partial=True)
            if serializer.is_valid():
                serializer.save()
                updated.append(serializer.data)
            else:
                errors.append({"id": obj_id, "error": serializer.errors})

        return Response({
            "updated": len(updated),
            "errors": len(errors),
            "results": updated,
            "error_details": errors,
        }, status=status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        """Delete multiple objects by ID in one request."""
        ids = request.data.get("ids", [])
        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": {"code": "invalid_format", "message": "Expected {'ids': [...]}"}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(pk__in=ids)
        deleted_count = queryset.count()
        queryset.delete()
        return Response({
            "deleted": deleted_count,
            "requested": len(ids),
        }, status=status.HTTP_200_OK)

    def perform_bulk_create(self, serializer):
        """Override to customize bulk creation behavior."""
        serializer.save()
