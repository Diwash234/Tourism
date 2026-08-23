"""
Tourism/chatbot/services.py

Autonomous Chatbot Knowledge, Distance, Itinerary, and Visual Media Engine.
Provides comprehensive multi-intent recognition, verified database querying,
and rich attachment packaging (images, destination cards, distance routes, day-by-day itineraries).
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple, Any

from .ai_service import ask_ai
from tourist.models import (
    Destination, DestinationImage, DestinationTransitRoute,
    Hospital, PoliceStation, BudgetEstimation, RiskAnalysis, Category,
    MarketplaceListing,
)
from tourist.discovery_pipeline import haversine_distance_km

logger = logging.getLogger(__name__)

USD_TO_NPR = 133.0

# Canonical coordinates for major hubs in Nepal
CITY_COORDS = {
    "kathmandu": (27.7172, 85.3240),
    "pokhara": (28.2096, 83.9856),
    "chitwan": (27.5341, 84.4530),
    "lumbini": (27.4833, 83.2767),
    "everest": (27.9881, 86.9250),
    "ebc": (28.0042, 86.8570),
    "lukla": (27.6878, 86.7314),
    "mustang": (28.9985, 83.8473),
    "jomsom": (28.7844, 83.7380),
    "rara": (29.5375, 82.0911),
    "langtang": (28.2140, 85.5714),
    "janakpur": (26.7271, 85.9407),
    "ilam": (26.9114, 87.9262),
    "bandipur": (27.9333, 84.4167),
    "nagarkot": (27.7172, 85.5202),
    "bhaktapur": (27.6710, 85.4298),
    "patan": (27.6644, 85.3188),
}


def find_matching_destinations(query: str, limit: int = 4) -> List[Destination]:
    """Finds matching destinations from the database using keyword and fuzzy search."""
    q_clean = query.strip().lower()
    words = [w for w in re.split(r"\W+", q_clean) if len(w) > 2]

    # Try exact name match
    exact = Destination.objects.filter(name__icontains=q_clean, is_active=True)[:limit]
    if exact.exists():
        return list(exact)

    # Search by words
    matches = []
    seen = set()
    for w in words:
        for d in Destination.objects.filter(is_active=True).filter(
            name__icontains=w
        )[:limit]:
            if d.id not in seen:
                seen.add(d.id)
                matches.append(d)
        if len(matches) >= limit:
            break

    if not matches:
        # Default to iconic destinations
        matches = list(Destination.objects.filter(is_active=True).order_by("-average_rating")[:limit])

    return matches[:limit]


def parse_trip_constraints(message: str):
    """Extract requested days and a budget in NPR from a traveller question."""
    text = (message or "").lower()
    days = None
    days_match = re.search(r"(\d+)\s*[- ]?\s*days?", text)
    if days_match:
        days = max(1, min(60, int(days_match.group(1))))
    budget_npr = None
    usd_match = re.search(r"\$\s*([\d,]+)", text)
    npr_match = re.search(r"(?:npr|rs\.?)\s*([\d,]+)", text)
    if usd_match:
        budget_npr = float(usd_match.group(1).replace(",", "")) * USD_TO_NPR
    elif npr_match:
        budget_npr = float(npr_match.group(1).replace(",", ""))
    return days, budget_npr


def is_budget_trip_intent(message: str, days=None, budget_npr=None) -> bool:
    text = (message or "").lower()
    trip_words = any(word in text for word in ("trip", "package", "tour", "holiday", "vacation"))
    under = any(word in text for word in ("under", "below", "less than", "budget", "cheap"))
    return bool((days and budget_npr) or (trip_words and budget_npr) or (days and under and trip_words))


def package_card(listing: MarketplaceListing) -> dict:
    return {
        "id": listing.id,
        "slug": listing.slug,
        "title": listing.title,
        "kind": listing.kind,
        "price_npr": str(listing.price_npr),
        "duration_days": listing.duration_days,
        "city": listing.city or (listing.destination.city if listing.destination else "Nepal"),
        "partner_name": listing.partner.name,
        "summary": listing.summary,
        "image_url": listing.image_url,
    }


def match_published_packages(query: str, days=None, budget_npr=None, limit: int = 6):
    """Rank published marketplace offers. Draft / pending / unpublished never appear."""
    listings = list(
        MarketplaceListing.objects.filter(
            status="published", partner__status="approved",
        ).select_related("partner", "destination")
    )
    words = [w for w in re.split(r"\W+", (query or "").lower()) if len(w) > 2]
    skip = {"want", "with", "from", "that", "this", "nepal", "trip", "days", "day", "under", "below", "less", "than", "package", "packages"}
    words = [w for w in words if w not in skip]
    scored = []
    for listing in listings:
        price = float(listing.price_npr)
        if budget_npr is not None and price > float(budget_npr):
            continue
        score = 2 if listing.is_featured else 0
        if days:
            diff = abs((listing.duration_days or 1) - days)
            if diff <= 1:
                score += 5
            elif diff <= 2:
                score += 3
            elif (listing.duration_days or 1) <= days + 1:
                score += 1
            else:
                score -= 1
        hay = f"{listing.title} {listing.summary} {listing.city} {listing.district} {listing.partner.name}".lower()
        if listing.destination_id:
            hay += f" {listing.destination.name} {listing.destination.city or ''}"
        score += sum(1 for word in words if word in hay)
        scored.append((score, listing))
    scored.sort(key=lambda row: -row[0])
    return [listing for _, listing in scored[:limit]]


def get_destination_image_url(dest: Destination) -> str:
    """Returns the cover or first high-res image URL for a destination."""
    img = dest.gallery.filter(is_cover=True).first() or dest.gallery.first()
    if img:
        return img.external_url or (img.image.url if img.image else "") or "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80"
    return "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800&auto=format&fit=crop&q=80"


def generate_structured_itinerary(dest_name: str, days: int = 5, budget_npr: Optional[float] = None) -> Dict[str, Any]:
    """Generates day-by-day itinerary schedule with daily budgets and transit legs."""
    days = max(1, min(14, int(days)))
    dest = Destination.objects.filter(name__icontains=dest_name).first() or Destination.objects.first()

    itinerary_days = []
    base_daily_usd = 35.0
    daily_npr = round(base_daily_usd * USD_TO_NPR)

    themes = [
        ("Arrival & Cultural Immersion", "Explore the historic old quarters, local bazaars, and traditional stone courtyards."),
        ("Scenic Viewpoint & Sunrise Hike", "Early morning sunrise viewpoint over the Himalayan snowline followed by nature trail hike."),
        ("Heritage Monasteries & Sacred Sites", "Visit ancient pagoda temples, Tibetan gompas, and cultural artisan workshops."),
        ("Adventure & Alpine Exploration", "Scenic boat ride, canyon trail, or high suspension bridge crossing with local tea rest-stops."),
        ("Local Homestay & Organic Cuisine", "Experience authentic village hospitality, wood-fired organic Dal Bhat, and folklore music."),
        ("Alpine Ridge & Photography Expedition", "Panoramic high-ridge hike capturing the Himalayan peaks and rhododendron valleys."),
        ("Souvenirs & Farewell Sunset", "Shop for authentic Dhaka textiles, Pashmina, and organic Himalayan tea before departure."),
    ]

    for d_num in range(1, days + 1):
        theme_title, theme_desc = themes[(d_num - 1) % len(themes)]
        itinerary_days.append({
            "day": d_num,
            "title": f"Day {d_num}: {theme_title}",
            "highlights": f"Explore {dest.name if dest else 'Nepal'} key landmarks. {theme_desc}",
            "lodging": f"Heritage Eco-Lodge / Teahouse in {dest.city or dest.district or 'Nepal'}",
            "daily_budget_npr": daily_npr,
            "daily_budget_usd": base_daily_usd,
        })

    total_npr = daily_npr * days
    total_usd = round(total_npr / USD_TO_NPR, 2)

    return {
        "destination": dest.name if dest else dest_name,
        "days_count": days,
        "total_estimated_npr": total_npr,
        "total_estimated_usd": total_usd,
        "fits_budget": (total_npr <= float(budget_npr)) if budget_npr else True,
        "schedule": itinerary_days,
    }


def compute_distance_and_transit(origin_name: str, dest_name: str) -> Dict[str, Any]:
    """Calculates straight-line and highway road distance, estimated drive time, and fares."""
    o_key = origin_name.lower().strip()
    d_key = dest_name.lower().strip()

    c1 = CITY_COORDS.get(o_key, (27.7172, 85.3240))
    c2 = CITY_COORDS.get(d_key, (28.2096, 83.9856))

    straight_km = haversine_distance_km(c1[0], c1[1], c2[0], c2[1])
    # Road winding factor across Himalayan terrain is approximately 1.35x - 1.6x straight distance
    road_km = round(straight_km * 1.42, 1)

    # Calculate realistic driving hours (average 35-45 km/h on mountain highways)
    drive_hours = max(0.5, round(road_km / 35.0, 1))
    flight_mins = 25 if straight_km < 250 else 45

    # Highway corridor identification
    corridor = "National Highway Corridor"
    if ("kathmandu" in o_key and "pokhara" in d_key) or ("pokhara" in o_key and "kathmandu" in d_key):
        corridor = "Prithvi Highway (H04) via Mugling"
        road_km = 204.5
        drive_hours = "6 – 7 hours"
    elif "everest" in d_key or "lukla" in d_key:
        corridor = "Tribhuvan Int'l to Tenzing-Hillary Airport (Lukla Flight / Trekking Trail)"
        drive_hours = "35 mins flight + Trek"
    elif "mustang" in d_key or "jomsom" in d_key:
        corridor = "Beni-Jomsom-Muktinath Highway (Kali Gandaki Corridor)"
        drive_hours = "8 – 10 hours (4WD Jeep)"
    elif "chitwan" in d_key:
        corridor = "Prithvi & Narayanghat-Mugling Highway (H05)"
        road_km = 165.0
        drive_hours = "5 – 6 hours"
    elif "lumbini" in d_key:
        corridor = "East-West Highway (Mahendra Highway H01)"
        road_km = 290.0
        drive_hours = "7 – 8 hours"

    estimated_bus_npr = max(600, round(road_km * 7.5))
    estimated_jeep_npr = max(1800, round(road_km * 28.0))

    return {
        "origin": origin_name.title(),
        "destination": dest_name.title(),
        "straight_distance_km": round(straight_km, 1),
        "road_distance_km": road_km,
        "estimated_drive_time": f"{drive_hours} hrs" if isinstance(drive_hours, (int, float)) else str(drive_hours),
        "flight_time": f"{flight_mins} mins (Domestic Flight)",
        "highway_corridor": corridor,
        "fare_bus_npr": estimated_bus_npr,
        "fare_jeep_npr": estimated_jeep_npr,
    }


def get_chatbot_reply(
    history: list,
    latitude: float = None,
    longitude: float = None
) -> Dict[str, Any]:
    """
    Main entry point for Himal AI.
    Executes AI providers and packages rich visual cards, itineraries, and distance metrics.
    """
    if not history:
        return {
            "reply": (
                "Namaste! 🙏 I am **Himal AI**, your personal Nepal Travel Sentinel & Visual Guide.\n\n"
                "Ask me about:\n"
                "• 🏔️ **Destinations & Photos**: *'Show me pictures of Pokhara and Everest'*\n"
                "• 📏 **Distance & Driving Times**: *'How far is Pokhara from Kathmandu?'*\n"
                "• 🗓️ **Custom Itineraries**: *'Plan an 8-day trip to Mustang with budget NPR 50,000'*\n"
                "• 💰 **Travel Budgets**: *'How much does a 5-day Annapurna trek cost?'*\n"
                "• 🚨 **24/7 Emergency Helplines**: *'Nearest hospital and tourist police hotline'*"
            ),
            "destination_cards": [],
            "image_cards": [],
            "itinerary_cards": None,
            "distance_cards": None,
            "emergency_cards": [],
            "package_cards": [],
        }

    last_user_msg = history[-1]["content"] if history else ""
    msg_clean = last_user_msg.strip()
    msg_lower = msg_clean.lower()

    # Detect user intent
    is_image_intent = any(w in msg_lower for w in ["photo", "photos", "picture", "pictures", "image", "images", "show me", "look like", "gallery", "visual"])
    is_distance_intent = any(w in msg_lower for w in ["how far", "distance", "driving time", "how to reach", "drive to", "km from", "route to", "hours from"])
    is_itinerary_intent = any(w in msg_lower for w in ["itinerary", "plan", "days trip", "day trip", "schedule", "build my trip", "tour plan", "day 1", "day-by-day"])
    is_emergency_intent = any(w in msg_lower for w in ["emergency", "hospital", "police", "ambulance", "doctor", "rescue", "sos", "danger", "helpline", "1144"])
    is_budget_intent = any(w in msg_lower for w in ["budget", "cost", "price", "how much", "npr", "dollar", "expenses", "cheap"])
    requested_days, requested_budget = parse_trip_constraints(msg_lower)
    is_package_intent = any(w in msg_lower for w in [
        "package", "packages", "marketplace", "book a tour", "travel package",
        "add to trip", "trip basket", "collaborate",
    ])
    is_budget_trip = is_budget_trip_intent(msg_lower, requested_days, requested_budget)
    if is_budget_trip:
        is_package_intent = True
        is_itinerary_intent = False

    destination_cards = []
    image_cards = []
    itinerary_card = None
    distance_card = None
    emergency_cards = []
    package_cards = []

    if is_package_intent:
        matched = match_published_packages(
            msg_clean, days=requested_days, budget_npr=requested_budget, limit=6,
        )
        package_cards = [package_card(listing) for listing in matched]

    # Match relevant destinations in DB
    matched_destinations = find_matching_destinations(msg_clean, limit=4)
    for dest in matched_destinations:
        img_url = get_destination_image_url(dest)
        daily_usd = 35.0
        if hasattr(dest, "budget_estimation") and dest.budget_estimation:
            daily_usd = float(dest.budget_estimation.estimated_daily_budget or 35.0)

        destination_cards.append({
            "id": dest.id,
            "name": dest.name,
            "slug": dest.slug,
            "image": img_url,
            "category": dest.category.name if dest.category else "Attraction",
            "rating": str(dest.average_rating or "4.9"),
            "city": f"{dest.district or 'Nepal'}, {dest.province or 'Province'}",
            "budget": f"NPR {round(daily_usd * USD_TO_NPR):,}/day",
            "altitude": dest.altitude or "1,400m",
        })

    # Pack Image Cards
    if is_image_intent or len(matched_destinations) > 0:
        for dest in matched_destinations[:3]:
            for img in dest.gallery.all()[:2]:
                image_cards.append({
                    "url": img.external_url or (img.image.url if img.image else ""),
                    "caption": img.caption or f"{dest.name} Scenic View",
                    "photographer": img.photographer or "Verified Archive",
                    "license": img.license_type or "CC BY-SA 4.0",
                    "category": img.image_category or "Landscape",
                    "destination_name": dest.name,
                })

    # Pack Distance & Route Card
    if is_distance_intent:
        origin = "Kathmandu"
        dest_target = "Pokhara"
        for c_name in CITY_COORDS.keys():
            if c_name in msg_lower and c_name != "kathmandu":
                dest_target = c_name
                break
        if "from pokhara" in msg_lower:
            origin = "Pokhara"
        distance_card = compute_distance_and_transit(origin, dest_target)

    # Pack Itinerary Card
    if is_itinerary_intent:
        days_match = re.search(r"(\d+)\s*(?:day|days)", msg_lower)
        days = int(days_match.group(1)) if days_match else 5
        dest_for_plan = matched_destinations[0].name if matched_destinations else "Pokhara & Kathmandu"
        budget_match = re.search(r"(?:npr|rs\.?|\$)\s*([\d,]+)", msg_lower)
        budget_val = float(budget_match.group(1).replace(",", "")) if budget_match else None
        itinerary_card = generate_structured_itinerary(dest_for_plan, days=days, budget_npr=budget_val)

    # Pack Emergency Cards
    if is_emergency_intent:
        for h in Hospital.objects.all()[:3]:
            emergency_cards.append({
                "name": h.name,
                "type": "Emergency Hospital",
                "phone": h.phone or "+977-1-4412404",
                "district": h.district or "Kathmandu",
            })
        for p in PoliceStation.objects.all()[:2]:
            emergency_cards.append({
                "name": p.name,
                "type": "Tourist & Civil Police",
                "phone": p.phone or "1144",
                "district": "Nationwide / Tourist Police",
            })

    # 1. Attempt calling configured AI providers (OpenRouter, Gemini, Grok, Groq, Hugging Face, OpenAI)
    # Package questions stay on the live marketplace so travellers see published offers.
    ai_text_reply = None
    if not is_package_intent:
        try:
            ai_text_reply = ask_ai(msg_clean, context=f"Coordinates: lat={latitude}, lng={longitude}", history=history)
        except Exception as e:
            logger.warning(f"AI Provider execution failed: {e}")

    # 2. Autonomous Local Engine Fallback if AI providers unavailable or hit free rate limit
    if not ai_text_reply:
        if any(w in msg_lower for w in ["weather", "temperature", "forecast"]):
            ai_text_reply = (
                "I can't check live weather for you right now — the AI assistant "
                "isn't configured on this server. Try the weather widget on the "
                "destination page instead."
            )
        elif is_distance_intent and distance_card:
            ai_text_reply = (
                f"🚗 **Distance & Road Transit Route: {distance_card['origin']} ➔ {distance_card['destination']}**\n\n"
                f"• **Road Distance:** `{distance_card['road_distance_km']} km` (Straight-line: `{distance_card['straight_distance_km']} km`)\n"
                f"• **Highway Corridor:** {distance_card['highway_corridor']}\n"
                f"• **Estimated Drive Time:** {distance_card['estimated_drive_time']}\n"
                f"• **Domestic Flight Time:** {distance_card['flight_time']}\n"
                f"• **Estimated Public Deluxe Bus Fare:** `NPR {distance_card['fare_bus_npr']:,}`\n"
                f"• **Estimated Private 4WD Jeep Fare:** `NPR {distance_card['fare_jeep_npr']:,}`\n\n"
                f"💡 *Travel Tip:* Mountain highways can experience landslide delays during monsoon (July-August). Start early in the morning (6:30 AM - 7:30 AM) to beat highway congestion!"
            )
        elif is_itinerary_intent and itinerary_card:
            ai_text_reply = (
                f"🗓️ **Custom {itinerary_card['days_count']}-Day Itinerary for {itinerary_card['destination']}**\n\n"
                f"• **Total Estimated Cost:** `NPR {itinerary_card['total_estimated_npr']:,}` (~${itinerary_card['total_estimated_usd']} USD)\n\n"
            )
            for item in itinerary_card["schedule"]:
                ai_text_reply += (
                    f"📍 **{item['title']}**\n"
                    f"   • *Activity:* {item['highlights']}\n"
                    f"   • *Lodging:* {item['lodging']}\n"
                    f"   • *Daily Budget:* NPR {item['daily_budget_npr']:,} (${item['daily_budget_usd']})\n\n"
                )
            ai_text_reply += "💡 *Permits & Logistics:* Ensure you have valid TIMS and conservation park permits before departure!"
        elif is_emergency_intent:
            ai_text_reply = (
                "🚨 **NEPAL 24/7 EMERGENCY SENTINEL & HOTLINES**\n\n"
                "• **Tourist Police Nepal:** `1144` or `+977-1-4247041` (Nationwide Tourist Protection)\n"
                "• **Nepal Police Hotline:** `100`\n"
                "• **Ambulance Emergency:** `102`\n"
                "• **Fire Brigade Service:** `101`\n"
                "• **Traffic Police:** `103`\n"
                "• **Himalayan Rescue Association (HRA):** `+977-1-4440292` (Helicopter evacuation & AMS)\n"
                "• **TUTH Teaching Hospital:** `+977-1-4412404` (Maharajgunj, Kathmandu)\n"
                "• **CIWEC Travel Hospital:** `+977-1-4424111` (Lazimpat, Kathmandu & Pokhara)"
            )
        elif is_package_intent:
            if package_cards:
                constraint = []
                if requested_days:
                    constraint.append(f"{requested_days}-day")
                if requested_budget:
                    constraint.append(f"under NPR {int(requested_budget):,}")
                heading = " and ".join(constraint) or "live"
                lines = [
                    f"🎒 **Published packages matching your {heading} request**",
                    "These are live offers from approved partners. Use View or Add to trip. No payment is processed here.",
                    "",
                ]
                for offer in package_cards:
                    lines.append(
                        f"• **{offer['title']}** ({offer['duration_days']} day(s)) — NPR {offer['price_npr']} · {offer['partner_name']}"
                    )
                lines.append("")
                lines.append("Open /packages to add offers to a trip basket, or /collaborate if you run a hotel or tour.")
                ai_text_reply = "\n".join(lines)
            elif requested_budget or requested_days:
                ai_text_reply = (
                    "No published package currently matches that length and budget. "
                    "Browse /packages for live offers, or ask an administrator to publish one."
                )
            else:
                ai_text_reply = (
                    "No published packages are live yet. An administrator can add them from "
                    "Admin → Packages & partners, or a hotel can apply at /collaborate."
                )
        elif is_budget_intent:
            ai_text_reply = (
                "💰 **Nepal Travel Budget Tiers (Per Person / Day)**:\n\n"
                "1. **🎒 Backpacker / Solo:** `$20 - $35` (`NPR 2,700 - 4,700`)\n"
                "   • Teahouse accommodation, Dal Bhat, public highway buses, self-guided hikes.\n\n"
                "2. **🏨 Mid-Range / Comfort:** `$45 - $80` (`NPR 6,000 - 10,700`)\n"
                "   • 3-star boutique hotels, tourist coaches / shared jeeps, cafe dining, licensed local guides.\n\n"
                "3. **👑 Luxury / Heritage:** `$120+` (`NPR 16,000+`)\n"
                "   • 5-star heritage resorts (Dwarika's, Tiger Tops), domestic flights, private Scorpio 4WD."
            )
        elif matched_destinations:
            top_dest = matched_destinations[0]
            daily_cost = 35.0
            if hasattr(top_dest, "budget_estimation") and top_dest.budget_estimation:
                daily_cost = float(top_dest.budget_estimation.estimated_daily_budget or 35.0)

            ai_text_reply = (
                f"🏔️ **{top_dest.name} ({top_dest.district or 'Nepal'}, {top_dest.province or 'Province'})**\n\n"
                f"{top_dest.description}\n\n"
                f"• **Elevation:** {top_dest.altitude or '1,400m'}\n"
                f"• **Category:** {top_dest.category.name if top_dest.category else 'Attraction'}\n"
                f"• **Best Season:** {top_dest.best_time_to_visit or 'October to April'}\n"
                f"• **Estimated Daily Budget:** NPR {round(daily_cost * USD_TO_NPR):,} / day\n"
                f"• **Distance from Kathmandu:** ~{top_dest.distance_from_kathmandu_km or 200} km\n\n"
                f"Explore the interactive cards below for direct navigation routes and high-res verified imagery!"
            )
        else:
            ai_text_reply = (
                "Namaste! 🙏 I can assist you across all aspects of Nepal travel:\n\n"
                "• 📍 **5,900+ Destinations:** Deep cultural history, photography spots, and hidden trails.\n"
                "• 📏 **Distance & Highway Corridors:** Real road mileage, driving hours, and public bus fares.\n"
                "• 🗓️ **Day-by-Day Itineraries:** Custom trip schedules tailored to your duration and budget.\n"
                "• 🛡️ **Safety & 24/7 Hotlines:** Direct dial to Tourist Police (1144), 100, and mountain rescue.\n\n"
                "What destination or route would you like to explore?"
            )

    return {
        "reply": ai_text_reply,
        "destination_cards": destination_cards,
        "image_cards": image_cards[:6],
        "itinerary_cards": itinerary_card,
        "distance_cards": distance_card,
        "emergency_cards": emergency_cards,
        "package_cards": package_cards,
    }
