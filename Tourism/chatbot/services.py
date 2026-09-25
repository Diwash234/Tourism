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

# Common place words help package matching choose relevant published records.
# Coordinates are resolved from the location service at request time; no
# canonical coordinate guesses are stored here.
CITY_WORDS = {
    "kathmandu", "pokhara", "chitwan", "lumbini", "everest", "ebc", "lukla",
    "mustang", "jomsom", "rara", "langtang", "janakpur", "ilam", "bandipur",
    "nagarkot", "bhaktapur", "patan", "annapurna", "phewa",
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
        return []

    return matches[:limit]


def parse_trip_constraints(message: str):
    """Extract requested days and a budget in NPR from a traveller question."""
    text = (message or "").lower()
    days = None
    days_match = re.search(r"(\d+)\s*[- ]?\s*days?", text)
    if days_match:
        days = max(1, min(60, int(days_match.group(1))))
    budget_npr = None
    _usd_match = re.search(r"\$\s*([\d,]+)", text)
    npr_match = re.search(r"(?:npr|rs\.?)\s*([\d,]+)", text)
    # NPR package records can be compared directly. A USD amount is retained
    # as an intent signal only; without a dated exchange-rate source we do not
    # manufacture an NPR value for matching or display.
    if npr_match:
        budget_npr = float(npr_match.group(1).replace(",", ""))
    return days, budget_npr


def is_budget_trip_intent(message: str, days=None, budget_npr=None) -> bool:
    text = (message or "").lower()
    trip_words = any(word in text for word in ("trip", "package", "tour", "holiday", "vacation"))
    under = any(word in text for word in ("under", "below", "less than", "budget", "cheap"))
    return bool((days and budget_npr) or (trip_words and budget_npr) or (days and under and trip_words))


KNOWN_PLACE_WORDS = set(CITY_WORDS)


def package_card(listing: MarketplaceListing, is_alternative: bool = False) -> dict:
    return {
        "id": listing.id,
        "slug": listing.slug,
        "title": listing.title,
        "kind": listing.kind,
        "price_npr": str(listing.price_npr),
        "duration_days": listing.duration_days,
        "city": listing.city or (listing.destination.city if listing.destination else "Location unavailable"),
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
        duration = listing.duration_days
        if duration is None:
            continue
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
    """Return only media recorded for this destination.

    A missing image is intentionally an empty value. Stock/AI imagery can
    depict a different place, so it must never be presented as this record's
    cover.
    """
    img = dest.gallery.filter(is_cover=True).first() or dest.gallery.first()
    if not img:
        return ""
    return img.external_url or (img.image.url if img.image else "")


def generate_structured_itinerary(dest_name: str, days: int = 5, budget_npr: Optional[float] = None) -> Dict[str, Any]:
    """Generates day-by-day itinerary schedule with daily budgets and transit legs."""
    days = max(1, min(14, int(days)))
    dest = Destination.objects.filter(name__icontains=dest_name).first() if dest_name else None

    itinerary_days = []

    themes = [
        ("Arrival & orientation", "Confirm the arrival route and the places that are actually recorded for this destination."),
        ("Recorded place visit", "Use the destination catalogue and local directory records to choose the next place."),
        ("Plan a free day", "Add a nearby recorded place, rest, or an activity after confirming availability."),
    ]

    for d_num in range(1, days + 1):
        theme_title, theme_desc = themes[(d_num - 1) % len(themes)]
        itinerary_days.append({
            "day": d_num,
            "title": f"Day {d_num}: {theme_title}",
            "highlights": theme_desc,
            "lodging": None,
            "daily_budget_npr": None,
            "daily_budget_usd": None,
        })

    return {
        "destination": dest.name if dest else dest_name,
        "days_count": days,
        "total_estimated_npr": None,
        "total_estimated_usd": None,
        "fits_budget": None,
        "schedule": itinerary_days,
        "note": "A day-by-day structure is a planning scaffold. Costs, stays and availability must be confirmed from recorded or current sources.",
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

    # Fares: only a recorded transit fare is shown. If none is available,
    # the card leaves it unavailable rather than calculating a made-up quote.
    dest_id = dest.get("destination_id")
    if dest_id:
        transit = DestinationTransitRoute.objects.filter(
            destination_id=dest_id, is_verified=True
        ).exclude(estimated_fare_npr__isnull=True).first()
        if transit:
            card["fare_bus_npr"] = int(transit.estimated_fare_npr)
            card["fare_note"] = f"Curated fare ({transit.route_name or 'transit route'})"

    if card["fare_bus_npr"] is None:
        card["fare_note"] = "Fare unavailable — no verified fare record was supplied"

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
                "Namaste! I am **Himal AI**, your Nepal travel companion.\n\n"
                "I can help you discover recorded destinations, compare published packages and shape an itinerary. "
                "For urgent help, use the Emergency page and its available directory records.\n"
                "Try: *'Show me recorded places in Pokhara'*, *'Help me compare two destinations'* or *'Plan a five-day trip'*."
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
        daily_usd = None
        if hasattr(dest, "budget_estimation") and dest.budget_estimation and dest.budget_estimation.estimated_daily_budget is not None:
            daily_usd = float(dest.budget_estimation.estimated_daily_budget)

        destination_cards.append({
            "id": dest.id,
            "name": dest.name,
            "slug": dest.slug,
            "image": img_url,
            "category": dest.category.name if dest.category else "Destination",
            "rating": str(dest.average_rating) if dest.average_rating is not None else None,
            "city": ", ".join(part for part in [dest.district, dest.province] if part) or None,
            "budget": f"USD {daily_usd:,.0f}/day (recorded estimate)" if daily_usd is not None else "Budget unavailable",
            "altitude": dest.altitude or None,
        })

    # Pack Image Cards
    if is_image_intent or len(matched_destinations) > 0:
        for dest in matched_destinations[:3]:
            for img in dest.gallery.all()[:2]:
                image_url = img.external_url or (img.image.url if img.image else "")
                if not image_url:
                    continue
                image_cards.append({
                    "url": image_url,
                    "caption": img.caption or f"{dest.name} Scenic View",
                    "photographer": img.photographer or "Attribution unavailable",
                    "license": img.license_type or "License not recorded",
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
        dest_for_plan = matched_destinations[0].name if matched_destinations else ""
        budget_match = re.search(r"(?:npr|rs\.?|\$)\s*([\d,]+)", msg_lower)
        budget_val = float(budget_match.group(1).replace(",", "")) if budget_match else None
        itinerary_card = generate_structured_itinerary(dest_for_plan, days=days, budget_npr=budget_val)

    # Pack Emergency Cards only from verified records near an explicitly
    # supplied position. Without coordinates, the assistant points to the
    # location-aware directory instead of returning arbitrary national rows.
    if is_emergency_intent and latitude is not None and longitude is not None:
        nearby_records = []
        for hospital in Hospital.objects.filter(is_archived=False, is_verified=True).select_related("destination")[:100]:
            distance = haversine_distance_km(latitude, longitude, float(hospital.latitude), float(hospital.longitude))
            phone = str(hospital.phone or "").strip()
            if distance is not None and distance <= 50 and phone:
                nearby_records.append((distance, {
                    "name": hospital.name,
                    "type": "Emergency Hospital",
                    "phone": phone,
                    "district": hospital.district or "",
                    "distance_km": round(distance, 1),
                }))
        for station in PoliceStation.objects.filter(is_archived=False, is_verified=True).select_related("destination")[:100]:
            distance = haversine_distance_km(latitude, longitude, float(station.latitude), float(station.longitude))
            phone = str(station.phone or "").strip()
            if distance is not None and distance <= 50 and phone:
                nearby_records.append((distance, {
                    "name": station.name,
                    "type": "Tourist & Civil Police",
                    "phone": phone,
                    "district": station.destination.district if station.destination_id else "",
                    "distance_km": round(distance, 1),
                }))
        emergency_cards = [card for _, card in sorted(nearby_records, key=lambda item: item[0])[:5]]

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
            total = itinerary_card.get("total_estimated_npr")
            total_text = f"NPR {total:,}" if total is not None else "Information unavailable"
            ai_text_reply = (
                f"🗓️ **Planning scaffold for {itinerary_card['destination'] or 'your route'}**\n\n"
                f"• **Days:** {itinerary_card['days_count']}\n"
                f"• **Cost:** {total_text}\n\n"
                "The schedule is a starting structure, not a confirmed booking or quote. "
                "Confirm current prices, stays, permits and availability with the relevant providers.\n\n"
            )
            for item in itinerary_card["schedule"]:
                daily = item.get("daily_budget_npr")
                daily_text = f"NPR {daily:,} (estimate)" if daily is not None else "Information unavailable"
                ai_text_reply += (
                    f"📍 **{item['title']}**\n"
                    f"   • *Planning note:* {item['highlights']}\n"
                    f"   • *Daily cost:* {daily_text}\n\n"
                )
        elif is_emergency_intent:
            ai_text_reply = (
                "For an emergency, open the Emergency page to search the directory records available for a destination or location. "
                "The assistant does not replace local emergency dispatch, and a missing local phone number is left unavailable."
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
                "Budget values depend on the destination, season, transport and provider. "
                "I can show a budget only when a recorded estimate or published package price is available; "
                "otherwise browse /packages or use the itinerary planner to confirm current costs."
            )
        elif matched_destinations:
            top_dest = matched_destinations[0]
            daily_usd = None
            if hasattr(top_dest, "budget_estimation") and top_dest.budget_estimation and top_dest.budget_estimation.estimated_daily_budget is not None:
                daily_usd = float(top_dest.budget_estimation.estimated_daily_budget)
            location = ", ".join(part for part in [top_dest.district, top_dest.province] if part) or "Location not recorded"
            season = top_dest.best_time_to_visit or "Not recorded"
            distance = f"{top_dest.distance_from_kathmandu_km} km from Kathmandu" if top_dest.distance_from_kathmandu_km is not None else "Distance from Kathmandu unavailable"
            budget_text = f"USD {daily_usd:,.0f} / day (recorded estimate)" if daily_usd is not None else "Daily budget unavailable"
            ai_text_reply = (
                f"**{top_dest.name} ({location})**\n\n"
                f"{top_dest.description or 'Description unavailable'}\n\n"
                f"• **Elevation:** {top_dest.altitude or 'Information unavailable'}\n"
                f"• **Category:** {top_dest.category.name if top_dest.category else 'Destination'}\n"
                f"• **Best season:** {season}\n"
                f"• **Daily budget:** {budget_text}\n"
                f"• **Distance from Kathmandu:** {distance}\n\n"
                "Open the destination record for the details that are available."
            )
        else:
            ai_text_reply = (
                "Namaste! I can help you discover recorded destinations, compare published packages, "
                "and build a trip scaffold. Missing costs, schedules and emergency details stay unavailable. "
                "For urgent help, use the Emergency page and its available directory records.\n\n"
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
