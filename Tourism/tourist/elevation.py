"""Destination elevations from a cited digital elevation model.

Only 3 of ~6,000 destinations had an ``altitude`` text value, so altitude
and acclimatization planning had nothing to work with. This module fills
``Destination.elevation_m`` from the Copernicus DEM GLO-90 (served by the
Open-Meteo elevation API), with these guard rails:

  * Only coordinates with >= 3 decimal places (~110 m) are looked up. A
    coarse coordinate such as 27.8, 86.7 can sit kilometres from the real
    place, and in the Himalaya that is a difference of 1,000+ m, so those
    destinations stay "not recorded" instead of getting a misleading value.
  * Imports match on destination id AND the stored coordinates, so a value
    is discarded if the destination has since been moved.
  * Every value keeps its source and retrieval date.
  * DEM elevation is terrain height at the point, not a surveyed summit or
    village height; the UI labels it "approx." with the source.
"""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings

OPEN_METEO_ELEVATION = "https://api.open-meteo.com/v1/elevation"
DEM_SOURCE = "Copernicus DEM GLO-90 via Open-Meteo"
BATCH_SIZE = 100  # Open-Meteo accepts up to 100 coordinates per request
MIN_DECIMALS = 3
NEPAL_BBOX = (26.3, 30.5, 80.0, 88.3)  # lat_min, lat_max, lon_min, lon_max
DATA_FILE = Path(settings.BASE_DIR) / "dataset" / "destination_elevations.json"
ALTITUDE_THRESHOLD_M = 2500  # NTB: AMS risk above 2,500 m

_ALT_RE = re.compile(r"(\d{1,2}[,\s]?\d{3}|\d{3,4})\s*(?:m\b|metres|meters|masl)", re.I)


def decimals(value) -> int:
    if value is None:
        return 0
    try:
        text = format(Decimal(str(value)).normalize(), "f")
    except InvalidOperation:
        return 0
    return len(text.split(".", 1)[1]) if "." in text else 0


def _arc_minute_rounded(value) -> bool:
    """True for values like 28.0833 / 85.4167 (whole arc-minutes, ~1.8 km grid)."""
    if decimals(value) > 4:
        return False
    minutes = (abs(float(value)) % 1) * 60
    return abs(minutes - round(minutes)) < 0.01


def coordinate_precision_ok(lat, lon) -> bool:
    if lat is None or lon is None:
        return False
    lat_f, lon_f = float(lat), float(lon)
    in_nepal = NEPAL_BBOX[0] <= lat_f <= NEPAL_BBOX[1] and NEPAL_BBOX[2] <= lon_f <= NEPAL_BBOX[3]
    if not (in_nepal and decimals(lat) >= MIN_DECIMALS and decimals(lon) >= MIN_DECIMALS):
        return False
    # 28.0833, 85.4167 passes a "4 decimals" test but is really degree-minute
    # data rounded to whole arc-minutes (+-900 m) -- too coarse in the mountains.
    return not (_arc_minute_rounded(lat) and _arc_minute_rounded(lon))


def parse_altitude_text(text) -> int | None:
    """'2,175m / 7,135 ft' -> 2175. Returns None for anything unparseable."""
    if not text:
        return None
    match = _ALT_RE.search(str(text))
    if not match:
        return None
    value = int(re.sub(r"[,\s]", "", match.group(1)))
    return value if 50 <= value <= 8849 else None


def best_elevation(dest) -> dict:
    """Best known elevation for a destination, with provenance.

    Returns {"elevation_m": int|None, "source": str, "kind": "dem"|"record"|None,
             "retrieved_at": str|None}.
    """
    if getattr(dest, "elevation_m", None) is not None:
        retrieved = getattr(dest, "elevation_retrieved_at", None)
        return {
            "elevation_m": int(dest.elevation_m),
            "source": dest.elevation_source or DEM_SOURCE,
            "kind": "dem",
            "retrieved_at": retrieved.isoformat() if retrieved else None,
        }
    parsed = parse_altitude_text(getattr(dest, "altitude", None))
    if parsed is not None:
        return {"elevation_m": parsed, "source": "Destination record (altitude field)", "kind": "record", "retrieved_at": None}
    return {"elevation_m": None, "source": "", "kind": None, "retrieved_at": None}


def batch_url(points) -> str:
    lats = ",".join(f"{float(lat):.6f}" for lat, _ in points)
    lons = ",".join(f"{float(lon):.6f}" for _, lon in points)
    return f"{OPEN_METEO_ELEVATION}?latitude={lats}&longitude={lons}"


def fetch_batch(points, timeout: int = 15) -> list:
    import requests

    resp = requests.get(batch_url(points), timeout=timeout)
    resp.raise_for_status()
    values = (resp.json() or {}).get("elevation") or []
    if len(values) != len(points):
        raise ValueError(f"Open-Meteo returned {len(values)} values for {len(points)} points")
    return values


def eligible_queryset(qs):
    """Destinations whose coordinates are precise enough for a DEM lookup."""
    return [d for d in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True).order_by("id")
            if coordinate_precision_ok(d.latitude, d.longitude)]


def _same_point(a, b) -> bool:
    return abs(float(a) - float(b)) < 1e-5


def apply_records(records, *, dry_run: bool = False) -> dict:
    """Apply [{id, lat, lon, elevation_m, source, retrieved_at}] to destinations."""
    from .models import Destination

    stats = {"applied": 0, "moved": 0, "missing": 0, "invalid": 0, "imprecise": 0}
    by_id = {r.get("id"): r for r in records if r.get("id") is not None}
    for dest in Destination.objects.filter(id__in=list(by_id)):
        rec = by_id[dest.id]
        elev = rec.get("elevation_m")
        if elev is None or not (-100 <= float(elev) <= 8849):
            stats["invalid"] += 1
            continue
        if dest.latitude is None or not (_same_point(dest.latitude, rec["lat"]) and _same_point(dest.longitude, rec["lon"])):
            stats["moved"] += 1
            continue
        if not coordinate_precision_ok(dest.latitude, dest.longitude):
            stats["imprecise"] += 1
            continue
        stats["applied"] += 1
        if not dry_run:
            Destination.objects.filter(pk=dest.pk).update(
                elevation_m=int(round(float(elev))),
                elevation_source=rec.get("source") or DEM_SOURCE,
                elevation_retrieved_at=date.fromisoformat(rec.get("retrieved_at") or date.today().isoformat()),
            )
    stats["missing"] = len(by_id) - stats["applied"] - stats["moved"] - stats["invalid"] - stats["imprecise"]
    return stats


def load_data_file(path=None, *, dry_run: bool = False) -> dict:
    path = Path(path or DATA_FILE)
    if not path.exists():
        return {"applied": 0, "file": str(path), "exists": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records") if isinstance(data, dict) else data
    stats = apply_records(records or [], dry_run=dry_run)
    stats.update({"file": str(path), "exists": True})
    return stats
