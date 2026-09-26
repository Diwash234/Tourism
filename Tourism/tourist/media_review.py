"""Permission-based media review and moderation score assignment.

Design rules
------------
1. Scores are never invented. Nothing in this module (or in the release gate it
   feeds) writes a score that a human did not supply. An unreviewed image keeps
   ``NULL`` scores and is reported as *awaiting media review*.
2. Review authority is permission-based, not role-name-based. A member may
   review media because an admin/manager granted the permission, never because
   of a username or a hard-coded role string.
3. Every score write records *who* wrote it and *when*, so provenance is
   queryable and a fabricated-looking value is distinguishable from a reviewed
   one. Existing scores are never backfilled with a guess: their provenance
   stays NULL, which is the honest representation of "nobody signed this".
4. The canonical release gate is configurable, and the active rule is recorded
   in the published payload so a release always states which rule produced it.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.utils import timezone

# --- Canonical media gate -------------------------------------------------
# "scored"   : approved + verified + score >= threshold for both scores
#              (the historical rule; requires a completed human review)
# "approval" : the rule the running application actually applies
#              (approved + verified + destination-specific match), with no score
#              requirement, because those scores were never legitimately set
GATE_SCORED = "scored"
GATE_APPROVAL = "approval"
MEDIA_GATES = (GATE_SCORED, GATE_APPROVAL)

DEFAULT_SCORE_THRESHOLD = 0.85

# --- Permissions ----------------------------------------------------------
PERMISSION_REVIEW = "tourist.review_destinationimage"
PERMISSION_AUTHENTICITY = "tourist.assign_destinationimage_authenticity"
PERMISSION_DESTINATION_MATCH = "tourist.assign_destinationimage_destination_match"
PERMISSION_APPROVE_REVIEW = "tourist.approve_destinationimage_review"

MEDIA_REVIEW_PERMISSIONS = (
    PERMISSION_REVIEW,
    PERMISSION_AUTHENTICITY,
    PERMISSION_DESTINATION_MATCH,
    PERMISSION_APPROVE_REVIEW,
)

# Roles that may review and may delegate the capability to a member.  This is a
# convenience tier, not the source of truth: a member granted the permission
# below can review even without one of these roles, and a user with none of
# them still cannot review unless the permission was granted.
DELEGATING_ROLES = frozenset(
    {
        "admin",
        "super_admin",
        "tourism_admin",
        "content_moderator",
        "district_manager",
    }
)

# --- Review states surfaced to the UI and the release report -------------
STATE_ELIGIBLE = "eligible_under_application_rule"
STATE_AWAITING_REVIEW = "awaiting_media_review"
STATE_BELOW_THRESHOLD = "reviewed_below_threshold"
STATE_CANONICAL = "approved_for_canonical_release"

REVIEW_STATES = (
    STATE_ELIGIBLE,
    STATE_AWAITING_REVIEW,
    STATE_BELOW_THRESHOLD,
    STATE_CANONICAL,
)


def _setting(name: str, default: Any = None) -> Any:
    """Read a setting, falling back to the environment then the default.

    Reading the environment directly keeps this toggle usable without editing
    settings.py, which is convenient for a per-release build.
    """
    value = getattr(settings, name, None)
    if value not in (None, ""):
        return value
    env_value = os.environ.get(name)
    if env_value not in (None, ""):
        return env_value
    return default


def resolve_media_gate() -> str:
    """Return the active canonical media gate: 'scored' or 'approval'."""
    raw = str(_setting("PUBLIC_SNAPSHOT_MEDIA_GATE", GATE_SCORED) or GATE_SCORED)
    gate = raw.strip().lower()
    if gate not in MEDIA_GATES:
        raise ValueError(
            f"PUBLIC_SNAPSHOT_MEDIA_GATE must be one of {MEDIA_GATES}, got {raw!r}"
        )
    return gate


def score_threshold() -> float:
    raw = _setting("PUBLIC_SNAPSHOT_SCORE_THRESHOLD", DEFAULT_SCORE_THRESHOLD)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_SCORE_THRESHOLD
    if not 0.0 < value <= 1.0:
        return DEFAULT_SCORE_THRESHOLD
    return value


def requires_review_provenance() -> bool:
    """When true, a score without a named reviewer counts as unreviewed.

    This is how legacy scores written by import scripts (never by a human) are
    kept out of the canonical release without rewriting them.
    """
    raw = _setting("PUBLIC_SNAPSHOT_REQUIRE_REVIEW_PROVENANCE", "true")
    return str(raw).strip().lower() not in {"0", "false", "no", "off", ""}


# --- Capability resolution ------------------------------------------------


def _is_delegating_role(user) -> bool:
    role = getattr(user, "role", "") or ""
    return role in DELEGATING_ROLES


def _has_django_permission(user, codename: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    try:
        return bool(user.has_perm(f"tourist.{codename}"))
    except Exception:  # pragma: no cover - defensive around auth backends
        return False


def _capability_profile(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None
    try:
        from .models import StaffCapabilityProfile

        # Read the row directly so a grant takes effect on the next request
        # even when Django cached the reverse OneToOne relation.
        return StaffCapabilityProfile.objects.filter(user=user).first()
    except Exception:  # pragma: no cover - table may not exist pre-migrate
        return None


def _capability_profile_allows(user, action: str) -> bool:
    profile = _capability_profile(user)
    return bool(profile and profile.is_active and profile.allows("images", action))


# CapabilityProfile ACTIONS used for media review delegation.
ACTION_REVIEW = "review"
ACTION_SCORE_AUTHENTICITY = "score_authenticity"
ACTION_SCORE_DESTINATION_MATCH = "score_destination_match"
ACTION_APPROVE_REVIEW = "approve_review"

# Actions a delegating profile must be able to grant, mapped to permissions.
GRANTABLE_ACTIONS = {
    ACTION_REVIEW: PERMISSION_REVIEW,
    ACTION_SCORE_AUTHENTICITY: PERMISSION_AUTHENTICITY,
    ACTION_SCORE_DESTINATION_MATCH: PERMISSION_DESTINATION_MATCH,
    ACTION_APPROVE_REVIEW: PERMISSION_APPROVE_REVIEW,
}


def can_review_media(user) -> bool:
    return (
        _has_django_permission(user, "review_destinationimage")
        or _is_delegating_role(user)
        or _capability_profile_allows(user, ACTION_REVIEW)
    )


def can_assign_authenticity(user) -> bool:
    return (
        _has_django_permission(user, "assign_destinationimage_authenticity")
        or _is_delegating_role(user)
        or _capability_profile_allows(user, ACTION_SCORE_AUTHENTICITY)
    )


def can_assign_destination_match(user) -> bool:
    return (
        _has_django_permission(user, "assign_destinationimage_destination_match")
        or _is_delegating_role(user)
        or _capability_profile_allows(user, ACTION_SCORE_DESTINATION_MATCH)
    )


def can_approve_review(user) -> bool:
    return (
        _has_django_permission(user, "approve_destinationimage_review")
        or _is_delegating_role(user)
        or _capability_profile_allows(user, ACTION_APPROVE_REVIEW)
    )


def delegating_user(user) -> bool:
    """True when this user may grant the review capability to somebody else."""
    return _is_delegating_role(user) or bool(
        user and getattr(user, "is_superuser", False)
    )


def media_review_capabilities(user) -> dict[str, Any]:
    """Answer, for one user, every question the review workflow must decide."""
    profile = _capability_profile(user)
    granted_by = None
    granted_at = None
    if profile is not None and profile.assigned_by_id:
        granted_by = profile.assigned_by
        granted_at = profile.updated_at
    return {
        "user": getattr(user, "email", None) or str(user),
        "is_superuser": bool(getattr(user, "is_superuser", False)),
        "role": getattr(user, "role", None),
        "can_review_media": can_review_media(user),
        "can_assign_authenticity": can_assign_authenticity(user),
        "can_assign_destination_match": can_assign_destination_match(user),
        "can_approve_review": can_approve_review(user),
        "can_delegate": delegating_user(user),
        "capability_granted_by": getattr(granted_by, "email", None),
        "capability_granted_at": granted_at.isoformat() if granted_at else None,
        "active_gate": resolve_media_gate(),
        "score_threshold": score_threshold(),
    }


# --- Gate evaluation ------------------------------------------------------


def is_destination_specific(image, destination=None) -> bool:
    """Reuse the running application's own name-match rule for an image.

    The canonical release and the website must not disagree about which photo
    belongs to which place, so this delegates to the single implementation the
    API already uses.
    """
    from .serializers import is_destination_specific_image

    target = destination if destination is not None else getattr(image, "destination", None)
    if target is None:
        return False
    return bool(is_destination_specific_image(target, image))


def image_satisfies_application_rule(image, destination=None) -> bool:
    """The rule the running site applies, and nothing more.

    Mirrors ``serializers.verified_destination_photos``: approved, verified, and
    a remote URL the site can render. Attribution (``source_url``) is *not* part
    of it -- the site can show a photo without attribution -- so requiring it
    here would mislabel this as the application's rule. It stays a release-only
    requirement in :func:`image_gate_exclusion`.
    """
    from .models import DestinationImage as _Image

    if image.verification_status != _Image.ImageStatus.APPROVED:
        return False
    if not image.is_verified:
        return False
    if not (image.external_url or "").strip():
        return False
    return is_destination_specific(image, destination)


def score_is_reviewed(image, field: str) -> bool:
    """True when a score value exists and a named reviewer stands behind it."""
    if getattr(image, field, None) is None:
        return False
    if not requires_review_provenance():
        return True
    attribution = f"{field}_by"
    stamp = f"{field}_at"
    return bool(getattr(image, attribution, None) and getattr(image, stamp, None))


def image_gate_exclusion(image, destination=None) -> str | None:
    """Return why an image is excluded from the canonical release, or None.

    Returning a reason instead of a bare boolean is what lets the release tell
    an operator *why* a record is missing rather than silently shrinking.
    """
    from .models import DestinationImage as _Image

    if image.verification_status != _Image.ImageStatus.APPROVED:
        return "not_approved"
    if not image.is_verified:
        return "not_verified"
    if not (image.external_url or "").strip():
        return "missing_external_url"
    if not (image.source_url or "").strip():
        return "missing_source_url"
    if not is_destination_specific(image, destination):
        return "not_destination_specific"
    if image.verification_status == _Image.ImageStatus.PENDING:
        return "awaiting_approval"

    gate = resolve_media_gate()
    if gate == GATE_APPROVAL:
        # The application rule is the whole rule; no score is required.
        return None

    threshold = score_threshold()
    if image.destination_match_score is None or image.authenticity_score is None:
        return "awaiting_media_review"
    if requires_review_provenance():
        if not score_is_reviewed(image, "authenticity_score"):
            return "authenticity_score_unreviewed"
        if not score_is_reviewed(image, "destination_match_score"):
            return "destination_match_score_unreviewed"
    if image.destination_match_score < threshold:
        return "destination_match_score_below_threshold"
    if image.authenticity_score < threshold:
        return "authenticity_score_below_threshold"
    return None


def image_is_canonical(image, destination=None) -> bool:
    return image_gate_exclusion(image, destination) is None


def media_review_state(image, destination=None) -> str:
    """Classify one image for the review UI and the release report.

    The four states are non-overlapping and ordered by what an operator can act
    on:

    * ``approved_for_canonical_release`` - passes the currently active gate.
    * ``reviewed_below_threshold`` - a reviewer judged it and it fell short.
    * ``eligible_under_application_rule`` - the site already displays it, but
      the active gate holds it back (scored gate with no provenance yet, missing
      attribution, ...), so it is actionable work.
    * ``awaiting_media_review`` - the site does not display it yet either, so
      there is nothing a media reviewer can score; it needs approval or better
      media data first.
    """
    if not image_satisfies_application_rule(image, destination):
        return STATE_AWAITING_REVIEW

    exclusion = image_gate_exclusion(image, destination)
    if exclusion is None:
        return STATE_CANONICAL
    if exclusion in {
        "destination_match_score_below_threshold",
        "authenticity_score_below_threshold",
    }:
        return STATE_BELOW_THRESHOLD
    # The site shows it, so whatever release-only rule is blocking it is
    # actionable: review it, attribute it, or fix its media data.
    return STATE_ELIGIBLE


# --- Score assignment -----------------------------------------------------


class MediaReviewError(Exception):
    """Raised when a score write is not allowed or is not meaningful."""


class MediaReviewPermissionError(MediaReviewError):
    """Raised when the reviewer lacks a required capability (HTTP 403)."""


@dataclass
class ScoreChange:
    field: str
    previous: float | None
    new: float | None
    reviewer: Any
    at: Any

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "previous": self.previous,
            "new": self.new,
            "reviewer": getattr(self.reviewer, "email", None),
            "at": self.at.isoformat() if self.at else None,
        }


def _coerce_score(value, field: str) -> float:
    if value is None:
        raise MediaReviewError(f"{field} must be a number; it is never invented")
    if isinstance(value, bool):
        raise MediaReviewError(f"{field} must be a number, not a boolean")
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise MediaReviewError(f"{field} must be a number") from exc
    if not 0.0 <= score <= 1.0:
        raise MediaReviewError(f"{field} must be between 0 and 1, got {score}")
    return round(score, 3)


def assign_scores(
    image,
    *,
    reviewer,
    authenticity=None,
    destination_match=None,
    approve=None,
    note: str = "",
) -> list[ScoreChange]:
    """Assign moderation scores from a real reviewer's explicit values.

    Nothing here supplies a default. A field left as ``None`` is left untouched,
    and a score that already exists without provenance is only re-stamped when
    this reviewer deliberately re-submitted a value for it.
    """
    if not can_review_media(reviewer):
        raise MediaReviewPermissionError("You do not have permission to review media")
    if not image.is_verified and approve is not True:
        raise MediaReviewError("Only an approved review can be recorded here")

    now = timezone.now()
    changes: list[ScoreChange] = []
    updates: list[str] = []

    if authenticity is not None:
        if not can_assign_authenticity(reviewer):
            raise MediaReviewPermissionError("You cannot assign the authenticity score")
        score = _coerce_score(authenticity, "authenticity_score")
        changes.append(
            ScoreChange("authenticity_score", image.authenticity_score, score, reviewer, now)
        )
        image.authenticity_score = score
        image.authenticity_score_by = reviewer
        image.authenticity_score_at = now
        updates += ["authenticity_score", "authenticity_score_by", "authenticity_score_at"]

    if destination_match is not None:
        if not can_assign_destination_match(reviewer):
            raise MediaReviewPermissionError("You cannot assign the destination-match score")
        score = _coerce_score(destination_match, "destination_match_score")
        changes.append(
            ScoreChange(
                "destination_match_score", image.destination_match_score, score, reviewer, now
            )
        )
        image.destination_match_score = score
        image.destination_match_score_by = reviewer
        image.destination_match_score_at = now
        updates += [
            "destination_match_score",
            "destination_match_score_by",
            "destination_match_score_at",
        ]

    if approve is not None:
        if not can_approve_review(reviewer):
            raise MediaReviewPermissionError("You cannot approve or reject a media review")
        from .models import DestinationImage as _Image

        if approve:
            if not image_satisfies_application_rule(image):
                raise MediaReviewError(
                    "Cannot approve: the image is not approved, verified, "
                    "URL-backed and destination-specific yet"
                )
            image.verification_status = _Image.ImageStatus.APPROVED
            image.is_verified = True
        else:
            image.verification_status = _Image.ImageStatus.REJECTED
            image.is_verified = False
        image.media_reviewed_by = reviewer
        image.media_reviewed_at = now
        updates += ["verification_status", "is_verified", "media_reviewed_by", "media_reviewed_at"]

    if not changes and approve is None:
        # Nothing was actually requested. Refuse rather than quietly writing a
        # reviewer stamp that would imply a review happened.
        raise MediaReviewError("No score supplied; nothing was changed")

    if image.media_reviewed_by_id is None or approve is not None:
        image.media_reviewed_by = reviewer
        image.media_reviewed_at = now
        updates += ["media_reviewed_by", "media_reviewed_at"]

    image.save(update_fields=sorted(set(updates)))

    for change in changes:
        audit_score_change(image, change, note=note)
    if approve is not None:
        audit_review_decision(image, reviewer, approved=bool(approve), note=note)
    return changes


def audit_score_change(image, change: ScoreChange, note: str = "") -> None:
    _audit(
        action="media.score.assigned",
        image=image,
        user=change.reviewer,
        payload={
            "field": change.field,
            "previous": change.previous,
            "new": change.new,
            "reviewer": getattr(change.reviewer, "email", None),
            "reviewer_id": getattr(change.reviewer, "id", None),
            "assigned_at": change.at.isoformat() if change.at else None,
            "note": note or "",
            "active_gate": resolve_media_gate(),
        },
    )


def audit_review_decision(image, reviewer, *, approved: bool, note: str = "") -> None:
    _audit(
        action="media.review.approved" if approved else "media.review.rejected",
        image=image,
        user=reviewer,
        payload={
            "reviewer": getattr(reviewer, "email", None),
            "reviewer_id": getattr(reviewer, "id", None),
            "approved": approved,
            "note": note or "",
        },
    )


def audit_delegation(target_user, actor, *, granted: bool, actions) -> None:
    _audit(
        action="media.review.delegated" if granted else "media.review.delegation_revoked",
        image=None,
        user=actor,
        payload={
            "target_user": getattr(target_user, "email", None),
            "target_user_id": getattr(target_user, "id", None),
            "granted_by": getattr(actor, "email", None),
            "granted_by_id": getattr(actor, "id", None),
            "actions": sorted(actions or []),
        },
    )


def _audit(*, action: str, image, user, payload: dict[str, Any]) -> None:
    """Write to the project audit log; logging must never break the action."""
    try:
        from audit.logging_services import log_action
        from audit.models import ActionCategory
    except Exception:  # pragma: no cover - audit app optional in some installs
        return
    try:
        log_action(
            action=action,
            category=ActionCategory.MEDIA,
            obj=image,
            object_type="DestinationImage" if image is not None else "User",
            user=user,
            extra=payload,
        )
    except Exception:
        # An audit failure must not silently discard a legitimate review, but it
        # must also never be swallowed without trace.
        import logging

        logging.getLogger(__name__).warning(
            "audit write failed for %s: %s", action, payload, exc_info=True
        )


def provenance(image) -> dict[str, Any]:
    """Who set each score, and when. Used by the API and the release report."""
    def stamp(field: str) -> dict[str, Any]:
        by = getattr(image, f"{field}_by", None)
        at = getattr(image, f"{field}_at", None)
        return {
            "value": getattr(image, field, None),
            "assigned_by": getattr(by, "email", None),
            "assigned_by_id": getattr(by, "id", None),
            "assigned_at": at.isoformat() if at else None,
            "reviewed": bool(by and at),
        }

    reviewed_by = getattr(image, "media_reviewed_by", None)
    reviewed_at = getattr(image, "media_reviewed_at", None)
    return {
        "authenticity_score": stamp("authenticity_score"),
        "destination_match_score": stamp("destination_match_score"),
        "review": {
            "reviewer": getattr(reviewed_by, "email", None),
            "reviewer_id": getattr(reviewed_by, "id", None),
            "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        },
        "verification_status": image.verification_status,
        "is_verified": image.is_verified,
        "state": media_review_state(image),
        "canonical_exclusion_reason": image_gate_exclusion(image),
        "active_gate": resolve_media_gate(),
        "score_threshold": score_threshold(),
    }
