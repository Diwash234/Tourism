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

    # Detect if overrides are provided in NPR (> 250) and convert to USD
    USD_NPR_RATE = 133.0
    def _to_usd(val):
        if val is None:
            return None
        v = float(val)
        return v / USD_NPR_RATE if v > 250 else v

    t_override = _to_usd(payload.transport_cost)
    f_override = _to_usd(payload.food_cost_day)
    a_override = _to_usd(payload.accommodation_night)
    x_override = _to_usd(payload.taxi_cost)

    distance_km = None
    if (
        t_override is None
        and payload.user_latitude is not None and payload.user_longitude is not None
        and payload.latitude is not None and payload.longitude is not None
    ):
        distance_km = _haversine_km(payload.user_latitude, payload.user_longitude, payload.latitude, payload.longitude)
        transport = max(MIN_TRANSPORT_USD, round(distance_km * TRANSPORT_USD_PER_KM, 2))
    else:
        transport = t_override if t_override is not None else baseline["transport"]

    food = f_override if f_override is not None else baseline["food"]
    accommodation = a_override if a_override is not None else baseline["accommodation"]
    taxi = x_override if x_override is not None else baseline["taxi"]

    # Multiply per-person daily figures
    food *= travelers
    transport *= travelers
    taxi *= travelers
    accommodation = accommodation * multiplier * max(1, round(travelers / 2))

    result = estimate_budget(transport, food, accommodation, taxi, days)

    result["estimated_total"] = result["total_budget_usd"]
    result["total_budget_npr"] = round(result["total_budget_usd"] * USD_NPR_RATE, 2)
    
    # Itemized NPR breakdown for direct display
    result["breakdown"]["activities"] = round(result["breakdown"]["accommodation"] * 0.15, 2)
    result["breakdown_npr"] = {
        "accommodation": round(result["breakdown"]["accommodation"] * USD_NPR_RATE, 2),
        "food": round(result["breakdown"]["food"] * USD_NPR_RATE, 2),
        "transport": round(result["breakdown"]["transport"] * USD_NPR_RATE, 2),
        "local_transport": round(result["breakdown"]["local_transport"] * USD_NPR_RATE, 2),
        "activities": round(result["breakdown"]["activities"] * USD_NPR_RATE, 2),
        "emergency_reserve": round(result["total_budget_usd"] * 0.10 * USD_NPR_RATE, 2),
    }

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