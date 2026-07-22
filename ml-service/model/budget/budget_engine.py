"""
model/budget/budget_engine.py

Loads the trained budget regressor and exposes estimate_budget().
Falls back to a simple linear estimate if no trained model exists yet.
"""
import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "budget_model.joblib")
STYLE_MAP = {"budget": 0, "mid_range": 1, "luxury": 2}
STYLE_MULTIPLIER = {"budget": 0.8, "mid_range": 1.0, "luxury": 1.8}

_model = None
if os.path.exists(MODEL_PATH):
    _model = joblib.load(MODEL_PATH)


def estimate_budget(num_destinations: int, num_days: int,
                     avg_daily_cost_usd: float, travel_style: str = "mid_range") -> dict:
    style_code = STYLE_MAP.get(travel_style, 1)

    if _model is not None:
        pred = _model.predict([[num_destinations, num_days, avg_daily_cost_usd, style_code]])[0]
        return {"estimated_total_usd": round(float(pred), 2), "source": "model"}

    multiplier = STYLE_MULTIPLIER.get(travel_style, 1.0)
    estimate = num_days * avg_daily_cost_usd * multiplier
    return {"estimated_total_usd": round(estimate, 2), "source": "rule_based_fallback"}