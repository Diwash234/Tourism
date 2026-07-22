"""
services/recommendation_service.py

Combines destination data, risk scores, and simple preference matching to
produce a ranked list of recommended destinations. This is what
api/recommendation.py calls.
"""
import os
import pandas as pd

from model.risk.risk_engine import predict_risk
from model.route.route_engine import haversine_km

DESTINATIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "destinations", "nepal_destinations_sample.csv"
)

KATHMANDU = (27.7172, 85.3240)


def recommend(category: str | None = None, max_budget_per_day: float | None = None,
               risk_tolerance: str = "medium", limit: int = 5) -> list:
    """
    risk_tolerance: 'low' (only low-risk places), 'medium' (low+medium),
    'high' (everything).
    """
    df = pd.read_csv(DESTINATIONS_PATH)

    if category:
        df = df[df["category"].str.lower() == category.lower()]
    if max_budget_per_day:
        df = df[df["avg_daily_cost_usd"] <= max_budget_per_day]

    allowed_risk = {
        "low": {"low"},
        "medium": {"low", "medium"},
        "high": {"low", "medium", "high"},
    }.get(risk_tolerance, {"low", "medium"})
    df = df[df["risk_level"].isin(allowed_risk)]

    results = []
    for _, row in df.iterrows():
        distance = haversine_km(*KATHMANDU, row["lat"], row["lon"])
        results.append({
            "name": row["name"],
            "category": row["category"],
            "avg_daily_cost_usd": row["avg_daily_cost_usd"],
            "risk_level": row["risk_level"],
            "distance_from_kathmandu_km": round(distance, 1),
            "best_season": row["best_season"],
        })

    # Simple scoring: prefer closer + cheaper + lower risk
    risk_penalty = {"low": 0, "medium": 15, "high": 40}
    for r in results:
        r["score"] = round(
            100 - r["distance_from_kathmandu_km"] * 0.05
            - r["avg_daily_cost_usd"] * 0.3
            - risk_penalty[r["risk_level"]],
            1,
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]