"""
services/itinerary_service.py

Rich, dataset-driven itinerary builder.

Takes the traveler's inputs (number of days, budget in NPR, travel style,
travel type, interests) and produces a day-by-day plan:

  - Destinations are chosen from the OSM/dataset CSV
    (model/recommendation/destinations.csv — 12k+ places across Nepal)
    filtered by the interests -> Tourism_Category mapping.
  - Days are grouped by city so travel between stops stays short.
  - Travel legs between stops use the real road graph
    (model/route/nepal_graph.graphml) via route_engine.best_route so the
    distances/durations match the navigation feature.
  - Budget values are shown only when a complete recorded CSV baseline exists;
    no city fallback, static exchange rate or synthetic destination is used.

The endpoint is a pure function of its inputs, so the frontend can call it
on every form change (debounced) for "continuous" updates.
"""

import os
import math

import pandas as pd

from model.route.route_engine import best_route, haversine_km
from model.budget import csv_baselines

# One-time dataset load (cached in memory like the other engines).
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../ml_service
_DATASET_PATH = os.path.join(_BASE_DIR, "model", "recommendation", "destinations.csv")

_destinations_df = None

# Interest keyword -> dataset Tourism_Category values (from the actual CSV)
INTEREST_CATEGORIES = {
    "culture": ["museum", "artwork", "attraction", "theme_park"],
    "heritage": ["museum", "artwork", "attraction"],
    "nature": ["viewpoint", "picnic_site", "alpine_hut", "attraction"],
    "adventure": ["viewpoint", "camp_site", "attraction", "picnic_site"],
    "spiritual": ["attraction", "artwork", "museum"],
    "city": ["information", "attraction", "artwork"],
    "wildlife": ["viewpoint", "attraction", "picnic_site"],
    "trekking": ["alpine_hut", "camp_site", "viewpoint"],
}

# These are model behavior parameters, not recorded prices. A day's budget
# remains unavailable unless csv_baselines supplies a complete recorded base.
STYLE_MULTIPLIER = {"budget": 0.75, "mid": 1.0, "standard": 1.0, "luxury": 1.8}

# Per-person cost share by travel type (family/group share rooms & rides).
TRAVEL_TYPE_PERSON_MULTIPLIER = {"solo": 1.0, "couple": 0.9, "family": 0.8, "group": 0.7}

# Cities with enough dataset entries to plan around.
PRIORITY_CITIES = [
    "Kathmandu", "Pokhara", "Lumbini", "Bhaktapur", "Patan", "Nagarkot",
    "Chitwan", "Sauraha", "Dhulikhel", "Gorkha", "Bandipur", "Mustang",
    "Jomsom", "Janakpur", "Ilam", "Dharan", "Biratnagar", "Tansen",
]

# Nepali (and variant) city names from the OSM dataset -> canonical English,
# so city grouping and budget baselines match even when the dataset stores
# the Devanagari form.
CITY_ALIASES = {
    "काठमाडौँ महानगरपालिका": "Kathmandu",
    "काठमाडौं महानगरपालिका": "Kathmandu",
    "काठमाण्डौ महानगरपालिका": "Kathmandu",
    "पोखरा महानगरपालिका": "Pokhara",
    "पोखरा उपमहानगरपालिका": "Pokhara",
    "ललितपुर महानगरपालिका": "Patan",
    "ललितपुर": "Patan",
    "पाटन": "Patan",
    "भक्तपुर नगरपालिका": "Bhaktapur",
    "भक्तपुर": "Bhaktapur",
    "चाँगुनारायण": "Changunarayan",
    "चांगुनारायण": "Changunarayan",
    "कीर्तिपुर": "Kirtipur",
    "नगरकोट": "Nagarkot",
    "पनौती": "Panauti",
    "सौराहा": "Sauraha",
    "चितवन": "Chitwan",
    "भरतपुर महानगरपालिका": "Chitwan",
    "लुम्बिनी": "Lumbini",
    "धुलिखेल नगरपालिका": "Dhulikhel",
    "गोरखा नगरपालिका": "Gorkha",
    "बन्दीपुर गाउँपालिका": "Bandipur",
    "जनकपुर": "Janakpur",
    "इलाम नगरपालिका": "Ilam",
    "धरान उपमहानगरपालिका": "Dharan",
    "बिराटनगर महानगरपालिका": "Biratnagar",
    "जोमसोम": "Jomsom",
    "मुस्ताङ": "Mustang",
    "तानसेन नगरपालिका": "Tansen",
    # District names travellers actually type -> the dataset city that is
    # the district seat / main tourism hub (public administrative facts).
    "kaski": "Pokhara",
    "tanahun": "Bandipur",
    "chitwan": "Chitwan",
    "rupandehi": "Lumbini",
    "kathmandu district": "Kathmandu",
    "lalitpur district": "Patan",
    "bhaktapur district": "Bhaktapur",
    "mustang district": "Mustang",
    "gorkha district": "Gorkha",
    "sindhupalchok": "Nagarkot",
}


def _normalize_city(city):
    """Map a dataset city value to its canonical English name when known."""
    city = str(city or "").strip()
    if not city:
        return city
    low = city.lower()
    # direct English match stays as-is (case fixed)
    for canon in PRIORITY_CITIES:
        if canon.lower() == low:
            return canon
    # alias lookup is case-insensitive so traveller-typed district names
    # ("kaski", "Kaski") normalise the same way dataset values do
    if low in CITY_ALIASES:
        return CITY_ALIASES[low]
    if city in CITY_ALIASES:
        return CITY_ALIASES[city]
    return city


def _load_dataset():
    global _destinations_df
    if _destinations_df is not None:
        return _destinations_df
    if not os.path.exists(_DATASET_PATH):
        return None
    df = pd.read_csv(_DATASET_PATH)
    # Normalize column names (both datasets have similar shape).
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    for col in ("latitude", "longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    _destinations_df = df
    return df


def _category_matches(interest_categories, row_cat):
    rc = str(row_cat or "").strip().lower()
    return any(rc == c or c in rc for c in interest_categories)


def _city_centroid(df, city):
    sub = df[df["city"].str.lower() == city.lower()]
    if sub.empty or sub["latitude"].isna().all() or sub["longitude"].isna().all():
        return None
    return {
        "lat": float(sub["latitude"].mean()),
        "lng": float(sub["longitude"].mean()),
    }


def _pick_cities(df, interests, days, start_city):
    """Choose up to `days` cities ordered by proximity to start_city."""
    cats = []
    for i in interests or ["culture"]:
        cats.extend(INTEREST_CATEGORIES.get(i.lower(), ["attraction"]))

    usable = df[df["name"].notna() & (df["name"].astype(str).str.strip() != "")]
    usable = usable[usable["city"].notna()]
    # Keep only rows whose category matches one of our interests.
    cat_col = "tourism_category" if "tourism_category" in usable.columns else "category"
    if cat_col not in usable.columns:
        return []
    usable = usable[[_category_matches(cats, row) for row in usable[cat_col]]]

    # Normalize Nepali city names to canonical English before counting.
    usable = usable.copy()
    usable["city"] = usable["city"].map(_normalize_city)
    usable = usable[usable["city"].str.strip() != ""]

    city_counts = usable["city"].value_counts()
    candidates = [str(c).strip() for c in city_counts.index if str(c).strip()]
    # Prefer known tourist cities, then fill with whatever has the most places.
    ordered = [c for c in PRIORITY_CITIES if c in candidates]
    rest = [c for c in candidates if c not in ordered]
    ordered += rest

    if start_city:
        start_low = start_city.lower()
        if any(c.lower() == start_low for c in ordered):
            ordered = [c for c in ordered if c.lower() != start_low]
            ordered.insert(0, start_city)

    centroids = {c: _city_centroid(df, c) for c in ordered[: days * 3]}

    # Sort by distance to start centroid (or first centroid) to keep travel short.
    origin = centroids.get(ordered[0]) if ordered else None
    if origin:
        def key(c):
            cen = centroids.get(c)
            if not cen:
                return 1e9
            return haversine_km(origin["lat"], origin["lng"], cen["lat"], cen["lng"])
        ordered.sort(key=key)

    return ordered[: max(1, days)]


def _per_day_budget_usd(city, days, travelers, budget_level, travel_type):
    try:
        baseline = csv_baselines.lookup_baseline(city=city)
    except Exception:
        baseline = None
    if not baseline or any(baseline.get(key) is None for key in ("transport", "food", "accommodation", "taxi")):
        return None

    style = STYLE_MULTIPLIER.get((budget_level or "mid").lower(), 1.0)
    person = TRAVEL_TYPE_PERSON_MULTIPLIER.get((travel_type or "solo").lower(), 1.0)
    per_person_per_day = (
        baseline["food"] + baseline["accommodation"] + baseline["taxi"]
    ) * style * person
    transport_share = (baseline["transport"] * style * person) / max(1, days)
    return round((per_person_per_day + transport_share) * travelers, 2)


def _day_theme(interests):
    if not interests:
        return "Culture"
    first = interests[0].lower()
    labels = {
        "culture": "Culture & Heritage", "heritage": "Culture & Heritage",
        "nature": "Nature & Scenery", "adventure": "Adventure",
        "spiritual": "Spiritual", "city": "City Sights",
        "wildlife": "Wildlife & Safari", "trekking": "Trekking",
    }
    return labels.get(first, "Explore")


def build_rich_itinerary(
    days=3,
    travelers=1,
    budget_npr=None,
    budget_level="mid",
    travel_style="leisure",
    travel_type="solo",
    interests=None,
    start_city=None,
):
    days = max(1, int(days or 3))
    travelers = max(1, int(travelers or 1))
    interests = [i for i in (interests or ["culture"]) if i]

    df = _load_dataset()
    if df is None:
        return {"error": "Destination dataset not found. Run the ML training/data setup first."}

    # district names typed by travellers ("Kaski") must map to the dataset
    # city that serves them ("Pokhara") before city picking
    start_city = _normalize_city(start_city)
    cities = _pick_cities(df, interests, days, start_city)
    if not cities:
        return {"error": "No recorded destinations match the selected interests."}

    cat_col = "tourism_category" if "tourism_category" in df.columns else "category"
    cats = []
    for i in interests:
        cats.extend(INTEREST_CATEGORIES.get(i.lower(), ["attraction"]))

    itinerary = []
    used_names = set()
    for day_num in range(1, days + 1):
        city = cities[(day_num - 1) % len(cities)]

        city_norm = df.copy()
        city_norm["city"] = city_norm["city"].map(_normalize_city)
        city_df = city_norm[city_norm["city"].str.lower() == city.lower()]
        if not city_df.empty and cat_col in city_df.columns:
            matches = city_df[[_category_matches(cats, r) for r in city_df[cat_col]]]
        else:
            matches = city_df
        matches = matches[matches["name"].notna() & (matches["name"].astype(str).str.strip() != "")]
        matches = matches[~matches["name"].astype(str).str.lower().isin(used_names)]
        # Rank: strongest category match first, then by dataset order.
        if not matches.empty:
            matches = matches.head(20).copy()
            matches["_score"] = [
                sum(1 for c in cats if c in str(r).lower()) for r in matches[cat_col]
            ]
            matches = matches.sort_values("_score", ascending=False)
        chosen = []
        for _, row in matches.head(3).iterrows():
            nm = str(row["name"]).strip()
            if not nm or nm.lower() in used_names:
                continue
            used_names.add(nm.lower())
            chosen.append({
                "name": nm,
                "city": city,
                "latitude": float(row["latitude"]) if pd.notna(row["latitude"]) else None,
                "longitude": float(row["longitude"]) if pd.notna(row["longitude"]) else None,
                "category": str(row[cat_col]) if cat_col in row else "attraction",
            })
        if not chosen:
            return {"error": f"No recorded destination is available for {city} on this day."}

        daily_budget_usd = _per_day_budget_usd(city, days, travelers, budget_level, travel_type)
        itinerary.append({
            "day": day_num,
            "city": city,
            "theme": _day_theme(interests),
            "destinations": chosen,
            "daily_budget_usd": daily_budget_usd,
            "daily_budget_npr": None,
        })

    # Travel legs between consecutive days using the real graphml road graph.
    for i in range(len(itinerary) - 1):
        a = itinerary[i]
        b = itinerary[i + 1]
        a_coords = next((d for d in a["destinations"] if d["latitude"]), None)
        b_coords = next((d for d in b["destinations"] if d["latitude"]), None)
        legs = []
        if a_coords and b_coords:
            try:
                r = best_route(
                    a_coords["latitude"], a_coords["longitude"],
                    b_coords["latitude"], b_coords["longitude"],
                    "fastest",
                )
                if "distance_km" in r and "error" not in r:
                    legs.append({
                        "from": a_coords["name"],
                        "to": b_coords["name"],
                        "distance_km": r["distance_km"],
                        "distance_m": int(round(r["distance_km"] * 1000)),
                        "duration_min": r.get("duration_min"),
                    })
            except Exception:
                pass
        a["legs"] = legs

    # Budget totals remain unavailable unless every day has a recorded USD
    # baseline. No static exchange rate is used to manufacture an NPR value.
    daily_costs = [d.get("daily_budget_usd") for d in itinerary]
    total_usd = round(sum(daily_costs), 2) if all(v is not None for v in daily_costs) else None
    total_npr = None
    per_person_npr = None
    fits_budget = None
    if total_usd is not None and budget_npr:
        fits_budget = None

    return {
        "days": days,
        "travelers": travelers,
        "budget_level": budget_level,
        "travel_style": travel_style,
        "travel_type": travel_type,
        "interests": interests,
        "start_city": start_city,
        "total_estimated_npr": total_npr,
        "total_estimated_usd": total_usd,
        "per_person_npr": per_person_npr,
        "budget_npr": budget_npr,
        "fits_budget": fits_budget,
        "itinerary": itinerary,
    }


# ---------------------------------------------------------------------------
# Backwards-compatible simple builder (used by /routes/itinerary)
# ---------------------------------------------------------------------------
def build_itinerary(destination_names: list[str], num_days: int) -> dict:
    if not destination_names:
        return {"error": "No destinations provided"}

    if num_days < 1:
        num_days = 1

    per_day = max(1, len(destination_names) // num_days)
    days = []
    idx = 0
    for day_num in range(1, num_days + 1):
        stops = destination_names[idx: idx + per_day]
        if day_num == num_days:
            stops = destination_names[idx:]
        idx += per_day
        days.append({
            "day": day_num,
            "stops": stops,
            "legs": [],
            "route_note": "Route distances and durations require recorded coordinates and the routing service.",
        })
        if not stops:
            break

    return {"num_days": num_days, "itinerary": days}
