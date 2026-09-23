"""Duplicate candidate detection for Destinations.

Shared service used by the admin Duplicate Review CMS. Pairs that an admin
has already ruled on (DuplicateDecision) are excluded. Tiers:

  high         — normalized names match and records are < 0.5 km apart
  medium       — normalized names match and records are < 2 km apart
  needs_review — normalized names match and records are < 5 km apart, or
                 names are very similar (difflib ratio >= 0.92) and < 1 km.
"""
import math
import re
import unicodedata
from difflib import SequenceMatcher

from .models import Destination, DuplicateDecision

_SUFFIXES = {
    "the", "a", "an", "of", "and", "at", "in", "on", "to", "for", "nepal",
    "hotel", "lodge", "resort", "inn", "guesthouse", "guest house", "homestay",
    "restaurant", "cafe", "temple", "stupa", "monastery", "park", "museum",
    "hospital", "school", "college", "bank", "office", "station", "police",
}


def normalize_name(name):
    text = unicodedata.normalize("NFKD", (name or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [w for w in text.split() if w and w not in _SUFFIXES]
    return " ".join(sorted(words))


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = p2 - p1
    dl = math.radians(float(lon2) - float(lon1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def find_duplicates(max_km=5.0, district=None, limit=500):
    """Return (tier_counts, results). Deterministic ordering by distance."""
    qs = Destination.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    if district:
        qs = qs.filter(district__iexact=district)

    ruled = DuplicateDecision.objects.all().values_list("destination_a_id", "destination_b_id")
    ruled_pairs = {frozenset((a, b)) for a, b in ruled}

    rows = list(qs.values("id", "name", "district", "latitude", "longitude"))
    # bucket by district + first normalized word to bound comparisons
    buckets = {}
    for r in rows:
        key = (r["district"] or "", normalize_name(r["name"]).split(" ")[0] if normalize_name(r["name"]) else "")
        buckets.setdefault(key, []).append(r)

    counts = {"high": 0, "medium": 0, "needs_review": 0}
    results = []
    for bucket in buckets.values():
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                a, b = bucket[i], bucket[j]
                if frozenset((a["id"], b["id"])) in ruled_pairs:
                    continue
                na, nb = normalize_name(a["name"]), normalize_name(b["name"])
                if not na or not nb:
                    continue
                dist = haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
                tier = None
                evidence = f"{dist:.1f} km apart"
                if na == nb and dist < 0.5:
                    tier = "high"
                elif na == nb and dist < 2.0:
                    tier = "medium"
                elif na == nb and dist < max_km:
                    tier = "needs_review"
                elif dist < 1.0 and SequenceMatcher(None, na, nb).ratio() >= 0.92:
                    tier = "needs_review"
                    evidence = f"{dist:.1f} km apart + similar names"
                if tier:
                    counts[tier] += 1
                    if len(results) < limit:
                        results.append({
                            "pair": [a["id"], b["id"]],
                            "normalized_name": na,
                            "confidence": tier,
                            "distance_km": round(dist, 2),
                            "evidence": evidence,
                            "a": {"id": a["id"], "name": a["name"], "district": a["district"]},
                            "b": {"id": b["id"], "name": b["name"], "district": b["district"]},
                        })
    results.sort(key=lambda r: ({"high": 0, "medium": 1, "needs_review": 2}[r["confidence"]], r["distance_km"]))
    return counts, results
