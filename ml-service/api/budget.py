from fastapi import APIRouter
from pydantic import BaseModel

from model.budget.budget_engine import estimate_budget

router = APIRouter()


class BudgetRequest(BaseModel):
    num_destinations: int = 1
    num_days: int = 3
    avg_daily_cost_usd: float = 35.0
    travel_style: str = "mid_range"  # budget | mid_range | luxury
    city: str | None = None
    country: str | None = None
    travelers: int = 1
    budget_level: str = "mid"
    destination: str | int | None = None


@router.post("/estimate")
def estimate(payload: BudgetRequest):
    return estimate_budget(
        payload.num_destinations,
        payload.num_days,
        payload.avg_daily_cost_usd,
        payload.travel_style,
    )


@router.post("/predict-budget")
def predict_budget(payload: BudgetRequest):
    style = {
        "budget": "budget",
        "mid": "mid_range",
        "mid_range": "mid_range",
        "luxury": "luxury",
    }.get(payload.budget_level or payload.travel_style, "mid_range")

    avg_daily_cost_usd = payload.avg_daily_cost_usd or 35.0
    if payload.budget_level == "budget":
        avg_daily_cost_usd = 25.0
    elif payload.budget_level == "luxury":
        avg_daily_cost_usd = 95.0

    estimate = estimate_budget(
        num_destinations=max(1, payload.travelers or payload.num_destinations or 1),
        num_days=max(1, payload.num_days or 3),
        avg_daily_cost_usd=avg_daily_cost_usd,
        travel_style=style,
    )

    total = estimate.get("estimated_total_usd", 0.0)
    return {
        "total": round(float(total), 2),
        "accommodation": round(float(total) * 0.42, 2),
        "food": round(float(total) * 0.24, 2),
        "transport": round(float(total) * 0.17, 2),
        "activities": round(float(total) * 0.17, 2),
        "source": estimate.get("source", "rule_based_fallback"),
    }