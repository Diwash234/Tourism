import random
import logging
from .ai_service import ask_ai

logger = logging.getLogger(__name__)


def get_chatbot_reply(
    history,
    latitude=None,
    longitude=None
):
    if not history:
        return (
            "Namaste! 🙏 I am Himal AI, your personal Nepal Tourism Assistant.\n\n"
            "Ask me about:\n"
            "• 🏔️ Himalayan Treks & Hidden Destinations\n"
            "• 💰 Real-time Travel Budget Estimations\n"
            "• 🏨 Handpicked Hotels & Homestays\n"
            "• 🚗 Turn-by-Turn Routes & Navigation\n"
            "• 🚨 24/7 Emergency Helplines & Hospitals\n"
            "• 🗣️ Local Language & Cultural Phrases"
        )

    last_user_msg = history[-1]["content"] if history else ""
    user_message_lower = last_user_msg.lower().strip()

    # 1. Try configured AI providers (Grok, Gemini, Groq, HuggingFace, OpenAI)
    try:
        ai_reply = ask_ai(last_user_msg, context=f"User Coords: lat={latitude}, lng={longitude}", history=history)
        if ai_reply:
            return ai_reply
    except Exception as e:
        logger.warning(f"AI Provider error: {e}")

    # 2. Intelligent Smart Rule / Knowledge Engine fallback

    # Weather / forecast check
    if any(w in user_message_lower for w in ["weather", "temperature", "forecast"]):
        return (
            "I can't check live weather for you right now — the AI assistant "
            "isn't configured on this server. Try the weather widget on the "
            "destination page instead."
        )

    # Greetings
    if any(w in user_message_lower for w in ["hi", "hello", "hey", "namaste", "namaskar", "tashi delek", "salam"]):
        return (
            "Namaste! 🙏 Welcome to Nepal.\n\n"
            "I'm here to help you plan your journey across all 7 provinces of Nepal — from the world's highest peaks in Everest to the serene lakes of Pokhara and the jungles of Chitwan.\n\n"
            "How can I assist your trip today?"
        )

    # Emergency / SOS / Police / Hospital
    if any(w in user_message_lower for w in ["emergency", "hospital", "police", "ambulance", "doctor", "rescue", "sos", "accident", "danger", "help"]):
        return (
            "🚨 **NEPAL EMERGENCY & HELPLINES (24/7)**\n\n"
            "• **Tourist Police Nepal:** `1144` or `+977-1-4247041` (Bhrikutimandap / Nationwide)\n"
            "• **Nepal Police:** `100`\n"
            "• **Ambulance Service:** `102`\n"
            "• **Fire Brigade:** `101`\n"
            "• **Traffic Police:** `103`\n"
            "• **Himalayan Rescue Association (HRA):** `+977-1-4440292` (Altitude & Mountain Rescue)\n"
            "• **Tribhuvan University Teaching Hospital (TUTH):** `+977-1-4412404` (Kathmandu)\n"
            "• **CIWEC Travel Hospital:** `+977-1-4424111` (Kathmandu / Pokhara)\n\n"
            "Tip: You can also tap the red **Emergency** button in the top menu to view nearest hospitals and police stations on the live GPS map."
        )

    # Budget / Expenses / Cost
    if any(w in user_message_lower for w in ["budget", "cost", "price", "expense", "how much", "npr", "dollar", "cheap", "expensive"]):
        return (
            "💰 **Nepal Travel Budget Guide (Per Person/Day)**:\n\n"
            "1. **🎒 Backpacker / Budget:** $20 - $35 (NPR 2,700 - 4,700)\n"
            "   • Local teahouses/hostels, Dal Bhat, public buses, local entry fees.\n\n"
            "2. **🏨 Mid-Range / Comfort:** $45 - $80 (NPR 6,000 - 10,700)\n"
            "   • 3-star boutique hotels, tourist bus / shared jeep, cozy cafes, guided day tours.\n\n"
            "3. **👑 Luxury / Deluxe:** $120+ (NPR 16,000+)\n"
            "   • 5-star heritage resorts (Dwarika's, Marriott, Tiger Tops), domestic flights, private 4WD SUVs.\n\n"
            "You can use our **Budget Estimator** tab to get an AI-predicted cost calculation customized by duration, group size, and destination!"
        )

    # Everest / EBC / Trekking
    if any(w in user_message_lower for w in ["everest", "ebc", "khumbu", "namche", "gokyo", "trek", "trekking", "kala patthar"]):
        return (
            "🏔️ **Everest Region Trekking Highlights**:\n\n"
            "• **Everest Base Camp (5,364m):** Iconic 12-14 day trek starting with a flight to Lukla (Tenzing-Hillary Airport).\n"
            "• **Key Stops:** Phakding, Namche Bazaar (Sherpa Capital & Acclimatization), Tengboche Monastery, Dingboche, Gorak Shep, and Kala Patthar (5,545m panoramic summit).\n"
            "• **Required Permits:** Sagarmatha National Park Permit (NPR 3,000) & Khumbu Pasang Lhamu Rural Municipality Permit (NPR 2,000).\n"
            "• **Best Season:** March-May (Spring) & September-November (Autumn).\n"
            "• **Health Note:** Spend at least 2 acclimatization nights (Namche & Dingboche) to avoid AMS."
        )

    # Pokhara / Annapurna / ABC
    if any(w in user_message_lower for w in ["pokhara", "annapurna", "abc", "phewa", "sarangkot", "poon hill", "mardihimal", "mardi"]):
        return (
            "🌊 **Pokhara & Annapurna Region Highlights**:\n\n"
            "• **Phewa Lake & Tal Barahi:** Scenic boat rides with Annapurna reflection.\n"
            "• **Sarangkot Viewpoint:** Sunrise over Machhapuchhre (Fishtail) & Dhaulagiri.\n"
            "• **Annapurna Base Camp (4,130m):** 7-10 day spectacular sanctuary trek surrounded by 8,000m giants.\n"
            "• **Ghorepani Poon Hill (3,210m):** 4-5 day easy-moderate classic trek with world-famous sunrise.\n"
            "• **Adventure Activities:** Paragliding from Sarangkot, Zip-flyer, Bungee jumping, and Ultralight flights."
        )

    # Kathmandu Valley
    if any(w in user_message_lower for w in ["kathmandu", "pashupatinath", "boudhanath", "swayambhunath", "bhaktapur", "patan", "thamel"]):
        return (
            "🏛️ **Kathmandu Valley UNESCO World Heritage Sites**:\n\n"
            "• **Pashupatinath Temple:** Sacred Hindu temple dedicated to Lord Shiva on the Bagmati River.\n"
            "• **Boudhanath Stupa:** One of the largest spherical Buddhist stupas in the world.\n"
            "• **Swayambhunath (Monkey Temple):** Ancient hilltop stupa overlooking the valley.\n"
            "• **Kathmandu, Patan & Bhaktapur Durbar Squares:** Magnificent ancient Newari palaces, pagoda temples, and stone architecture.\n"
            "• **Thamel:** Bustling tourist hub for gear shops, vibrant restaurants, live music, and cafes."
        )

    # Chitwan / Bardiya / Safari
    if any(w in user_message_lower for w in ["chitwan", "bardiya", "safari", "wildlife", "rhino", "tiger", "national park"]):
        return (
            "🐅 **Nepal Wildlife & Jungle Safaris**:\n\n"
            "• **Chitwan National Park (UNESCO):** Home to One-Horned Rhinoceros, Bengal Tigers, Gharial crocodiles, and 500+ bird species. Activities: Jeep safari, dugout canoe rides, Tharu cultural dance.\n"
            "• **Bardiya National Park:** Pristine and untamed western wilderness with highest tiger sighting probability and wild elephant herds.\n"
            "• **Best Time:** October to March (dry and pleasant)."
        )

    # Lumbini
    if any(w in user_message_lower for w in ["lumbini", "buddha", "maya devi", "birthplace"]):
        return (
            "☸️ **Lumbini - Birthplace of Lord Buddha**:\n\n"
            "• **Maya Devi Temple & Sacred Garden:** The exact historical birthplace of Siddhartha Gautama in 623 BC.\n"
            "• **Ashoka Pillar:** Inscribed pillar erected by Emperor Ashoka in 249 BC.\n"
            "• **Monastic Zones:** International monasteries built by Thailand, Germany, China, Japan, Myanmar, and Sri Lanka.\n"
            "• **Peace Flame:** Eternal peace flame burning continuously since 1986."
        )

    # Weather / live forecast query check when AI provider is not configured
    if any(w in user_message_lower for w in ["weather", "temperature", "forecast"]) and not ask_ai(last_user_msg):
        return (
            "I can't check live weather for you right now — the AI assistant "
            "isn't configured on this server. Try the weather widget on the "
            "destination page instead."
        )

    # Navigation / Routes / Transport
    if any(w in user_message_lower for w in ["route", "how to reach", "bus", "flight", "taxi", "transport", "drive", "navigation"]):
        return (
            "🚗 **Transportation in Nepal**:\n\n"
            "• **Tourist Coaches:** Daily AC deluxe coaches between Kathmandu ⇄ Pokhara ⇄ Chitwan ⇄ Lumbini (NPR 1,200 - 2,500).\n"
            "• **Domestic Flights:** Buddha Air, Yeti Airlines, Tara Air connecting Kathmandu to Pokhara (25 min), Bharatpur (20 min), Lukla (35 min), Biratnagar, and Nepalgunj.\n"
            "• **Ride-Sharing in Cities:** Pathao and InDrive mobile apps work seamlessly in Kathmandu and Pokhara.\n"
            "• **Private 4WD Jeeps:** Recommended for rugged routes (Mustang, Manang, Rara, Langtang Syabrubesi)."
        )

    # Default friendly helpful response
    return (
        "I can help you with everything you need for Nepal:\n\n"
        "• 📍 **Destinations:** In-depth guide to all 77 districts and hidden trekking trails.\n"
        "• 💵 **Budget Estimator:** Personalized cost calculations based on actual travel expenditures.\n"
        "• 🗺️ **Navigation & Routes:** Turn-by-turn game-HUD map with distance and waypoint guidance.\n"
        "• 🛡️ **Safety & Risk:** Live hazard indices, emergency contacts, and altitude guidelines.\n"
        "• 🗣️ **Language Translation:** Instant Nepali and ethnic dialect phrase translations.\n\n"
        "Please ask me any specific question about your trip!"
    )
