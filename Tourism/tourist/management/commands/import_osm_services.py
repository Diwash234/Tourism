"""Repeatable, idempotent importer for real OpenStreetMap service records.

Data flow (per the platform contract "AI proposes. Database stores. Admin
verifies. API distributes. Frontend displays."):

    Overpass extract JSON (dataset/osm_raw/*.json)
        -> normalization (name/operator/phone/opening_hours tags)
        -> category mapping (amenity/shop/tourism -> OSMEssentialService.Category)
        -> Nepal bounding-box validation (out-of-country rows rejected)
        -> district/province assignment (nearest District centroid, <=80 km,
           documented approximation - never fabricated precision)
        -> canonical ID: osm_id = "<type>/<id>" (unique, stable, re-runnable)
        -> OSMEssentialService rows (is_archived=False; admin can archive)
        -> JSON import report (dataset/osm_reports/<name>-<ts>.json)

Nothing is invented: rows without any name/operator still get an honest
label "Atm (node/123456)" built from category + OSM id, and every row keeps
its source (osm_id + source_url to the OSM element).

Usage:
    python manage.py import_osm_services                 # import everything in dataset/osm_raw
    python manage.py import_osm_services --dry-run       # report only, no writes
    python manage.py import_osm_services --source /path  # custom extract dir
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import District, OSMEssentialService

# Nepal bounding box (mainland, generous margin). Rows outside are rejected -
# the Overpass area query already scopes to NP, this guards bbox-sourced files.
NEPAL_BBOX = {"min_lat": 26.30, "max_lat": 30.50, "min_lng": 79.90, "max_lng": 88.30}

# OSM tag value -> OSMEssentialService.Category value
CATEGORY_MAP = {
    "atm": "atm", "bank": "bank", "restaurant": "restaurant", "cafe": "cafe",
    "fast_food": "fast_food", "bakery": "bakery", "bar": "bar", "pub": "bar",
    "pharmacy": "pharmacy", "hospital": "hospital", "clinic": "clinic",
    "doctors": "doctors", "dentist": "dentist", "police": "police",
    "fire_station": "fire_station", "bus_station": "bus_station",
    "fuel": "fuel", "charging_station": "charging_station",
    "ambulance": "ambulance", "blood_bank": "blood_bank", "taxi": "taxi",
    "supermarket": "supermarket", "marketplace": "marketplace",
    "guest_house": "guest_house", "hostel": "guest_house",
    "information": "tourism_office",
}


def haversine_km(lat1, lng1, lat2, lng2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class Command(BaseCommand):
    help = "Import real OSM essential-service records from Overpass extract JSON files."

    def add_arguments(self, parser):
        parser.add_argument("--source", default=None,
                            help="Directory with Overpass JSON extracts (default: dataset/osm_raw)")
        parser.add_argument("--dry-run", action="store_true",
                            help="Validate and report without writing to the database")
        parser.add_argument("--default-category", default=None,
                            help="OSM tag value to assume when elements carry no amenity/shop/tourism "
                                 "tag (for compact per-category skel extracts)")
        parser.add_argument("--report-dir", default=None,
                            help="Where to write the JSON report (default: dataset/osm_reports)")

    def handle(self, *args, **opts):
        base = Path(__file__).resolve().parents[3]  # Tourism/Tourism
        source_dir = Path(opts["source"]) if opts["source"] else base / "dataset" / "osm_raw"
        report_dir = Path(opts["report_dir"]) if opts["report_dir"] else base / "dataset" / "osm_reports"
        if not source_dir.exists():
            self.stderr.write(f"Source directory not found: {source_dir}")
            return

        districts = [
            (d.id, d.name, d.province.name, d.latitude, d.longitude)
            for d in District.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        ]

        report = {
            "source": "openstreetmap.org (ODbL) via Overpass API extracts",
            "started": datetime.now(timezone.utc).isoformat(),
            "dry_run": opts["dry_run"],
            "found": 0, "created": 0, "updated": 0, "duplicate": 0,
            "rejected_outside_nepal": 0, "rejected_no_coords": 0,
            "rejected_unknown_category": 0, "rejected_no_district": 0,
            "by_category": {}, "by_province": {}, "by_district": {},
            "files": [],
        }

        files = sorted(source_dir.glob("*.json"))
        if not files:
            self.stderr.write(f"No .json extracts in {source_dir}")
            return

        for fp in files:
            file_report = {"file": fp.name, "found": 0, "created": 0, "updated": 0,
                           "rejected": 0}
            try:
                payload = json.loads(fp.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self.stderr.write(f"Skipping {fp.name}: invalid JSON ({exc})")
                continue
            elements = payload.get("elements", [])
            with transaction.atomic():
                for el in elements:
                    report["found"] += 1
                    file_report["found"] += 1
                    tags = el.get("tags") or {}
                    cat_raw = (tags.get("amenity") or tags.get("shop")
                               or tags.get("tourism") or opts["default_category"])
                    category = CATEGORY_MAP.get(cat_raw)
                    if not category:
                        report["rejected_unknown_category"] += 1
                        file_report["rejected"] += 1
                        continue
                    lat = el.get("lat") or (el.get("center") or {}).get("lat")
                    lng = el.get("lon") or (el.get("center") or {}).get("lon")
                    if lat is None or lng is None:
                        report["rejected_no_coords"] += 1
                        file_report["rejected"] += 1
                        continue
                    lat, lng = float(lat), float(lng)
                    if not (NEPAL_BBOX["min_lat"] <= lat <= NEPAL_BBOX["max_lat"]
                            and NEPAL_BBOX["min_lng"] <= lng <= NEPAL_BBOX["max_lng"]):
                        report["rejected_outside_nepal"] += 1
                        file_report["rejected"] += 1
                        continue
                    osm_id = f"{el.get('type', 'node')}/{el.get('id')}"
                    name = (tags.get("name:en") or tags.get("name")
                            or tags.get("operator")
                            or f"{category.replace('_', ' ').title()} ({osm_id})")
                    defaults = {
                        "category": category,
                        "name": name[:255],
                        "phone": (tags.get("phone") or tags.get("contact:phone") or "")[:50],
                        "address": (tags.get("addr:full")
                                    or ", ".join(x for x in [
                                        tags.get("addr:street"), tags.get("addr:city")] if x)
                                    or "")[:255],
                        "latitude": round(lat, 6),
                        "longitude": round(lng, 6),
                        "opening_hours": (tags.get("opening_hours") or "")[:160],
                        "source_name": "OpenStreetMap",
                        "source_url": f"https://www.openstreetmap.org/{el.get('type', 'node')}/{el.get('id')}",
                        "raw_tags": tags,
                    }
                    # Nearest district centroid within 80 km; otherwise leave
                    # province/district blank (honest gap, reported below).
                    best, best_km = None, 80.0
                    for d_id, d_name, p_name, d_lat, d_lng in districts:
                        km = haversine_km(lat, lng, d_lat, d_lng)
                        if km < best_km:
                            best, best_km = (d_id, d_name, p_name), km
                    if not best:
                        # Inside the bbox but >80 km from any district centroid:
                        # almost certainly cross-border bleed or a bad
                        # coordinate. Never import geographically unverifiable
                        # rows; report them instead.
                        report["rejected_no_district"] = report.get("rejected_no_district", 0) + 1
                        file_report["rejected"] += 1
                        continue

                    existing = OSMEssentialService.objects.filter(osm_id=osm_id).first()
                    if opts["dry_run"]:
                        if existing:
                            report["duplicate"] += 1
                        else:
                            report["created"] += 1
                    else:
                        def _differs(current, new):
                            # Decimal fields (lat/lng) never equal their float
                            # counterparts; compare numerically where possible.
                            try:
                                return float(current) != float(new)
                            except (TypeError, ValueError):
                                return current != new

                        if existing:
                            changed = False
                            for k, v in defaults.items():
                                if hasattr(existing, k) and _differs(getattr(existing, k), v):
                                    setattr(existing, k, v)
                                    changed = True
                            if changed:
                                existing.save()
                                report["updated"] += 1
                            else:
                                report["duplicate"] += 1
                        else:
                            obj = OSMEssentialService(osm_id=osm_id)
                            for k, v in defaults.items():
                                if hasattr(obj, k):
                                    setattr(obj, k, v)
                            obj.save()
                            report["created"] += 1
                    report["by_category"][category] = report["by_category"].get(category, 0) + 1
                    report["by_province"][best[2]] = report["by_province"].get(best[2], 0) + 1
                    report["by_district"][best[1]] = report["by_district"].get(best[1], 0) + 1
                    if existing is None and not opts["dry_run"]:
                        file_report["created"] += 1
                    elif existing is not None:
                        file_report["updated"] += 1
            report["files"].append(file_report)

        report["finished"] = datetime.now(timezone.utc).isoformat()
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        report_path = report_dir / f"import_osm_services-{stamp}.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        self.stdout.write(json.dumps({k: v for k, v in report.items()
                                      if k not in ("files",)}, indent=2, ensure_ascii=False))
        self.stdout.write(f"Report: {report_path}")
