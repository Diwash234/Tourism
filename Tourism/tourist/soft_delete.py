"""
Soft delete mixin — marks objects as deleted instead of removing them.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet with soft delete support."""

    def delete(self):
        """Soft delete all objects in the queryset."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Actually delete objects from the database."""
        return super().delete()

    def alive(self):
        """Return only non-deleted objects."""
        return self.filter(is_deleted=False)

    def dead(self):
        """Return only deleted objects."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def with_deleted(self):
        """Include soft-deleted objects."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self):
        """Only soft-deleted objects."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)


class SoftDeleteMixin:
    """
    Mixin to add soft delete to a model.

    Usage:
        class MyModel(SoftDeleteMixin, models.Model):
            # your fields here
            pass

    Adds:
        - is_deleted (BooleanField)
        - deleted_at (DateTimeField)
        - objects (SoftDeleteManager — excludes deleted by default)
        - all_objects (Manager — includes deleted)
        - delete() — soft delete
        - hard_delete() — actually delete
        - restore() — un-delete
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete this object."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete from the database."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])
