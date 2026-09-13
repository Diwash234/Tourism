"""Duplicate detection: find likely same-place destination records.

The review requirement: "Pashupatinath Temple / Pashupati Nath /
Pashupati Temple" must be recognizable as one place so an admin can merge
the records safely (see AdminDestinationMergeView). This command NEVER
merges or modifies anything — it only reports candidates for human review.

Matching rules (deliberately conservative — false positives are cheap,
silent wrong merges are not):
  * names equal after normalization (casefold, punctuation stripped,
    whitespace collapsed), AND
  * either both within --max-km (default 5 km), or same district, or one
    of the two has no coordinates (reported as "distance unknown").

Usage:
    python manage.py detect_duplicate_destinations
    python manage.py detect_duplicate_destinations --max-km 10 --report /tmp/dupes.json
"""
import json
import math
import os
import re
import unicodedata
from collections import defaultdict

from django.core.management.base import BaseCommand

from tourist.models import Destination


def normalize_name(name):
    s = unicodedata.normalize("NFKD", name or "").casefold()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def haversine_km(la1, lo1, la2, lo2):
    r = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


class Command(BaseCommand):
    help = "Report likely duplicate destinations (same normalized name + proximity). Read-only."

    def add_arguments(self, parser):
        parser.add_argument("--max-km", type=float, default=5.0, help="Proximity threshold when both have coordinates")
        parser.add_argument("--report", default=None, help="Write JSON report to this path")

    def handle(self, *args, **options):
        groups = defaultdict(list)
        qs = (Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)
              .values("id", "name", "district", "latitude", "longitude"))
        for row in qs:
            key = normalize_name(row["name"])
            if key:
                groups[key].append(row)

        candidates = []
        seen_pairs = set()

        def add_pair(a, b, key, evidence, confidence, distance_km=None):
            pair = (min(a["id"], b["id"]), max(a["id"], b["id"]))
            if pair in seen_pairs:
                return
            seen_pairs.add(pair)
            candidates.append({
                "normalized_name": key,
                "confidence": confidence,          # high | medium | needs_review
                "distance_km": distance_km,
                "a": {"id": a["id"], "name": a["name"], "district": a["district"]},
                "b": {"id": b["id"], "name": b["name"], "district": b["district"]},
                "evidence": evidence,
            })

        # Rule 1: identical normalized names + proximity/same district
        for key, rows in groups.items():
            if len(rows) < 2:
                continue
            rows.sort(key=lambda r: r["id"])
            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    a, b = rows[i], rows[j]
                    has_coords = all(r["latitude"] and r["longitude"] for r in (a, b))
                    if has_coords:
                        dist = haversine_km(float(a["latitude"]), float(a["longitude"]),
                                            float(b["latitude"]), float(b["longitude"]))
                        near = dist <= options["max_km"]
                        same_district = bool(a["district"]) and a["district"] == b["district"]
                        if not (near or same_district):
                            continue
                        evidence = f"{dist:.1f} km apart" + (" + same district" if same_district else "")
                        # Confidence triage: identical names at (near-)identical
                        # coordinates are almost certainly the same place.
                        confidence = "high" if dist <= 0.5 else ("medium" if near else "needs_review")
                        add_pair(a, b, key, evidence, confidence, round(dist, 2))
                    else:
                        evidence = "distance unknown (missing coordinates)"
                        add_pair(a, b, key, evidence, "needs_review")

        # Rule 2: high name similarity WITHIN the same district (catches
        # "Pashupatinath Temple" vs "Pashupati Temple" style variants).
        # District-scoped to keep the pairwise scan bounded and to avoid
        # matching same-named shrines in different parts of Nepal.
        import difflib
        by_district = defaultdict(list)
        for rows in groups.values():
            for row in rows:
                if row["district"]:
                    by_district[row["district"]].append(row)
        for district, rows in by_district.items():
            if len(rows) < 2 or len(rows) > 3000:  # bounded; huge districts: use rule 1 only
                continue
            rows = sorted(rows, key=lambda r: r["id"])
            for i in range(len(rows)):
                ni = normalize_name(rows[i]["name"])
                for j in range(i + 1, len(rows)):
                    nj = normalize_name(rows[j]["name"])
                    if ni == nj or abs(len(ni) - len(nj)) > max(len(ni), len(nj)) * 0.3:
                        continue  # identical handled by rule 1; wild length gaps skipped
                    sm = difflib.SequenceMatcher(None, ni, nj)
                    if sm.real_quick_ratio() < 0.85 or sm.quick_ratio() < 0.85:
                        continue
                    ratio = sm.ratio()
                    if ratio >= 0.85:
                        add_pair(rows[i], rows[j], f"{ni} ~ {nj}",
                                 f"same district ({district}), name similarity {ratio:.2f}",
                                 "needs_review")

        # Priority order for admin review: high confidence first, then by
        # proximity (closest pairs are the safest merges).
        tier_rank = {"high": 0, "medium": 1, "needs_review": 2}
        candidates.sort(key=lambda c: (tier_rank[c["confidence"]],
                                       c["distance_km"] if c["distance_km"] is not None else 9e9))
        tier_counts = {t: sum(1 for c in candidates if c["confidence"] == t)
                       for t in ("high", "medium", "needs_review")}

        self.stdout.write(f"Scanned {qs.count()} approved destinations; "
                          f"{len(candidates)} candidate duplicate pair(s): "
                          f"high={tier_counts['high']} medium={tier_counts['medium']} "
                          f"needs_review={tier_counts['needs_review']}")
        for c in candidates[:15]:
            self.stdout.write(f"  [{c['confidence']}] #{c['a']['id']} '{c['a']['name']}' <-> "
                              f"#{c['b']['id']} '{c['b']['name']}' ({c['evidence']})")
        if len(candidates) > 15:
            self.stdout.write(f"  ... and {len(candidates) - 15} more (use --report for the full list)")

        if options["report"]:
            os.makedirs(os.path.dirname(options["report"]) or ".", exist_ok=True)
            with open(options["report"], "w", encoding="utf-8") as f:
                json.dump({"tier_counts": tier_counts, "candidates": candidates,
                           "total": len(candidates)}, f, indent=2, ensure_ascii=False)
            self.stdout.write(f"Report: {options['report']}")
