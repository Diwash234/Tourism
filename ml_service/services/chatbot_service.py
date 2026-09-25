"""
Tourism chatbot intent router
"""


import re

from .emergency_service import get_nearest_emergency_contacts
from .recommendation_service import recommend


INTENT_PATTERNS = {


    "emergency": re.compile(
        r"\b(emergency|police|hospital|ambulance|accident|danger|help)\b",
        re.I
    ),


    "budget": re.compile(
        r"\b(budget|cost|price|expense|how much)\b",
        re.I
    ),


    "recommend": re.compile(
        r"\b(recommend|suggest|places|visit|travel)\b",
        re.I
    ),


    "greeting": re.compile(
        r"\b(hi|hello|hey|namaste)\b",
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


    intent = _detect_intent(
        message
    )



    if intent == "greeting":


        return {

            "intent": "greeting",

            "reply":
            "Namaste! I can help you with Nepal destinations, budgets, travel plans and safety."

        }




    if intent == "emergency":


        places = {}


        if lat and lon:

            places = get_nearest_emergency_contacts(
                lat,
                lon
            )


        return {

            "intent":
            "emergency",

            "emergency_places":
            places

        }





    if intent == "budget":


        return {

            "intent": "budget",

            "reply": "A budget is unavailable unless a recorded estimate is returned for the selected destination. Browse the catalogue or Budget Estimator for an honest result.",

            "estimate": None

        }





    if intent == "recommend":


        places = recommend(
            limit=3
        )


        return {

            "intent":
            "recommend",

            "reply":
            "Recommended places:",

            "recommendations":
            places

        }





    # Important:
    # Do NOT return reply here.
    # This allows OpenAI to answer.

    return {

        "intent":
        "unknown"

    }
