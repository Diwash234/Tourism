"""Recorded-dataset budget baselines.

The ML sidecar (pandas/sklearn) is optional and often absent, so a destination
budget has to be answerable from the verified travel-cost dataset that is
imported into ``BudgetEstimation`` — never from an invented average.

This lives in its own module rather than inside ``views_ml.py`` because
``views_ml`` has been rewritten repeatedly during the ML refactor, and the
baseline behaviour must not depend on which copy of that file survives.

Resolution order (recorded, never guessed):
  1. the destination's own row                     -> scope "destination"
  2. the MEDIAN of recorded rows in its district    -> scope "district"
  3. the MEDIAN of recorded rows in its province    -> scope "province"
  4. nothing in the dataset covers the area        -> (None, None)

An area baseline is returned because a district median is a real, sourced
figure — but it is always labelled as an area baseline, never presented as this
place's own price.
"""

from types import SimpleNamespace

from statistics import median

from .models import BudgetEstimation

#: Fields that are medians when a district/province baseline is used.
BASELINE_FIELDS = (
    "estimated_daily_budget",
    "accommodation_per_night",
    "food_cost_per_day",
    "transport_cost",
    "local_transport",
)


def recorded_budget_baseline(destination):
    """Return ``(row_like, scope)`` for the best recorded baseline.

    ``row_like`` is either the destination's own ``BudgetEstimation`` row or a
    ``SimpleNamespace`` carrying the median of a wider area. ``(None, None)``
    means the dataset does not cover this area at all, and the caller must fall
    back to official fees only instead of inventing a living-cost figure.
    """
    own = BudgetEstimation.objects.filter(destination=destination).first()
    if own is not None:
        return own, "destination"

    for scope, lookup in (
        ("district", {"destination__district__iexact": destination.district}),
        ("province", {"destination__province__iexact": destination.province}),
    ):
        value = next(iter(lookup.values()), None)
        if not value:
            continue
        rows = list(BudgetEstimation.objects.filter(**lookup))
        if not rows:
            continue
        return SimpleNamespace(**{
            field: median(float(getattr(row, field) or 0) for row in rows)
            for field in BASELINE_FIELDS
        }), scope

    return None, None


def recorded_budget_response(recorded, data, destination, scope="destination"):
    """Build the budget payload from a recorded baseline row.

    Categories the dataset does not hold stay ``None`` — they are never filled
    with an estimate. The dataset also has no budget/mid/luxury bands, so the
    response says so rather than implying a tiered quote.
    """
    # Imported lazily: views_ml imports this module, so a module-level import
    # here would be circular.
    from .views_ml import _official_budget_context

    days = max(1, int(data["days"]))
    travelers = max(1, int(data["travelers"]))
    daily = float(recorded.estimated_daily_budget or 0)
    accommodation = float(recorded.accommodation_per_night or 0)
    food = float(recorded.food_cost_per_day or 0)
    transport = float(recorded.transport_cost or 0) + float(recorded.local_transport or 0)
    total = daily * days * travelers

    if scope == "destination":
        living_note = (
            "Recorded baseline from the bundled Nepal travel-cost dataset; "
            "not a live hotel or operator quote."
        )
    else:
        living_note = (
            f"No cost row exists for {destination.name} itself, so this is the "
            f"median of recorded places in the same {scope} of the bundled Nepal "
            "travel-cost dataset. Treat it as an area baseline, not this place's price."
        )

    result = {
        "source": "dataset_csv",
        "baseline_source": "dataset_csv",
        "dataset": {
            "name": "budget_features.csv",
            "destinations": BudgetEstimation.objects.count(),
        },
        "currency": "USD",
        "total_budget_usd": round(total, 2),
        "daily_cost_usd": round(daily * travelers, 2),
        "total": round(total, 2),
        "estimated_total": round(total, 2),
        "known_cost_total_usd": round(total, 2),
        "breakdown": {
            "accommodation": round(accommodation * days * travelers, 2),
            "food": round(food * days * travelers, 2),
            "transport": round(transport * travelers, 2),
            "activities": None,
            "shopping": None,
        },
        "living_costs_available": True,
        "living_costs_note": living_note,
        "baseline_scope": scope,
        "style_note": (
            "The source dataset has no separate budget/mid/luxury bands; the "
            "recorded destination baseline is used."
        ),
        "days": days,
        "travelers": travelers,
        "official_fees_only": False,
    }
    result.update(_official_budget_context(result, data, destination))
    result["matched_destination"] = {
        "id": destination.id,
        "name": destination.name,
        "district": destination.district or "",
    }
    return result
