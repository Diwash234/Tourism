"""
chatbot/services.py — OpenAI-backed assistant for the tourism platform.
Reuses the same OPENAI_API_KEY/OPENAI_MODEL settings as tourist/utils.py's
translation tier. Degrades gracefully with a clear message if not configured.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the assistant for a Nepal tourism platform. Help travelers with "
    "destination info, budget planning, safety, and navigation questions. "
    "Keep answers concise and practical. If asked something outside travel/"
    "tourism in Nepal, politely redirect to that topic."
)


def get_chatbot_reply(message_history):
    """
    `message_history` is a list of {"role": "user"|"assistant", "content": str},
    oldest first. Returns the assistant's reply text, or a graceful
    fallback string if OpenAI isn't configured/reachable — never raises.
    """
    if not settings.OPENAI_API_KEY:
        return "The chat assistant isn't configured yet (missing OPENAI_API_KEY)."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + message_history[-20:]  # cap context length

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={"model": settings.OPENAI_MODEL, "messages": messages, "temperature": 0.4},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("Chatbot OpenAI call failed: %s", exc)
        return "Sorry, I couldn't process that right now — please try again in a moment."