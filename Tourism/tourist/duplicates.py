"""Duplicate-candidate detection service (shared by the management command
and the admin CMS endpoints — spec §10).

Read-only: this module only FINDS candidates; merging happens through the
audited admin merge endpoint, and "not duplicate" dismissals are stored so
reviewed pairs never resurface.
"""
import math
import re
import unicodedata

from .models import Destination, DuplicateDecision


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


def find_duplicates(max_km=5.0, include_dismissed=False, limit=None):
    """Return confidence-tiered candidate pairs (high -> medium -> needs_review).

    Identical logic to `manage.py detect_duplicate_destinations`; dismissed
    pairs (admin said "not duplicate") are excluded unless asked for.
    """
    from collections import defaultdict
    import difflib

    rows_all = list(Destination.objects.filter(
        is_active=True, status=Destination.SubmissionStatus.APPROVED
    ).values("id", "name", "district", "latitude", "longitude"))

    dismissed = set()
    if not include_dismissed:
        dismissed = {(d.id_a, d.id_b) for d in DuplicateDecision.objects.all()}

    groups = defaultdict(list)
    for row in rows_all:
        key = normalize_name(row["name"])
        if key:
            groups[key].append(row)

    candidates = []
    seen = set()

    def add(a, b, key, evidence, confidence, distance_km=None):
        pair = (min(a["id"], b["id"]), max(a["id"], b["id"]))
        if pair in seen or pair in dismissed:
            return
        seen.add(pair)
        candidates.append({
            "pair": pair, "normalized_name": key, "confidence": confidence,
            "distance_km": distance_km,
            "a": {"id": a["id"], "name": a["name"], "district": a["district"]},
            "b": {"id": b["id"], "name": b["name"], "district": b["district"]},
            "evidence": evidence,
        })

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
                    same_district = bool(a["district"]) and a["district"] == b["district"]
                    if not (dist <= max_km or same_district):
                        continue
                    evidence = f"{dist:.1f} km apart" + (" + same district" if same_district else "")
                    confidence = "high" if dist <= 0.5 else ("medium" if dist <= max_km else "needs_review")
                    add(a, b, key, evidence, confidence, round(dist, 2))
                else:
                    add(a, b, key, "distance unknown (missing coordinates)", "needs_review")

    by_district = defaultdict(list)
    for rows in groups.values():
        for row in rows:
            if row["district"]:
                by_district[row["district"]].append(row)
    for district, rows in by_district.items():
        if len(rows) < 2 or len(rows) > 3000:
            continue
        rows = sorted(rows, key=lambda r: r["id"])
        for i in range(len(rows)):
            ni = normalize_name(rows[i]["name"])
            for j in range(i + 1, len(rows)):
                nj = normalize_name(rows[j]["name"])
                if ni == nj or abs(len(ni) - len(nj)) > max(len(ni), len(nj)) * 0.3:
                    continue
                sm = difflib.SequenceMatcher(None, ni, nj)
                if sm.real_quick_ratio() < 0.85 or sm.quick_ratio() < 0.85:
                    continue
                ratio = sm.ratio()
                if ratio >= 0.85:
                    add(rows[i], rows[j], f"{ni} ~ {nj}",
                        f"same district ({district}), name similarity {ratio:.2f}",
                        "needs_review")

    tier_rank = {"high": 0, "medium": 1, "needs_review": 2}
    candidates.sort(key=lambda c: (tier_rank[c["confidence"]],
                                   c["distance_km"] if c["distance_km"] is not None else 9e9))
    if limit:
        candidates = candidates[:limit]
    return candidates
