from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from model.budget.budget_engine import estimate_budget

router = APIRouter()


# ---------------------------------------------------------------------------
# Per-city baseline daily costs (USD), used until training/processed_data
# /clean_budget.py is fixed to produce a usable travel_cost_cleaned.csv
# (right now that CSV's `destination` column holds numeric ranges like
# "20-40" instead of city names, so it can't be looked up by city yet).
# Add more cities here as real data becomes available.
# ---------------------------------------------------------------------------
CITY_BASELINE_USD = {
    "kathmandu":  {"transport": 8,  "food": 12, "accommodation": 20, "taxi": 6},
    "pokhara":    {"transport": 7,  "food": 10, "accommodation": 18, "taxi": 5},
    "chitwan":    {"transport": 10, "food": 10, "accommodation": 22, "taxi": 6},
    "lumbini":    {"transport": 9,  "food": 9,  "accommodation": 16, "taxi": 5},
    "nagarkot":   {"transport": 12, "food": 11, "accommodation": 25, "taxi": 8},
    "bandipur":   {"transport": 11, "food": 9,  "accommodation": 15, "taxi": 6},
}
DEFAULT_BASELINE = {"transport": 10, "food": 15, "accommodation": 25, "taxi": 5}

# Multiplies the accommodation + activity portion of the estimate.
# Transport/food scale with travelers directly (handled below); style mainly
# changes lodging/activity comfort level.
STYLE_MULTIPLIER = {
    "budget": 0.75,
    "mid": 1.0,
    "standard": 1.0,
    "luxury": 1.8,
}


class BudgetRequest(BaseModel):
    """
    Matches what Django's get_ml_budget_prediction() actually sends
    (Tourism/tourist/utils.py). Previously this model expected
    transport_cost/food_cost_day/accommodation_night/taxi_cost directly,
    which Django never sent -- so every request silently fell back to
    this model's defaults and the estimate never varied. Raw per-category
    overrides are kept as optional fields so direct/manual testing of the
    ml-service (e.g. via /docs) still works.
    """
    city: Optional[str] = None
    country: Optional[str] = None
    days: int = 3
    travelers: int = 1
    budget_level: str = "mid"

    # Optional direct overrides (bypasses the city lookup table above)
    transport_cost: Optional[float] = None
    food_cost_day: Optional[float] = None
    accommodation_night: Optional[float] = None
    taxi_cost: Optional[float] = None


@router.post("/predict-budget")
def predict_budget(payload: BudgetRequest):
    city_key = (payload.city or "").strip().lower()
    baseline = CITY_BASELINE_USD.get(city_key, DEFAULT_BASELINE)
    multiplier = STYLE_MULTIPLIER.get((payload.budget_level or "mid").lower(), 1.0)
    travelers = max(1, payload.travelers)

    transport = payload.transport_cost if payload.transport_cost is not None else baseline["transport"]
    food = payload.food_cost_day if payload.food_cost_day is not None else baseline["food"]
    accommodation = payload.accommodation_night if payload.accommodation_night is not None else baseline["accommodation"]
    taxi = payload.taxi_cost if payload.taxi_cost is not None else baseline["taxi"]

    # Food/transport/taxi scale per traveler; accommodation is per room
    # (roughly 2 travelers/room) and gets the style multiplier since that's
    # where "budget vs luxury" shows up most.
    food *= travelers
    transport *= travelers
    taxi *= travelers
    accommodation = accommodation * multiplier * max(1, round(travelers / 2))

    result = estimate_budget(transport, food, accommodation, taxi, payload.days)

    # Django's BudgetPredictionView (Tourism/tourist/views_ml.py) reads
    # result["estimated_total"] and result["breakdown"] specifically --
    # estimate_budget() returns "total_budget_usd" instead, so without this
    # alias `flattened["total"]` always came back None regardless of the
    # fixes above. Also add an "activities" line to breakdown since the
    # frontend's BudgetEstimator pie chart reads breakdown.activities and
    # the model has no such category yet.
    result["estimated_total"] = result["total_budget_usd"]
    result["breakdown"]["activities"] = round(result["breakdown"]["accommodation"] * 0.15, 2)

    result["city"] = payload.city
    result["budget_level"] = payload.budget_level
    result["travelers"] = travelers
    return result

#     cd ml-service
# venv\Scripts\activate
# python training/process_budget.py
# python training/train_budget_model.py