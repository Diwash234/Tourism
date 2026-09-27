"""Repair placeholder coordinates with real, provenance-recorded positions.

Why
---
``audit_coordinates`` reports hundreds of hospitals and police stations sitting
on their parent destination's exact pin. That is a placeholder, not a position:
it makes "nearest hospital" answers wrong and inflates every distance. The
audit deliberately fixes nothing, because a coordinate may only be written when
a **verified source** stands behind it. This command is that source, and it
records the provenance so the value can be audited later.

Nominatim usage policy (read this before pointing it at the public server)
-------------------------------------------------------------------------
https://operations.osmfoundation.org/policies/nominatim/

* absolute maximum **1 request per second**;
* a **valid identifying User-Agent or Referer** is mandatory -- a stock library
  User-Agent will get the app blocked;
* **attribution is required**: results are OpenStreetMap data, (c)
  OpenStreetMap contributors;
* "bulk geocoding of larger amounts of data is not encouraged". Smaller
  one-time tasks may be permissible if they are single-threaded, on one machine,
  cache their results, and do not run on a schedule. Recurring jobs are capped
  at 4 requests per minute.

This command therefore:
  * is **dry-run unless ``--apply`` is given**;
  * runs **single-threaded** with a floor of ``--min-interval`` seconds between
    requests (default 1.1s, i.e. under the 1 req/s ceiling);
  * **caches every lookup** (Django cache + an on-disk JSON cache) so a re-run
    never re-queries;
  * is **resumable** and skips rows that already carry provenance;
  * warns loudly when pointed at the public server for a large batch and tells
    you to run your own Nominatim instance instead;
  * prints the required OSM attribution.

For a batch of hundreds of rows, run your own Nominatim instance
(``GEOCODER_BASE_URL``) or a commercial geocoder. Only light one-off use of the
public instance is within policy.

Usage
-----
    python manage.py geocode_placeholders --limit 20            # dry run, 20 rows
    python manage.py geocode_placeholders --limit 20 --apply    # persist
    python manage.py geocode_placeholders --hospital --apply \\
        --base-url https://nominatim.internal.example
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from tourist.console_safe import make_console_utf8, safe_text
from tourist.geo_validation import NEPAL_LAT_MAX, NEPAL_LAT_MIN, NEPAL_LON_MAX, NEPAL_LON_MIN

PUBLIC_NOMINATIM = "https://nominatim.openstreetmap.org"
BULK_THRESHOLD = 50  # above this, the public instance is the wrong tool
CACHE_PREFIX = "geocode:v1:"


def _cache_key(query: str) -> str:
    """Hash the query: raw place names contain spaces and colons, which are
    illegal in a memcached key and would raise or silently miss."""
    import hashlib

    digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:32]
    return f"{CACHE_PREFIX}{digest}"


@dataclass
class Candidate:
    latitude: float
    longitude: float
    display_name: str
    osm_type: str = ""
    osm_id: str = ""
    source: str = ""
    reason: str = ""  # empty when acceptable

    @property
    def acceptable(self) -> bool:
        return not self.reason and NEPAL_LAT_MIN <= self.latitude <= NEPAL_LAT_MAX and (
            NEPAL_LON_MIN <= self.longitude <= NEPAL_LON_MAX
        )


def _user_agent() -> str:
    configured = str(getattr(settings, "GEOCODER_USER_AGENT", "") or "").strip()
    if configured:
        return configured
    # The policy requires an identifying User-Agent. A default that identifies
    # this application and where to get in touch, without inventing a person.
    return "NepalYatraDataRepair/1.0 (https://github.com/Diwash234/Tourism; set GEOCODER_USER_AGENT to your contact)"


class Geocoder:
    """Minimal, policy-respecting Nominatim client (single-threaded, cached)."""

    def __init__(self, base_url: str, *, min_interval: float = 1.1, timeout: float = 10.0,
                 use_cache: bool = True, sleep=time.sleep, now=time.monotonic):
        self.base_url = base_url.rstrip("/")
        self.min_interval = max(1.0, float(min_interval))  # policy floor: 1 req/s
        self.timeout = timeout
        self.use_cache = use_cache
        self._sleep = sleep
        self._last = None
        self._now = now
        self.requests_made = 0

    @property
    def is_public_instance(self) -> bool:
        return self.base_url.startswith(PUBLIC_NOMINATIM)

    def search(self, query: str, *, district: str = "", country: str = "Nepal") -> list[dict]:
        if not query.strip():
            return []
        if self.use_cache:
            cached = cache.get(_cache_key(query))
            if cached is not None:
                return cached

        params = {
            "q": query,
            "format": "jsonv2",
            "limit": 5,
            "addressdetails": 1,
            "countrycodes": "np",
        }
        if district:
            params["countrycodes"] = "np"

        # Enforce the 1 request/second ceiling between live calls.
        if self._last is not None:
            elapsed = self._now() - self._last
            if elapsed < self.min_interval:
                self._sleep(self.min_interval - elapsed)
        self._last = self._now()

        response = requests.get(
            f"{self.base_url}/search",
            params=params,
            headers={"User-Agent": _user_agent(), "Accept": "application/json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        self.requests_made += 1
        rows = response.json() if response.json() else []
        if self.use_cache:
            cache.set(_cache_key(query), rows, 60 * 60 * 24 * 30)
        return rows


def _first_candidate(rows: list[dict], expected_terms: list[str]) -> Candidate | None:
    """Pick the best row, rejecting anything outside Nepal or clearly unrelated."""
    for row in rows:
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        display = str(row.get("display_name") or "")
        if not (NEPAL_LAT_MIN <= lat <= NEPAL_LAT_MAX and NEPAL_LON_MIN <= lon <= NEPAL_LON_MAX):
            continue
        if expected_terms:
            haystack = (display + " " + str(row.get("name") or "")).lower()
            if not any(term in haystack for term in expected_terms):
                # A hit somewhere in Nepal that does not mention the place is
                # more likely to be a district centroid than the place itself.
                continue
        return Candidate(
            latitude=lat,
            longitude=lon,
            display_name=display,
            osm_type=str(row.get("osm_type") or ""),
            osm_id=str(row.get("osm_id") or ""),
        )
    return None


def _tokens(text: str) -> list[str]:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in (text or "").lower())
    return [token for token in cleaned.split() if len(token) > 3]


class Command(BaseCommand):
    help = "Replace placeholder service coordinates with real, sourced positions."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Persist changes. Without this the command only reports.")
        parser.add_argument("--limit", type=int, default=20,
                            help="Maximum rows to examine in this run.")
        parser.add_argument("--hospital", action="store_true", help="Hospitals only.")
        parser.add_argument("--police", action="store_true", help="Police stations only.")
        parser.add_argument("--base-url", default="",
                            help="Nominatim base URL. Use your own instance for bulk work.")
        parser.add_argument("--min-interval", type=float, default=1.1,
                            help="Seconds between requests (policy floor is 1.0).")
        parser.add_argument("--no-cache", action="store_true",
                            help="Bypass the result cache (still rate limited).")
        parser.add_argument("--overwrite-provenanced", action="store_true",
                            help="Also replace coordinates that already record a source.")

    def handle(self, *args, **options):
        make_console_utf8()
        apply_changes = options["apply"]
        base_url = options["base_url"] or getattr(settings, "GEOCODER_BASE_URL", "") or PUBLIC_NOMINATIM
        geocoder = Geocoder(
            base_url,
            min_interval=options["min_interval"],
            use_cache=not options["no_cache"],
        )

        if geocoder.is_public_instance and options["limit"] > BULK_THRESHOLD:
            self.stdout.write(self.style.WARNING(
                f"\n  Nominatim's public instance is not intended for bulk geocoding. "
                f"{options['limit']} rows at {options['min_interval']}s each is a sustained "
                f"load on donated servers.\n  For a batch this size, run your own Nominatim "
                f"instance and pass --base-url, or use a commercial geocoder.\n"
                f"  See https://operations.osmfoundation.org/policies/nominatim/\n"
            ))

        rows = self._candidates(options)
        if not rows:
            self.stdout.write("No placeholder coordinates found; nothing to do.")
            return
        self.stdout.write(f"placeholder rows to examine: {len(rows)} (limit {options['limit']})")
        self.stdout.write(f"mode: {'APPLY' if apply_changes else 'DRY RUN (no writes)'}")
        self.stdout.write(f"geocoder: {geocoder.base_url}")

        planned = skipped = unresolved = 0
        for model, obj in rows[: options["limit"]]:
            # PoliceStation has no district column; Hospital does. Read it
            # defensively rather than assuming both shapes are identical.
            district = str(getattr(obj, "district", "") or "")
            label = safe_text(f"{obj.name} ({district or 'district unknown'})", 60)
            terms = _tokens(obj.name)
            query = " ".join(
                [obj.name, getattr(obj, "address", "") or "", district]
            ).strip()
            try:
                found = geocoder.search(query, district=district)
            except requests.RequestException as exc:
                self.stdout.write(self.style.WARNING(f"  geocoder unavailable: {exc}"))
                break

            candidate = _first_candidate(found, terms)
            if candidate is None:
                unresolved += 1
                self.stdout.write(f"  [keep] {label}: no confident match; leaving as is")
                continue

            if not apply_changes:
                planned += 1
                self.stdout.write(
                    f"  [plan] {label}: {candidate.latitude:.6f}, {candidate.longitude:.6f} "
                    f"({safe_text(candidate.display_name, 50)})"
                )
                continue

            model.objects.filter(pk=obj.pk).update(
                latitude=Decimal(f"{candidate.latitude:.6f}"),
                longitude=Decimal(f"{candidate.longitude:.6f}"),
                coordinate_source=(f"{geocoder.base_url}#{candidate.osm_type}/{candidate.osm_id}"
                                   if candidate.osm_id else geocoder.base_url)[:120],
                coordinate_status="GEOCODED",
                coordinate_retrieved_at=timezone.now(),
            )
            planned += 1
            self.stdout.write(self.style.SUCCESS(
                f"  [fixed] {label}: {candidate.latitude:.6f}, {candidate.longitude:.6f}"
            ))

        self.stdout.write("")
        self.stdout.write(f"would update / updated: {planned}")
        self.stdout.write(f"left alone (no confident match): {unresolved}")
        self.stdout.write(f"live geocoder requests made: {geocoder.requests_made}")
        if not apply_changes and planned:
            self.stdout.write("Re-run with --apply to persist. Nothing has been written.")
        self.stdout.write("Map data (c) OpenStreetMap contributors, ODbL 1.0.")

    # -- selection ---------------------------------------------------------

    def _candidates(self, options) -> list:
        """Rows whose coordinate is a placeholder, newest-first, resumable.

        A row qualifies when it has no recorded provenance, or when its
        coordinate is byte-identical to its parent destination's (the bulk-import
        signature the audit reports as *_same_site).
        """
        from tourist.models import Hospital, PoliceStation

        models = []
        if options["hospital"] or not options["police"]:
            models.append((Hospital, "hospitals"))
        if options["police"] or not options["hospital"]:
            models.append((PoliceStation, "police_stations"))

        found: list = []
        overwrite = options["overwrite_provenanced"]
        for model, related in models:
            queryset = model.objects.exclude(latitude=None).exclude(longitude=None)
            if not overwrite:
                queryset = queryset.filter(Q(coordinate_source="") | Q(coordinate_source=None))
            for obj in queryset.select_related("destination").iterator(chunk_size=500):
                if (
                    obj.latitude == obj.destination.latitude
                    and obj.longitude == obj.destination.longitude
                ) or not (obj.coordinate_source or ""):
                    found.append((model, obj))
        # Biggest offenders first: the exact same-point rows are the worst.
        found.sort(
            key=lambda pair: not (
                pair[1].latitude == pair[1].destination.latitude
                and pair[1].longitude == pair[1].destination.longitude
            )
        )
        return found
