"""
Full replacement for ml_service/model/budget/budget_engine.py.

THE ACTUAL BUG (confirmed by re-reading the live code):
estimate_budget()'s breakdown multiplied transport by `days`:

    "transport": round(transport * days, 2)

But budget.py (the API layer, already fixed earlier) ALREADY multiplies
transport by `travelers` before calling this function:

    transport = payload.transport_cost if ... else baseline["transport"]
    transport *= travelers

So a 5-day trip for 2 travelers ended up with transport counted as
(base_transport * 2 travelers * 5 days) -- scaling with trip LENGTH,
which is wrong for something that's realistically a ~1-2x one-time
cost per person (flight/bus in and out), not a daily recurring cost.
That's exactly the "numbers" bug: change `days` and the transport line
inflates even though nothing about the actual transport changed.

Same latent issue existed for `taxi` in some usages, and accommodation
correctly SHOULD scale with days (nights stayed) so that one was fine.

FIX: transport is now treated as a ONE-TIME total (already multiplied by
travelers in budget.py), and is NOT multiplied by days again here. Food,
accommodation, and taxi remain per-day/per-night figures and ARE
multiplied by days, which is correct. The final total is computed as a
plain, transparent sum of the real breakdown -- not by trusting the
model's single blended `daily_prediction * days` number, since that
number bakes in the same days-multiplication issue for transport that
we're fixing here. The model's prediction is still returned, clearly
labeled, as a secondary "AI daily cost estimate" reference figure.
"""
import os
import joblib

BASE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE, "budget_model.joblib")

model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None


def estimate_budget(transport_total, food_per_day, accommodation_per_night, taxi_per_day, days):
    """
    transport_total: ONE-TIME total transport cost (already scaled by
        travelers upstream in budget.py) -- NOT multiplied by days here.
    food_per_day, accommodation_per_night, taxi_per_day: per-day figures,
        multiplied by `days` below as expected.
    """
    days = max(1, days)

    food_total = round(food_per_day * days, 2)
    accommodation_total = round(accommodation_per_night * days, 2)
    taxi_total = round(taxi_per_day * days, 2)
    transport_total = round(transport_total, 2)

    real_total = transport_total + food_total + accommodation_total + taxi_total

    result = {
        "total_budget_usd": round(real_total, 2),
        "breakdown": {
            "transport": transport_total,
            "food": food_total,
            "accommodation": accommodation_total,
            "local_transport": taxi_total,
        },
    }

    if model is not None:
        # Model was trained on daily-equivalent features (see
        # train_budget_model.py / budget_features.csv). Approximate
        # transport's daily-equivalent share for the model input only --
        # this number is NOT used for the real total above, it's kept
        # purely as an informational cross-check.
        transport_daily_equiv = transport_total / days
        daily_prediction = model.predict(
            [[transport_daily_equiv, food_per_day, accommodation_per_night, taxi_per_day]]
        )[0]
        result["ai_daily_estimate_usd"] = round(float(daily_prediction), 2)

    return result