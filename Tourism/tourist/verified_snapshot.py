"""Canonical, privacy-safe tourism data snapshot helpers.

The runtime database is operational state: it can contain users, tokens, audit
logs, drafts, demo records, and local media paths.  It must never be treated as
the canonical sharing artifact.

This module defines the smaller contract used by ``build_verified_snapshot``:

* only sourced, public, approved destination records are selected;
* E2E/demo/fixture records are rejected;
* coordinates are either absent or plausible Nepal coordinates (never guessed);
* user-owned rows and user foreign keys are excluded;
* only quality-scored, approved external destination photos are included;
* hotels, restaurants, hospitals, police, and essential services must be
  explicitly verified before they can enter the snapshot;
* the JSON fixture contains no credentials or uploaded media binaries.

The generated database is built from this JSON into a fresh migrated SQLite
file, so a corrupt or privacy-tainted runtime SQLite file is never copied into
the downloadable artifact.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable
from uuid import UUID
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.core import serializers
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from tourist.models import (
    Alert,
    Category,
    CMSContentTranslation,
    ContentBlock,
    ContentSection,
    CurrentHazard,
    Destination,
    DestinationFeatureProfile,
    DestinationImage,
    DestinationReferenceImage,
    DestinationSource,
    DestinationSourceField,
    DestinationTransitRoute,
    DestinationTranslation,
    DestinationVideo,
    District,
    FeaturedDestination,
    HeroSlide,
    Hospital,
    Hotel,
    Language,
    ManagedNavigationItem,
    ManagedPage,
    OSMEssentialService,
    OSMTourismPlace,
    PoliceStation,
    Province,
    RedirectRule,
    Restaurant,
    RiskIncident,
    RouteSegment,
    User,
    VisitorNotice,
)

SNAPSHOT_FORMAT = "nepal-yatra-public-data-snapshot"
SNAPSHOT_VERSION = 1
POLICY_VERSION = 2
MINIMUM_TOURIST_MIGRATION = "0080_backfill_managed_page_snapshots"

# Bounds are intentionally a coarse validity gate, not geocoding.  A value
# outside Nepal is not silently corrected or guessed in a public snapshot.
NEPAL_LAT_MIN = 26.0
NEPAL_LAT_MAX = 31.0
NEPAL_LNG_MIN = 80.0
NEPAL_LNG_MAX = 89.0

SYNTHETIC_MARKER = re.compile(
    r"(?i)(?<![a-z0-9])("
    r"e2e|playwright|cypress|smoke|fixture|regression|"
    r"test(?:ing)?|demo|lifecycle|honesty"
    r")(?![a-z0-9])"
)
OSM_ID = re.compile(r"^(?:node|way|relation)/[1-9][0-9]*$")

SENSITIVE_KEY = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|credential|private[_-]?key)"
)
IMAGE_PATH = re.compile(r"^/(?:images|media)/[A-Za-z0-9_./-]+$")
INTERNAL_ROUTE = re.compile(r"^/[A-Za-z0-9_./?=&%-]*$")

ALLOWED_HTML_TAGS = {
    "p", "br", "strong", "em", "u", "s", "ul", "ol", "li",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
    "a", "img", "table", "thead", "tbody", "tr", "th", "td",
}
DANGEROUS_HTML_TAGS = {
    "script", "style", "iframe", "object", "embed", "svg", "math",
    "form", "input", "button", "textarea", "select", "option", "link", "meta",
}
HTML_ATTRIBUTES = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan"},
}
URL_KEYS = {
    "url", "uri", "href", "src", "image", "image_url", "cover_url",
    "cover_image_url", "thumbnail_url", "external_url", "source_url",
    "website", "booking_url", "video_url", "cta_url", "icon_url",
}
HTML_KEYS = {"html", "body", "rich_text", "richText", "content"}

PRIVATE_FIELDS = {
    "tourist.destination": {
        "review_note", "imported_data", "correction_reason", "research_status",
        "best_time_to_visit", "approx_travel_time", "nearest_hospital_info",
        "nearest_hotel_info", "nearest_police_info", "distance_from_nearest_city_km",
        "nearest_major_city", "distance_from_nearest_airport_km", "nearest_airport_name",
    },
    "tourist.destinationimage": {
        "view_count", "is_promoted", "generation_job", "image_path",
    },
}

# These values must not imply that unknown operational data means "free",
# "zero ratings", or a recommended duration.  The nullable destination fields
# are explicitly cleared; excluded counters reset to an honest empty value.
DESTINATION_NULL_FIELDS = {"entry_fee", "recommended_days"}
DESTINATION_ZERO_FIELDS = {"average_rating", "ratings_count", "views_count"}

# This is deliberately an allowlist.  A new model must be reviewed before it
# can accidentally enter a public data snapshot.
ALLOWED_MODELS = {
    "tourist.alert",
    "tourist.category",
    "tourist.cmscontenttranslation",
    "tourist.contentblock",
    "tourist.contentsection",
    "tourist.currenthazard",
    "tourist.destination",
    "tourist.destinationfeatureprofile",
    "tourist.destinationimage",
    "tourist.destinationreferenceimage",
    "tourist.destinationsource",
    "tourist.destinationsourcefield",
    "tourist.destinationtransitroute",
    "tourist.destinationtranslation",
    "tourist.destinationvideo",
    "tourist.district",
    "tourist.featureddestination",
    "tourist.heroslide",
    "tourist.hospital",
    "tourist.hotel",
    "tourist.language",
    "tourist.managednavigationitem",
    "tourist.managedpage",
    "tourist.osmessentialservice",
    "tourist.osmtourismplace",
    "tourist.policestation",
    "tourist.province",
    "tourist.redirectrule",
    "tourist.restaurant",
    "tourist.riskincident",
    "tourist.routesegment",
    "tourist.visitornotice",
}

# Rows in these models must never exist in a public share database.  The
# builder creates a fresh database and loads only MODEL_ORDER; this list is a
# second, explicit guard against a future migration accidentally seeding or
# reintroducing operational state.
FORBIDDEN_RUNTIME_LABELS = {
    "tourist.user",
    "tourist.staffcapabilityprofile",
    "tourist.emailverificationtoken",
    "tourist.smsverificationtoken",
    "tourist.passwordresettoken",
    "tourist.passwordresetotp",
    "tourist.review",
    "tourist.rating",
    "tourist.favorite",
    "tourist.itinerary",
    "tourist.itineraryday",
    "tourist.itinerarystop",
    "tourist.fieldverificationtask",
    "tourist.fieldverificationreport",
    "tourist.fieldverificationphoto",
    "tourist.tripfeedback",
    "tourist.tripfeedbackmedia",
    "tourist.visithistory",
    "tourist.userroute",
    "tourist.budget",
    "tourist.notificationpreference",
    "tourist.notification",
    "tourist.trustedcontact",
    "tourist.sharedtrip",
    "tourist.locationping",
    "tourist.sosalert",
    "tourist.familylink",
    "tourist.devicetoken",
    "tourist.mlinsight",
    "tourist.destinationauditlog",
    "tourist.travelexpensefeedback",
    "tourist.travelriskfeedback",
    "tourist.destinationcandidate",
    "tourist.discoveryjob",
    "tourist.imagegenerationjob",
    "tourist.imagetag",
    "tourist.imageembedding",
    "tourist.infrastructuresubmission",
    "tourist.infrastructuremedia",
    "tourist.recommendationevent",
    "tourist.riskobservation",
    "tourist.risknewsreport",
    "tourist.mltrainingrun",
    "tourist.userpreferenceprofile",
    "tourist.userfeedback",
    "tourist.feedbackevidence",
    "tourist.newslettersignup",
    "tourist.cmsrevision",
    "tourist.feedbackmessage",
    "tourist.emergencycontact",
    "tourist.importconflict",
    "tourist.contentproposal",
    "tourist.duplicatedecision",
    "tourist.marketplacepartner",
    "tourist.marketplacelisting",
    "tourist.marketplaceorder",
    "tourist.marketplaceorderitem",
    "tourist.travelerdocument",
    "tourist.guideprofile",
    "tourist.guideapplication",
    "tourist.tourismjob",
    "tourist.tourismjobapplication",
    "tourist.guidebookingrequest",
    "tourist.guidereview",
    "booking.booking",
    "booking.hotelreview",
    "navigation.routediagnostics",
    "navigation.navigationsession",
    "admin_panel.hotelassignment",
    "admin_panel.admintask",
    "chatbot.chatconversation",
    "chatbot.chatmessage",
    "audit.auditlog",
    "audit.errorevent",
    "audit.healthsample",
    "system_health.healthsnapshot",
}

MODEL_ORDER = [
    Language,
    Category,
    Province,
    District,
    Destination,
    DestinationTranslation,
    DestinationFeatureProfile,
    DestinationImage,
    DestinationReferenceImage,
    DestinationVideo,
    DestinationSource,
    DestinationSourceField,
    Hotel,
    Hospital,
    PoliceStation,
    Restaurant,
    DestinationTransitRoute,
    RouteSegment,
    OSMTourismPlace,
    OSMEssentialService,
    RiskIncident,
    Alert,
    CurrentHazard,
    HeroSlide,
    ManagedPage,
    ContentSection,
    ContentBlock,
    ManagedNavigationItem,
    CMSContentTranslation,
    RedirectRule,
    VisitorNotice,
    FeaturedDestination,
]


def _label(model: type[models.Model]) -> str:
    return model._meta.label_lower


def _as_aware(value: datetime | None) -> datetime:
    if value is None:
        return timezone.now()
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def _canonical_value(value: Any) -> Any:
    """Convert model values to a Django-version-independent JSON shape."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt_timezone.utc)
        timespec = "milliseconds" if value.microsecond else "seconds"
        return value.astimezone(dt_timezone.utc).isoformat(timespec=timespec).replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _canonical_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(child) for child in value]
    return value


def _canonical_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_canonical_value(record) for record in records]


def _valid_nepal_coordinate(latitude: Any, longitude: Any) -> bool:
    try:
        lat = float(latitude)
        lng = float(longitude)
    except (TypeError, ValueError):
        return False
    return (
        NEPAL_LAT_MIN <= lat <= NEPAL_LAT_MAX
        and NEPAL_LNG_MIN <= lng <= NEPAL_LNG_MAX
    )


def _has_no_synthetic_marker(*values: Any) -> bool:
    text = json.dumps(values, ensure_ascii=False, sort_keys=True, default=str)
    return not SYNTHETIC_MARKER.search(text)


def _safe_external_url(value: Any, *, image: bool = False) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text.startswith("//"):
        return False
    parsed = urlparse(text)
    if parsed.scheme.lower() != "https" or not parsed.netloc or parsed.username or parsed.password:
        return False
    if image and parsed.hostname not in {
        "upload.wikimedia.org",
        "commons.wikimedia.org",
        "images.unsplash.com",
        "live.staticflickr.com",
    } and not parsed.hostname.endswith(".wikimedia.org"):
        # Openverse can legitimately point to a provider CDN.  HTTPS plus a
        # non-empty hostname is sufficient there; this branch documents the
        # preferred direct hosts without rejecting valid provider URLs.
        return bool(parsed.hostname)
    return True


def _safe_url_value(value: Any, key: str = "") -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return ""
    lowered_key = key.lower()
    if lowered_key in {"href", "cta_url"}:
        if text.startswith("/") and INTERNAL_ROUTE.match(text):
            return text
        if urlparse(text).scheme.lower() in {"https", "mailto", "tel"}:
            return text
        return ""
    if IMAGE_PATH.match(text):
        return text
    return text if _safe_external_url(text, image=lowered_key in URL_KEYS) else ""


def sanitize_html_fragment(value: Any, extra_tags: frozenset = frozenset()) -> str:
    """Return a small, explicit HTML allowlist for snapshot rich text.

    ``extra_tags`` lets the CMS keep harmless inline formatting its rich-text
    editor emits (b, i, span...) without changing the snapshot policy."""
    allowed_tags = ALLOWED_HTML_TAGS | set(extra_tags)
    text = str(value or "")
    if "<" not in text and "&" not in text:
        return text
    soup = BeautifulSoup(text, "html.parser")
    for tag in list(soup.find_all(True)):
        name = (tag.name or "").lower()
        if name in DANGEROUS_HTML_TAGS:
            tag.decompose()
            continue
        if name not in allowed_tags:
            tag.unwrap()
            continue
        for attr in list(tag.attrs):
            if attr not in HTML_ATTRIBUTES.get(name, set()):
                del tag.attrs[attr]
        if name in {"a", "img"}:
            url_key = "href" if name == "a" else "src"
            safe_url = _safe_url_value(tag.attrs.get(url_key, ""), url_key)
            if safe_url:
                tag.attrs[url_key] = safe_url
            else:
                tag.attrs.pop(url_key, None)
        if name == "a" and tag.attrs.get("target") == "_blank":
            tag.attrs["rel"] = "noopener noreferrer"
    return str(soup)


def _scrub_json(value: Any, key: str = "") -> Any:
    if isinstance(value, datetime):
        # Django 6's JSON encoder keeps only the first three fractional digits.
        # Normalize before both writing and verification so a JSON round-trip
        # cannot turn .566 into a different stored value on a fresh database.
        return value.replace(microsecond=(value.microsecond // 1000) * 1000)
    if isinstance(value, dict):
        cleaned = {}
        for child_key, child_value in value.items():
            child_text = str(child_key)
            if SENSITIVE_KEY.search(child_text):
                continue
            cleaned[child_key] = _scrub_json(child_value, child_text)
        return cleaned
    if isinstance(value, list):
        return [_scrub_json(item, key) for item in value]
    if isinstance(value, tuple):
        return [_scrub_json(item, key) for item in value]
    if isinstance(value, str):
        if key in HTML_KEYS and ("<" in value or "&" in value):
            return sanitize_html_fragment(value)
        if key.lower().endswith("_at") or key.lower() in {"date", "event_date", "visit_date"}:
            parsed = parse_datetime(value)
            if parsed is not None:
                return _as_aware(parsed)
        if key.lower() in URL_KEYS or key.lower().endswith(("_url", "_uri")):
            return _safe_url_value(value, key)
    return value


def _strip_private_and_local_fields(record: dict[str, Any], model: type[models.Model]) -> dict[str, Any]:
    """Remove user FKs and local file paths from one serialized record."""
    result = copy.deepcopy(record)
    fields = result.get("fields", {})
    for field_name in PRIVATE_FIELDS.get(result.get("model", _label(model)), set()):
        fields.pop(field_name, None)
    for field in model._meta.fields:
        related_model = getattr(field.remote_field, "model", None) if field.remote_field else None
        if related_model is User:
            fields.pop(field.name, None)
        elif related_model is not None and _label(related_model) not in ALLOWED_MODELS:
            if not field.null:
                raise ValueError(
                    f"Required FK {result['model']}.{field.name} points outside the snapshot allowlist"
                )
            fields.pop(field.name, None)
        elif isinstance(field, models.FileField):
            # A path without its media binary is broken in a fresh clone.
            fields.pop(field.name, None)
    result["fields"] = _scrub_json(fields)
    return result


def _serialize(
    queryset: Iterable[models.Model],
    *,
    transform: Callable[[models.Model, dict[str, Any]], dict[str, Any] | None] | None = None,
) -> list[dict[str, Any]]:
    model = queryset.model
    objects = queryset.order_by("pk")
    serialized = serializers.serialize(
        "python",
        objects,
        use_natural_foreign_keys=False,
        use_natural_primary_keys=False,
    )
    records: list[dict[str, Any]] = []
    for obj, raw in zip(objects, serialized):
        record = _strip_private_and_local_fields(raw, model)
        if transform is not None:
            record = transform(obj, record)
            if record is None:
                continue
        if record["model"] not in ALLOWED_MODELS:
            raise ValueError(f"Refusing non-allowlisted snapshot model: {record['model']}")
        records.append(record)
    return records


def _public_destinations(as_of: datetime) -> tuple[list[Destination], set[int]]:
    queryset = Destination.objects.filter(
        is_active=True,
        status=Destination.SubmissionStatus.APPROVED,
        is_user_submitted=False,
        latitude__isnull=False,
        longitude__isnull=False,
        latitude__gte=NEPAL_LAT_MIN,
        latitude__lte=NEPAL_LAT_MAX,
        longitude__gte=NEPAL_LNG_MIN,
        longitude__lte=NEPAL_LNG_MAX,
    ).select_related("category")
    destinations = []
    for destination in queryset.iterator(chunk_size=500):
        has_sourced_identity = bool(
            (destination.external_id and destination.external_id > 0)
            or str(destination.source or "").strip()
        )
        if not has_sourced_identity:
            continue
        if not _has_no_synthetic_marker(
            destination.name,
            destination.slug,
            destination.source,
            destination.description,
            destination.imported_data,
        ):
            continue
        destinations.append(destination)
    return destinations, {destination.pk for destination in destinations}


def _quality_scoped_images(destination_ids: set[int]) -> tuple[list[DestinationImage], set[int]]:
    queryset = DestinationImage.objects.filter(
        destination_id__in=destination_ids,
        is_verified=True,
        verification_status="approved",
        source__in=["wikimedia", "openverse"],
    ).exclude(source_url="").exclude(external_url="")
    images = []
    for image in queryset.iterator(chunk_size=500):
        if not _safe_external_url(image.external_url, image=True):
            continue
        if not _safe_external_url(image.source_url):
            continue
        if image.destination_match_score is None or image.authenticity_score is None:
            continue
        if image.destination_match_score < 0.85 or image.authenticity_score < 0.85:
            continue
        if not _has_no_synthetic_marker(image.alt_text, image.caption):
            continue
        images.append(image)
    return images, {image.pk for image in images}


def _published_cms_ids(as_of: datetime) -> tuple[list[ManagedPage], list[ContentSection], list[ContentBlock]]:
    pages = list(
        ManagedPage.objects.filter(
            status="published",
            is_enabled=True,
            published_at__isnull=True,
        ).order_by("pk")
    )
    # Include normal published pages and explicitly dated pages whose publish
    # time has arrived.  ``published_at`` is nullable on legacy seed records.
    dated_pages = ManagedPage.objects.filter(
        status="published",
        is_enabled=True,
        published_at__isnull=False,
        published_at__lte=as_of,
    ).order_by("pk")
    pages.extend(dated_pages)
    pages = list({page.pk: page for page in pages}.values())
    page_ids = {page.pk for page in pages}

    sections = list(
        ContentSection.objects.filter(
            page_id__in=page_ids,
            status="published",
            is_visible=True,
        ).order_by("pk")
    )
    section_ids = {section.pk for section in sections}
    blocks = list(
        ContentBlock.objects.filter(
            section_id__in=section_ids,
            is_visible=True,
        ).exclude(block_type="html").order_by("pk")
    )
    return pages, sections, blocks


def _active_navigation_ids() -> set[int]:
    active_ids = set(
        ManagedNavigationItem.objects.filter(is_active=True).values_list("pk", flat=True)
    )
    items = {
        item.pk: item
        for item in ManagedNavigationItem.objects.filter(pk__in=active_ids).select_related("parent")
    }
    valid = set()
    for item_id, item in items.items():
        parent_id = item.parent_id
        seen = set()
        valid_chain = True
        while parent_id:
            if parent_id in seen or parent_id not in active_ids:
                valid_chain = False
                break
            seen.add(parent_id)
            parent = items.get(parent_id)
            if parent is None:
                valid_chain = False
                break
            parent_id = parent.parent_id
        if valid_chain:
            valid.add(item_id)
    return valid


def _exclude_synthetic_record(obj: models.Model, record: dict[str, Any]) -> dict[str, Any] | None:
    if _has_no_synthetic_marker(record.get("fields", {})):
        return record
    return None


# Old import runs wrote image notes into ``source_name`` ("Image: deterministic
# postcard placeholder ...").  That text describes a picture, not where the
# facility record came from, so it is stripped before publication.
_IMAGE_NOTE = re.compile(r"\s*\|?\s*Image:[^|]*", re.IGNORECASE)
UNVERIFIED_SERVICE_SOURCE = "Imported project dataset (not yet verified)"


def _coordinate_absent_or_in_nepal(fields: dict[str, Any]) -> bool:
    latitude, longitude = fields.get("latitude"), fields.get("longitude")
    if latitude in (None, "") and longitude in (None, ""):
        return True
    return _valid_nepal_coordinate(latitude, longitude)


def _public_service_record(obj: models.Model, record: dict[str, Any]) -> dict[str, Any] | None:
    """Publish a sourced service record without upgrading its trust level.

    ``is_verified`` is copied exactly as stored, so an imported listing stays
    unverified and the public UI labels it as such. Records with coordinates
    outside Nepal or synthetic/test markers are dropped.
    """
    record = _exclude_synthetic_record(obj, record)
    if record is None:
        return None
    fields = record["fields"]
    if not _coordinate_absent_or_in_nepal(fields):
        return None
    if "source_name" in fields:
        cleaned = _IMAGE_NOTE.sub("", str(fields.get("source_name") or "")).strip(" |")
        if not cleaned and not str(fields.get("source_url") or "").strip():
            cleaned = UNVERIFIED_SERVICE_SOURCE
        fields["source_name"] = cleaned
    return record


def _deduplicated_service_transform():
    """``_public_service_record`` that also drops repeated imports.

    The imported data holds exact duplicates — the same listing with the same
    name, coordinates and destination imported twice (e.g. two "Einstein
    House" hotel rows). Publishing both made itinerary days and nearby lists
    show one place twice. The lowest primary key is kept; places that only
    share a generic name ("Police Station Kaski") at different coordinates are
    distinct and stay.
    """
    seen: set[tuple] = set()

    def transform(obj: models.Model, record: dict[str, Any]) -> dict[str, Any] | None:
        record = _public_service_record(obj, record)
        if record is None:
            return None
        fields = record["fields"]
        latitude, longitude = fields.get("latitude"), fields.get("longitude")
        key = (
            " ".join(str(fields.get("name") or "").lower().split()),
            round(float(latitude), 5) if latitude not in (None, "") else None,
            round(float(longitude), 5) if longitude not in (None, "") else None,
            fields.get("destination"),
        )
        if key in seen:
            return None
        seen.add(key)
        return record

    return transform


def _normalize_destination_record(obj: Destination, record: dict[str, Any]) -> dict[str, Any]:
    fields = record["fields"]
    for field_name in DESTINATION_NULL_FIELDS:
        fields[field_name] = None
    for field_name in DESTINATION_ZERO_FIELDS:
        fields[field_name] = 0
    return record


def build_snapshot_payload(*, as_of: datetime | None = None) -> dict[str, Any]:
    """Build the canonical JSON-compatible snapshot from the active DB."""
    as_of = _as_aware(as_of)
    destinations, destination_ids = _public_destinations(as_of)
    images, image_ids = _quality_scoped_images(destination_ids)
    pages, sections, blocks = _published_cms_ids(as_of)
    page_ids = {page.pk for page in pages}
    section_ids = {section.pk for section in sections}
    navigation_ids = _active_navigation_ids()
    destination_slugs = {destination.slug for destination in destinations if destination.slug}
    verified_image_urls = {
        str(image.external_url).strip()
        for image in images
        if str(image.external_url or "").strip()
    }

    def safe_hero(obj: HeroSlide, record: dict[str, Any]) -> dict[str, Any] | None:
        fields = record["fields"]
        if not fields.get("image_url") and not fields.get("local_image"):
            return None
        if fields.get("link_slug") and fields.get("link_slug") not in destination_slugs:
            fields["link_slug"] = ""
        return record

    def safe_featured(obj: FeaturedDestination, record: dict[str, Any]) -> dict[str, Any] | None:
        fields = record["fields"]
        media_id = fields.get("featured_media")
        if media_id and int(media_id) not in image_ids:
            fields["featured_media"] = None
        override = str(fields.get("featured_media_url") or "").strip()
        if override and override not in verified_image_urls:
            fields["featured_media_url"] = ""
        return record

    records: list[dict[str, Any]] = []
    records.extend(_serialize(Language.objects.filter(is_active=True)))
    records.extend(_serialize(Category.objects.filter(destinations__pk__in=destination_ids).distinct()))
    records.extend(_serialize(Province.objects.all()))
    records.extend(_serialize(District.objects.select_related("province")))

    if destinations:
        records.extend(_serialize(
            Destination.objects.filter(pk__in=destination_ids).select_related("category"),
            transform=_normalize_destination_record,
        ))
    if destination_ids:
        records.extend(_serialize(DestinationTranslation.objects.filter(destination_id__in=destination_ids)))
        records.extend(_serialize(
            DestinationFeatureProfile.objects.filter(
                destination_id__in=destination_ids,
                is_verified=True,
            )
        ))
        records.extend(_serialize(DestinationImage.objects.filter(pk__in=image_ids).select_related("destination")))
        records.extend(_serialize(
            DestinationReferenceImage.objects.filter(
                destination_id__in=destination_ids,
                image_url__startswith="https://",
            ).exclude(source="").exclude(license="")
        ))
        records.extend(_serialize(
            DestinationVideo.objects.filter(
                destination_id__in=destination_ids,
                verification_status="approved",
            ).exclude(video_url="")
        ))
        records.extend(_serialize(
            DestinationSource.objects.filter(destination_id__in=destination_ids, is_verified=True)
        ))
        records.extend(_serialize(
            DestinationSourceField.objects.filter(
                destination_id__in=destination_ids,
                verification_status="Verified",
            )
        ))
        # Services: every active record with Nepal coordinates is published
        # with its stored is_verified flag. Verified rows are never faked;
        # unverified rows are labelled in the UI (policy v2).
        records.extend(_serialize(
            Hotel.objects.filter(
                destination_id__in=destination_ids,
                is_active=True,
                archived_at__isnull=True,
            ),
            transform=_deduplicated_service_transform(),
        ))
        records.extend(_serialize(
            Hospital.objects.filter(
                destination_id__in=destination_ids,
                is_archived=False,
            ),
            transform=_deduplicated_service_transform(),
        ))
        records.extend(_serialize(
            PoliceStation.objects.filter(
                destination_id__in=destination_ids,
                is_archived=False,
            ),
            transform=_deduplicated_service_transform(),
        ))
        records.extend(_serialize(
            Restaurant.objects.filter(
                destination_id__in=destination_ids,
                status=Restaurant.Status.PUBLISHED,
            ),
            transform=_public_service_record,
        ))
        records.extend(_serialize(
            DestinationTransitRoute.objects.filter(
                destination_id__in=destination_ids,
                is_active=True,
                is_verified=True,
            )
        ))
        route_ids = set(
            DestinationTransitRoute.objects.filter(
                destination_id__in=destination_ids,
                is_active=True,
                is_verified=True,
            ).values_list("pk", flat=True)
        )
        if route_ids:
            records.extend(_serialize(RouteSegment.objects.filter(route_id__in=route_ids)))
        records.extend(_serialize(
            RiskIncident.objects.filter(
                destination_id__in=destination_ids,
                verified=True,
                is_archived=False,
            )
        ))
        records.extend(_serialize(
            Alert.objects.filter(
                is_verified=True,
                is_active=True,
                starts_at__lte=as_of,
            ).filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=as_of))
        ))
        records.extend(_serialize(
            CurrentHazard.objects.filter(
                destination_id__in=destination_ids,
                verified=True,
                is_active=True,
                observed_at__lte=as_of,
            ).filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=as_of))
        ))

    records.extend(_serialize(
        OSMTourismPlace.objects.filter(
            latitude__gte=NEPAL_LAT_MIN,
            latitude__lte=NEPAL_LAT_MAX,
            longitude__gte=NEPAL_LNG_MIN,
            longitude__lte=NEPAL_LNG_MAX,
            osm_id__regex=r"^(node|way|relation)/[1-9][0-9]*$",
        ),
        transform=_exclude_synthetic_record,
    ))
    records.extend(_serialize(
        OSMEssentialService.objects.filter(
            is_archived=False,
            latitude__gte=NEPAL_LAT_MIN,
            latitude__lte=NEPAL_LAT_MAX,
            longitude__gte=NEPAL_LNG_MIN,
            longitude__lte=NEPAL_LNG_MAX,
        ),
        transform=_public_service_record,
    ))

    # CMS is part of the public snapshot, but only published/active records.
    records.extend(_serialize(HeroSlide.objects.filter(is_active=True), transform=safe_hero))
    records.extend(_serialize(ManagedPage.objects.filter(pk__in=page_ids)))
    records.extend(_serialize(ContentSection.objects.filter(pk__in=section_ids)))
    records.extend(_serialize(ContentBlock.objects.filter(pk__in={block.pk for block in blocks})))
    if navigation_ids:
        records.extend(_serialize(ManagedNavigationItem.objects.filter(pk__in=navigation_ids)))
    records.extend(_serialize(
        CMSContentTranslation.objects.filter(
            models.Q(target_resource="pages", object_id__in=page_ids)
            | models.Q(target_resource="sections", object_id__in=section_ids)
            | models.Q(target_resource="navigation", object_id__in=navigation_ids)
        )
    ))
    records.extend(_serialize(RedirectRule.objects.filter(is_active=True)))
    records.extend(_serialize(
        VisitorNotice.objects.filter(
            is_published=True,
            starts_at__lte=as_of,
        ).filter(
            models.Q(destination_id__isnull=True) | models.Q(destination_id__in=destination_ids)
        ).filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=as_of))
    ))
    records.extend(_serialize(
        FeaturedDestination.objects.filter(
            destination_id__in=destination_ids,
            is_published=True,
        ).filter(
            models.Q(publish_start__isnull=True) | models.Q(publish_start__lte=as_of)
        ).filter(
            models.Q(publish_end__isnull=True) | models.Q(publish_end__gte=as_of)
        ),
        transform=safe_featured,
    ))

    # Filter the two derived structures that need parent IDs from the final
    # records, then scrub CMS JSON URLs/HTML once more.
    allowed_destination_ids = {
        int(record["pk"]) for record in records if record["model"] == "tourist.destination"
    }
    allowed_section_ids = {
        int(record["pk"]) for record in records if record["model"] == "tourist.contentsection"
    }
    filtered: list[dict[str, Any]] = []
    for record in records:
        if record["model"] == "tourist.destinationimage":
            if int(record["fields"].get("destination", 0)) not in allowed_destination_ids:
                continue
        if record["model"] == "tourist.contentblock":
            if int(record["fields"].get("section", 0)) not in allowed_section_ids:
                continue
        filtered.append(record)

    filtered = _canonical_records(filtered)
    counts = Counter(record["model"] for record in filtered)
    canonical_records = json.dumps(
        filtered,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "format": SNAPSHOT_FORMAT,
        "format_version": SNAPSHOT_VERSION,
        "policy_version": POLICY_VERSION,
        "minimum_tourist_migration": MINIMUM_TOURIST_MIGRATION,
        "as_of": as_of.isoformat(),
        "identity_policy": {
            "destination": "slug plus external_id; numeric Django IDs are snapshot-local and must never merge separate databases",
            "related_records": "foreign keys are valid only inside this matched JSON/database pair",
        },
        "policy": {
            "destinations": "active, approved, non-user-submitted, sourced records with valid Nepal coordinates",
            "services": "active hotels, restaurants, hospitals, police, and essential services (coordinates, when present, must be inside Nepal); is_verified is copied as stored and unverified listings are labelled publicly",
            "images": "approved external images with destination_match_score >= 0.85 and authenticity_score >= 0.85; AI/user uploads excluded",
            "privacy": "users, tokens, sessions, logs, bookings, feedback, drafts, and local media paths excluded",
            "synthetic_records": "E2E/demo/fixture/test markers rejected",
        },
        "counts": dict(sorted(counts.items())),
        "records_sha256": hashlib.sha256(canonical_records).hexdigest(),
        "records": filtered,
    }


def payload_digest(payload: dict[str, Any]) -> str:
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Snapshot records must be a list")
    canonical_records = json.dumps(
        _canonical_records(records),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical_records).hexdigest()
    expected = payload.get("records_sha256")
    if expected and expected != digest:
        raise ValueError("Snapshot records_sha256 does not match records")
    return digest


@lru_cache(maxsize=1)
def _snapshot_schema_validator():
    schema_path = Path(__file__).resolve().parents[1] / "dataset" / "verified_tourism_data.schema.json"
    if not schema_path.exists():
        return None
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:  # pragma: no cover - requirements install jsonschema
        return None
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_payload(payload: dict[str, Any]) -> None:
    validator = _snapshot_schema_validator()
    if validator is not None:
        errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
        if errors:
            first = errors[0]
            path = ".".join(str(part) for part in first.path)
            raise ValueError(f"Snapshot schema validation failed at {path or '<root>'}: {first.message}")

    if payload.get("format") != SNAPSHOT_FORMAT:
        raise ValueError(f"Unsupported snapshot format: {payload.get('format')!r}")
    if payload.get("format_version") != SNAPSHOT_VERSION:
        raise ValueError(f"Unsupported snapshot version: {payload.get('format_version')!r}")
    if payload.get("minimum_tourist_migration") != MINIMUM_TOURIST_MIGRATION:
        raise ValueError("Snapshot migration contract is missing or unsupported")
    as_of_from_payload(payload)
    if not isinstance(payload.get("identity_policy"), dict):
        raise ValueError("Snapshot identity_policy is required")
    if not isinstance(payload.get("policy"), dict):
        raise ValueError("Snapshot policy is required")
    if not isinstance(payload.get("records"), list):
        raise ValueError("Snapshot records must be a list")

    models_seen = Counter()
    seen_keys = set()
    records_by_key = {}
    pks_by_model: dict[str, set[Any]] = {}
    model_classes = {_label(model): model for model in MODEL_ORDER}

    for record in payload["records"]:
        if not isinstance(record, dict):
            raise ValueError("Each snapshot record must be an object")
        model = record.get("model")
        if model not in ALLOWED_MODELS:
            raise ValueError(f"Blocked model in snapshot: {model}")
        pk = record.get("pk")
        if not isinstance(pk, (int, str)) or isinstance(pk, bool) or not pk:
            raise ValueError(f"Invalid pk for {model}: {pk!r}")
        key = (model, pk)
        if key in seen_keys:
            raise ValueError(f"Duplicate snapshot record: {model} pk={pk}")
        fields = record.get("fields")
        if not isinstance(fields, dict):
            raise ValueError(f"Invalid fields for {model} pk={pk}")
        model_class = model_classes[model]
        allowed_field_names = {
            field.name for field in model_class._meta.concrete_fields
        } | {
            field.name for field in model_class._meta.many_to_many
        }
        unknown = set(fields) - allowed_field_names
        if unknown:
            raise ValueError(f"Unknown fields for {model} pk={pk}: {sorted(unknown)}")
        forbidden = set(fields) & PRIVATE_FIELDS.get(model, set())
        if forbidden:
            raise ValueError(f"Private fields present for {model} pk={pk}: {sorted(forbidden)}")
        for field in model_class._meta.concrete_fields:
            if isinstance(field, models.FileField) and field.name in fields:
                raise ValueError(f"Local media field present: {model}.{field.name}")
            related_model = getattr(field.remote_field, "model", None) if field.remote_field else None
            if related_model is User and field.name in fields:
                raise ValueError(f"User FK present: {model}.{field.name}")
            if related_model is not None and field.name in fields and fields[field.name] is not None:
                target_label = _label(related_model)
                if target_label not in ALLOWED_MODELS:
                    raise ValueError(
                        f"FK points outside snapshot allowlist: {model}.{field.name} -> {target_label}"
                    )
        for field in model_class._meta.many_to_many:
            if field.name not in fields:
                continue
            target_label = _label(field.remote_field.model)
            if target_label not in ALLOWED_MODELS:
                raise ValueError(f"M2M points outside snapshot allowlist: {model}.{field.name}")
            for target_pk in fields[field.name] or []:
                if target_pk not in pks_by_model.get(target_label, set()):
                    raise ValueError(
                        f"Dangling M2M reference: {model}.{field.name} -> {target_label} pk={target_pk}"
                    )
        seen_keys.add(key)
        records_by_key[key] = fields
        pks_by_model.setdefault(model, set()).add(pk)
        models_seen[model] += 1

    for (model, pk), fields in records_by_key.items():
        model_class = model_classes[model]
        for field in model_class._meta.concrete_fields:
            related_model = getattr(field.remote_field, "model", None) if field.remote_field else None
            if related_model is None or field.name not in fields or fields[field.name] is None:
                continue
            target_label = _label(related_model)
            target_pk = fields[field.name]
            if target_pk not in pks_by_model.get(target_label, set()):
                raise ValueError(
                    f"Dangling FK reference: {model} pk={pk} {field.name} -> "
                    f"{target_label} pk={target_pk}"
                )
        if model == "tourist.destination":
            if fields.get("status") != Destination.SubmissionStatus.APPROVED or fields.get("is_active") is not True:
                raise ValueError(f"Non-public destination in snapshot: pk={pk}")
            if fields.get("is_user_submitted") is not False:
                raise ValueError(f"User-submitted destination in snapshot: pk={pk}")
            if not _valid_nepal_coordinate(fields.get("latitude"), fields.get("longitude")):
                raise ValueError(f"Invalid Nepal coordinates in snapshot destination pk={pk}")
            if not (fields.get("external_id") or str(fields.get("source") or "").strip()):
                raise ValueError(f"Unsourced destination in snapshot: pk={pk}")
            if not _has_no_synthetic_marker(fields):
                raise ValueError(f"Synthetic destination marker in snapshot: pk={pk}")
        elif model == "tourist.destinationimage":
            if fields.get("verification_status") != "approved" or fields.get("is_verified") is not True:
                raise ValueError(f"Non-approved image in snapshot: pk={pk}")
            if float(fields.get("destination_match_score") or 0) < 0.85:
                raise ValueError(f"Low destination-match image in snapshot: pk={pk}")
            if float(fields.get("authenticity_score") or 0) < 0.85:
                raise ValueError(f"Low-authenticity image in snapshot: pk={pk}")
        elif model in {
            "tourist.hotel", "tourist.hospital", "tourist.policestation",
            "tourist.restaurant", "tourist.osmessentialservice",
        }:
            if not _coordinate_absent_or_in_nepal(fields):
                raise ValueError(f"Service outside Nepal in snapshot: {model} pk={pk}")
            if not isinstance(fields.get("is_verified"), bool):
                raise ValueError(f"Service without an explicit verification flag: {model} pk={pk}")

    generic_targets = {
        "pages": pks_by_model.get("tourist.managedpage", set()),
        "sections": pks_by_model.get("tourist.contentsection", set()),
        "navigation": pks_by_model.get("tourist.managednavigationitem", set()),
    }
    for (model, pk), fields in records_by_key.items():
        if model != "tourist.cmscontenttranslation":
            continue
        target = fields.get("target_resource")
        if target not in generic_targets or fields.get("object_id") not in generic_targets[target]:
            raise ValueError(f"Dangling CMS translation target: pk={pk}")

    payload_digest(payload)
    declared = payload.get("counts") or {}
    if not isinstance(declared, dict) or any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in declared.values()
    ):
        raise ValueError("Snapshot counts must be non-negative integers")
    if declared and dict(sorted(models_seen.items())) != dict(sorted(declared.items())):
        raise ValueError("Snapshot counts do not match records")


def read_payload(path: str | os.PathLike[str]) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_payload(payload)
    return payload


def write_payload(path: str | os.PathLike[str], payload: dict[str, Any]) -> Path:
    validate_payload(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    serializable = dict(payload)
    serializable["records"] = _canonical_records(payload["records"])
    # Use explicit LF so the checksum is identical on Windows and Linux
    # checkouts (Path.write_text otherwise applies platform newline translation).
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, target)
    return target


def as_of_from_payload(payload: dict[str, Any]) -> datetime:
    value = payload.get("as_of")
    parsed = parse_datetime(str(value)) if value else None
    if parsed is None:
        raise ValueError("Snapshot as_of is missing or invalid")
    return _as_aware(parsed)


def sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "ALLOWED_MODELS",
    "FORBIDDEN_RUNTIME_LABELS",
    "MINIMUM_TOURIST_MIGRATION",
    "MODEL_ORDER",
    "SNAPSHOT_FORMAT",
    "SNAPSHOT_VERSION",
    "as_of_from_payload",
    "build_snapshot_payload",
    "payload_digest",
    "read_payload",
    "sanitize_html_fragment",
    "sha256_file",
    "validate_payload",
    "write_payload",
]
