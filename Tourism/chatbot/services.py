import random
from .ai_service import ask_ai

def get_chatbot_reply(
    history,
    latitude=None,
    longitude=None
):

    # Get latest user message

    if not history:
        return (
            "Hello! I am your Nepal Tourism Assistant. "
            "How can I help you?"
        )   


    user_message = history[-1]["content"].lower()

    # Try the configured AI provider (Groq/Gemini/OpenAI) first. If no
    # provider or API key is configured this degrades gracefully to the
    # rule-based answers below — never an error.
    ai_unavailable = False
    try:
        ai_reply = ask_ai(history[-1]["content"], context="")
        if ai_reply:
            return ai_reply
    except Exception:  # noqa: BLE001 - missing key/library => fall back to rules
        ai_unavailable = True

    # Weather/temperature questions have no canned answer in the rule set —
    # route them straight to a graceful reply instead of a mismatched rule.
    if any(word in user_message for word in ("weather", "temperature", "forecast", "rain")):
        if ai_unavailable:
            return (
                "I can't check live weather for you right now — the AI assistant "
                "isn't configured on this server. Try the weather widget on the "
                "destination page instead."
            )
        return (
            "I can't check live weather with the rule-based assistant. "
            "Please ask a destination-specific question or use the "
            "weather widget on a destination page."
        )


    # -------------------------
    # Greetings
    # -------------------------

    greetings = [
        "hi",
        "hello",
        "hey",
        "namaste"
    ]


    if any(word in user_message for word in greetings):

        return random.choice([

            "Namaste! I can help you plan your Nepal trip, find destinations, hotels, budgets and emergency services.",

            "Hello! I am your Nepal Tourism Assistant. Ask me about places, travel plans, safety or expenses."

        ])



    # -------------------------
    # Destinations
    # -------------------------

    if any(
        word in user_message
        for word in [
            "destination",
            "place",
            "visit",
            "where to go",
            "travel"
        ]
    ):

        return (
            "Popular destinations in Nepal include:\n\n"
            "🏔️ Kathmandu - temples, culture and heritage sites\n"
            "🏔️ Pokhara - lakes, mountains and adventure activities\n"
            "🏔️ Chitwan - wildlife safari and nature\n"
            "🏔️ Everest Region - trekking and Himalayan views\n"
            "🏔️ Lumbini - birthplace of Buddha"
        )



    # -------------------------
    # Pokhara
    # -------------------------

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



    # -------------------------
    # Kathmandu
    # -------------------------

    if "kathmandu" in user_message:

        return (
            "Kathmandu is Nepal's cultural capital.\n\n"
            "You can visit:\n"
            "• Pashupatinath Temple\n"
            "• Boudhanath Stupa\n"
            "• Swayambhunath\n"
            "• Kathmandu Durbar Square"
        )



    # -------------------------
    # Budget
    # -------------------------

    if any(
        word in user_message
        for word in [
            "budget",
            "cost",
            "price",
            "expense"
        ]
    ):

        return (
            "Estimated Nepal travel budget:\n\n"
            "💰 Backpacker: $20-$35/day\n"
            "💰 Moderate: $40-$80/day\n"
            "💰 Luxury: $100+/day\n\n"
            "Costs depend on accommodation, transport and activities."
        )



    # -------------------------
    # Emergency
    # -------------------------

    if any(
        word in user_message
        for word in [
            "emergency",
            "hospital",
            "police",
            "help"
        ]
    ):

           # -------------------------
    # AI fallback
    # -------------------------


        context = """

    Nepal tourism information:

    Popular places:
    Kathmandu, Pokhara, Chitwan, Lumbini,
    Everest Region, Mustang, Rara Lake.

    The chatbot helps with:
    destinations,
    budget,
    hotels,
    transport,
    safety.

    """


        ai_reply = ask_ai(
            user_message,
            context
        )


        if ai_reply:

            return ai_reply



        return (
            "I can help you with Nepal tourism."
        )



    # -------------------------
    # Hotels
    # -------------------------

    if any(
        word in user_message
        for word in [
            "hotel",
            "stay",
            "accommodation"
        ]
    ):

        return (
            "Nepal has many accommodation options:\n\n"
            "• Budget guesthouses\n"
            "• Boutique hotels\n"
            "• Luxury resorts\n\n"
            "Popular areas include Thamel (Kathmandu) "
            "and Lakeside (Pokhara)."
        )



    # -------------------------
    # Safety
    # -------------------------

    if any(
        word in user_message
        for word in [
            "safe",
            "safety",
            "risk"
        ]
    ):

        return (
            "Nepal is generally safe for tourists. "
            "Keep your documents safe, check weather before trekking, "
            "and use registered guides for adventure activities."
        )



    # -------------------------
    # Transport
    # -------------------------

    if any(
        word in user_message
        for word in [
            "transport",
            "bus",
            "flight",
            "taxi"
        ]
    ):

        return (
            "Transportation options in Nepal include:\n\n"
            "• Tourist buses\n"
            "• Domestic flights\n"
            "• Taxis\n"
            "• Ride-sharing services in major cities"
        )



    # -------------------------
    # Default response
    # -------------------------

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
