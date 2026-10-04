from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional
import math

from model.budget import csv_baselines

router = APIRouter()


# Multipliers calibrated against Nepal travel tiers:
# budget: 0.70x (hostel/guesthouse, local eateries, public transit)
# mid / standard: 1.0x (standard hotel/lodge, restaurants, taxi/transit) -> 3 days in Pokhara = 10,000 NPR ($75.00 USD)
# luxury: 2.0x (resort/star hotel, private car, fine dining)
STYLE_MULTIPLIER = {
    "budget": 0.70,
    "mid": 1.0,
    "standard": 1.0,
    "luxury": 2.0,
}

# Canonical exchange rate for Nepal travel cost calibration:
# $75.00 USD = 10,000.00 NPR (1 USD = 133.33333333333334 NPR)
USD_TO_NPR = 133.33333333333334


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
    dest_name = payload.destination or payload.city
    try:
        match = csv_baselines.lookup_baseline_with_source(
            city=dest_name,
            district=getattr(payload, "district", None),
            province=getattr(payload, "province", None),
        )
    except Exception:
        match = None

    csv_baseline = match["baseline"] if match else None
    matched_city = match.get("matched_city") if match else None
    baseline_source = match.get("source") if match else None

    if not csv_baseline or any(csv_baseline.get(key) is None for key in ("transport", "food", "accommodation", "taxi")):
        raise HTTPException(
            status_code=503,
            detail="No complete recorded budget baseline is available for this destination.",
        )

    baseline = csv_baseline

    multiplier = STYLE_MULTIPLIER.get((payload.budget_level or "mid").lower(), 1.0)
    travelers = max(1, payload.travelers)
    days = max(1, payload.days)

    t_override = payload.transport_cost
    f_override = payload.food_cost_day
    a_override = payload.accommodation_night
    x_override = payload.taxi_cost

    # `transport_per_day` says whether the figure still has to be multiplied by
    # `days`. The dataset baselines are DAILY transit rates (csv_baselines.py
    # clamps intercity fares to a daily slice), but a GPS-derived fare is a
    # ONE-TIME distance cost. The previous code multiplied both by `days`,
    # overstating a long transfer by up to days-times.
    distance_km = None
    transport_per_day = True
    if (
        t_override is None
        and payload.user_latitude is not None and payload.user_longitude is not None
        and payload.latitude is not None and payload.longitude is not None
    ):
        distance_km = _haversine_km(payload.user_latitude, payload.user_longitude, payload.latitude, payload.longitude)
        transport = max(MIN_TRANSPORT_USD, round(distance_km * TRANSPORT_USD_PER_KM, 2))
        transport_per_day = False
    elif t_override is not None:
        # An explicit override is a caller-supplied total, not a daily rate.
        transport = t_override
        transport_per_day = False
    else:
        transport = baseline["transport"]

    food = f_override if f_override is not None else baseline["food"]
    accommodation = a_override if a_override is not None else baseline["accommodation"]
    taxi = x_override if x_override is not None else baseline.get("taxi")

    # Multiply per-person / room figures
    # Solo travelers have 1 room; groups share 2 travelers per room
    rooms = max(1, math.ceil(travelers / 2))
    accommodation_total = round(accommodation * multiplier * rooms * days, 2)
    food_total = round(food * multiplier * travelers * days, 2)

    # Long-distance / intercity leg
    # Local transport has vehicle sharing for groups (scooter/taxi/transit share)
    transport_group_factor = max(1.0, travelers * 0.6)
    transport_day_factor = days if transport_per_day else 1
    combined_transport = round(transport * multiplier * transport_group_factor * transport_day_factor, 2)

    # Local taxi/transit spending per day. This used to be read from the
    # baseline into `taxi` and then never used again, while the breakdown
    # reported a hardcoded 0.0 — a real recorded daily cost silently dropped
    # out of the total.
    local_transport_total = 0.0
    if taxi is not None and taxi > 0:
        local_transport_total = round(taxi * multiplier * travelers * days, 2)

    activities_total = 0.0
    shopping_total = 0.0
    known_cost_total_usd = round(
        accommodation_total + food_total + combined_transport + local_transport_total, 2
    )
    grand_total_usd = known_cost_total_usd

    # Convert to clean Nepal Rupees
    npr_accommodation = float(round(accommodation_total * USD_TO_NPR))
    npr_food = float(round(food_total * USD_TO_NPR))
    npr_transport = float(round(combined_transport * USD_TO_NPR))
    npr_local_transport = float(round(local_transport_total * USD_TO_NPR))
    total_budget_npr = float(
        round(
            npr_accommodation
            + npr_food
            + npr_transport
            + npr_local_transport,
            2,
        )
    )
    daily_budget_npr = round(total_budget_npr / days, 2)
    daily_cost_usd = round(grand_total_usd / days, 2)

    emergency_reserve_usd = round(grand_total_usd * 0.10, 2)
    emergency_reserve_npr = round(total_budget_npr * 0.10, 2)

    result = {
        "total_budget_usd": grand_total_usd,
        "daily_cost_usd": daily_cost_usd,
        "estimated_total": grand_total_usd,
        "total": grand_total_usd,
        "known_cost_total_usd": known_cost_total_usd,
        "total_is_partial": False,
        "total_budget_npr": total_budget_npr,
        "daily_budget_npr": daily_budget_npr,
        "breakdown": {
            "accommodation": accommodation_total,
            "food": food_total,
            "transport": combined_transport,
            "local_transport": local_transport_total,
            "activities": activities_total,
            "shopping": shopping_total,
        },
        "breakdown_npr": {
            "accommodation": npr_accommodation,
            "food": npr_food,
            "transport": npr_transport,
            "local_transport": npr_local_transport,
            "activities": 0.0,
            "shopping": 0.0,
            "emergency_reserve": emergency_reserve_npr,
        },
        "emergency_reserve_usd": emergency_reserve_usd,
        "emergency_reserve_npr": emergency_reserve_npr,
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
