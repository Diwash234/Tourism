from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional
import math

from model.budget.budget_engine import estimate_budget
from model.budget import csv_baselines

router = APIRouter()


# ---------------------------------------------------------------------------
# Calibrated per-city baseline daily costs (USD) for Nepal travel.
# 1 USD = 133 NPR.
# ---------------------------------------------------------------------------
CITY_BASELINE_USD = {
    "kathmandu":  {"transport": 6,  "food": 11, "accommodation": 18, "taxi": 4, "lat": 27.7172, "lon": 85.3240},
    "pokhara":    {"transport": 5,  "food": 10, "accommodation": 15, "taxi": 3, "lat": 28.2096, "lon": 83.9856},
    "chitwan":    {"transport": 7,  "food": 10, "accommodation": 16, "taxi": 4, "lat": 27.5291, "lon": 84.3542},
    "lumbini":    {"transport": 6,  "food": 9,  "accommodation": 14, "taxi": 3, "lat": 27.4833, "lon": 83.2767},
    "nagarkot":   {"transport": 8,  "food": 11, "accommodation": 20, "taxi": 4, "lat": 27.7172, "lon": 85.5202},
    "bandipur":   {"transport": 6,  "food": 9,  "accommodation": 15, "taxi": 3, "lat": 27.9333, "lon": 84.4167},
}
DEFAULT_BASELINE = {"transport": 6, "food": 10, "accommodation": 16, "taxi": 3}

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
    city: Optional[str] = None
    country: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    destination: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    user_latitude: Optional[float] = None
    user_longitude: Optional[float] = None
    days: int = 3
    travelers: int = 1
    budget_level: str = "mid"

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
                "A destination is required (city name or GPS coordinates)."
            )
        return self


TRANSPORT_USD_PER_KM = 0.08
MIN_TRANSPORT_USD = 2.5


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
        csv_accom = csv_baseline.get("accommodation")
        csv_food = csv_baseline.get("food")
        csv_trans = csv_baseline.get("transport")
        csv_taxi = csv_baseline.get("taxi")

        if (payload.budget_level or "").lower() != "luxury":
            if csv_accom and csv_accom > 20:
                csv_accom = 15.0
            if csv_food and csv_food > 15:
                csv_food = 10.0
            if csv_trans and csv_trans > 15:
                csv_trans = 5.0
            if csv_taxi and csv_taxi > 6:
                csv_taxi = 3.0

        baseline = {
            "transport": csv_trans if csv_trans is not None else baseline["transport"],
            "food": csv_food if csv_food is not None else baseline["food"],
            "accommodation": csv_accom if csv_accom is not None else baseline["accommodation"],
            "taxi": csv_taxi if csv_taxi is not None else baseline["taxi"],
        }
        baseline_source = "dataset_csv"

    multiplier = STYLE_MULTIPLIER.get((payload.budget_level or "mid").lower(), 1.0)
    travelers = max(1, payload.travelers)
    days = max(1, payload.days)

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

    # Multiply per-person figures
    food_total = food * multiplier * travelers * days
    accommodation_total = accommodation * multiplier * max(1, round(travelers / 2)) * days
    combined_transport = (transport * travelers) + (taxi * travelers * days)

    activities_total = round((accommodation_total * 0.12), 2)
    shopping_total = round((food_total * 0.08), 2)
    grand_total_usd = round(accommodation_total + food_total + combined_transport + activities_total + shopping_total, 2)

    result = {
        "total_budget_usd": grand_total_usd,
        "estimated_total": grand_total_usd,
        "total_budget_npr": round(grand_total_usd * USD_NPR_RATE, 2),
        "breakdown": {
            "accommodation": round(accommodation_total, 2),
            "food": round(food_total, 2),
            "transport": round(combined_transport, 2),
            "local_transport": 0,
            "activities": activities_total,
            "shopping": shopping_total,
        },
        "breakdown_npr": {
            "accommodation": round(accommodation_total * USD_NPR_RATE, 2),
            "food": round(food_total * USD_NPR_RATE, 2),
            "transport": round(combined_transport * USD_NPR_RATE, 2),
            "local_transport": 0,
            "activities": round(activities_total * USD_NPR_RATE, 2),
            "shopping": round(shopping_total * USD_NPR_RATE, 2),
            "emergency_reserve": round(grand_total_usd * 0.10 * USD_NPR_RATE, 2),
        },
        "city": payload.city or payload.destination or matched_city,
        "matched_baseline_city": matched_city,
        "budget_level": payload.budget_level,
        "travelers": travelers,
        "days": days,
        "baseline_source": baseline_source,
        "dataset": csv_baselines.dataset_info(),
        "transport_basis": "gps_distance" if distance_km is not None else baseline_source,
    }
    return result
