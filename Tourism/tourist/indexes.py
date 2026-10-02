"""
Database index definitions for query optimization.
These should be added to model Meta classes.
"""
from django.db import models


class DestinationIndexes:
    """Recommended indexes for Destination model."""
    indexes = [
        models.Index(fields=["slug"], name="dest_slug_idx"),
        models.Index(fields=["is_published", "is_featured"], name="dest_pub_feat_idx"),
        models.Index(fields=["province", "district"], name="dest_prov_dist_idx"),
        models.Index(fields=["category", "is_published"], name="dest_cat_pub_idx"),
        models.Index(fields=["average_rating"], name="dest_rating_idx"),
        models.Index(fields=["created_at"], name="dest_created_idx"),
        models.Index(fields=["latitude", "longitude"], name="dest_coords_idx"),
    ]


class ReviewIndexes:
    """Recommended indexes for Review model."""
    indexes = [
        models.Index(fields=["destination", "is_approved"], name="rev_dest_appr_idx"),
        models.Index(fields=["user", "created_at"], name="rev_user_created_idx"),
        models.Index(fields=["rating"], name="rev_rating_idx"),
    ]


class UserIndexes:
    """Recommended indexes for User model."""
    indexes = [
        models.Index(fields=["email"], name="user_email_idx"),
        models.Index(fields=["role", "is_active"], name="user_role_active_idx"),
        models.Index(fields=["date_joined"], name="user_joined_idx"),
        models.Index(fields=["last_login"], name="user_login_idx"),
    ]


class AuditLogIndexes:
    """Recommended indexes for AuditLog model."""
    indexes = [
        models.Index(fields=["created_at"], name="audit_created_idx"),
        models.Index(fields=["user", "created_at"], name="audit_user_created_idx"),
        models.Index(fields=["action", "created_at"], name="audit_action_created_idx"),
        models.Index(fields=["category", "created_at"], name="audit_cat_created_idx"),
    ]
