from fastapi import APIRouter
from pydantic import BaseModel

from model.budget.budget_engine import estimate_budget

router = APIRouter()


class BudgetRequest(BaseModel):
    num_destinations: int
    num_days: int
    avg_daily_cost_usd: float
    travel_style: str = "mid_range"  # budget | mid_range | luxury


@router.post("/estimate")
def estimate(payload: BudgetRequest):
    return estimate_budget(
        payload.num_destinations,
        payload.num_days,
        payload.avg_daily_cost_usd,
        payload.travel_style,
    )