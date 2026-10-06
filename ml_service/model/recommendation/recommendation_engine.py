import os
import math
import random
import csv
import threading
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "model",
    "recommendation"
)
os.makedirs(MODEL_DIR, exist_ok=True)

VEC_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")
DEST_VEC_PATH = os.path.join(MODEL_DIR, "destination_vectors.joblib")
DEST_CSV_PATH = os.path.join(MODEL_DIR, "destinations.csv")
_dataset_lock = threading.Lock()
_dataset_mtime = None
_csv_records = None
vectorizer = None
destinations = None

def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 9999.0
    try:
        r = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
        return 2.0 * r * math.asin(math.sqrt(a))
    except (TypeError, ValueError):
        return 9999.0

def load_or_build_model():
    import pandas as pd

    if not os.path.exists(VEC_PATH) or not os.path.exists(DEST_CSV_PATH):
        source_csv = os.path.join(BASE_DIR, "processed_data", "destinations_clean.csv")
        if not os.path.exists(source_csv):
            source_csv = os.path.join(BASE_DIR, "data", "destinations", "nepal_destinations.csv")

        if os.path.exists(source_csv):
            df = pd.read_csv(source_csv)
            for col in ["Name", "Type", "Tourism_Category", "City", "Area", "District", "Province", "search_text"]:
                if col not in df.columns:
                    df[col] = ""
                df[col] = df[col].fillna("").astype(str)

            df["features"] = (
                df["Name"] + " " + df["Type"] + " " + df["Tourism_Category"] + " " +
                df["City"] + " " + df["Area"] + " " + df["District"] + " " + df["Province"] + " " + df["search_text"]
            ).str.lower().str.replace(r"\s+", " ", regex=True).str.strip()

            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=10000)
            vec.fit(df["features"])

            joblib.dump(vec, VEC_PATH)
            df.to_csv(DEST_CSV_PATH, index=False)
            return vec, None, df
        else:
            vec = TfidfVectorizer()
            df = pd.DataFrame([{"Name": "Everest Base Camp", "Type": "Trek", "Tourism_Category": "Nature", "City": "Solukhumbu", "Latitude": 28.0042, "Longitude": 86.8570}])
            vec.fit(["Everest Base Camp Trek Nature Solukhumbu"])
            joblib.dump(vec, VEC_PATH)
            df.to_csv(DEST_CSV_PATH, index=False)
            return vec, None, df
    else:
        vec = joblib.load(VEC_PATH)
        df = pd.read_csv(DEST_CSV_PATH)
        return vec, None, df


# ---------------------------------------------------------------------------
# Category gating
# ---------------------------------------------------------------------------
# The bundled OpenStreetMap extract labels rows with accommodation-style tags
# (hotel 4218, guest_house 2964, hostel 655, information 583) rather than with
# visitor interests. A requested category could therefore only ever be a soft
# +0.15 score nudge, so every category ranked the same places and the caller
# saw "the same 20 destinations" whatever it asked for.
#
# These keyword sets are matched against each row's real text (name, area,
# district, search_text), which is what actually distinguishes a peak from a
# temple from a national park in this dataset.
CATEGORY_KEYWORDS = {
    "mountain": ["mountain", "himal", "peak", "summit", "alpine", "glacier", "highland"],
    "mountains": ["mountain", "himal", "peak", "summit", "alpine", "glacier", "highland"],
    "trek": ["trek", "trekking", "hike", "hiking", "trail", "base camp"],
    "trekking": ["trek", "trekking", "hike", "hiking", "trail", "base camp"],
    "adventure": ["adventure", "raft", "bungee", "paraglid", "canyoning", "zipline", "climb"],
    "heritage": ["heritage", "durbar", "palace", "fort", "gadhi", "monument", "archaeolog", "historic"],
    "culture": ["culture", "cultural", "newar", "gurung", "tharu", "limbu", "maithal", "tamang", "folk"],
    "temple": ["temple", "mandir", "stupa", "shrine", "deul", "chaitya", "dham"],
    "temples": ["temple", "mandir", "stupa", "shrine", "deul", "chaitya", "dham"],
    "buddhist": ["buddhist", "monastery", "gompa", "stupa", "lama", "tibetan"],
    "pilgrimage": ["pilgrim", "dham", "muktinath", "pashupati", "pathibhara", "boudha", "lumbini"],
    "spiritual": ["spiritual", "meditation", "yoga", "retreat", "ashram", "sanctuary"],
    "wellness": ["wellness", "meditation", "yoga", "retreat", "spa", "hot spring", "tatopani"],
    "food": ["food", "cuisine", "restaurant", "thali", "momo", "kulha", "cafe", "bhojanalaya"],
    "culinary": ["food", "cuisine", "restaurant", "thali", "momo", "kulha", "cafe"],
    "wildlife": ["wildlife", "national park", "reserve", "safari", "elephant", "rhino", "tiger", "jungle"],
    "bird": ["bird", "birding", "florican", "crane", "wetland", "ornithol"],
    "lake": ["lake", "phewa", "begnas", "rara", "gokyo", "gosaikunda", "tali", "pokhari"],
    "lakes": ["lake", "phewa", "begnas", "rara", "gokyo", "gosaikunda", "tali", "pokhari"],
    "river": ["river", "gandaki", "koshi", "karnali", "narayani", "bagmati", "rafting"],
    "waterfall": ["waterfall", "falls", "jharana", "chhahara", "cascade"],
    "cave": ["cave", "gufa", "cavern", "karst"],
    "forest": ["forest", "jungle", "botanical", "rhododendron", "sal forest", "community forest"],
    "museum": ["museum", "gallery", "exhibition", "collection", "art gallery"],
    "shopping": ["bazaar", "market", "shopping", "handicraft", "souvenir", "craft", "thamel", "asan"],
    "viewpoint": ["viewpoint", "panorama", "lookout", "sunrise", "scenic view"],
    "village": ["village", "homestay", "gaun", "community", "rural"],
    "camping": ["camp", "camping", "tent", "glamping"],
    "monument": ["monument", "statue", "pillar", "inscription"],
    "historic": ["historic", "ancient", "old", "heritage", "archaeolog"],
    "city": ["city", "bazaar", "market", "centre", "center", "thamel", "patan", "bhaktapur"],
    "festival": ["festival", "jatra", "mela", "dashain", "tihar", "holi", "losar"],
    "garden": ["garden", "botanical", "park", "green"],
}

# Words the UI sends that are not themselves keys above. Without these an
# underscore key such as "lakes_rivers" fell through to a literal keyword that
# can never appear in any row, silently disabling the category gate.
CATEGORY_ALIASES = {
    "himalaya": "mountain", "himalayan": "mountain", "peak": "mountain",
    "mountains & peaks": "mountain", "adventure & mountain": "mountain",
    "nature": "forest", "national park": "wildlife", "national-parks": "wildlife",
    "national_parks": "wildlife", "national parks": "wildlife", "jungle": "wildlife",
    "temples & hindu sites": "temple", "hindu": "temple",
    "buddhist sites": "buddhist", "monastery": "buddhist",
    "pilgrimage sites": "pilgrimage", "religious": "pilgrimage",
    "food & culinary": "food", "culinary tourism": "food",
    "lakes & water bodies": "lake", "lakes-rivers": "river",
    "heritage & culture": "heritage", "unesco": "heritage",
    "viewpoints & hillstations": "viewpoint", "viewpoints & lookouts": "viewpoint",
    "hill-stations": "viewpoint", "hill stations": "viewpoint",
    "wildlife & safari": "wildlife", "wildlife and nature": "wildlife",
    "camping & glamping": "camping", "museums & galleries": "museum",
    "tea & coffee gardens": "garden", "waterfalls": "waterfall",
    "caves": "cave", "villages & rural tourism": "village",
    "cultural & ethnic tourism": "culture", "shopping & handicrafts": "shopping",
    "trekking & nature": "trek", "adventure sports": "adventure",
    "rivers & river valleys": "river", "festivals & events": "festival",
    "eco & community": "forest", "lakes_rivers": "lake", "lakes rivers": "lake",
    "birdwatching": "bird", "bird watching": "bird",
    "artisan_crafts": "shopping", "artisan crafts": "shopping",
    "village_life": "village", "village life": "village",
    "history": "historic", "cultural": "culture", "photography": "viewpoint",
    "cycling": "adventure", "family": "city", "relaxed": "lake",
    "solitude": "lake", "educational": "museum", "romantic": "viewpoint",
    "ecotourism": "forest", "eco tourism": "forest", "tea_coffee": "garden",
    "hill_stations": "viewpoint", "wildlife_safari": "wildlife",
    "adventure_sports": "adventure", "camping_glamping": "camping",
    "food_culinary": "food", "spirits": "spiritual",
}

# ---------------------------------------------------------------------------
# Not-a-destination filter
# ---------------------------------------------------------------------------
# `_is_recommendable` is called by recommend() but was never defined in this
# module. The NameError was swallowed by the broad `except Exception: return []`
# at the bottom of recommend(), so this endpoint returned an EMPTY list on
# every call instead of reporting an error. These are the categories and name
# patterns that are real map records but not somewhere a traveller visits.
_NON_VISITABLE_CATEGORIES = {
    "information", "office", "townhall", "government", "embassy", "consulate",
    "bank", "atm", "post_office", "school", "university", "college",
    "fire_station", "police", "town_hall", "shop", "supermarket",
    "convenience", "fuel", "charging_station", "toilets", "waste_basket",
    "bench", "tree", "way", "bus_stop", "car", "motorcycle", "bicycle",
    "aeroway", "railway", "hospital", "clinic", "doctors", "pharmacy",
    "courthouse", "prison", "yes", "no", "unknown", "",
}

_NON_VISITABLE_NAME_HINTS = (
    "tourism board", "tourism office", "association", "committee", "council",
    "department", "ministry", "municipality", "district office", "embassy of",
    "consulate", "university", "college of", "school of", "bank of",
    "electricity", "water supply", "telecom", "post office", "bus park",
    "car park", "parking", "nepal rastra", "youth club", "ward office",
    "village office", "gram panchayat",
)


def _is_recommendable(row):
    """True when the record is somewhere a traveller would actually go.

    Filters organisational records (tourism boards, municipalities, utilities,
    banks) and administrative map tags. These matched interest text well and
    were being returned as "suggestions", which is a data bug rather than a
    recommendation.
    """
    category = str(row.get("Tourism_Category", "") or "").strip().lower()
    if category in _NON_VISITABLE_CATEGORIES:
        return False
    name = str(row.get("Name", "") or "").strip()
    if not name:
        return False
    lowered = name.lower()
    for hint in _NON_VISITABLE_NAME_HINTS:
        if hint in lowered:
            return False
    return True


def _normalize_category(value):
    """Map a requested category onto a known keyword profile."""
    if not value:
        return None, []
    key = str(value).strip().lower()
    if not key:
        return None, []
    if key in CATEGORY_KEYWORDS:
        return key, list(CATEGORY_KEYWORDS[key])
    aliased = CATEGORY_ALIASES.get(key)
    if not aliased:
        # Fall back to a single-token match ("wildlife safari" -> "wildlife").
        parts = [p.strip() for p in key.replace("-", " ").split() if p.strip()]
        for part in parts:
            if part in CATEGORY_KEYWORDS:
                return part, list(CATEGORY_KEYWORDS[part])
            if part in CATEGORY_ALIASES:
                resolved = CATEGORY_ALIASES[part]
                return resolved, list(CATEGORY_KEYWORDS.get(resolved, []))
        return key, [key]
    return aliased, list(CATEGORY_KEYWORDS.get(aliased, []))


def _row_text(row):
    """All searchable text for a row, lowercased."""
    parts = [
        row.get("Name"), row.get("Type"), row.get("Tourism_Category"),
        row.get("City"), row.get("Area"), row.get("District"),
        row.get("Province"), row.get("search_text"),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def _category_match(text, keywords):
    """How strongly a row's text matches the requested category (0..1)."""
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw and kw in text)
    if not hits:
        return 0.0
    return min(1.0, 0.55 + 0.15 * (hits - 1))


def _candidate_frame(candidate_rows):
    """Normalise Django's live-DB candidate rows into the shared row shape.

    Django selects up to 100 real, approved destinations (already filtered by
    the caller's interest/province/category) and sends them with every request.
    Those rows used to be ignored entirely, so recommendations came from the
    static OpenStreetMap extract instead of the live catalogue.
    """
    records = []
    for row in candidate_rows or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        records.append({
            "ID": row.get("id"),
            "Name": name,
            "Type": str(row.get("type") or ""),
            "Tourism_Category": str(row.get("category") or row.get("type") or ""),
            "City": str(row.get("city") or ""),
            "Area": "",
            "District": str(row.get("district") or ""),
            "Province": str(row.get("province") or ""),
            "search_text": " ".join(
                str(row.get(field) or "")
                for field in ("name", "type", "city", "district", "province")
            ),
            "Latitude": row.get("latitude") or 0.0,
            "Longitude": row.get("longitude") or 0.0,
            "average_rating": row.get("average_rating"),
        })
    return records


def _records_from_frame(frame):
    """Flatten the destination DataFrame once, instead of ``.iloc[i]`` per row.

    Row-wise ``.iloc`` on a 12k-row frame dominated request time; a list of
    plain dicts is what the scoring loop actually wants.
    """
    columns = [
        "ID", "Name", "Type", "Tourism_Category", "City", "Area",
        "District", "Province", "Latitude", "Longitude", "search_text",
    ]
    return frame.reindex(columns=columns).to_dict("records")


def _refresh_dataset(*, load_records=False):
    """Load only the vectorizer for live rows; read the bundled CSV on fallback."""
    global vectorizer, destinations, _csv_records, _dataset_mtime
    with _dataset_lock:
        if vectorizer is None:
            if os.path.exists(VEC_PATH):
                vectorizer = joblib.load(VEC_PATH)
            else:
                vectorizer, _unused_vectors, destinations = load_or_build_model()

        if not load_records or not os.path.exists(DEST_CSV_PATH):
            return
        mtime = os.path.getmtime(DEST_CSV_PATH)
        if _dataset_mtime == mtime and _csv_records is not None:
            return

        columns = (
            "ID", "Name", "Type", "Tourism_Category", "City", "Area",
            "District", "Province", "Latitude", "Longitude", "search_text",
        )
        records = []
        with open(DEST_CSV_PATH, newline="", encoding="utf-8-sig") as source:
            for row in csv.DictReader(source):
                record = {column: row.get(column) or "" for column in columns}
                for column in ("Latitude", "Longitude"):
                    try:
                        record[column] = float(record[column])
                    except (TypeError, ValueError):
                        record[column] = 0.0
                records.append(record)
        _csv_records = records
        _dataset_mtime = mtime


def recommend(user_input, top_n=5, user_lat=None, user_lon=None, budget_level=None,
              category_filter=None, candidate_rows=None):
    """Rank destinations for a traveller.

    ``candidate_rows`` are the live, approved catalogue rows Django selected
    (already filtered by the caller's interest/province/category). When they
    are supplied they are the ranking pool, so the answer reflects the real
    catalogue instead of the static OpenStreetMap extract.

    A requested ``category_filter`` is a gate, not a nudge: rows are matched
    against real category keywords and those rank first. This is what stops
    every category returning the same places.
    """
    if not user_input and not category_filter and user_lat is None:
        user_input = "nepal tourism heritage nature adventure mountain"

    try:
        live_rows = _candidate_frame(candidate_rows)
        if live_rows:
            _refresh_dataset()
            records = live_rows
            source = "live_catalog"
        else:
            _refresh_dataset(load_records=True)
            records = _csv_records or []
            source = "bundled_osm_extract"
        if not records:
            return []

        category_name, category_keywords = _normalize_category(category_filter)
        texts = [_row_text(r) for r in records]

        query_text = str(user_input or "")
        if category_filter:
            query_text += f" {category_filter}"
        similarity = cosine_similarity(
            vectorizer.transform([query_text]),
            vectorizer.transform(texts),
        )[0]

        user_loc_known = (
            user_lat is not None
            and user_lon is not None
            and not (float(user_lat) == 0.0 and float(user_lon) == 0.0)
        )

        candidates = []
        for index, row in enumerate(records):
            if not _is_recommendable(row):
                continue

            cat_match = _category_match(texts[index], category_keywords)

            sim_score = float(similarity[index])
            if not math.isfinite(sim_score):
                sim_score = 0.0

            try:
                d_lat = float(row.get("Latitude") or 0.0)
                d_lon = float(row.get("Longitude") or 0.0)
            except (TypeError, ValueError):
                d_lat = d_lon = 0.0

            dist_km = None
            prox_score = 0.0
            if user_loc_known and d_lat != 0.0 and d_lon != 0.0:
                dist_km = round(haversine_km(user_lat, user_lon, d_lat, d_lon), 1)
                if dist_km < 10.0:
                    prox_score = 0.20
                elif dist_km < 50.0:
                    prox_score = 0.14
                elif dist_km < 150.0:
                    prox_score = 0.08

            rating_score = 0.0
            try:
                rating = row.get("average_rating")
                if rating is not None and float(rating) > 0:
                    rating_score = min(float(rating) / 5.0, 1.0) * 0.05
            except (TypeError, ValueError):
                rating_score = 0.0

            final_score = (
                (sim_score * 0.45)
                + (cat_match * 0.35 if category_keywords else 0.0)
                + prox_score
                + rating_score
            )

            reasons = []
            if cat_match > 0 and category_name:
                reasons.append(f"âœ“ Matches {category_name.replace('_', ' ')}")
            elif sim_score > 0.1:
                first_term = str(user_input or "").split()
                if first_term:
                    reasons.append(f"âœ“ Matches interest in {first_term[0].title()}")
            cat_label = row.get("Tourism_Category") or row.get("Type")
            if cat_label:
                reasons.append(f"âœ“ Category: {cat_label}")
            if dist_km is not None and dist_km < 999:
                place = row.get("City") or row.get("District") or "Nepal"
                reasons.append(f"âœ“ {dist_km} km from your current location ({place})")

            candidates.append({
                "destination_id": int(row.get("ID") or 0) or None,
                "name": str(row.get("Name") or ""),
                "type": str(row.get("Type") or ""),
                "category": str(cat_label or "Experience"),
                "city": str(row.get("City") or ""),
                "district": str(row.get("District") or ""),
                "province": str(row.get("Province") or ""),
                "latitude": d_lat,
                "longitude": d_lon,
                "distance_km": dist_km,
                "similarity_score": round(sim_score, 4),
                "category_match": round(cat_match, 4),
                "score": round(max(0.0, final_score), 4),
                "source": source,
                "match_reasons": reasons,
            })

        if not candidates:
            return []

        candidates.sort(key=lambda item: item["score"], reverse=True)

        # Diversity: spread across districts and cities instead of taking one
        # place per city, which for a narrow category returned a single town.
        picked, district_seen, city_seen = [], {}, {}
        remaining = list(candidates)
        while remaining and len(picked) < top_n:
            def adjusted(item):
                district = (item["district"] or "unknown").lower()
                city = (item["city"] or district).lower()
                return (
                    item["score"]
                    - district_seen.get(district, 0) * 0.08
                    - city_seen.get(city, 0) * 0.04
                )

            best = max(remaining, key=adjusted)
            remaining.remove(best)
            district = (best["district"] or "unknown").lower()
            city = (best["city"] or district).lower()
            district_seen[district] = district_seen.get(district, 0) + 1
            city_seen[city] = city_seen.get(city, 0) + 1
            picked.append(best)

        # match_percentage is derived from the actual blended signals, so a
        # weak match is reported as weak. It used to be clamped into a
        # flattering 65-98% band for every result.
        for item in picked:
            blended = min(
                1.0,
                0.45 * min(1.0, item["similarity_score"] / 0.35)
                + 0.35 * item["category_match"]
                + 0.15 * (1.0 if item["distance_km"] is not None else 0.0)
                + 0.05,
            )
            item["match_percentage"] = int(round(blended * 100))
            item["score"] = round(blended, 4)

        return picked[:top_n]
    except Exception:  # noqa: BLE001
        # Surface the failure instead of pretending there are no results: an
        # empty list here is indistinguishable from "nothing matched".
        import logging

        logging.getLogger("ml-service").exception(
            "recommendation scoring failed for category_filter=%r", category_filter
        )
        raise
