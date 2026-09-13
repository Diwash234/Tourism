"""Enrich imported OSM service rows from a TAGGED Overpass extract.

Replaces honest placeholders ("Hospital (node/123)") with the real OSM name
and fills phone/website/opening_hours/operator/address ONLY from actual tags.
Nothing is invented: fields absent in OSM stay empty.

Trust rules (§2/§6):
  - rows with verification_state=VERIFIED keep every curated field; if the
    source disagrees we record a discrepancy and queue ADMIN_REVIEW instead
    of overwriting
  - verification_state is never auto-upgraded; enrichment sets
    last_enriched_at and, for still-IMPORTED rows whose tags matched the
    stored osm_id, SOURCE_VERIFIED (source cross-check, still not admin
    verified)
  - provenance (osm_id/source_url/raw_tags) is refreshed, never dropped

Usage:
    python manage.py enrich_osm_services --source dir_or_file [--dry-run]
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import OSMEssentialService


def load_elements(fp: Path):
    text = fp.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        if isinstance(parsed.get("elements"), list):
            return parsed["elements"]
        # single-element file (whole file is one tagged element)
        if parsed.get("id") is not None and parsed.get("tags") is not None:
            return [parsed]
        return []
    els = []
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line or line in ("{", "}"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("id") is not None and obj.get("tags") is not None:
            els.append(obj)
    return els


class Command(BaseCommand):
    help = "Enrich OSMEssentialService rows from tagged Overpass extracts (no fabrication)."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        src = Path(opts["source"])
        if src.is_dir():
            files = sorted(list(src.glob("*.json")) + list(src.glob("*.ndjson")))
        else:
            files = [src]
        report = {"started": datetime.now(timezone.utc).isoformat(), "dry_run": opts["dry_run"],
                  "seen": 0, "matched": 0, "unknown_osm_id": 0, "names_filled": 0,
                  "fields_filled": 0, "verified_conflicts_queued": 0, "files": []}
        now = datetime.now(timezone.utc)
        VS = OSMEssentialService.VerificationState
        with transaction.atomic():
            for fp in files:
                if fp.name == "manifest.json":
                    continue
                for el in load_elements(fp):
                    report["seen"] += 1
                    osm_id = f"{el['type']}/{el['id']}"
                    tags = el.get("tags") or {}
                    row = OSMEssentialService.objects.filter(osm_id=osm_id).first()
                    if row is None:
                        report["unknown_osm_id"] += 1
                        continue
                    report["matched"] += 1
                    name = tags.get("name") or tags.get("name:en") or ""
                    changes = {}
                    if name:
                        changes["name_en"] = tags.get("name:en", "")
                        changes["name_ne"] = tags.get("name:ne", "")
                        if "(node/" in row.name or "(way/" in row.name or "(relation/" in row.name:
                            changes["name"] = name
                            report["names_filled"] += 1
                    for field, tag in (("phone", "phone"), ("website", "website"),
                                       ("opening_hours", "opening_hours"),
                                       ("operator", "operator")):
                        val = tags.get(tag, "")
                        if val and not getattr(row, field):
                            changes[field] = val
                    addr = tags.get("addr:full") or ", ".join(
                        x for x in (tags.get("addr:street"), tags.get("addr:city")) if x)
                    if addr and not row.address:
                        changes["address"] = addr
                    if row.verification_state == VS.VERIFIED:
                        # Never overwrite admin-verified data; queue conflicts.
                        conflict = any(k != "name" and getattr(row, k) and getattr(row, k) != v
                                       for k, v in changes.items())
                        if (name and name != row.name) or conflict:
                            report["verified_conflicts_queued"] += 1
                            if not opts["dry_run"]:
                                row.verification_state = VS.ADMIN_REVIEW
                                row.raw_tags = tags
                                row.last_enriched_at = now
                                row.save(update_fields=["verification_state", "raw_tags",
                                                        "last_enriched_at", "updated_at"])
                        continue
                    report["fields_filled"] += sum(1 for k in changes if k != "name")
                    if not opts["dry_run"] and (changes or tags):
                        for k, v in changes.items():
                            setattr(row, k, v)
                        row.raw_tags = tags
                        row.last_enriched_at = now
                        if row.verification_state == VS.IMPORTED:
                            row.verification_state = VS.SOURCE_VERIFIED
                        row.save()
        report["finished"] = datetime.now(timezone.utc).isoformat()
        self.stdout.write(json.dumps(report, indent=2))
