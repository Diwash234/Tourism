"""
CSV-driven budget baselines.

Loads ``ml_service/processed_data/budget_features.csv`` (and the raw
``data/budget/travel_cost_cleaned.csv``) and exposes province/district/
destination-level daily cost ranges so the budget estimator uses the REAL
dataset instead of a handful of hard-coded city numbers.

The CSV cells contain ranges like "40-120" (USD); we parse the midpoint.
Rows are keyed by destination name, district and province so a query for
"Chitwan", "Chitwan district", or "Bagmati province" all resolve.
"""

import csv
import os
import re
import threading
from typing import Optional, Dict, List

_BASE = os.path.dirname(__file__)
_FEATURES_CSV = os.path.normpath(os.path.join(_BASE, "..", "..", "processed_data", "budget_features.csv"))
_RAW_CSV = os.path.normpath(os.path.join(_BASE, "..", "..", "data", "budget", "travel_cost_cleaned.csv"))

_lock = threading.Lock()
_cache = None


def _midpoint(value: str) -> Optional[float]:
    """Parse '40-120' / '25.5' / '0' into a float midpoint. None if unusable."""
    if value is None:
        return None
    s = str(value).strip().replace("$", "").replace(",", "")
    if not s or s == "0":
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None
    nums = [float(n) for n in nums]
    return sum(nums) / len(nums)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _build_cache() -> Dict:
    by_dest: Dict[str, Dict[str, float]] = {}
    by_district: Dict[str, List[Dict[str, float]]] = {}
    by_province: Dict[str, List[Dict[str, float]]] = {}

    def _ingest(dest, district, province, transport, food, accom, taxi):
        entry = {
            "transport": _midpoint(transport),
            "food": _midpoint(food),
            "accommodation": _midpoint(accom),
            "taxi": _midpoint(taxi),
        }
        # only keep entries with at least one usable cost figure
        if not any(v is not None for v in entry.values()):
            return
        if dest:
            by_dest[_norm(dest)] = entry
        if district:
            by_district.setdefault(_norm(district), []).append(entry)
        if province:
            by_province.setdefault(_norm(province), []).append(entry)

    # 1. Processed features CSV (header is 8 cols but rows carry extra
    #    trailing range columns; we only read the first 8).
    try:
        with open(_FEATURES_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            for row in reader:
                if len(row) < 8:
                    continue
                _ingest(row[1], row[2], row[3], row[4], row[5], row[6], row[7])
    except FileNotFoundError:
        pass

    # 2. Raw province-level ranges
    try:
        with open(_RAW_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) < 8:
                    continue
                # raw file: source=province, destination, district, province...
                _ingest(row[1], row[2], row[0] or row[3], row[4], row[5], row[6], row[7])
    except FileNotFoundError:
        pass

    def _average(entries: List[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if not entries:
            return None
        keys = ("transport", "food", "accommodation", "taxi")
        out = {}
        for k in keys:
            vals = [e[k] for e in entries if e.get(k) is not None]
            out[k] = round(sum(vals) / len(vals), 2) if vals else None
        return out

    return {
        "by_dest": by_dest,
        "by_district": {k: _average(v) for k, v in by_district.items() if _average(v)},
        "by_province": {k: _average(v) for k, v in by_province.items() if _average(v)},
    }


def _cache_get():
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                _cache = _build_cache()
    return _cache


def dataset_info() -> Dict:
    c = _cache_get()
    return {
        "destinations": len(c["by_dest"]),
        "districts": len(c["by_district"]),
        "provinces": len(c["by_province"]),
        "source_file": os.path.basename(_FEATURES_CSV),
    }


def lookup_baseline(city: str = None, district: str = None, province: str = None) -> Optional[Dict[str, float]]:
    """
    Return {transport, food, accommodation, taxi} daily USD figures from the
    CSV dataset for the most specific match available (destination >
    district > province). Returns None when nothing matches so the caller
    can fall back to built-in baselines.
    """
    c = _cache_get()

    for value, bucket in (
        (city, c["by_dest"]),
        (district, c["by_district"]),
        (province, c["by_province"]),
    ):
        if not value:
            continue
        key = _norm(value)
        if key in bucket and bucket[key]:
            return dict(bucket[key])
        # substring match (e.g. "Chitwan National Park" -> "chitwan")
        for k, v in bucket.items():
            if k and (k in key or key in k) and v:
                return dict(v)
    return None
