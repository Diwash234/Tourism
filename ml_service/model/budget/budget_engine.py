"""
Budget calculation engine.

Supports:
- USD (US Dollars)
- NPR (Nepalese Rupees)

Important:
- Transport is a ONE-TIME total.
- Food is calculated per day.
- Accommodation is calculated per night/day.
- Taxi/local transport is calculated per day.
- The ML model works with USD-based values.
- The final response includes both USD and NPR.

The exchange rate can be configured through the environment:

    USD_TO_NPR_RATE=145

If not provided, the default rate below is used.

For production, consider getting the exchange rate from a
reliable currency API instead of using a fixed rate.
"""

import os

import joblib


# ============================================================
# CONFIGURATION
# ============================================================

BASE = os.path.dirname(__file__)

MODEL_PATH = os.path.join(
    BASE,
    "budget_model.joblib",
)

# Default USD -> NPR exchange rate.
# Change this according to the rate you want to use.
DEFAULT_USD_TO_NPR = 145.0

try:
    USD_TO_NPR = float(
        os.getenv(
            "USD_TO_NPR_RATE",
            DEFAULT_USD_TO_NPR,
        )
    )
except (TypeError, ValueError):
    USD_TO_NPR = DEFAULT_USD_TO_NPR


# ============================================================
# LOAD ML MODEL
# ============================================================

model = (
    joblib.load(MODEL_PATH)
    if os.path.exists(MODEL_PATH)
    else None
)


# ============================================================
# CURRENCY HELPERS
# ============================================================

def usd_to_npr(amount):
    """
    Convert USD to Nepalese Rupees.

    Example:
        100 USD -> 14500 NPR
    """

    return round(
        float(amount) * USD_TO_NPR,
        2,
    )


def make_currency_response(usd_amount):
    """
    Return the same amount in both USD and NPR.
    """

    usd_amount = round(
        float(usd_amount),
        2,
    )

    return {
        "usd": usd_amount,
        "npr": usd_to_npr(usd_amount),
    }


# ============================================================
# BUDGET ESTIMATION
# ============================================================

def estimate_budget(
    transport_total,
    food_per_day,
    accommodation_per_night,
    taxi_per_day,
    days,
):
    """
    Calculate the complete travel budget.

    Parameters
    ----------
    transport_total:
        ONE-TIME total transport cost.

        This should already be multiplied by the number
        of travelers in budget.py.

        Example:
            Flight = $100/person
            Travelers = 2

            transport_total = $200

        DO NOT multiply transport by `days`.

    food_per_day:
        Food cost per day.

    accommodation_per_night:
        Hotel/accommodation cost per night.

    taxi_per_day:
        Local transportation/taxi cost per day.

    days:
        Number of travel days/nights.

    Returns
    -------
    dict
        Budget in both USD and NPR.
    """

    # --------------------------------------------------------
    # Validate days
    # --------------------------------------------------------

    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 1

    days = max(1, days)

    # --------------------------------------------------------
    # Convert inputs to numbers safely
    # --------------------------------------------------------

    try:
        transport_total = float(transport_total or 0)
    except (TypeError, ValueError):
        transport_total = 0.0

    try:
        food_per_day = float(food_per_day or 0)
    except (TypeError, ValueError):
        food_per_day = 0.0

    try:
        accommodation_per_night = float(
            accommodation_per_night or 0
        )
    except (TypeError, ValueError):
        accommodation_per_night = 0.0

    try:
        taxi_per_day = float(taxi_per_day or 0)
    except (TypeError, ValueError):
        taxi_per_day = 0.0

    # Prevent negative budget values.
    transport_total = max(0, transport_total)
    food_per_day = max(0, food_per_day)
    accommodation_per_night = max(
        0,
        accommodation_per_night,
    )
    taxi_per_day = max(0, taxi_per_day)

    # ========================================================
    # REAL BUDGET CALCULATION
    # ========================================================

    # Food is a daily cost.
    food_total = round(
        food_per_day * days,
        2,
    )

    # Accommodation is a nightly cost.
    accommodation_total = round(
        accommodation_per_night * days,
        2,
    )

    # Taxi/local transport is a daily cost.
    taxi_total = round(
        taxi_per_day * days,
        2,
    )

    # IMPORTANT:
    # Transport is already a total.
    # DO NOT multiply it by days.
    transport_total = round(
        transport_total,
        2,
    )

    # ========================================================
    # REAL TOTAL
    # ========================================================

    real_total_usd = round(
        transport_total
        + food_total
        + accommodation_total
        + taxi_total,
        2,
    )

    # ========================================================
    # BUILD BREAKDOWN
    # ========================================================

    breakdown_usd = {
        "transport": transport_total,
        "food": food_total,
        "accommodation": accommodation_total,
        "local_transport": taxi_total,
    }

    breakdown_npr = {
        "transport": usd_to_npr(
            transport_total
        ),
        "food": usd_to_npr(
            food_total
        ),
        "accommodation": usd_to_npr(
            accommodation_total
        ),
        "local_transport": usd_to_npr(
            taxi_total
        ),
    }

    # ========================================================
    # RESPONSE
    # ========================================================

    result = {
        "currency": {
            "base": "USD",
            "converted": "NPR",
            "usd_to_npr_rate": USD_TO_NPR,
        },

        "total_budget_usd": real_total_usd,

        "total_budget_npr": usd_to_npr(
            real_total_usd
        ),

        "total_budget": {
            "usd": real_total_usd,
            "npr": usd_to_npr(
                real_total_usd
            ),
        },

        "breakdown": {
            "usd": breakdown_usd,
            "npr": breakdown_npr,
        },

        "days": days,
    }

    # ========================================================
    # AI / ML ESTIMATE
    # ========================================================

    if model is not None:
        try:
            # The ML model expects daily-equivalent features.
            #
            # Transport is a one-time total in the real
            # calculation, so convert it to a daily equivalent
            # ONLY for the ML model input.
            #
            # This does NOT affect the real budget total.
            transport_daily_equiv = (
                transport_total / days
            )

            daily_prediction = model.predict(
                [[
                    transport_daily_equiv,
                    food_per_day,
                    accommodation_per_night,
                    taxi_per_day,
                ]]
            )[0]

            daily_prediction = round(
                float(daily_prediction),
                2,
            )

            ai_period_prediction_usd = round(
                daily_prediction * days,
                2,
            )

            result["ai_daily_estimate"] = {
                "usd": daily_prediction,
                "npr": usd_to_npr(
                    daily_prediction
                ),
            }

            result["ai_period_estimate"] = {
                "usd": ai_period_prediction_usd,
                "npr": usd_to_npr(
                    ai_period_prediction_usd
                ),
            }

        except Exception:
            # Don't allow an ML prediction problem to
            # break the actual budget calculation.
            result["ai_daily_estimate"] = None
            result["ai_period_estimate"] = None

    return result