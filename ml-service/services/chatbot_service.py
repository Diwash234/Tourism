"""
services/chatbot_service.py

Lightweight rule/keyword-based intent router for the in-app chatbot.
This keeps the ml-service self-contained (no external LLM API key
required) while still giving you a working assistant that can answer
emergency, budget, risk, and recommendation questions. If you later
want to swap in a real LLM for open-ended conversation, this is the
single place to change - handle_message() is the only entry point
api/recommendation.py (or a future api/chat.py) needs to call.
"""
import re

from services.emergency_service import get_national_hotlines, nearest_facilities
from services.recommendation_service import recommend
from model.budget.budget_engine import estimate_budget

INTENT_PATTERNS = {
    "emergency": re.compile(r"\b(emergency|police|hospital|ambulance|help|danger|disaster)\b", re.I),
    "budget": re.compile(r"\b(budget|cost|price|how much|expens)\b", re.I),
    "recommend": re.compile(r"\b(recommend|suggest|where should|places? to (go|visit))\b", re.I),
    "greeting": re.compile(r"\b(hi|hello|namaste|hey)\b", re.I),
}


def _detect_intent(message: str) -> str:
    for intent, pattern in INTENT_PATTERNS.items():
        if pattern.search(message):
            return intent
    return "unknown"


def handle_message(message: str, lat: float | None = None, lon: float | None = None) -> dict:
    intent = _detect_intent(message)

    if intent == "greeting":
        return {"intent": intent, "reply": "Namaste! Ask me about emergency contacts, trip budgets, or destination recommendations."}

    if intent == "emergency":
        hotlines = get_national_hotlines()
        nearby = nearest_facilities(lat, lon) if lat is not None and lon is not None else []
        return {"intent": intent, "hotlines": hotlines, "nearest_facilities": nearby}

    if intent == "budget":
        estimate = estimate_budget(num_destinations=3, num_days=7, avg_daily_cost_usd=30, travel_style="mid_range")
        return {"intent": intent, "reply": "Here's a rough estimate for a typical 7-day, 3-stop trip:", "estimate": estimate}

    if intent == "recommend":
        picks = recommend(limit=3)
        return {"intent": intent, "reply": "A few places you might like:", "recommendations": picks}

    return {"intent": intent, "reply": "I can help with emergency contacts, budget estimates, or destination recommendations - try asking about one of those."}