"""Traveller-facing facts for every public destination, with provenance.

One cached table powers the traveller filters, the season-aware recommender,
universal search and decision pages, so each feature answers from the same
facts.

Rules this module keeps (the project's real-data policy):

* **Never invent a value.** Unknown elevation means "unknown", not "easy".
  No matching official fee means "no official fee on record", not "free".
* **Every derived value carries its basis**: what it was derived from and
  which source the rule comes from, so the UI can explain it.
* **Straight-line distance is labelled as straight-line.** Road distance is
  always longer, and this module never pretends otherwise.

Sources:
* ``dataset/season_guidance.json``: Nepal Tourism Board climate guidance.
* ``dataset/travel_requirements.json``: DOI and NTB permits, park and
  heritage fees, and the altitude-sickness rules.
* Elevation from the destination record (Copernicus DEM via Open-Meteo).
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Max

from . import travel_requirements as treq
from .elevation import best_elevation

SEASON_PATH = Path(settings.BASE_DIR) / "dataset" / "season_guidance.json"

# --------------------------------------------------------------------------
# Activities
# --------------------------------------------------------------------------
# Category slug -> traveller activity. Categories are curated in the admin,
# so this mapping is a presentation grouping, not a data claim.
ACTIVITIES = {
    "trekking": {"label": "Trekking & mountains", "categories": [
        "trekking", "trekking-nature", "mountains", "adventure-and-mountain", "winter"]},
    "adventure": {"label": "Adventure sports", "categories": [
        "adventure", "air-sports", "water-sports", "cycling", "camping"]},
    "culture": {"label": "Culture & heritage", "categories": [
        "heritage", "heritage-culture", "culture", "museums", "festivals", "villages",
        "agriculture", "tea-coffee", "shopping"]},
    "spiritual": {"label": "Temples & pilgrimage", "categories": [
        "temples", "pilgrimage", "pilgrimage-and-sacred", "religious-pilgrimage",
        "buddhist-sites", "spiritual-wellness"]},
    "wildlife": {"label": "Wildlife & forests", "categories": [
        "wildlife", "wildlife-and-nature", "bird-watching", "forests", "eco-tourism"]},
    "water": {"label": "Lakes, rivers & hot springs", "categories": [
        "lakes", "lakes-water-bodies", "rivers", "waterfalls", "hot-springs"]},
    "views": {"label": "Viewpoints, hills & valleys", "categories": [
        "viewpoints", "viewpoints-hillstations", "hill-stations-and-views", "hills",
        "scenic-routes", "valleys", "natural-wonders", "caves"]},
    "city": {"label": "Cities & towns", "categories": ["cities"]},
    "food": {"label": "Food & culinary", "categories": ["food-culinary"]},
    "sightseeing": {"label": "General sightseeing", "categories": ["attraction"]},
}
CATEGORY_TO_ACTIVITY = {slug: key for key, a in ACTIVITIES.items() for slug in a["categories"]}
# Activities whose enjoyment depends on dry weather and clear views.
OUTDOOR_ACTIVITIES = {"trekking", "adventure", "views", "wildlife", "water"}

DIFFICULTY_LABELS = {
    "easy": "Easy",
    "moderate": "Moderate",
    "strenuous": "Strenuous",
    "unknown": "Unknown",
}
COST_LABELS = {
    "restricted_permit": "Restricted-area permit",
    "park_fee": "Park / conservation-area fee",
    "heritage_fee": "Heritage-site fee",
    "none_on_record": "No official fee on record",
}
SEASON_LEVELS = {"best": 3, "good": 2, "fair": 1, "caution": 0, "poor": -1}
SEASON_LEVEL_LABELS = {
    "best": "Best time", "good": "Good time", "fair": "Possible",
    "caution": "Take care", "poor": "Not ideal", "unknown": "Unknown",
}
MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]

# Reach bands from the traveller's origin (straight-line km).
REACH_BANDS = [
    ("day_trip", 60, "Day trip"),
    ("overnight", 200, "Overnight or weekend"),
    ("multi_day", None, "Multi-day journey"),
]


@lru_cache(maxsize=1)
def season_dataset() -> dict:
    with SEASON_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def season_source(key: str = "ntb_climate") -> dict:
    return dict(season_dataset()["sources"][key])


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def parse_month(value) -> int | None:
    try:
        month = int(value)
    except (TypeError, ValueError):
        return None
    return month if 1 <= month <= 12 else None


# --------------------------------------------------------------------------
# Derived facts (pure functions; each returns its basis)
# --------------------------------------------------------------------------
def activity_for(category_slug: str) -> str:
    return CATEGORY_TO_ACTIVITY.get(category_slug or "", "other")


def difficulty_for(elevation_m, activity: str) -> dict:
    """Effort level derived from altitude. Not an official route grading."""
    threshold = treq.ALTITUDE_THRESHOLD_M
    if elevation_m is None:
        return {"level": "unknown", "label": DIFFICULTY_LABELS["unknown"],
                "basis": "No measured elevation on record, so the effort level is unknown."}
    active = activity in {"trekking", "adventure"}
    if elevation_m >= 3500 or (active and elevation_m >= 3000):
        level = "strenuous"
    elif elevation_m >= threshold or active:
        level = "moderate"
    else:
        level = "easy"
    why = f"Elevation {elevation_m:,} m"
    if elevation_m >= threshold:
        why += f" is above the {threshold:,} m altitude-sickness threshold (NTB)"
    else:
        why += f" is below the {threshold:,} m altitude-sickness threshold (NTB)"
    if active:
        why += "; trekking/adventure activity"
    return {"level": level, "label": DIFFICULTY_LABELS[level],
            "basis": why + ". Derived by this site from altitude, not an official route grading."}


def estimated_temperatures(elevation_m) -> dict | None:
    """NTB Kathmandu averages adjusted by NTB's 6 °C / 1,000 m lapse rate."""
    if elevation_m is None:
        return None
    data = season_dataset()
    ref = data["reference_stations"]["kathmandu"]
    shift = (ref["elevation_m"] - elevation_m) * data["lapse_rate_c_per_1000m"] / 1000.0
    return {
        "winter_min_c": round(ref["winter"]["min_c"] + shift),
        "winter_max_c": round(ref["winter"]["max_c"] + shift),
        "summer_max_c": round(ref["summer"]["max_c"] + shift),
        "summer_min_c": round(ref["summer"]["min_c"] + shift),
        "basis": ("Estimate: NTB's Kathmandu seasonal averages adjusted by NTB's rule that "
                  "temperatures drop 6 °C per 1,000 m. Not a measurement or forecast."),
        "source": season_source(),
    }


def season_fit(*, month: int, activity: str, elevation_m, district: str, province: str = "") -> dict:
    """How well ``month`` suits a destination, citing NTB's climate guidance."""
    data = season_dataset()
    facts = data["facts"]
    season = data["months"][str(month)]
    zones = data["zones"]
    district_n = (district or "").strip().lower().replace(" district", "")
    rain_shadow = district_n in data["rain_shadow_districts"]
    outdoor = activity in OUTDOOR_ACTIVITIES
    high = elevation_m is not None and elevation_m >= zones["high_altitude_min_m"]
    tarai = elevation_m is not None and elevation_m < zones["tarai_max_m"]
    notes = []

    if season == "autumn":
        level, reason = "best", facts["autumn"]
    elif season == "spring":
        if outdoor:
            level, reason = "best", f"{facts['best_trekking']} {facts['spring']}"
        else:
            level, reason = "good", facts["spring"]
    elif season == "monsoon":
        if rain_shadow:
            level, reason = "good", facts["rain_shadow"]
        elif outdoor:
            level, reason = "poor", facts["monsoon"]
        else:
            level, reason = "fair", f"{facts['monsoon']} {facts['year_round']}"
    elif season == "winter":
        if high:
            level, reason = "caution", facts["winter"]
        elif elevation_m is None and activity == "trekking":
            level, reason = "fair", facts["winter"]
            notes.append("Elevation is not on record, so high-altitude winter cold cannot be ruled out.")
        else:
            level, reason = "good", facts["winter"]
        if (province or "").lower().startswith(("karnali", "sudurpashchim", "sudur")):
            notes.append(facts["winter_west"])
    else:  # summer (May)
        if tarai:
            level, reason = "caution", facts["tarai_summer"]
        else:
            level, reason = "good", facts["year_round"]

    temps = estimated_temperatures(elevation_m)
    if temps and season == "winter" and high:
        notes.append(f"Typical winter nights ≈ {temps['winter_min_c']} °C (estimate from NTB averages and lapse rate).")
    return {
        "month": month, "month_name": MONTH_NAMES[month], "season": season,
        "level": level, "label": SEASON_LEVEL_LABELS[level], "score": SEASON_LEVELS[level],
        "reason": reason, "notes": notes, "rain_shadow": rain_shadow,
        "source": season_source(),
    }


class _CompiledRule:
    """``travel_requirements.match_rule`` with its text work done once.

    Same semantics (verified against the original in tests), but district
    names and keyword patterns are normalised and compiled once instead of
    per destination, which makes the 6k-row table build fast.
    """

    def __init__(self, rule: dict):
        self.districts = {treq._norm(d) for d in rule.get("districts") or []}
        self.whole = {treq._norm(d) for d in rule.get("whole_districts") or []}
        self.keywords = []
        # Normalized keyword set for the "can any rule match at all?" pre-check
        # in cost_class_for, so the common no-match case does not have to run
        # every rule's regex against every destination.
        self.keyword_map = set()
        for k in rule.get("name_keywords") or []:
            kw = treq._norm(k)
            if kw:
                self.keyword_map.add(kw)
                self.keywords.append((k, re.compile(rf"(?<![a-z]){re.escape(kw)}(?![a-z])")))

    def match(self, district_norm: str, district_raw: str, haystack: str) -> str | None:
        if district_norm and district_norm in self.whole:
            return f"The destination is in {district_raw} district, which lies within this area."
        hit = next((k for k, rx in self.keywords if rx.search(haystack)), None)
        if hit is None:
            return None
        if self.districts and district_norm and district_norm not in self.districts:
            return None
        where = f" in {district_raw} district" if district_raw else ""
        return f"Place name matches “{hit}”{where}."


@lru_cache(maxsize=1)
def _compiled_rules():
    data = treq.load_dataset()
    return {
        "restricted": [(r, _CompiledRule(r["match"])) for r in data["restricted_areas"]],
        "protected": [(r, _CompiledRule(r["match"])) for r in data["protected_areas"]],
        "tims": [(r, _CompiledRule(r["match"])) for r in data["tims"]["regions"]],
        "heritage": [(r, _CompiledRule(r["match"])) for r in data["heritage_sites"]],
    }


def _letter_tokens(text):
    """Lowercase-letter runs, split on every other character (digits included)."""
    return tuple(re.findall(r"[a-z]+", str(text or "")))


@lru_cache(maxsize=1)
def _rule_reach_probe():
    """Fast "can any rule possibly match this place?" test.

    ``_CompiledRule.match`` can only return a basis in two ways: the
    destination's district is in a rule's ``whole_districts`` list, or one of the
    rule's ``name_keywords`` appears in the destination text. When neither is
    true for *any* rule, ``cost_class_for`` is guaranteed to end at
    ``none_on_record``, so the whole per-rule chain can be skipped.

    Running every rule's regex against every destination made the ~6,700-row
    fact-table build (which recommendation requests wait on) take ~50 s.
    Keywords are matched as letter-run token tuples rather than one giant
    alternation regex, because a 2,300-branch regex is itself slow in Python.

    Returns ``(keyword_token_tuples, whole_districts, max_keyword_words)``.
    """
    rules = _compiled_rules()
    token_tuples: set[tuple] = set()
    whole: set[str] = set()
    for group in rules.values():
        for _rule, compiled in group:
            whole.update(compiled.whole)
            for kw in compiled.keyword_map:
                tokens = _letter_tokens(kw)
                if tokens:
                    token_tuples.add(tokens)
    max_words = max((len(k) for k in token_tuples), default=1)
    return frozenset(token_tuples), frozenset(whole), max_words


def _haystack_hits_any_keyword(haystack: str, token_set, max_words: int) -> bool:
    """True when any rule keyword appears in the normalized haystack.

    Reproduces the per-rule ``(?<![a-z])kw(?![a-z])`` boundary rule exactly:
    every character that is not a lowercase letter acts as a word boundary, so
    "rara" matches inside "rara1" but not inside "rarakot".
    """
    words = _letter_tokens(haystack)
    if not words:
        return False
    size_limit = min(max_words, len(words))
    for size in range(1, size_limit + 1):
        for start in range(len(words) - size + 1):
            if words[start:start + size] in token_set:
                return True
    return False


def cost_class_for(dest) -> dict:
    """Which official fee rule (if any) matches, from the transcribed DOI/NTB data."""
    rules = _compiled_rules()
    district_raw = getattr(dest, "district", "") or ""
    district_norm = treq._district(dest)
    haystack = treq._haystack(dest)

    # Cheap rejection first: no rule keyword in the text and no whole-district
    # match means no rule can match, so the per-rule scan is pure waste.
    token_set, whole_districts, max_words = _rule_reach_probe()
    if district_norm not in whole_districts and not _haystack_hits_any_keyword(
        haystack, token_set, max_words
    ):
        return {"class": "none_on_record", "label": COST_LABELS["none_on_record"], "area": "",
                "basis": ("No DOI permit, NTB park or heritage fee rule matches this place. "
                          "Local entry charges may still apply."),
                "source": None}

    def first(group):
        for rule, compiled in rules[group]:
            basis = compiled.match(district_norm, district_raw, haystack)
            if basis:
                return rule, basis
        return None, None

    rule, basis = first("restricted")
    if rule:
        return {"class": "restricted_permit", "label": COST_LABELS["restricted_permit"],
                "area": rule["name"], "fee_text": rule["fee_text"], "basis": basis,
                "source": treq._source("doi_permits")}
    rule, basis = first("protected")
    if rule:
        return {"class": "park_fee", "label": COST_LABELS["park_fee"], "area": rule["name"],
                "fee_npr": rule["fees_npr"], "basis": basis, "source": treq._source("ntb_parks")}
    rule, basis = first("tims")
    if rule:
        return {"class": "park_fee", "label": "TIMS trekking area", "area": rule["region"],
                "basis": basis, "source": treq._source("ntb_tims")}
    rule, basis = first("heritage")
    if rule:
        return {"class": "heritage_fee", "label": COST_LABELS["heritage_fee"], "area": rule["name"],
                "fee_npr": rule["fees_npr"], "basis": basis, "source": treq._source("ntb_heritage")}
    return {"class": "none_on_record", "label": COST_LABELS["none_on_record"], "area": "",
            "basis": ("No DOI permit, NTB park or heritage fee rule matches this place. "
                      "Local entry charges may still apply."),
            "source": None}


def reach_for(distance_km) -> dict | None:
    if distance_km is None:
        return None
    for key, limit, label in REACH_BANDS:
        if limit is None or distance_km <= limit:
            return {"band": key, "label": label,
                    "basis": f"{distance_km:,.0f} km in a straight line from your starting point; "
                             "the road distance is longer."}
    return None


def acclimatization_days(start_elevation_m, target_elevation_m) -> dict | None:
    """Minimum ascent days above the AMS threshold, using NTB's published rules."""
    if target_elevation_m is None:
        return None
    alt = treq.load_dataset()["altitude"]
    threshold = int(alt["threshold_m"])
    if target_elevation_m < threshold:
        return None
    start = max(int(start_elevation_m or 0), threshold)
    gain = max(target_elevation_m - start, 0)
    per_day = int(alt["max_daily_sleeping_gain_m"])
    rest_every = int(alt["rest_day_every_gain_m"])
    ascent_days = math.ceil(gain / per_day) if gain else 0
    rest_days = int(gain // rest_every) if gain else 0
    return {
        "ascent_days": ascent_days, "rest_days": rest_days, "minimum_days": ascent_days + rest_days,
        "basis": (f"Sleeping altitude should rise no more than {per_day} m a day above {threshold:,} m, "
                  f"with a rest day for every {rest_every} m gained (NTB). This is the minimum on foot "
                  "from the threshold, not a full itinerary."),
        "source": treq._source("ntb_mountain_safety"),
    }


# --------------------------------------------------------------------------
# Origins (trips need not start in Kathmandu)
# --------------------------------------------------------------------------
def list_origins() -> list[dict]:
    from .models import District
    rows = District.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).order_by("name")
    return [{"slug": d.slug, "label": f"{d.name} district", "name": d.name,
             "latitude": float(d.latitude), "longitude": float(d.longitude),
             "elevation_m": d.elevation_m} for d in rows]


def resolve_origin(params) -> dict | None:
    """Origin from explicit coordinates or a district slug. Invalid input is ignored."""
    lat, lng = params.get("origin_lat") or params.get("lat"), params.get("origin_lng") or params.get("lng")
    if lat not in (None, "") and lng not in (None, ""):
        try:
            lat_f, lng_f = float(lat), float(lng)
        except (TypeError, ValueError):
            lat_f = lng_f = None
        if lat_f is not None and -90 <= lat_f <= 90 and -180 <= lng_f <= 180:
            return {"kind": "coordinates", "slug": "", "label": "Your location",
                    "latitude": lat_f, "longitude": lng_f, "elevation_m": None}
    slug = (params.get("origin") or "").strip().lower()
    if slug:
        from .models import District
        d = District.objects.filter(slug=slug).first() or District.objects.filter(name__iexact=slug).first()
        if d and d.latitude is not None and d.longitude is not None:
            return {"kind": "district", "slug": d.slug, "label": f"{d.name} district",
                    "latitude": float(d.latitude), "longitude": float(d.longitude),
                    "elevation_m": d.elevation_m}
    return None


# --------------------------------------------------------------------------
# Cached fact table
# --------------------------------------------------------------------------
_TABLE_LOCK = threading.Lock()
_BUILD_LOCK = threading.Lock()
_TABLE = {"signature": None, "rows": [], "checked_at": 0.0}
SIGNATURE_RECHECK_SECONDS = 30


def _signature():
    from .models import Destination, Hospital, OSMEssentialService
    d = Destination.objects.aggregate(n=Count("id"), m=Max("updated_at"))
    h = Hospital.objects.aggregate(n=Count("id"), m=Max("updated_at"))
    o = OSMEssentialService.objects.filter(category="hospital").aggregate(n=Count("id"), m=Max("updated_at"))
    return (d["n"], d["m"], h["n"], h["m"], o["n"], o["m"])


def _hospital_points():
    from .models import Hospital, OSMEssentialService
    pts = []
    for name, lat, lng, verified in Hospital.objects.filter(is_archived=False).values_list(
            "name", "latitude", "longitude", "is_verified"):
        if lat is not None and lng is not None:
            pts.append((float(lat), float(lng), name, bool(verified)))
    for name, lat, lng, verified in OSMEssentialService.objects.filter(
            category="hospital", is_archived=False).values_list("name", "latitude", "longitude", "is_verified"):
        if lat is not None and lng is not None:
            pts.append((float(lat), float(lng), name, bool(verified)))
    return pts


class _Grid:
    """Tiny spatial hash so nearest-hospital lookups stay fast for 6k places."""

    CELL = 0.25  # degrees, about 27 km

    def __init__(self, points):
        self.cells = {}
        for p in points:
            self.cells.setdefault((int(p[0] // self.CELL), int(p[1] // self.CELL)), []).append(p)
        self._memo = {}

    def nearest(self, lat, lng, max_rings=3):
        # Destinations cluster, so many share a grid cell. The candidate list
        # for a cell is built once and reused; the exact distance is still
        # computed per destination, so the answer is unchanged -- only the
        # repeated ring walking is skipped.
        ci, cj = int(lat // self.CELL), int(lng // self.CELL)
        bucket = self._memo.get((ci, cj))
        if bucket is None:
            seen = []
            for i in range(ci - max_rings, ci + max_rings + 1):
                for j in range(cj - max_rings, cj + max_rings + 1):
                    seen.extend(self.cells.get((i, j), ()))
            bucket = self._memo[(ci, cj)] = seen
        if not bucket:
            return None
        best = None
        for p in bucket:
            d = haversine_km(lat, lng, p[0], p[1])
            if best is None or d < best[0]:
                best = (d, p)
        return best


class _AttrRow:
    """Read-only attribute view over a ``.values()`` dict.

    ``best_elevation`` and ``cost_class_for`` only read plain columns through
    ``getattr``, so the fact table can be built from plain dicts instead of
    ~6,700 instantiated model objects. This runs on every request that follows
    a catalogue change.
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict):
        object.__setattr__(self, "_data", data)

    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, "_data")[item]
        except KeyError:
            return None


def _build_rows(ids=None):
    from .models import Destination
    grid = _Grid(_hospital_points())
    # Plain values(), not model instances.
    qs = Destination.publicly_visible()
    if ids is not None:
        qs = qs.filter(id__in=ids)
    qs = qs.values(
        "id", "name", "slug", "aliases", "municipality", "city", "district", "province",
        "latitude", "longitude", "elevation_m", "elevation_source", "elevation_retrieved_at",
        "altitude", "category__slug", "category__name", "short_description", "is_featured",
        "views_count", "cover_image",
    )
    rows = []
    for data in qs.iterator(chunk_size=1000):
        cat_slug = data["category__slug"] or ""
        activity = activity_for(cat_slug)
        dest = _AttrRow(data)
        elev = best_elevation(dest)
        lat = float(data["latitude"]) if data["latitude"] is not None else None
        lng = float(data["longitude"]) if data["longitude"] is not None else None
        nearest = grid.nearest(lat, lng) if lat is not None and lng is not None else None
        rows.append({
            "id": data["id"], "name": data["name"] or "", "slug": data["slug"] or "",
            "aliases": data["aliases"] or "", "district": data["district"] or "", "province": data["province"] or "",
            "category_slug": cat_slug, "category_name": data["category__name"] or "",
            "activity": activity, "latitude": lat, "longitude": lng,
            "elevation_m": elev["elevation_m"], "elevation_source": elev["source"], "elevation_kind": elev["kind"],
            "difficulty": difficulty_for(elev["elevation_m"], activity),
            "cost": cost_class_for(dest),
            "nearest_hospital": ({"km": round(nearest[0], 1), "name": nearest[1][2], "verified": nearest[1][3]}
                                 if nearest else None),
            "is_featured": bool(data["is_featured"]), "views_count": data["views_count"] or 0,
            "has_cover": bool(data["cover_image"]),
        })
    return rows


def fact_rows(force: bool = False, ids=None) -> list[dict]:
    """All public destinations as fact rows, rebuilt when the data changes.

    The ~6,700-row build can take many seconds. It runs OUTSIDE ``_TABLE_LOCK``
    (guarded by ``_BUILD_LOCK``) so that, while one thread rebuilds, every other
    request keeps getting the previous table instead of queueing behind the lock
    (that queueing showed up as 30-780 s "slow requests" with 0 queries). Only the
    very first build, when there is no table yet, makes callers wait.
    """
    if ids is not None:
        selected_ids = tuple(dict.fromkeys(ids))
        return _build_rows(selected_ids) if selected_ids else []

    now = time.monotonic()
    with _TABLE_LOCK:
        have_rows = _TABLE["signature"] is not None
        if not force and have_rows and now - _TABLE["checked_at"] < SIGNATURE_RECHECK_SECONDS:
            return _TABLE["rows"]
    if not _BUILD_LOCK.acquire(blocking=not have_rows):
        return _TABLE["rows"]  # someone else is rebuilding; serve the stale table
    try:
        sig = _signature()
        with _TABLE_LOCK:
            _TABLE["checked_at"] = time.monotonic()
            unchanged = not force and sig == _TABLE["signature"]
            current = _TABLE["rows"]
        if unchanged:
            return current
        rows = _build_rows()
        with _TABLE_LOCK:
            _TABLE["rows"] = rows
            _TABLE["signature"] = sig
        return rows
    finally:
        _BUILD_LOCK.release()


def invalidate():
    with _TABLE_LOCK:
        _TABLE["signature"] = None
        _TABLE["checked_at"] = 0.0


def row_distance(row, origin) -> float | None:
    if not origin or row["latitude"] is None or row["longitude"] is None:
        return None
    return round(haversine_km(origin["latitude"], origin["longitude"], row["latitude"], row["longitude"]), 1)


def facts_for_row(row, *, month=None, origin=None) -> dict:
    """The explainable fact bundle returned to the UI for one destination."""
    distance = row_distance(row, origin)
    out = {
        "activity": {"key": row["activity"], "label": ACTIVITIES.get(row["activity"], {}).get("label", "Other"),
                     "basis": f"Category: {row['category_name'] or 'not set'}"},
        "elevation": {"meters": row["elevation_m"], "source": row["elevation_source"] or None,
                      "kind": row["elevation_kind"]},
        "difficulty": row["difficulty"],
        "cost": row["cost"],
        "nearest_hospital": row["nearest_hospital"],
        "temperatures": estimated_temperatures(row["elevation_m"]),
        "distance_from_origin_km": distance,
        "distance_kind": "straight_line" if distance is not None else None,
        "reach": reach_for(distance),
        "acclimatization": acclimatization_days(origin.get("elevation_m") if origin else None, row["elevation_m"]),
    }
    if month:
        out["season"] = season_fit(month=month, activity=row["activity"], elevation_m=row["elevation_m"],
                                   district=row["district"], province=row["province"])
    return out