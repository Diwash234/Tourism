"""Media review endpoints: queue, provenance, score assignment, delegation.

These views are the only supported way to change a moderation score. They are
permission-based (see :mod:`tourist.media_review`): an admin/manager may review
directly or delegate the capability to a member, and a member can only review
what was explicitly granted to them.
"""
from __future__ import annotations

from django.contrib.auth.models import Permission
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .media_review import (
    ACTION_REVIEW,
    GRANTABLE_ACTIONS,
    MediaReviewError,
    MediaReviewPermissionError,
    assign_scores,
    audit_delegation,
    can_review_media,
    image_gate_exclusion,
    media_review_capabilities,
    media_review_state,
    provenance,
    resolve_media_gate,
    score_threshold,
)
from .models import (
    Destination,
    DestinationImage,
    StaffCapabilityProfile,
    User,
)
from .permissions import IsAdminOrStaff
from .views_admin import _has_capability, _is_platform_admin, _require_capability, _scope_destination_queryset


class IsMediaReviewer(BasePermission):
    """Authenticated and holding the media review capability."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return bool(IsAdminOrStaff().has_permission(request, view) and can_review_media(user))


def _image_payload(image) -> dict:
    return {
        "id": image.id,
        "destination_id": image.destination_id,
        "destination": getattr(image.destination, "name", None),
        "external_url": image.external_url,
        "source_url": image.source_url,
        "caption": image.caption,
        "verification_status": image.verification_status,
        "is_verified": image.is_verified,
        "authenticity_score": image.authenticity_score,
        "destination_match_score": image.destination_match_score,
        "review_state": media_review_state(image),
        "canonical_exclusion_reason": image_gate_exclusion(image),
        "authenticity_reviewed_by": (
            image.authenticity_score_by.email if image.authenticity_score_by_id else None
        ),
        "destination_match_reviewed_by": (
            image.destination_match_score_by.email
            if image.destination_match_score_by_id
            else None
        ),
    }


class MediaReviewCapabilitiesView(APIView):
    """Report what the calling user may do, and which gate is active."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        return Response(media_review_capabilities(request.user))


class MediaReviewQueueView(APIView):
    """Media awaiting a decision, with the reason each record is held back."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request):
        # Anyone who may review media needs to see the queue, otherwise a
        # delegated reviewer can score an image they cannot find.
        if not _has_capability(request, "images", "view") and not can_review_media(request.user):
            return Response(
                {"detail": "Missing images.view or media review capability."}, status=403
            )
        destinations = _scope_destination_queryset(
            Destination.objects.filter(is_active=True), request.user
        ).values("id")
        queryset = (
            DestinationImage.objects.filter(destination_id__in=destinations)
            .select_related("destination", "authenticity_score_by", "destination_match_score_by")
            .order_by("-is_cover", "-id")
        )
        state_filter = str(request.query_params.get("state") or "").strip()
        reason_filter = str(request.query_params.get("reason") or "").strip()
        try:
            limit = min(int(request.query_params.get("limit", 50)), 200)
        except (TypeError, ValueError):
            limit = 50

        rows = []
        summary: dict[str, int] = {}
        for image in queryset.iterator(chunk_size=500):
            state = media_review_state(image)
            reason = image_gate_exclusion(image)
            summary[state] = summary.get(state, 0) + 1
            if state_filter and state != state_filter:
                continue
            if reason_filter and reason != reason_filter:
                continue
            rows.append(_image_payload(image))
            if len(rows) >= limit:
                break

        return Response(
            {
                "active_gate": resolve_media_gate(),
                "score_threshold": score_threshold(),
                "state_summary": summary,
                "count": len(rows),
                "results": rows,
            }
        )


class MediaReviewDetailView(APIView):
    """Full provenance for one image."""

    permission_classes = [IsAdminOrStaff]

    def get(self, request, image_id):
        if not _has_capability(request, "images", "view") and not can_review_media(request.user):
            return Response(
                {"detail": "Missing images.view or media review capability."}, status=403
            )
        image = DestinationImage.objects.filter(pk=image_id).first()
        if not image:
            return Response({"detail": "Image not found."}, status=404)
        _require_destination_access_for(request, image.destination)
        payload = _image_payload(image)
        payload["provenance"] = provenance(image)
        return Response(payload)


class MediaReviewScoreView(APIView):
    """Assign moderation scores from a reviewer's explicit values.

    No field is ever defaulted: omitting a score leaves it exactly as it was, so
    an unreviewed image keeps NULL scores and reports as awaiting review.
    """

    permission_classes = [IsMediaReviewer]

    def post(self, request, image_id):
        image = DestinationImage.objects.filter(pk=image_id).first()
        if not image:
            return Response({"detail": "Image not found."}, status=404)
        _require_destination_access_for(request, image.destination)

        data = request.data or {}
        if "authenticity_score" not in data and "destination_match_score" not in data \
                and "approve" not in data:
            return Response(
                {
                    "detail": (
                        "Supply authenticity_score, destination_match_score or approve. "
                        "Scores are never assigned automatically."
                    )
                },
                status=400,
            )

        approve_raw = data.get("approve", None)
        approve = None
        if approve_raw is not None:
            approve = str(approve_raw).strip().lower() in {"1", "true", "yes", "on", "approve"}

        try:
            changes = assign_scores(
                image,
                reviewer=request.user,
                authenticity=data.get("authenticity_score", None),
                destination_match=data.get("destination_match_score", None),
                approve=approve,
                note=str(data.get("note") or "")[:500],
            )
        except MediaReviewPermissionError as exc:
            return Response({"detail": str(exc)}, status=403)
        except MediaReviewError as exc:
            return Response({"detail": str(exc)}, status=400)

        image.refresh_from_db()
        return Response(
            {
                "message": "Review recorded.",
                "changes": [change.as_dict() for change in changes],
                "image": _image_payload(image),
                "provenance": provenance(image),
            }
        )


class MediaReviewDelegationView(APIView):
    """Grant or revoke a member's media review capability.

    Only a delegating role may call this, and the grant records who gave it.
    """

    permission_classes = [IsAdminOrStaff]

    def _profile(self, user) -> StaffCapabilityProfile:
        profile, _ = StaffCapabilityProfile.objects.get_or_create(user=user)
        return profile

    def post(self, request):
        from .media_review import delegating_user

        if not delegating_user(request.user):
            return Response(
                {"detail": "Only an admin or manager may delegate media review."},
                status=403,
            )
        email = str((request.data or {}).get("email") or "").strip().lower()
        if not email:
            return Response({"detail": "email is required."}, status=400)
        target = User.objects.filter(email__iexact=email).first()
        if not target:
            return Response({"detail": "User not found."}, status=404)
        if target.pk == request.user.pk:
            return Response({"detail": "You already hold media review."}, status=400)

        requested = (request.data or {}).get("actions") or [ACTION_REVIEW]
        if isinstance(requested, str):
            requested = [requested]
        unknown = [a for a in requested if a not in GRANTABLE_ACTIONS]
        if unknown:
            return Response(
                {"detail": f"Unknown actions: {unknown}. Allowed: {sorted(GRANTABLE_ACTIONS)}"},
                status=400,
            )

        grant = str((request.data or {}).get("grant", "true")).strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
        profile = self._profile(target)
        capabilities = dict(profile.capabilities or {})
        images_actions = set(capabilities.get("images") or [])
        if grant:
            images_actions |= set(requested)
        else:
            images_actions -= set(requested)
        capabilities["images"] = sorted(images_actions)
        profile.capabilities = capabilities
        profile.assigned_by = request.user
        profile.is_active = True
        profile.save()

        audit_delegation(target, request.user, granted=grant, actions=requested)

        # Mirror the capability grant into Django's permission framework so the
        # grant survives a profile reset and shows up in the admin.
        codename = GRANTABLE_ACTIONS[ACTION_REVIEW]
        permission = Permission.objects.filter(
            content_type__app_label="tourist", codename=codename
        ).first()
        if permission is not None:
            if grant:
                target.user_permissions.add(permission)
            else:
                target.user_permissions.remove(permission)

        return Response(
            {
                "message": "Media review capability granted." if grant else "Media review capability revoked.",
                "user": target.email,
                "granted_by": request.user.email,
                "capabilities": media_review_capabilities(target),
            }
        )


def _require_destination_access_for(request, destination):
    """District / hotel-assignment boundary for a media record."""
    if _is_platform_admin(request.user):
        return
    scoped = _scope_destination_queryset(
        Destination.objects.filter(pk=getattr(destination, "pk", None)), request.user
    )
    if not scoped.exists():
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("This destination is outside your assigned scope.")
