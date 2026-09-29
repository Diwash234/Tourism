"""
curated_planning.py
Advanced analytical tools for curated Nepal itineraries:
- Dual-persona cost and budget calculation (Nepali domestic vs SAARC vs Foreign, across Budget, Standard, Luxury tiers)
- High-altitude safety analysis, Lake Louise AMS scoring rubric, and emergency rescue directory
- Multi-itinerary side-by-side comparison matrix
"""
from typing import Dict, List, Any, Optional

USD_TO_NPR_RATE = 133.0  # Representative base conversion rate for travel estimations


def calculate_cost_breakdown(
    itinerary_data: Dict[str, Any],
    nationality: str = "nepali",
    style: str = "standard",
    travelers: int = 1
) -> Dict[str, Any]:
    """
    Calculates a realistic, itemized dual-persona budget breakdown.
    Nationalities: 'nepali', 'saarc', 'foreign'
    Styles: 'budget', 'standard', 'luxury'
    """
    nationality = (nationality or "nepali").lower()
    if nationality not in ("nepali", "saarc", "foreign"):
        nationality = "nepali"

    style = (style or "standard").lower()
    if style not in ("budget", "standard", "luxury"):
        style = "standard"

    travelers = max(1, int(travelers or 1))
    days = max(1, int(itinerary_data.get("days", 3)))
    category = (itinerary_data.get("category") or "trekking").lower()
    slug = (itinerary_data.get("slug") or "").lower()
    is_high_altitude = int(itinerary_data.get("max_elevation_m") or 0) >= 3000

    # 1. Official Permits & Fees
    if nationality == "nepali":
        permits_cost_npr = 100 * travelers if is_high_altitude or "national-park" in slug else 0
        permits_description = "Nepali citizen park entry (NPR 100). No TIMS permit required."
    elif nationality == "saarc":
        tims = 1000 * travelers if is_high_altitude else 0
        park = 1500 * travelers
        permits_cost_npr = tims + park
        permits_description = f"SAARC national rates: Conservation/Park entry (NPR 1,500){' + SAARC TIMS card (NPR 1,000)' if tims else ''}."
    else:  # foreign
        tims = 2000 * travelers if is_high_altitude else 0
        park = 3000 * travelers
        khumbu_fee = 3000 * travelers if "everest" in slug else 0
        permits_cost_npr = tims + park + khumbu_fee
        permits_description = f"International visitor rates: TIMS card (NPR 2,000) + Park permit (NPR 3,000){' + Khumbu Municipality fee (NPR 3,000)' if khumbu_fee else ''}."

    # 2. Accommodation
    rooms_needed = (travelers + 1) // 2
    if style == "budget":
        room_daily_rate = 750 if is_high_altitude else 1200
    elif style == "standard":
        room_daily_rate = 2200 if is_high_altitude else 3500
    else:  # luxury
        room_daily_rate = 6500 if is_high_altitude else 11000
    accommodation_cost_npr = room_daily_rate * rooms_needed * (days - 1 if days > 1 else 1)

    # 3. Food, Water & Tea House Sustenance
    if style == "budget":
        food_daily_person = 1400 if is_high_altitude else 1100
    elif style == "standard":
        food_daily_person = 2600 if is_high_altitude else 2200
    else:  # luxury
        food_daily_person = 4800 if is_high_altitude else 4200
    food_cost_npr = food_daily_person * travelers * days

    # 4. Transportation
    is_lukla_route = "everest" in slug or "lukla" in slug
    is_jomsom_route = "mustang" in slug or "muktinath" in slug or "jomsom" in slug

    if is_lukla_route:
        # Mountain flight Lukla return
        if nationality == "nepali":
            flight_person = 14000  # Domestic resident fare
        else:
            flight_person = 42000  # International visitor round-trip (~$320)
        transport_cost_npr = flight_person * travelers if style != "budget" else (flight_person * travelers)
    elif is_jomsom_route:
        if style == "budget":
            transport_cost_npr = 4500 * travelers  # Local shared jeep/bus round trip
        elif style == "standard":
            transport_cost_npr = 8500 * travelers  # Express tourist micro / shared Scorpio
        else:
            transport_cost_npr = 32000  # Private 4WD Scorpio dedicated for group
    else:
        if style == "budget":
            transport_cost_npr = 1800 * travelers  # Public express bus
        elif style == "standard":
            transport_cost_npr = 4000 * travelers  # Deluxe tourist coach / shared VIP HiAce
        else:
            transport_cost_npr = 22000  # Private chartered AC car / SUV

    # 5. Guide and Porter
    # According to Nepal Tourism Board regulations, foreign trekkers in protected mountain zones
    # must be accompanied by a licensed trekking guide.
    if is_high_altitude:
        porters_needed = (travelers + 1) // 2 if travelers > 1 else (1 if style != "budget" else 0)
        guide_daily = 3500
        porter_daily = 2500

        if nationality == "nepali":
            # Optional for domestic trekkers
            if style == "budget":
                guide_porter_cost_npr = 0
            elif style == "standard":
                guide_porter_cost_npr = (guide_daily * days) // 2  # Shared local scout
            else:
                guide_porter_cost_npr = (guide_daily + porter_daily * porters_needed) * days
        else:
            # Mandatory/strongly recommended for international trekkers
            if style == "budget":
                guide_porter_cost_npr = guide_daily * days  # 1 guide for group
            else:
                guide_porter_cost_npr = (guide_daily + porter_daily * porters_needed) * days
    else:
        guide_porter_cost_npr = 0 if style == "budget" else (2500 * days if style == "standard" else 5000 * days)

    subtotal_npr = (
        permits_cost_npr
        + accommodation_cost_npr
        + food_cost_npr
        + transport_cost_npr
        + guide_porter_cost_npr
    )

    # 6. Safety & Contingency Buffer (10%)
    contingency_npr = round(subtotal_npr * 0.10)
    total_npr = subtotal_npr + contingency_npr
    total_usd = round(total_npr / USD_TO_NPR_RATE)

    return {
        "parameters": {
            "nationality": nationality,
            "style": style,
            "travelers": travelers,
            "days": days,
        },
        "itemized": [
            {
                "category": "Official Permits & Entrance",
                "amount_npr": permits_cost_npr,
                "amount_usd": round(permits_cost_npr / USD_TO_NPR_RATE),
                "description": permits_description,
                "is_mandatory": True,
            },
            {
                "category": "Accommodation & Lodging",
                "amount_npr": accommodation_cost_npr,
                "amount_usd": round(accommodation_cost_npr / USD_TO_NPR_RATE),
                "description": f"{days - 1 if days > 1 else 1} nights, {rooms_needed} room(s) for {travelers} traveler(s) ({style.capitalize()} comfort).",
                "is_mandatory": True,
            },
            {
                "category": "Food, Tea & Safe Drinking Water",
                "amount_npr": food_cost_npr,
                "amount_usd": round(food_cost_npr / USD_TO_NPR_RATE),
                "description": f"Daily meals (Dal Bhat, breakfast, soups, boiled water) for {travelers} person(s).",
                "is_mandatory": True,
            },
            {
                "category": "Transportation & Transfers",
                "amount_npr": transport_cost_npr,
                "amount_usd": round(transport_cost_npr / USD_TO_NPR_RATE),
                "description": "Round-trip regional transfer / mountain flights / 4WD jeep service.",
                "is_mandatory": True,
            },
            {
                "category": "Licensed Guide & Porter Support",
                "amount_npr": guide_porter_cost_npr,
                "amount_usd": round(guide_porter_cost_npr / USD_TO_NPR_RATE),
                "description": "NTB certified mountain guide & porter service (mandatory for foreign trekkers in alpine zones).",
                "is_mandatory": nationality != "nepali" and is_high_altitude,
            },
            {
                "category": "Emergency & Weather Contingency (10%)",
                "amount_npr": contingency_npr,
                "amount_usd": round(contingency_npr / USD_TO_NPR_RATE),
                "description": "Reserve for weather delays, high-altitude rest buffer, or route adjustments.",
                "is_mandatory": False,
            },
        ],
        "total_npr": total_npr,
        "total_usd": total_usd,
        "per_person_npr": round(total_npr / travelers),
        "per_person_usd": round(total_usd / travelers),
        "forex_rate_used": USD_TO_NPR_RATE,
    }


def calculate_altitude_safety(itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates high-altitude physiology assessment, risk classification,
    Lake Louise AMS symptom scoring rubric, and emergency rescue directory.
    """
    max_elevation = int(itinerary_data.get("max_elevation_m") or 0)
    days_schedule = itinerary_data.get("days_schedule") or []

    if max_elevation >= 5000:
        risk_level = "Extreme (High Alpine / HAPE-HACE Hazard)"
        risk_class = "extreme"
        color = "red"
        acclimatization_days_needed = 2
        summary = "Extreme high-altitude conditions. Atmospheric pressure is approximately 50% of sea level. Rigorous acclimatization, hydration (4L/day), and Diamox readiness are essential."
    elif max_elevation >= 3500:
        risk_level = "High (Severe AMS / Acclimatization Mandatory)"
        risk_class = "high"
        color = "amber"
        acclimatization_days_needed = 1
        summary = "Substantial altitude hazard. Do not ascend more than 300-500 meters sleeping elevation per 24 hours above 3,000m. Take scheduled acclimatization rest days."
    elif max_elevation >= 2500:
        risk_level = "Moderate (Altitude Awareness Required)"
        risk_class = "moderate"
        color = "yellow"
        acclimatization_days_needed = 0
        summary = "Mild altitude impact. Some individuals experience minor headache, sleep disturbances, or mild breathlessness during strenuous climbs."
    else:
        risk_level = "Low (Sub-Alpine / Lowland)"
        risk_class = "low"
        color = "emerald"
        acclimatization_days_needed = 0
        summary = "Standard low-altitude itinerary. Acute Mountain Sickness (AMS) is extremely unlikely below 2,500 meters."

    # Identify rest / acclimatization days in schedule
    acclimatization_stops = []
    highest_sleeping_stop = {"elevation_m": 0, "name": "", "day": 1}
    for day in days_schedule:
        elev = int(day.get("elevation_m") or 0)
        title = (day.get("title") or "").lower()
        if "acclimatization" in title or "rest" in title:
            acclimatization_stops.append({
                "day": day.get("day_number"),
                "location": day.get("destination_name"),
                "elevation_m": elev,
                "notes": "Scheduled acclimatization walk high, sleep low interval."
            })
        if elev > highest_sleeping_stop["elevation_m"]:
            highest_sleeping_stop = {
                "elevation_m": elev,
                "name": day.get("destination_name") or day.get("title"),
                "day": day.get("day_number"),
            }

    return {
        "max_elevation_m": max_elevation,
        "risk_level": risk_level,
        "risk_class": risk_class,
        "color": color,
        "summary": summary,
        "acclimatization_days_recommended": acclimatization_days_needed,
        "acclimatization_stops_found": acclimatization_stops,
        "highest_elevation_point": highest_sleeping_stop,
        "golden_rules": [
            "Never ascend to sleep at a higher altitude if you have any symptoms of Acute Mountain Sickness (AMS).",
            "If symptoms worsen while resting at the same altitude, descend immediately (at least 500 to 1,000 meters).",
            "Climb high, sleep low: take morning hikes to higher ridges, then return to lower camps for overnight sleep.",
            "Maintain 3.5 to 4 liters of fluid intake daily (avoid alcohol and sleeping sedatives at high altitude).",
            "Carry oral Acetazolamide (Diamox 125-250mg) after consulting a qualified physician."
        ],
        "lake_louise_score_chart": {
            "title": "Lake Louise Acute Mountain Sickness (AMS) Clinical Scoring System",
            "thresholds": [
                {"score": "0 - 2", "status": "Normal / No AMS", "action": "Proceed with regular caution and hydration."},
                {"score": "3 - 5", "status": "Mild to Moderate AMS", "action": "HALT ASCENT. Rest at current altitude. Take fluids, mild analgesics, or Diamox. Do not climb higher until score returns to 0."},
                {"score": "6+", "status": "Severe AMS / Impending HAPE or HACE", "action": "EMERGENCY: Immediate descent required (minimum 500m). Prepare oxygen or hyperbaric chamber and initiate helicopter evacuation if neurological symptoms or fluid in lungs arise."}
            ],
            "symptoms": [
                {
                    "name": "Headache",
                    "options": [
                        {"score": 0, "label": "None"},
                        {"score": 1, "label": "Mild headache"},
                        {"score": 2, "label": "Moderate headache"},
                        {"score": 3, "label": "Severe headache, incapacitating"}
                    ]
                },
                {
                    "name": "Gastrointestinal Symptoms",
                    "options": [
                        {"score": 0, "label": "Good appetite"},
                        {"score": 1, "label": "Poor appetite or nausea"},
                        {"score": 2, "label": "Moderate nausea or vomiting"},
                        {"score": 3, "label": "Severe nausea and vomiting, incapacitating"}
                    ]
                },
                {
                    "name": "Fatigue and / or Weakness",
                    "options": [
                        {"score": 0, "label": "Not tired or weak"},
                        {"score": 1, "label": "Mild fatigue / weakness"},
                        {"score": 2, "label": "Moderate fatigue / weakness"},
                        {"score": 3, "label": "Severe fatigue / weakness, incapacitating"}
                    ]
                },
                {
                    "name": "Dizziness / Lightheadedness",
                    "options": [
                        {"score": 0, "label": "None"},
                        {"score": 1, "label": "Mild dizziness"},
                        {"score": 2, "label": "Moderate dizziness"},
                        {"score": 3, "label": "Severe dizziness, incapacitating"}
                    ]
                }
            ]
        },
        "emergency_rescue_directory": [
            {
                "organization": "Himalayan Rescue Association (HRA) Head Office",
                "location": "Dhobichaur, Lazimpat, Kathmandu",
                "phone": "+977-1-4440292 / +977-1-4440293",
                "specialty": "Volunteer doctors, high-altitude mountain medicine, Everest & Annapurna posts."
            },
            {
                "organization": "HRA Pheriche Aid Post (Khumbu / Everest)",
                "location": "Pheriche (4,280m), Solukhumbu",
                "phone": "VHF Radio / Satellite or via HRA HQ",
                "specialty": "Seasonal alpine medical clinic, hyperbaric Gamow bags, oxygen therapy."
            },
            {
                "organization": "HRA Manang Aid Post (Annapurna Circuit)",
                "location": "Manang (3,550m), Gandaki",
                "phone": "+977-66-440114 / via HRA HQ",
                "specialty": "Altitude daily lectures, acclimatization medical check-ups."
            },
            {
                "organization": "Nepal Tourist Police National Emergency Hotline",
                "location": "National Operations (Bhrikutimandap, Kathmandu)",
                "phone": "1144 (Toll-Free in Nepal) / +977-1-4247041",
                "specialty": "24/7 tourist assistance, missing person coordination, search & rescue dispatch."
            },
            {
                "organization": "Armed Police Force (APF) Disaster Relief Command",
                "location": "National Command",
                "phone": "1114 (Emergency Helpline)",
                "specialty": "High-altitude search and rescue, river and avalanche disasters."
            }
        ]
    }


def compare_curated_itineraries(
    itineraries: List[Dict[str, Any]],
    nationality: str = "nepali",
    style: str = "standard",
    travelers: int = 1
) -> Dict[str, Any]:
    """
    Constructs a comparative evaluation matrix across 2 to 4 itineraries.
    """
    items_out = []
    for it in itineraries:
        cost = calculate_cost_breakdown(it, nationality=nationality, style=style, travelers=travelers)
        safety = calculate_altitude_safety(it)
        items_out.append({
            "slug": it["slug"],
            "title": it["title"],
            "title_nepali": it.get("title_nepali", ""),
            "persona": it.get("persona", "all"),
            "category": it.get("category", "trekking"),
            "days": it.get("days", 3),
            "difficulty": it.get("difficulty", "moderate"),
            "start_city": it.get("start_city", "Kathmandu"),
            "end_city": it.get("end_city", "Kathmandu"),
            "max_elevation_m": it.get("max_elevation_m"),
            "best_seasons": it.get("best_seasons", []),
            "cover_image": it.get("cover_image", ""),
            "summary": it.get("summary", ""),
            "highlights": it.get("highlights", [])[:3],
            "cost_breakdown": cost,
            "altitude_safety": safety,
            "permits_info": it.get("permits_info", {}),
            "transport_info": it.get("transport_info", ""),
            "local_food_recommendations": it.get("local_food_recommendations", ""),
        })

    return {
        "count": len(items_out),
        "comparison": items_out,
        "parameters": {
            "nationality": nationality,
            "style": style,
            "travelers": travelers,
        }
    }
