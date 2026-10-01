"""Fill missing destination data from real, derivable sources.

The seed catalogue was produced by importing OpenStreetMap rows, so whole
columns are empty for most destinations: distances, nearest city/airport,
English/Nepali city names, addresses, descriptions and entry fees.  The UI then
renders those empty columns as "Information unavailable" or a misleading
``0.0``.  Every value this module writes is *derived from data we already
have* (coordinates, district/province, category, cited elevations, service
CSVs) - nothing is guessed:

* distances           -> haversine from the destination's own coordinates
* nearest major city  -> nearest entry in a fixed table of Nepali cities
* nearest airport     -> nearest entry in a fixed table of Nepali airports
* city_english/city_nepali -> normalization of the mixed-script ``city`` column
* address             -> composed from city/district/province
* elevation/altitude  -> joined from ``dataset/destination_elevations.json``
                         (Copernicus DEM via Open-Meteo - a cited source)
* nearest hospital/police/hotel -> nearest row of the cleaned service CSVs
* entry fee 0         -> NULL: the project's own snapshot policy treats an
                         unrecorded fee as NULL, never as "free" (see
                         ``verified_snapshot.DESTINATION_NULL_FIELDS``)

The helpers are pure Python (no Django import) so the same rules can be
applied to a Django fixture (``data.json``), the Render catalogue
(``dataset/data.json``) or live rows through the ``enrich_destinations``
management command.  Every rule only ever fills an *empty* value - curated
data is never overwritten - so the command is idempotent.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

KATHMANDU = (27.7172, 85.3240)

# (english name, nepali name, latitude, longitude)
MAJOR_CITIES: list[tuple[str, str, float, float]] = [
    ("Kathmandu", "काठमाडौँ", 27.7172, 85.3240),
    ("Lalitpur", "ललितपुर", 27.6710, 85.3250),
    ("Bhaktapur", "भक्तपुर", 27.6710, 85.4298),
    ("Pokhara", "पोखरा", 28.2096, 83.9856),
    ("Bharatpur", "भरतपुर", 27.6766, 84.4350),
    ("Biratnagar", "विराटनगर", 26.4525, 87.2661),
    ("Birgunj", "विरगंज", 27.0360, 84.8769),
    ("Butwal", "बुटवल", 27.7006, 83.4484),
    ("Dharan", "धरान", 26.8065, 87.2846),
    ("Hetauda", "हेटौंडा", 27.4295, 85.0323),
    ("Janakpur", "जनकपुर", 26.7288, 85.9250),
    ("Nepalgunj", "नेपालगञ्ज", 28.0600, 81.6167),
    ("Dhangadhi", "धनगढी", 28.6990, 80.6000),
    ("Tansen", "ताँसेन", 27.8667, 83.5500),
    ("Damak", "दमक", 26.6646, 87.3510),
    ("Dhankuta", "धनकुटा", 26.9833, 87.3333),
    ("Ilam", "इलाम", 26.9124, 87.9313),
    ("Gorkha", "गोरखा", 28.0000, 84.6333),
    ("Siddharthanagar", "सिद्धार्थनगर", 27.5000, 83.4500),
    ("Itahari", "इथहरी", 26.6646, 87.2718),
    ("Baglung", "बागलुङ", 28.2667, 83.5833),
    ("Rajbiraj", "राजबिरज", 26.5333, 86.7500),
    ("Tulsipur", "तुल्सीपुर", 28.1333, 82.3000),
    ("Malangwa", "मलंगवा", 26.9333, 85.5667),
    ("Palpa", "पाल्पा", 27.8667, 83.5500),
]

# (display name, latitude, longitude)
AIRPORTS: list[tuple[str, float, float]] = [
    ("Tribhuvan International Airport (KTM)", 27.6966, 85.3591),
    ("Pokhara Airport (PKR)", 28.2008, 83.9821),
    ("Gautam Buddha Airport (BWA)", 27.5033, 83.4167),
    ("Biratnagar Airport (BIR)", 26.4414, 87.2634),
    ("Janakpur Airport (JKR)", 26.7088, 85.9241),
    ("Nepalgunj Airport (KEP)", 28.0510, 81.6313),
    ("Dhangadhi Airport (DHI)", 28.7533, 80.5819),
    ("Bharatpur Airport (BHR)", 27.6823, 84.4276),
    ("Surkhet Airport (SKH)", 28.5860, 81.6360),
    ("Bhadrapur Airport (BDP)", 26.6070, 87.9170),
    ("Tenzing-Hillary Lukla Airport (LUA)", 27.6869, 86.7314),
    ("Phaplu Airport (PPL)", 27.5177, 86.5843),
]

# Keys enrichment may add to a record.  ``convert_dataset_to_fixture`` passes
# exactly this set through when present, so values written into
# ``dataset/data.json`` reach PostgreSQL on Render.
DERIVABLE_KEYS = frozenset({
    "distance_from_kathmandu_km",
    "distance_from_nearest_city_km",
    "nearest_major_city",
    "distance_from_nearest_airport_km",
    "nearest_airport_name",
    "nearest_hospital_info",
    "nearest_police_info",
    "nearest_hotel_info",
    "city_english",
    "city_nepali",
    "country",
    "address",
    "best_time_to_visit",
    "description",
    "short_description",
    "altitude",
    "elevation_m",
    "elevation_source",
    "elevation_retrieved_at",
    "entry_fee",
    "category",
})


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _is_empty(value) -> bool:
    return value is None or value == "" or value == []


def nearest_city(lat: float, lon: float) -> tuple[tuple[str, str, float, float], float]:
    best = min(
        MAJOR_CITIES,
        key=lambda c: haversine_km(lat, lon, c[2], c[3]),
    )
    return best, haversine_km(lat, lon, best[2], best[3])


def nearest_airport(lat: float, lon: float) -> tuple[tuple[str, float, float], float]:
    best = min(
        AIRPORTS,
        key=lambda a: haversine_km(lat, lon, a[1], a[2]),
    )
    return best, haversine_km(lat, lon, best[1], best[2])


_EN_TO_NP = {en.lower(): np for en, np, _, _ in MAJOR_CITIES}
_NP_TO_EN = {np: en for en, np, _, _ in MAJOR_CITIES}
_EN_DISPLAY = {en.lower(): en for en, _, _, _ in MAJOR_CITIES}
# Longest first so "काठमाडौँ" wins over any shorter prefix.
_NP_PREFIXES = sorted(_NP_TO_EN, key=len, reverse=True)
_EN_PREFIXES = sorted(_EN_TO_NP, key=len, reverse=True)


def city_to_english(value: str) -> str | None:
    """Normalize a possibly-Nepali ``city`` value to English, if known."""
    text = (value or "").strip()
    if not text:
        return None
    if text.isascii():
        # Already English: use the canonical spelling when we know the city.
        lowered = text.lower()
        for prefix in _EN_PREFIXES:
            if lowered == prefix or lowered.startswith(prefix + " "):
                return _EN_DISPLAY[prefix]
        return text
    for prefix in _NP_PREFIXES:
        if text == prefix or text.startswith(prefix + " "):
            return _NP_TO_EN[prefix]
    return None


def city_to_nepali(value: str) -> str | None:
    """Normalize a possibly-English ``city`` value to Nepali, if known."""
    text = (value or "").strip()
    if not text:
        return None
    if not text.isascii():
        # Already Nepali script - keep the original value.
        return text
    lowered = text.lower()
    for prefix in _EN_PREFIXES:
        if lowered == prefix or lowered.startswith(prefix + " "):
            return _EN_TO_NP[prefix]
    return None


def best_time_for(category_name: str = "", dest_type: str = "") -> str:
    text = f"{category_name} {dest_type}".lower()
    if any(k in text for k in (
        "trek", "peak", "mountain", "himal", "summit", "glacier",
        "pass", "annapurna", "everest", "base camp", "adventure",
    )):
        return "March–May (Spring) and October–November (Autumn)"
    if any(k in text for k in ("wildlife", "safari", "jungle", "national park", "conservation")):
        return "October–March (dry and cool winter)"
    if any(k in text for k in ("lake", "river", "waterfall", "hot spring", "garden")):
        return "October–March (dry season); waterfalls peak in monsoon June–September"
    if any(k in text for k in (
        "temple", "heritage", "monastery", "stupa", "history", "unesco",
        "museum", "cultural", "shrine", "palace", "history", "pilgrim",
    )):
        return "Year-round; best October–March (festival season Sept–Nov)"
    return "October–November and February–March (dry season)"


def _place_phrase(fields: dict) -> str:
    """'Pokhara, Kaski District, Gandaki Province' - only real pieces."""
    parts: list[str] = []
    city = fields.get("city_english") or fields.get("city") or ""
    city = str(city).strip()
    if city and city.isascii():
        parts.append(city)
    district = str(fields.get("district") or "").strip()
    province = str(fields.get("province") or "").strip()
    if district and f"{district.lower()} district" not in " ".join(p.lower() for p in parts):
        parts.append(f"{district} District")
    if province:
        parts.append(f"{province} Province" if province.isascii() else province)
    if not parts:
        return "Nepal"
    if len(parts) == 1:
        return f"{parts[0]}, Nepal"
    return f"{parts[0]}, {', '.join(parts[1:])}, Nepal"


def load_elevation_lookup(dataset_dir: Path) -> dict[str, dict]:
    """slug/id -> record from ``destination_elevations.json`` (cited source)."""
    path = Path(dataset_dir) / "destination_elevations.json"
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    lookup: dict[str, dict] = {}
    for rec in payload.get("records", []):
        if rec.get("slug"):
            lookup[f"slug:{rec['slug']}"] = rec
        if rec.get("id"):
            lookup[f"id:{rec['id']}"] = rec
    return lookup


def load_service_points(dataset_dir: Path) -> dict[str, "PointIndex"]:
    """Nearest-service points from the cleaned CSVs, keyed by service type."""
    specs = {
        "hospital": ("hospital_cleaned.csv", "hospital_name"),
        "police": ("police_station_cleaned.csv", "police_station"),
        "hotel": ("nepal_hotels_cleaned.csv", "hotel_name"),
    }
    out: dict[str, PointIndex] = {}
    for key, (filename, name_col) in specs.items():
        path = Path(dataset_dir) / filename
        points: list[tuple[str, float, float]] = []
        if path.is_file():
            try:
                with path.open(newline="", encoding="utf-8-sig") as fh:
                    for row in csv.DictReader(fh):
                        name = (row.get(name_col) or "").strip()
                        lat = _float(row.get("latitude"))
                        lon = _float(row.get("longitude"))
                        if name and lat is not None and lon is not None:
                            points.append((name, lat, lon))
            except OSError:
                points = []
        out[key] = PointIndex(points)
    return out


class PointIndex:
    """Grid-bucketed points for fast exact nearest-neighbour lookup.

    Scanning ~2,900 service rows with haversine for every one of ~6,700
    destinations takes minutes; bucketing by 0.5 degree cells makes each
    lookup examine a handful of candidates instead of the whole table while
    still returning the true nearest point (the ring expansion stops only
    once no unchecked cell can possibly be closer).
    """

    CELL_DEG = 0.5
    # Conservative kilometres per cell at Nepal's latitude (0.5 deg * 111 km
    # * cos(31 deg)); a cell at Chebyshev ring r is at least r * this away.
    CELL_KM = 0.5 * 111.0 * 0.85

    def __init__(self, points: list[tuple[str, float, float]]):
        self.points = points
        self.grid: dict[tuple[int, int], list[tuple[str, float, float]]] = {}
        for point in points:
            key = self._cell(point[1], point[2])
            self.grid.setdefault(key, []).append(point)

    def _cell(self, lat: float, lon: float) -> tuple[int, int]:
        return (int(math.floor(lat / self.CELL_DEG)),
                int(math.floor(lon / self.CELL_DEG)))

    def nearest(self, lat: float, lon: float) -> tuple[str, float, float] | None:
        if not self.points:
            return None
        ci, cj = self._cell(lat, lon)
        best: tuple[str, float, float] | None = None
        best_km = math.inf
        ring = 0
        while ring <= 6:
            for i in range(ci - ring, ci + ring + 1):
                for j in range(cj - ring, cj + ring + 1):
                    if ring and max(abs(i - ci), abs(j - cj)) != ring:
                        continue  # inner rings already checked
                    for point in self.grid.get((i, j), ()):
                        km = haversine_km(lat, lon, point[1], point[2])
                        if km < best_km:
                            best_km, best = km, point
            if best is not None and best_km <= ring * self.CELL_KM:
                return best
            ring += 1
        # Extremely sparse regions: fall back to a full (exact) scan.
        return min(self.points, key=lambda p: haversine_km(lat, lon, p[1], p[2]))


def _nearest_service_info(
    lat: float,
    lon: float,
    index: "PointIndex | None",
) -> str | None:
    if index is None:
        return None
    point = index.nearest(lat, lon)
    if point is None:
        return None
    name, plat, plon = point
    km = round(haversine_km(lat, lon, plat, plon), 1)
    return f"{name} ({km} km)"


def enrich_destination_fields(
    fields: dict,
    *,
    category_name: str = "",
    elevations: dict[str, dict] | None = None,
    services: dict[str, "PointIndex"] | None = None,
) -> dict:
    """Fill empty destination fields from derivable data.

    ``fields`` is a fixture ``fields`` dict or a flat catalogue dict (both use
    the model's column names).  Returns ``{field: new_value}`` for every value
    written; the input dict is not mutated.
    """
    changes: dict = {}

    def set_if_empty(key: str, value) -> None:
        if value is None or value == "":
            return
        if key not in fields and key not in DERIVABLE_KEYS:
            return
        if _is_empty(fields.get(key)):
            changes[key] = value

    lat = _float(fields.get("latitude"))
    lon = _float(fields.get("longitude"))
    # Only derive geo facts for plausible Nepal coordinates: rows imported
    # without coordinates can sit at (0, 0), and distance-to-Kathmandu from
    # Null Island would be nonsense.
    in_nepal = (
        lat is not None
        and lon is not None
        and 26.0 <= lat <= 31.0
        and 80.0 <= lon <= 89.0
    )

    if in_nepal:
        # 1. Straight-line distance to Kathmandu.
        set_if_empty(
            "distance_from_kathmandu_km",
            round(haversine_km(lat, lon, KATHMANDU[0], KATHMANDU[1]), 2),
        )

        # 2. Nearest major city.
        city, city_km = nearest_city(lat, lon)
        set_if_empty("nearest_major_city", city[0])
        set_if_empty("distance_from_nearest_city_km", round(city_km, 2))

        # 3. Nearest airport.
        airport, airport_km = nearest_airport(lat, lon)
        set_if_empty("nearest_airport_name", airport[0])
        set_if_empty("distance_from_nearest_airport_km", round(airport_km, 2))

        # 4. Nearest hospital / police station / hotel from the cleaned CSVs.
        if services:
            set_if_empty(
                "nearest_hospital_info",
                _nearest_service_info(lat, lon, services.get("hospital")),
            )
            set_if_empty(
                "nearest_police_info",
                _nearest_service_info(lat, lon, services.get("police")),
            )
            set_if_empty(
                "nearest_hotel_info",
                _nearest_service_info(lat, lon, services.get("hotel")),
            )

    # 5. City name normalization (the source column mixes scripts).
    city_raw = str(fields.get("city") or "").strip()
    if city_raw:
        if _is_empty(fields.get("city_english")):
            en = city_to_english(city_raw)
            if en:
                changes["city_english"] = en
        if _is_empty(fields.get("city_nepali")):
            np = city_to_nepali(city_raw)
            if np:
                changes["city_nepali"] = np

    # 6. Country / address composed from real columns.
    set_if_empty("country", "Nepal")
    if city_raw or fields.get("district"):
        set_if_empty("address", _place_phrase({**fields, **changes}))

    # 7. Cited elevation joined from destination_elevations.json.
    if elevations:
        rec = elevations.get(f"slug:{fields.get('slug')}") or elevations.get(
            f"id:{fields.get('pk') or fields.get('id')}"
        )
        if rec and rec.get("elevation_m") is not None:
            set_if_empty("elevation_m", int(rec["elevation_m"]))
            if "elevation_m" in changes:
                set_if_empty("elevation_source", rec.get("source") or "")
                set_if_empty("elevation_retrieved_at", rec.get("retrieved_at") or "")

    elevation = changes.get("elevation_m", fields.get("elevation_m"))
    try:
        elevation_int = int(elevation) if elevation is not None else None
    except (TypeError, ValueError):
        elevation_int = None
    if elevation_int is not None:
        set_if_empty("altitude", f"{elevation_int:,} m")

    # 8. Best time to visit from the real category/type.
    set_if_empty("best_time_to_visit", best_time_for(category_name, str(fields.get("type") or "")))

    # 9. Honest descriptions built from real columns (only when missing).
    place = _place_phrase({**fields, **changes})
    name = str(fields.get("name") or "").strip()
    if name:
        if _is_empty(fields.get("short_description")):
            changes["short_description"] = f"{name} — {place}."[:300]
        if _is_empty(fields.get("description")):
            text = f"{name} is a tourist destination located in {place}."
            if elevation_int is not None:
                text += f" It sits at approximately {elevation_int:,} metres above sea level."
            changes["description"] = text

    # 10. Unrecorded entry fee is NULL, never a misleading 0 / "free"
    #     (matches verified_snapshot.DESTINATION_NULL_FIELDS policy).
    if "entry_fee" in fields:
        fee = _float(fields.get("entry_fee"))
        if fee is not None and fee == 0:
            changes["entry_fee"] = None

    return changes
