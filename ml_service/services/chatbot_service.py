"""
services/chatbot_service.py

Intent router for tourism chatbot.
Handles emergency, budget and recommendations.
"""

import re

from .emergency_service import get_nearest_emergency_contacts
from .recommendation_service import recommend
from model.budget.budget_engine import estimate_budget



INTENT_PATTERNS = {

    "emergency": re.compile(
        r"\b(emergency|police|hospital|ambulance|help|danger|disaster|nearest|nearby)\b",
        re.I
    ),

    "budget": re.compile(
        r"\b(budget|cost|price|how much|expens)\b",
        re.I
    ),

    "recommend": re.compile(
        r"\b(recommend|suggest|where should|places? to (go|visit))\b",
        re.I
    ),

    "greeting": re.compile(
        r"\b(hi|hello|namaste|hey)\b",
        re.I
    ),
}



def _detect_intent(message):

    for intent, pattern in INTENT_PATTERNS.items():

        if pattern.search(message):

            return intent

    return "unknown"





def handle_message(
    message,
    lat=None,
    lon=None
):

    intent = _detect_intent(message)



    if intent == "greeting":

        return {

            "intent": intent,

            "reply":
            "Namaste! Ask me about emergency contacts, trip budgets, or destination recommendations."

        }





    if intent == "emergency":


        emergency_places = {}


        if lat is not None and lon is not None:

            emergency_places = get_nearest_emergency_contacts(
                lat,
                lon
            )


        return {

            "intent": intent,

            "reply":
            "Here are the nearest emergency facilities:",

            "emergency_places":
            emergency_places

        }







    if intent == "budget":

        estimate = estimate_budget(
            num_destinations=3,
            num_days=7,
            avg_daily_cost_usd=30,
            travel_style="mid_range"
        )


        return {

            "intent": intent,

            "reply":
            "Here's a rough estimate for a typical 7-day, 3-stop trip:",

            "estimate":
            estimate

        }






    if intent == "recommend":

        places = recommend(
            limit=3
        )


        return {

            "intent": intent,

            "reply":
            "A few places you might like:",

            "recommendations":
            places

        }





    return {

        "intent": intent,

        "reply":
        "I can help with emergency contacts, budget estimates, or destination recommendations."

    }
