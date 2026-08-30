from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional
import math

from model.budget.budget_engine import estimate_budget
from model.budget import csv_baselines

router = APIRouter()


# ---------------------------------------------------------------------------
# Per-city baseline daily costs (USD), used until training/processed_data
# /clean_budget.py is fixed to produce a usable travel_cost_cleaned.csv
# (right now that CSV's `destination` column holds numeric ranges like
# "20-40" instead of city names, so it can't be looked up by city yet).
# lat/lon let a GPS-only request (no typed city name) still match the
# nearest known city instead of always falling to the generic default.
# ---------------------------------------------------------------------------
CITY_BASELINE_USD = {
    "kathmandu":  {"transport": 8,  "food": 12, "accommodation": 20, "taxi": 6, "lat": 27.7172, "lon": 85.3240},
    "pokhara":    {"transport": 7,  "food": 10, "accommodation": 18, "taxi": 5, "lat": 28.2096, "lon": 83.9856},
    "chitwan":    {"transport": 10, "food": 10, "accommodation": 22, "taxi": 6, "lat": 27.5291, "lon": 84.3542},
    "lumbini":    {"transport": 9,  "food": 9,  "accommodation": 16, "taxi": 5, "lat": 27.4833, "lon": 83.2767},
    "nagarkot":   {"transport": 12, "food": 11, "accommodation": 25, "taxi": 8, "lat": 27.7172, "lon": 85.5202},
    "bandipur":   {"transport": 11, "food": 9,  "accommodation": 15, "taxi": 6, "lat": 27.9333, "lon": 84.4167},
}
DEFAULT_BASELINE = {"transport": 10, "food": 15, "accommodation": 25, "taxi": 5}

STYLE_MULTIPLIER = {
    "budget": 0.75,
    "mid": 1.0,
    "standard": 1.0,
    "luxury": 1.8,
}


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _resolve_baseline(city, latitude, longitude):
    """
    Prefer an exact city-name match. If only GPS coordinates were given
    (or the city name doesn't match anything known), fall back to
    whichever baseline city is geographically nearest -- this is what
    makes the estimate genuinely GPS-aware rather than just city-string
    matching.
    """
    city_key = (city or "").strip().lower()
    if city_key in CITY_BASELINE_USD:
        return CITY_BASELINE_USD[city_key], city_key

    if latitude is not None and longitude is not None:
        nearest_key = min(
            CITY_BASELINE_USD,
            key=lambda k: _haversine_km(latitude, longitude, CITY_BASELINE_USD[k]["lat"], CITY_BASELINE_USD[k]["lon"]),
        )
        return CITY_BASELINE_USD[nearest_key], nearest_key

    return DEFAULT_BASELINE, None


class BudgetRequest(BaseModel):
    """
    Matches what Django's get_ml_budget_prediction() sends. A destination
    is required (city name OR destination lat/lon) -- see require_destination
    below. `user_latitude`/`user_longitude` are separate and optional: when
    given, transport cost is computed from REAL distance traveled (user's
    current location -> destination) instead of a flat per-city baseline --
    this is what makes the estimate genuinely GPS-aware rather than just
    picking a fixed number off a lookup table regardless of how far the
    trip actually is.
    """
    city: Optional[str] = None
    country: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    destination: Optional[str] = None       # alias used by the Django proxy
    latitude: Optional[float] = None       # destination's coordinates
    longitude: Optional[float] = None
    user_latitude: Optional[float] = None  # traveler's current location
    user_longitude: Optional[float] = None
    days: int = 3
    travelers: int = 1
    budget_level: str = "mid"

    # Optional direct overrides (bypasses the city lookup table above)
    transport_cost: Optional[float] = None
    food_cost_day: Optional[float] = None
    accommodation_night: Optional[float] = None
    taxi_cost: Optional[float] = None

    @model_validator(mode="after")
    def require_destination(self):
        has_city = bool((self.city or self.destination or "").strip())
        has_coords = self.latitude is not None and self.longitude is not None
        if not has_city and not has_coords:
            raise ValueError(
                "A destination is required (city name or GPS coordinates). "
                "Budget estimates are place-specific and can't be generated "
                "from trip length or traveler count alone."
            )
        return self


# Rough blended per-km transport cost for Nepal (bus/jeep/domestic-flight
# mix depending on distance) -- used only when real user->destination
# distance is available. This is a simple, honestly-labeled estimate, not
# a trained model; refine with real fare data if/when
# travel_cost_cleaned.csv is ever re-collected (see BUGS.md #3).
TRANSPORT_USD_PER_KM = 0.12
MIN_TRANSPORT_USD = 3.0  # even a short trip has some minimum transport cost


@router.post("/predict-budget")
def predict_budget(payload: BudgetRequest):
    try:
        baseline, matched_city = _resolve_baseline(payload.city, payload.latitude, payload.longitude)
    except Exception:
        baseline, matched_city = DEFAULT_BASELINE, None

    # Prefer real figures from the cleaned CSV dataset
    # (processed_data/budget_features.csv) when available. The CSV carries
    # per-destination/district/province cost ranges, so the estimate is
    # grounded in actual collected data rather than only the small built-in
    # city table. Missing fields fall back to the built-in baseline.
    csv_baseline = None
    try:
        csv_baseline = csv_baselines.lookup_baseline(
            city=payload.city,
            district=getattr(payload, "district", None),
            province=getattr(payload, "province", None),
        )
    except Exception:
        csv_baseline = None

    baseline_source = "built_in"
    if csv_baseline:
        baseline = {k: (csv_baseline.get(k) if csv_baseline.get(k) is not None else baseline.get(k))
                    for k in ("transport", "food", "accommodation", "taxi")}
        baseline_source = "dataset_csv"

    multiplier = STYLE_MULTIPLIER.get((payload.budget_level or "mid").lower(), 1.0)
    travelers = max(1, payload.travelers)
    days = max(1, payload.days)

    # GPS-aware transport: if we know both where the traveler actually is
    # AND the destination's real coordinates, compute a real distance-based
    # cost instead of the flat per-city baseline figure.
    distance_km = None
    if (
        payload.transport_cost is None
        and payload.user_latitude is not None and payload.user_longitude is not None
        and payload.latitude is not None and payload.longitude is not None
    ):
        distance_km = _haversine_km(payload.user_latitude, payload.user_longitude, payload.latitude, payload.longitude)
        transport = max(MIN_TRANSPORT_USD, round(distance_km * TRANSPORT_USD_PER_KM, 2))
    else:
        transport = payload.transport_cost if payload.transport_cost is not None else baseline["transport"]

    food = payload.food_cost_day if payload.food_cost_day is not None else baseline["food"]
    accommodation = payload.accommodation_night if payload.accommodation_night is not None else baseline["accommodation"]
    taxi = payload.taxi_cost if payload.taxi_cost is not None else baseline["taxi"]

    # Food/taxi scale per traveler and per day (handled by budget_engine.py
    # multiplying by `days`). Transport scales per traveler as a ONE-TIME
    # total -- it must NOT also be multiplied by days (see the fixed
    # budget_engine.py in this same file set -- confirm it's actually
    # applied, it was still the old double-counting version as of the
    # last check). Accommodation is per room (roughly 2 travelers/room)
    # and gets the style multiplier.
    food *= travelers
    transport *= travelers
    taxi *= travelers
    accommodation = accommodation * multiplier * max(1, round(travelers / 2))

    result = estimate_budget(transport, food, accommodation, taxi, days)

    # Django's BudgetPredictionView reads result["estimated_total"] and
    # result["breakdown"] specifically -- estimate_budget() returns
    # "total_budget_usd" instead, so without this alias `flattened["total"]`
    # always came back None. Also add an "activities" line since the
    # frontend's pie chart reads breakdown.activities.
    result["estimated_total"] = result["total_budget_usd"]
    result["breakdown"]["activities"] = round(result["breakdown"]["accommodation"] * 0.15, 2)

    result["city"] = payload.city or payload.destination or matched_city
    result["matched_baseline_city"] = matched_city
    result["budget_level"] = payload.budget_level
    result["travelers"] = travelers
    result["days"] = days
    result["baseline_source"] = baseline_source
    result["dataset"] = csv_baselines.dataset_info()
    if distance_km is not None:
        result["distance_km"] = round(distance_km, 1)
        result["transport_basis"] = "gps_distance"
    else:
        result["transport_basis"] = baseline_source
    return result