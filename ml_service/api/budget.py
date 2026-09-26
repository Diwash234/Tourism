from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional
import math

from model.budget import csv_baselines

router = APIRouter()


# Budget values are accepted only from the recorded CSV baseline. There is no
# hard-coded city fallback or static exchange rate in this service.
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
    csv_baseline = None
    try:
        csv_baseline = csv_baselines.lookup_baseline(
            city=payload.city,
            district=getattr(payload, "district", None),
            province=getattr(payload, "province", None),
        )
    except Exception:
        csv_baseline = None

    if not csv_baseline or any(csv_baseline.get(key) is None for key in ("transport", "food", "accommodation", "taxi")):
        raise HTTPException(
            status_code=503,
            detail="No complete recorded budget baseline is available for this destination.",
        )

    baseline = csv_baseline
    baseline_source = "dataset_csv"
    matched_city = None

    multiplier = STYLE_MULTIPLIER.get((payload.budget_level or "mid").lower(), 1.0)
    travelers = max(1, payload.travelers)
    days = max(1, payload.days)

    # Optional caller-supplied amounts are already denominated in USD by this
    # API. No NPR conversion is inferred without a dated exchange-rate source.
    t_override = payload.transport_cost
    f_override = payload.food_cost_day
    a_override = payload.accommodation_night
    x_override = payload.taxi_cost

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

    activities_total = None
    shopping_total = None
    known_cost_total_usd = round(accommodation_total + food_total + combined_transport, 2)
    grand_total_usd = known_cost_total_usd

    result = {
        "total_budget_usd": grand_total_usd,
        "estimated_total": grand_total_usd,
        "known_cost_total_usd": known_cost_total_usd,
        "total_is_partial": False,
        "total_budget_npr": None,
        "breakdown": {
            "accommodation": round(accommodation_total, 2),
            "food": round(food_total, 2),
            "transport": round(combined_transport, 2),
            "local_transport": 0,
            "activities": activities_total,
            "shopping": shopping_total,
        },
        "breakdown_npr": {
            "accommodation": None,
            "food": None,
            "transport": None,
            "local_transport": None,
            "activities": None,
            "shopping": None,
            "emergency_reserve": None,
            "note": "The service does not invent exchange rates; NPR conversion requires a verified rate source.",
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
