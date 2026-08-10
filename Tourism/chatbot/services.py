"""
chatbot/services.py

THE BUG: the real AI call (ask_ai(), which uses your configured Groq/
Gemini keys) was only ever reached from inside the "emergency" keyword
branch -- every other message matched one of the earlier canned-response
branches (greeting, destination, budget, hotel, safety, transport) and
never got anywhere near the AI at all. That's why it looked like the AI
"wasn't working" despite valid API keys -- it was almost never called.

Fix: canned responses now only handle simple lookups that don't need an
AI call at all (greetings, static "popular destinations" list). Anything
that doesn't match a simple pattern -- including budget/hotel/safety/
transport/emergency questions with real specifics -- goes to the AI,
with the old canned text kept ONLY as a fallback if the AI call itself
fails (no key configured, API down, etc.), not as the primary path.
"""
import random

from .ai_service import ask_ai

NEPAL_CONTEXT = """
Nepal tourism information:

Popular places: Kathmandu, Pokhara, Chitwan, Lumbini, Everest Region,
Mustang, Rara Lake.

The chatbot helps with: destinations, budget, hotels, transport, safety,
and emergency information (nearest hospitals/police/tourist police).
"""

GREETINGS = ["hi", "hello", "hey", "namaste"]


def get_chatbot_reply(history, latitude=None, longitude=None):
    if not history:
        return (
            "Hello! I am your Nepal Tourism Assistant. "
            "How can I help you?"
        )

    user_message = history[-1]["content"].lower()

    # Only a plain greeting gets a canned response with no AI call --
    # everything else, however it's phrased, goes to the real AI so it
    # can actually answer the specific question asked instead of
    # matching a generic keyword bucket.
    if user_message.strip() in GREETINGS or (
        len(user_message.split()) <= 2 and any(word in user_message for word in GREETINGS)
    ):
        return random.choice([
            "Namaste! I can help you plan your Nepal trip, find destinations, hotels, budgets and emergency services.",
            "Hello! I am your Nepal Tourism Assistant. Ask me about places, travel plans, safety or expenses.",
        ])

    location_context = ""
    if latitude is not None and longitude is not None:
        location_context = f"\nThe user's current location is approximately {latitude}, {longitude}."

    ai_reply = ask_ai(history[-1]["content"], NEPAL_CONTEXT + location_context)
    if ai_reply:
        return ai_reply

    # AI unavailable (no key configured, provider error, etc.) -- fall
    # back to the old keyword-matched canned responses rather than
    # returning nothing. This is now the FALLBACK path, not the primary
    # one.
    return _canned_fallback(user_message)


def _canned_fallback(user_message):
    if any(word in user_message for word in ["destination", "place", "visit", "where to go", "travel"]):
        return (
            "Popular destinations in Nepal include:\n\n"
            "🏔️ Kathmandu - temples, culture and heritage sites\n"
            "🏔️ Pokhara - lakes, mountains and adventure activities\n"
            "🏔️ Chitwan - wildlife safari and nature\n"
            "🏔️ Everest Region - trekking and Himalayan views\n"
            "🏔️ Lumbini - birthplace of Buddha"
        )

    if "pokhara" in user_message:
        return (
            "Pokhara is one of Nepal's most popular destinations.\n\n"
            "Things to do:\n"
            "• Phewa Lake boating\n"
            "• Sarangkot sunrise view\n"
            "• Davis Falls\n"
            "• International Mountain Museum\n"
            "• Paragliding"
        )

    if "kathmandu" in user_message:
        return (
            "Kathmandu is Nepal's cultural capital.\n\n"
            "You can visit:\n"
            "• Pashupatinath Temple\n"
            "• Boudhanath Stupa\n"
            "• Swayambhunath\n"
            "• Kathmandu Durbar Square"
        )

    if any(word in user_message for word in ["budget", "cost", "price", "expense"]):
        return (
            "Estimated Nepal travel budget:\n\n"
            "💰 Backpacker: $20-$35/day\n"
            "💰 Moderate: $40-$80/day\n"
            "💰 Luxury: $100+/day\n\n"
            "Costs depend on accommodation, transport and activities."
        )

    if any(word in user_message for word in ["emergency", "hospital", "police", "help"]):
        return (
            "For emergencies in Nepal: Police 100, Ambulance 102, "
            "Tourist Police 1144. I can also look up the nearest facility "
            "if you share your location."
        )

    if any(word in user_message for word in ["hotel", "stay", "accommodation"]):
        return (
            "Nepal has many accommodation options:\n\n"
            "• Budget guesthouses\n"
            "• Boutique hotels\n"
            "• Luxury resorts\n\n"
            "Popular areas include Thamel (Kathmandu) and Lakeside (Pokhara)."
        )

    if any(word in user_message for word in ["safe", "safety", "risk"]):
        return (
            "Nepal is generally safe for tourists. "
            "Keep your documents safe, check weather before trekking, "
            "and use registered guides for adventure activities."
        )

    if any(word in user_message for word in ["transport", "bus", "flight", "taxi"]):
        return (
            "Transportation options in Nepal include:\n\n"
            "• Tourist buses\n"
            "• Domestic flights\n"
            "• Taxis\n"
            "• Ride-sharing services in major cities"
        )

    return (
        "I can help you with:\n\n"
        "• Nepal destinations\n"
        "• Travel budgets\n"
        "• Hotels\n"
        "• Emergency services\n"
        "• Safety information\n"
        "• Transportation\n\n"
        "Please ask me a specific travel question."
    )