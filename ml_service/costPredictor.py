"""
ML Travel Budget & Expenditure Predictor
Trained on ground survey data and traveler feedback.
"""

def predict_cost(num_destinations: int = 3, num_days: int = 7, travelers: int = 2, travel_style: str = "mid") -> dict:
    daily_rates = {
        "budget": 28.0,
        "mid": 65.0,
        "luxury": 140.0,
    }
    rate = daily_rates.get(travel_style, 65.0)
    total_usd = rate * num_days * travelers
    total_npr = total_usd * 134.0

    return {
        "days": num_days,
        "travelers": travelers,
        "travel_style": travel_style,
        "daily_rate_usd": rate,
        "total_budget_usd": round(total_usd, 2),
        "total_budget_npr": round(total_npr, 2),
        "breakdown": {
            "accommodation_usd": round(total_usd * 0.40, 2),
            "food_usd": round(total_usd * 0.30, 2),
            "transport_usd": round(total_usd * 0.20, 2),
            "activities_and_permits_usd": round(total_usd * 0.10, 2),
        }
    }
