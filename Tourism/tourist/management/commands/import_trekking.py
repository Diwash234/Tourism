"""Import trekking routes from a curated JSON dataset into TrekkingRoute.

TREKKING DATA DEPENDENCY = EXTERNAL AUTHORITATIVE SOURCE REQUIRED.
No dataset ships with this repository; this pipeline exists so an
authoritative file (NTB/TAAN/DoI licensed extract) can be loaded when
obtained. Trust rules enforced here:

  - rows land as verification_state='unverified' (never auto-verified)
  - every row keeps source_name/source_url/source_imported_at provenance
  - re-running is idempotent on slug (update fields, never duplicate)
  - geographic sanity: lat 26.3-30.5, lon 80-88.3, elevation 0-9000 m;
    rows outside are rejected, never clamped

Usage:
    python manage.py import_trekking --source path/to/treks.json [--apply]
    (default is a dry-run report; --apply writes)

Expected JSON shape:
  [{"name","slug","region","district","start_point","end_point",
    "total_distance_km","total_duration_days","max_elevation_m",
    "difficulty","best_season","permits":[...],"accommodation",
    "safety_notes","description","source_name","source_url",
    "stages":[{"day_number","name","from_place","to_place","latitude",
               "longitude","distance_km","elevation_gain_m",
               "elevation_loss_m","duration_hours"}]}]
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import TrekkingRoute, TrekkingStage

NEPAL_BBOX = {"min_lat": 26.30, "max_lat": 30.50, "min_lng": 80.00, "max_lng": 88.30}
DIFFICULTIES = {c.value for c in TrekkingRoute.Difficulty}


def _valid_coords(lat, lon):
    return (lat is not None and lon is not None
            and NEPAL_BBOX["min_lat"] <= lat <= NEPAL_BBOX["max_lat"]
            and NEPAL_BBOX["min_lng"] <= lon <= NEPAL_BBOX["max_lng"])


class Command(BaseCommand):
    help = "Import trekking routes (idempotent; unverified until admin review)."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help="Path to curated trekking JSON")
        parser.add_argument("--apply", action="store_true", help="Write to DB (default: dry run)")

    def handle(self, *args, **opts):
        path = Path(opts["source"])
        if not path.exists():
            self.stderr.write(f"Source not found: {path}")
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.stderr.write(f"Invalid JSON: {exc}")
            return
        report = {"source": str(path), "dry_run": not opts["apply"],
                  "found": 0, "created": 0, "updated": 0, "rejected": 0,
                  "stages": 0, "finished": None}
        now = datetime.now(timezone.utc)
        with transaction.atomic():
            for entry in payload:
                report["found"] += 1
                name = (entry.get("name") or "").strip()
                slug = (entry.get("slug") or "").strip()
                if not name or not slug:
                    report["rejected"] += 1
                    self.stderr.write(f"Rejected (missing name/slug): {entry}")
                    continue
                elev = entry.get("max_elevation_m")
                if elev is not None and not (0 <= int(elev) <= 9000):
                    report["rejected"] += 1
                    self.stderr.write(f"Rejected (implausible elevation {elev}): {name}")
                    continue
                difficulty = entry.get("difficulty", "")
                if difficulty and difficulty not in DIFFICULTIES:
                    report["rejected"] += 1
                    self.stderr.write(f"Rejected (unknown difficulty {difficulty}): {name}")
                    continue
                defaults = {
                    "region": entry.get("region", ""),
                    "district": entry.get("district", ""),
                    "start_point": entry.get("start_point", ""),
                    "end_point": entry.get("end_point", ""),
                    "total_distance_km": entry.get("total_distance_km"),
                    "total_duration_days": entry.get("total_duration_days"),
                    "max_elevation_m": elev,
                    "difficulty": difficulty,
                    "best_season": entry.get("best_season", ""),
                    "permits": entry.get("permits", []),
                    "accommodation": entry.get("accommodation", ""),
                    "safety_notes": entry.get("safety_notes", ""),
                    "description": entry.get("description", ""),
                    "source_name": entry.get("source_name", ""),
                    "source_url": entry.get("source_url", ""),
                    "source_imported_at": now,
                    # Trust rule: imports NEVER self-verify.
                    "verification_state": TrekkingRoute.VerificationState.UNVERIFIED,
                }
                if opts["apply"]:
                    route, created = TrekkingRoute.objects.update_or_create(
                        slug=slug, defaults={**defaults, "name": name})
                    report["created" if created else "updated"] += 1
                    TrekkingStage.objects.filter(route=route).delete()
                    for st in entry.get("stages", []):
                        lat, lon = st.get("latitude"), st.get("longitude")
                        if not _valid_coords(lat, lon):
                            lat = lon = None  # stage kept without coords, flagged by report
                        else:
                            report["stages"] += 1
                        TrekkingStage.objects.create(
                            route=route,
                            day_number=int(st.get("day_number", 0)),
                            name=st.get("name", ""),
                            from_place=st.get("from_place", ""),
                            to_place=st.get("to_place", ""),
                            latitude=lat, longitude=lon,
                            distance_km=st.get("distance_km"),
                            elevation_gain_m=st.get("elevation_gain_m"),
                            elevation_loss_m=st.get("elevation_loss_m"),
                            duration_hours=st.get("duration_hours"))
                else:
                    report["created"] += 1
                    report["stages"] += sum(1 for s in entry.get("stages", [])
                                            if _valid_coords(s.get("latitude"), s.get("longitude")))
        report["finished"] = datetime.now(timezone.utc).isoformat()
        out = Path("dataset/osm_reports")
        out.mkdir(parents=True, exist_ok=True)
        fp = out / f"import_trekking-{now.strftime('%Y%m%d-%H%M%S')}.json"
        fp.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.stdout.write(json.dumps(report, indent=2))
        self.stdout.write(f"Report: {fp.resolve()}")
