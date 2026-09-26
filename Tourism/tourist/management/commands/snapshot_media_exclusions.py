"""Explain which canonical media rule is active and why records are excluded.

The release gate is configurable, so an operator must be able to answer two
questions without reading code:

* which rule is active right now, and
* for a record that is missing from the release, which specific reason held it
  back.

This command never writes anything and never changes a score.
"""
from __future__ import annotations

import json

from django.core.management.base import BaseCommand
from django.db.models import Count

from tourist.media_review import (
    GATE_APPROVAL,
    REVIEW_STATES,
    image_gate_exclusion,
    media_review_state,
    requires_review_provenance,
    resolve_media_gate,
    score_threshold,
)
from tourist.models import Destination, DestinationImage
from tourist.verified_snapshot import (
    _has_no_synthetic_marker,
    _quality_scoped_images,
    _safe_external_url,
)


class Command(BaseCommand):
    help = "Report the active canonical media gate and per-reason exclusion counts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=25,
            help="How many example image ids to list per exclusion reason.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emit machine-readable JSON instead of a table.",
        )
        parser.add_argument(
            "--destination",
            default="",
            help="Restrict the report to one destination id or slug.",
        )

    def handle(self, *args, **options):
        gate = resolve_media_gate()
        threshold = score_threshold()

        queryset = DestinationImage.objects.select_related(
            "destination", "authenticity_score_by", "destination_match_score_by"
        )
        destination = None
        if options["destination"]:
            destination = self._find_destination(options["destination"])
            if destination is None:
                self.stderr.write("Destination not found; reporting nothing.")
                return
            queryset = queryset.filter(destination=destination)

        reasons: dict[str, list[int]] = {}
        states: dict[str, int] = {state: 0 for state in REVIEW_STATES}
        total = 0
        for image in queryset.iterator(chunk_size=500):
            total += 1
            states[media_review_state(image)] = states.get(media_review_state(image), 0) + 1
            reason = self._reason(image)
            reasons.setdefault(reason or "included", []).append(image.pk)

        summary = {
            "active_gate": gate,
            "gate_description": (
                "approval rule (matches the running application): approved, verified, "
                "destination-specific images; no score required"
                if gate == GATE_APPROVAL
                else f"scored rule: approved, verified, destination-specific images with both "
                f"scores >= {threshold}"
            ),
            "score_threshold": threshold,
            "requires_review_provenance": requires_review_provenance(),
            "destination": getattr(destination, "slug", None),
            "images_examined": total,
            "release_eligible": len(reasons.get("included", [])),
            "state_counts": states,
            "exclusion_reasons": {
                reason: {
                    "count": len(ids),
                    "example_image_ids": sorted(ids)[: options["limit"]],
                }
                for reason, ids in sorted(reasons.items())
            },
        }

        if options["json"]:
            self.stdout.write(json.dumps(summary, indent=2, default=str))
            return

        self.stdout.write("Canonical media gate report")
        self.stdout.write(f"  active gate            : {gate}")
        self.stdout.write(f"  rule                   : {summary['gate_description']}")
        self.stdout.write(f"  score threshold        : {threshold}")
        self.stdout.write(f"  review provenance      : {requires_review_provenance()}")
        self.stdout.write(f"  images examined        : {total}")
        self.stdout.write(f"  release eligible       : {summary['release_eligible']}")
        self.stdout.write("")
        self.stdout.write("  review states:")
        for state, count in sorted(states.items()):
            self.stdout.write(f"    {state:<34} {count}")
        self.stdout.write("")
        self.stdout.write("  exclusion reasons:")
        for reason, detail in summary["exclusion_reasons"].items():
            self.stdout.write(f"    {reason:<38} {detail['count']}")
            if reason != "included" and detail["example_image_ids"]:
                self.stdout.write(
                    f"      example image ids: {detail['example_image_ids']}"
                )
        self.stdout.write("")
        if gate == GATE_APPROVAL:
            self.stdout.write(
                "  Note: the approval gate does not require scores, so a record can be "
                "eligible while still having no human review recorded."
            )
        else:
            self.stdout.write(
                "  Note: under the scored gate a record becomes eligible only after an "
                "authorised reviewer assigns both scores. See docs/MEDIA_REVIEW.md for "
                "how to grant the capability, and GET /api/v1/admin/media-review/queue "
                "to work through the backlog."
            )

    def _find_destination(self, identifier: str):
        lookup = {"slug": identifier}
        if str(identifier).isdigit():
            lookup = {"pk": int(identifier)}
        return Destination.objects.filter(**lookup).first()

    def _reason(self, image) -> str:
        """Report the first upstream reason, matching the builder's own filters."""
        if image.verification_status != DestinationImage.ImageStatus.APPROVED:
            return "not_approved"
        if not image.is_verified:
            return "not_verified"
        if not (image.external_url or "").strip():
            return "missing_external_url"
        if not (image.source_url or "").strip():
            return "missing_source_url"
        if not _safe_external_url(image.external_url, image=True):
            return "unsafe_external_url"
        if not _safe_external_url(image.source_url):
            return "unsafe_source_url"
        if not _has_no_synthetic_marker(image.alt_text, image.caption):
            return "synthetic_marker"
        if image.source not in ["wikimedia", "openverse"]:
            return "source_not_allowlisted"
        return image_gate_exclusion(image) or "included"
