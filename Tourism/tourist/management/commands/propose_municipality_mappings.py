"""Controlled municipality-mapping candidate proposal (§6 V4).

Reads unresolved MunicipalityMapping rows and proposes candidates ONLY from
authoritative internal data (the 77-row District table, itself loaded from
official 2015 federal-structure data). Nothing is auto-resolved: every
candidate is written to a controlled JSON file with source, confidence and
approval_state=pending_admin. Rows that cannot be matched honestly stay
unresolved with reason codes. No guessing, no fabrication.

Usage:
    python manage.py propose_municipality_mappings \
        [--out dataset/osm_reports/municipality_mapping_candidates.json]
"""

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand

from tourist.models import District, MunicipalityMapping


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip().lower()
    value = re.sub(r"\(.*?\)", " ", value)  # drop parentheticals
    value = re.sub(r"[^a-z0-9\u0900-\u097F\s/-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


class Command(BaseCommand):
    help = "Propose district/province candidates for unresolved municipality mappings (admin approval required)."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="dataset/osm_reports/municipality_mapping_candidates.json")

    def handle(self, *args, **opts):
        districts = list(District.objects.all())
        by_norm = {_normalize(d.name): d for d in districts}

        rows = MunicipalityMapping.objects.filter(verified=False).order_by("id")
        candidates = []
        stats = {"total_unresolved": rows.count(), "exact_district_match": 0,
                 "ambiguous": 0, "unmatched_needs_external_source": 0, "junk_recommended_reject": 0}

        for row in rows:
            raw = row.name
            norm = _normalize(raw)
            entry = {
                "mapping_id": row.id,
                "raw_value": raw,
                "normalized_value": norm,
                "current_district": row.district,
                "current_province": row.province,
                "source": row.source,
                "candidates": [],
                "confidence": None,
                "approval_state": "pending_admin",
                "recommendation": None,
            }

            if "/" in norm:  # ambiguous multi-district value: list all parts, never pick
                parts = [p.strip() for p in norm.split("/") if p.strip()]
                matched = [by_norm[p] for p in parts if p in by_norm]
                if matched:
                    entry["candidates"] = [{"district": d.name, "province": d.province.name,
                                            "basis": "district_table_exact_part"} for d in matched]
                    entry["confidence"] = "low"
                    entry["recommendation"] = "ambiguous_value_split_required"
                    stats["ambiguous"] += 1
                else:
                    entry["recommendation"] = "unmatched_ambiguous"
                    stats["unmatched_needs_external_source"] += 1
            elif norm in by_norm:
                d = by_norm[norm]
                entry["candidates"] = [{"district": d.name, "province": d.province.name,
                                        "basis": "district_table_exact"}]
                entry["confidence"] = "high"
                entry["recommendation"] = "verify_as_district_name"
                stats["exact_district_match"] += 1
            elif not re.search(r"[a-z\u0900-\u097F]{3}", norm) or re.fullmatch(r"[\d\s/-]+", norm) or norm in {"district", "province", "municipality"}:
                entry["recommendation"] = "reject_junk_value"
                stats["junk_recommended_reject"] += 1
            else:
                # e.g. "Dharan", "Itahari", "Kanyam": real place names that are NOT
                # district names. Resolving them needs an authoritative local-level
                # source (OSM admin_level>=7 or government gazette) - not available
                # offline. Stay unresolved; never guess.
                entry["recommendation"] = "needs_external_authoritative_source"
                stats["unmatched_needs_external_source"] += 1

            candidates.append(entry)

        out = Path(opts["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "authoritative_internal_source": "tourist.District (77 rows, official federal structure)",
            "policy": "No auto-resolution. Admin must approve each candidate before MunicipalityMapping.verified is set.",
            "stats": stats,
            "candidates": candidates,
        }
        out.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        self.stdout.write(json.dumps(stats, indent=1))
        self.stdout.write(f"wrote {out}")
