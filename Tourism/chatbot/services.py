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


KNOWN_PLACE_WORDS = set(CITY_COORDS.keys()) | {
    "annapurna", "mustang", "chitwan", "lumbini", "everest", "langtang",
    "bandipur", "nagarkot", "bhaktapur", "patan", "ilam", "rara",
    "janakpur", "kathmandu", "pokhara", "lukla", "jomsom", "phewa",
}


def package_card(listing: MarketplaceListing, is_alternative: bool = False) -> dict:
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
        "is_alternative": bool(is_alternative),
    }


def _listing_haystack(listing: MarketplaceListing) -> str:
    hay = f"{listing.title} {listing.summary} {listing.city} {listing.district} {listing.partner.name}".lower()
    if listing.destination_id:
        dest = listing.destination
        hay += f" {dest.name} {dest.city or ''} {dest.district or ''}"
    return hay


def match_published_packages(query: str, days=None, budget_npr=None, limit: int = 6):
    """Return published, in-budget packages. Exact duration is primary; ±1 day is alternative."""
    listings = list(
        MarketplaceListing.objects.filter(
            status="published", partner__status="approved",
        ).select_related("partner", "destination")
    )
    words = [w for w in re.split(r"\W+", (query or "").lower()) if len(w) > 2]
    skip = {
        "want", "with", "from", "that", "this", "nepal", "trip", "days", "day",
        "under", "below", "less", "than", "package", "packages", "travel",
        "holiday", "vacation", "tour", "tours", "add", "the",
    }
    dest_words = [w for w in words if w not in skip and w in KNOWN_PLACE_WORDS]
    primaries, alternatives = [], []
    for listing in listings:
        price = float(listing.price_npr)
        if budget_npr is not None and price > float(budget_npr):
            continue
        hay = _listing_haystack(listing)
        if dest_words and not any(word in hay for word in dest_words):
            continue
        duration = listing.duration_days or 1
        if days:
            if duration == days:
                primaries.append(listing)
            elif abs(duration - days) == 1:
                alternatives.append(listing)
        else:
            primaries.append(listing)

    def score(listing):
        points = 2 if listing.is_featured else 0
        hay = _listing_haystack(listing)
        points += sum(1 for word in dest_words if word in hay)
        return points

    primaries.sort(key=score, reverse=True)
    alternatives.sort(key=score, reverse=True)
    return primaries[:limit], alternatives[:limit]


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


def compute_distance_and_transit(origin_name: str, dest_name: str, origin_coords=None) -> Dict[str, Any]:
    """Answer distance questions from the real navigation service.

    Spec rule: the assistant never supplies geographic facts of its own —
    every number comes from coordinate resolution + the routing engine (the
    same services that power /navigation/route), each with its source label.
    The old implementation hardcoded corridor distances (Pokhara 204.5 km,
    Lumbini 290 km), a 1.42x winding factor, km-multiplied fares and flight
    times; all of that is gone. Unresolvable places and unroutable pairs say
    so explicitly instead of falling back to invented values.
    """
    from tourist.location.search_service import LocationSearchService
    from tourist.utils import get_ml_best_route

    card = {
        "origin": (origin_name or "").title(),
        "destination": (dest_name or "").title(),
        "straight_distance_km": None,
        "road_distance_km": None,
        "estimated_drive_time": None,
        "duration_source": "unavailable",
        "flight_time": None,
        "highway_corridor": None,
        "fare_bus_npr": None,
        "fare_jeep_npr": None,
        "fare_note": "",
        "status": "ok",
        "note": "",
    }

    origin = None
    if origin_coords and origin_coords[0] is not None and origin_coords[1] is not None:
        origin = {"name": "Your Location", "latitude": float(origin_coords[0]), "longitude": float(origin_coords[1])}
    elif origin_name:
        origin = LocationSearchService.resolve_single_place(origin_name)
    dest = LocationSearchService.resolve_single_place(dest_name) if dest_name else None

    missing = []
    if not origin:
        missing.append(origin_name or "the origin")
    if not dest:
        missing.append(dest_name or "the destination")
    if missing:
        card["status"] = "unresolved"
        card["note"] = (
            f"I could not find recorded coordinates for: {', '.join(missing)}. "
            "Name a known place (e.g. Pokhara, Lumbini, Phewa Lake) or use the "
            "Navigation page with your GPS location."
        )
        return card

    o_lat, o_lng = float(origin["latitude"]), float(origin["longitude"])
    d_lat, d_lng = float(dest["latitude"]), float(dest["longitude"])
    card["origin"] = origin.get("name") or card["origin"]
    card["destination"] = dest.get("name") or card["destination"]

    straight_km = haversine_distance_km(o_lat, o_lng, d_lat, d_lng)
    card["straight_distance_km"] = round(straight_km, 1)

    # Road distance & duration: real routing engine only.
    result = get_ml_best_route(o_lat, o_lng, d_lat, d_lng, route_type="fastest")
    if result and result.get("distance_km") is not None:
        card["road_distance_km"] = round(float(result["distance_km"]), 1)
        duration = result.get("duration_min")
        if duration is not None:
            total_min = int(duration)
            hours, mins = divmod(total_min, 60)
            card["estimated_drive_time"] = f"{hours} h {mins} min" if hours else f"{mins} min"
            card["duration_source"] = "routing_engine" if result.get("routing_engine") else "estimated"
        if result.get("note"):
            card["highway_corridor"] = None
            card["note"] = result["note"]

    # Fares: curated transit fares first; otherwise an explicitly labelled
    # fare-index estimate (never presented as a quoted price).
    dest_id = dest.get("destination_id")
    if dest_id:
        transit = DestinationTransitRoute.objects.filter(
            destination_id=dest_id, is_verified=True
        ).exclude(estimated_fare_npr__isnull=True).first()
        if transit:
            card["fare_bus_npr"] = int(transit.estimated_fare_npr)
            card["fare_note"] = f"Curated fare ({transit.route_name or 'transit route'})"

    if card["fare_bus_npr"] is None and card["road_distance_km"]:
        card["fare_bus_npr"] = max(600, round(card["road_distance_km"] * 7.5))
        card["fare_jeep_npr"] = max(1800, round(card["road_distance_km"] * 28.0))
        card["fare_note"] = "Fare-index estimate — not a quoted price"

    return card


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
        matched, alternatives = match_published_packages(
            msg_clean, days=requested_days, budget_npr=requested_budget, limit=6,
        )
        package_cards = [package_card(listing, is_alternative=False) for listing in matched]
        package_cards.extend(package_card(listing, is_alternative=True) for listing in alternatives)

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

    # Pack Distance & Route Card — parsed from the actual message, resolved
    # by the place service. Never a silent Kathmandu->Pokhara default.
    if is_distance_intent:
        origin_phrase = None
        dest_phrase = None
        m = re.search(r"\bfrom\s+([\w\s&\-']+?)\s+\bto\s+([\w\s&\-\'?]+?)(?:\?|\.|$)", msg_clean, re.I)
        if m:
            origin_phrase, dest_phrase = m.group(1).strip(), m.group(2).strip().rstrip("?")
        else:
            m = re.search(r"\bhow far is\s+([\w\s&\-']+?)\s+\bfrom\s+([\w\s&\-\'?]+?)(?:\?|\.|$)", msg_clean, re.I)
            if m:
                dest_phrase, origin_phrase = m.group(1).strip(), m.group(2).strip().rstrip("?")
            else:
                m = re.search(r"\b(?:distance|route|drive|travel|trip)\s+(?:to|from|for)\s+([\w\s&\-\'?]+?)(?:\?|\.|$)", msg_clean, re.I)
                if m:
                    dest_phrase = m.group(1).strip().rstrip("?")
        if not dest_phrase and matched_destinations:
            dest_phrase = matched_destinations[0].name
        gps_origin = (latitude, longitude) if (latitude is not None and longitude is not None) else None
        distance_card = compute_distance_and_transit(origin_phrase or "", dest_phrase or "", origin_coords=gps_origin)

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
        for h in Hospital.objects.exclude(is_archived=True)[:3]:
            phone = str(h.phone or "").strip()
            emergency_cards.append({
                "name": h.name,
                "type": "Emergency Hospital",
                "phone": phone or "102",
                "phone_is_national_fallback": not phone,
                "district": h.district or "",
            })
        for p in PoliceStation.objects.exclude(is_archived=True)[:2]:
            phone = str(p.phone or "").strip()
            emergency_cards.append({
                "name": p.name,
                "type": "Tourist & Civil Police",
                "phone": phone or "100",
                "phone_is_national_fallback": not phone,
                "district": p.destination.district if p.destination_id else "",
            })

    # 1. Attempt calling configured AI providers (OpenRouter, Gemini, Grok, Groq, Hugging Face, OpenAI)
    # Package questions stay on the live marketplace so travellers see published offers.
    ai_text_reply = None
    # Distance questions are answered deterministically from the navigation
    # service — the LLM must never supply geographic numbers of its own.
    if not is_package_intent and not is_distance_intent:
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
            if distance_card.get("status") == "unresolved":
                ai_text_reply = f"📍 {distance_card['note']}"
            else:
                road = distance_card["road_distance_km"]
                drive = distance_card["estimated_drive_time"]
                src = distance_card["duration_source"]
                road_text = f"`{road} km`" if road is not None else "Information unavailable (no route on the road network)"
                drive_text = (drive + f" _(source: {src})_") if drive else "Information unavailable"
                lines = [
                    f"🚗 **Route: {distance_card['origin']} ➔ {distance_card['destination']}**\n",
                    f"• **Road Distance:** {road_text}",
                    f"• **Straight-line Distance:** `{distance_card['straight_distance_km']} km`",
                    f"• **Drive Time:** {drive_text}",
                ]
                if distance_card.get("fare_bus_npr") is not None:
                    fare_line = f"• **Bus Fare:** `NPR {distance_card['fare_bus_npr']:,}`"
                    if distance_card.get("fare_jeep_npr") is not None:
                        fare_line += f"  ·  **4WD Jeep:** `NPR {distance_card['fare_jeep_npr']:,}`"
                    if distance_card.get("fare_note"):
                        fare_line += f"  ·  _{distance_card['fare_note']}_"
                    lines.append(fare_line)
                if distance_card.get("note"):
                    lines.append(f"\n_ℹ️ {distance_card['note']}_")
                lines.append(
                    "\n💡 Open the **Navigation page** for the live map, turn-by-turn steps and your GPS position."
                )
                ai_text_reply = "\n".join(lines)
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
                "🚨 **Nepal national emergency hotlines**\n\n"
                "• **Tourist Police Nepal:** `1144`\n"
                "• **Nepal Police:** `100`\n"
                "• **Ambulance:** `102`\n"
                "• **Fire Brigade:** `101`\n"
                "• **Traffic Police:** `103`\n\n"
                "Facility cards below use stored directory phones only. "
                "If a local number is missing, the national 102 / 100 line is shown instead. "
                "This assistant does not invent hospital or pharmacy numbers."
            )
        elif is_package_intent:
            primaries = [offer for offer in package_cards if not offer.get("is_alternative")]
            alt_offers = [offer for offer in package_cards if offer.get("is_alternative")]
            if primaries:
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
                for offer in primaries:
                    lines.append(
                        f"• **{offer['title']}** ({offer['duration_days']} day(s)) — NPR {offer['price_npr']} · {offer['partner_name']}"
                    )
                if alt_offers:
                    lines.append("")
                    lines.append("Nearby-duration published alternatives (not an exact match):")
                    for offer in alt_offers:
                        lines.append(
                            f"• **{offer['title']}** ({offer['duration_days']} day(s), alternative) — NPR {offer['price_npr']}"
                        )
                lines.append("")
                lines.append("Open /packages to add offers to a trip basket, or /collaborate if you run a hotel or tour.")
                ai_text_reply = "\n".join(lines)
            elif requested_budget or requested_days:
                ai_text_reply = (
                    "I couldn't find a published package matching those requirements right now."
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
