"""
chatbot/services.py

Main chatbot bridge:
- Connects Django chatbot with ML chatbot service
- Uses hospital/police CSV emergency engine
- Uses OpenAI for general tourism conversation
"""

import logging
import requests
import sys
import os

from django.conf import settings


logger = logging.getLogger(__name__)


# -------------------------------------------------
# Connect ML service folder
# -------------------------------------------------

# Current file:
# Chatbot/Tourism/chatbot/services.py
#
# ML folder:
# Chatbot/ml_service/

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../"
    )
)


ML_SERVICE_PATH = os.path.join(
    PROJECT_ROOT,
    "ml_service"
)


if ML_SERVICE_PATH not in sys.path:
    sys.path.insert(
        0,
        ML_SERVICE_PATH
    )


# Import ML chatbot service
try:
    from ml_service.services.chatbot_service import handle_message

except ImportError as exc:

    logger.error(
        "Could not import ML chatbot service: %s",
        exc
    )

    handle_message = None



SYSTEM_PROMPT = (
    "You are the assistant for a Nepal tourism platform. "
    "Help travelers with destination info, budget planning, safety, "
    "and navigation questions. Keep answers concise and practical."
)



def get_chatbot_reply(
    message_history,
    latitude=None,
    longitude=None
):

    if not message_history:

        return "How can I help you today?"


    latest_message = message_history[-1]["content"]



    # ---------------------------------------
    # Local ML chatbot service
    # ---------------------------------------

    local_result = {}


    if handle_message:


        try:

            local_result = handle_message(
                latest_message,
                latitude,
                longitude
            )


        except Exception as exc:

            logger.error(
                "ML chatbot service failed: %s",
                exc
            )

            local_result = {}



    # ---------------------------------------
    # Emergency response
    # ---------------------------------------

    if local_result.get("intent") == "emergency":


        emergency_places = local_result.get(
            "emergency_places",
            {}
        )


        reply = (
            "Nearest emergency facilities:\n\n"
        )


        hospitals = emergency_places.get(
            "hospitals",
            []
        )


        police_stations = emergency_places.get(
            "police_stations",
            []
        )


        if hospitals:

            reply += "🏥 Hospitals:\n\n"


            for hospital in hospitals:

                reply += (
                    f"Name: {hospital.get('name','Unknown')}\n"
                    f"Phone: {hospital.get('phone','Not available')}\n"
                    f"Address: {hospital.get('address','Not available')}\n"
                    f"District: {hospital.get('district','')}\n"
                    f"Distance: {hospital.get('distance_km',0)} km\n\n"
                )



        if police_stations:

            reply += "👮 Police Stations:\n\n"


            for police in police_stations:

                reply += (
                    f"Name: {police.get('name','Unknown')}\n"
                    f"Phone: {police.get('phone','Not available')}\n"
                    f"Address: {police.get('address','Not available')}\n"
                    f"District: {police.get('district','')}\n"
                    f"Distance: {police.get('distance_km',0)} km\n\n"
                )



        if hospitals or police_stations:

            return reply



        return (
            "I could not find nearby hospitals or police stations. "
            "Please allow location access and try again."
        )



    # ---------------------------------------
    # Local chatbot replies
    # ---------------------------------------

    if local_result.get("reply"):


        reply = local_result["reply"]


        if local_result.get("estimate"):

            reply += "\n\n"

            reply += str(
                local_result["estimate"]
            )


        if local_result.get("recommendations"):

            reply += "\n\n"

            reply += str(
                local_result["recommendations"]
            )


        return reply




    # ---------------------------------------
    # OpenAI fallback
    # ---------------------------------------

    if not settings.OPENAI_API_KEY:

        return (
            "I can help with Nepal travel, "
            "destinations, budgets, safety, "
            "and emergency information."
        )



    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }

    ] + message_history[-20:]



    try:

        response = requests.post(

            "https://api.openai.com/v1/chat/completions",

            headers={

                "Authorization":
                f"Bearer {settings.OPENAI_API_KEY}"

            },


            json={

                "model": settings.OPENAI_MODEL,

                "messages": messages,

                "temperature": 0.4

            },


            timeout=15

        )


        response.raise_for_status()


        return (

            response.json()
            ["choices"][0]
            ["message"]
            ["content"]
            .strip()

        )



    except (

        requests.RequestException,
        KeyError,
        IndexError

    ) as exc:


        logger.warning(
            "Chatbot OpenAI failed: %s",
            exc
        )


        return (
            "Sorry, I couldn't process that right now."
        )
