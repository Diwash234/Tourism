"""Seed the 15-Day Pokhara travel guide with real DB records.

Links every day to actual hotels, hospitals, and destinations already
in the database. Run:
    python manage.py seed_pokhara_guide
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seed the 15-Day Pokhara travel guide with real DB records."

    def handle(self, *args, **options):
        from tourist.models import (
            Destination, Hotel, Hospital, TravelGuide, TravelGuideDay,
        )
        from tourist.utils import haversine_distance

        def get_dest(name_part):
            return Destination.sightseeing().filter(
                name__icontains=name_part,
                is_active=True,
                status=Destination.SubmissionStatus.APPROVED,
            ).first()

        def get_hotel(name_part):
            return Hotel.objects.filter(
                name__icontains=name_part,
                is_active=True,
                is_verified=True,
                archived_at__isnull=True,
            ).exclude(source_url="").first()

        def get_hospitals_near_pokhara(limit=5):
            pokhara = get_dest("pokhara lakeside")
            if not pokhara or not pokhara.latitude:
                return []
            # Bounding box filter first (~0.15 deg ≈ 15km) to avoid
            # computing haversine for every hospital in the DB.
            lat, lng = float(pokhara.latitude), float(pokhara.longitude)
            candidates = Hospital.objects.filter(
                is_verified=True,
                is_archived=False,
                source_url__gt="",
                latitude__gte=lat - 0.15, latitude__lte=lat + 0.15,
                longitude__gte=lng - 0.15, longitude__lte=lng + 0.15,
            )
            rows = []
            for h in candidates:
                if h.latitude and h.longitude:
                    d = haversine_distance(lat, lng, float(h.latitude), float(h.longitude))
                    if d <= 10:
                        rows.append((d, h))
            return [h for _, h in sorted(rows, key=lambda x: x[0])[:limit]]

        pokhara = get_dest("pokhara lakeside")
        if not pokhara:
            self.stderr.write("Pokhara destination not found")
            return

        guide, created = TravelGuide.objects.update_or_create(
            slug="15-day-pokhara",
            defaults={
                "title": "15-Day Pokhara & Annapurna Guide",
                "subtitle": "Relaxed lakeside base with Sarangkot sunrises, Peace Pagoda, Begnas Lake, Australian Camp hike, Ghandruk overnight and Bandipur day trip.",
                "destination": pokhara,
                "days_count": 15,
                "pace": "Relaxed",
                "best_for": "Couples, families, first-time visitors, international tourists",
                "is_published": True,
            },
        )
        self.stdout.write(f"Guide: {guide.title} ({'created' if created else 'updated'})")

        hotel_names = [
            "Annapurna Heritage Palace", "Annapurna Himalayan Resort",
            "Bar Peepal Resort", "Fewa Grand Palace", "Pokhara Grand Heritage",
            "Pokhara Imperial Palace", "Begnas Lake Resort",
        ]
        hotels = [h for h in (get_hotel(n) for n in hotel_names) if h]
        hospitals = get_hospitals_near_pokhara(5)

        dest_map = {
            "sarangkot": get_dest("sarangkot paragliding"),
            "davis": get_dest("davis falls"),
            "gupteshwar": get_dest("gupteshwar cave nallu"),
            "peace": get_dest("world peace pagoda"),
            "pumdikot": get_dest("pumdikot"),
            "begnas": get_dest("begnas lake boating"),
            "rupa": get_dest("begnas rupa view tower"),
            "bindhyabasini": get_dest("bindhyabasini temple"),
            "kande": get_dest("kande inn"),
            "australian": get_dest("australian camp guest house"),
            "dhampus": get_dest("dhampus village eco lodge"),
            "ghandruk": get_dest("ghandruk gurung"),
            "bandipur": get_dest("bandipur silktrail"),
            "birethanti": get_dest("birethanti canyoning"),
        }

        days_data = [
            {
                "day_number": 1,
                "title": "Arrive in Pokhara + Lakeside",
                "route": "Pokhara International Airport → Lakeside",
                "travel_distance": "~5 km",
                "travel_time": "~20–30 min",
                "overnight_stay": "Lakeside hotel (e.g. Annapurna Heritage Palace)",
                "morning": "Arrive at Pokhara airport. Collect luggage. Hotel transfer.",
                "afternoon": "Check in. Rest 1–2 hours. Walk around Lakeside. Visit Phewa Lake waterfront.",
                "evening": "Relaxed evening boat ride on Phewa Lake. Visit Tal Barahi Temple island. Sunset at Lakeside.",
                "practical_notes": "Pokhara International Airport (PKR) is at Prithvi Chowk. Taxis wait outside; agree fare before departure.",
                "primary_destination": dest_map.get("sarangkot"),
                "attractions": [pokhara],
            },
            {
                "day_number": 2,
                "title": "Sarangkot Sunrise + Paragliding",
                "route": "Lakeside → Sarangkot → Lakeside",
                "travel_distance": "~10–13 km each way",
                "travel_time": "~30–40 min each way",
                "overnight_stay": "Lakeside hotel",
                "morning": "4:30–5:00 AM drive to Sarangkot. Sunrise over Annapurna, Machhapuchhre (Fishtail), Dhaulagiri. Breakfast at hilltop café.",
                "afternoon": "Optional tandem paragliding (1–2 hrs including prep and transport). Return to Lakeside. Lunch. Hotel rest.",
                "evening": "Spa/massage. Lakeside walk. Phewa Lake sunset.",
                "practical_notes": "Mountain views are weather-dependent. Paragliding operators are lined up along Lakeside; book the evening before.",
                "primary_destination": dest_map.get("sarangkot"),
                "attractions": [dest_map.get("sarangkot")],
            },
            {
                "day_number": 3,
                "title": "Davis Falls + Gupteshwor Cave + Mountain Museum",
                "route": "Lakeside → Davis Falls → Gupteshwor Cave → International Mountain Museum → Lakeside",
                "travel_distance": "Short city circuit",
                "travel_time": "~10–15 min between sites",
                "overnight_stay": "Lakeside hotel",
                "morning": "Davis Falls (Patale Chhango). Gupteshwor Mahadev Cave — one of Nepal's largest caves with a Shiva lingam.",
                "afternoon": "International Mountain Museum — Himalayan mountaineering history, culture and climbing equipment exhibits.",
                "evening": "Lakeside shopping. Nepalese handicrafts. Coffee at Phewa waterfront.",
                "practical_notes": "Cave can be slippery; wear grippy shoes. Museum closed on Tuesdays.",
                "primary_destination": dest_map.get("davis"),
                "attractions": [dest_map.get("davis"), dest_map.get("gupteshwar")],
            },
            {
                "day_number": 4,
                "title": "World Peace Pagoda + Phewa Lake",
                "route": "Lakeside → Phewa Lake boat → opposite shore → hike → World Peace Pagoda",
                "travel_distance": "Boat + 30–40 min hike",
                "travel_time": "Half/full day",
                "overnight_stay": "Lakeside hotel",
                "morning": "Boat across Phewa Lake to the opposite shore. Hike up to World Peace Pagoda (Shanti Stupa) — panoramic Annapurna views.",
                "afternoon": "Boat back. Lunch at Lakeside. Rest. Optional kayaking on Phewa Lake.",
                "evening": "Sunset boat ride. Dinner at Lakeside.",
                "practical_notes": "The hike is ~300 steps; go early to avoid heat. Boat operators wait at the Pagoda base for return trips.",
                "primary_destination": dest_map.get("peace"),
                "attractions": [dest_map.get("peace")],
            },
            {
                "day_number": 5,
                "title": "Pumdikot + Damside + Relaxed Lakeside Evening",
                "route": "Lakeside → Pumdikot → Damside → Lakeside",
                "travel_distance": "~6–8 km to Pumdikot",
                "travel_time": "~20–30 min uphill",
                "overnight_stay": "Lakeside hotel",
                "morning": "Drive to Pumdikot. Large Shiva statue (135 ft) with panoramic Pokhara Valley and mountain views.",
                "afternoon": "Drive toward Damside. Relaxed lunch. International Mountain Museum area if missed on Day 3.",
                "evening": "Lakeside shopping. Nepalese handicrafts. Coffee. Phewa waterfront. Optional live cultural performance.",
                "practical_notes": "Pumdikot road is steep; taxi recommended. Best light in early morning.",
                "primary_destination": dest_map.get("pumdikot"),
                "attractions": [dest_map.get("pumdikot")],
            },
            {
                "day_number": 6,
                "title": "Begnas Lake + Rupa Lake",
                "route": "Lakeside → Prithvi Chowk → Begnas Lake → Rupa Lake → Lakeside",
                "travel_distance": "~14–15 km to Begnas",
                "travel_time": "~40–50 min by taxi/car",
                "overnight_stay": "Lakeside hotel",
                "morning": "Drive to Begnas Lake — quieter than Phewa. Boating. Village walks. Local lunch.",
                "afternoon": "Explore Rupa Lake area — terraced fields, rural Nepal. Photography.",
                "evening": "Return to Lakeside. Free evening.",
                "practical_notes": "Begnas and Rupa are among the quieter lake experiences around Pokhara. Carry water and sunscreen.",
                "primary_destination": dest_map.get("begnas"),
                "attractions": [dest_map.get("begnas"), dest_map.get("rupa")],
            },
            {
                "day_number": 7,
                "title": "Pokhara Cultural & Old City Day",
                "route": "Lakeside → Bindhyabasini Temple → Old Bazaar → Seti River Gorge → Lakeside",
                "travel_distance": "~4–5 km",
                "travel_time": "Short drives + walking",
                "overnight_stay": "Lakeside hotel",
                "morning": "Bindhyabasini Temple — Pokhara's oldest Hindu temple. Old Bazaar — traditional streets, local shops, spice markets.",
                "afternoon": "Seti River Gorge viewpoint — the river cuts deeply through the city. Lunch at a local restaurant.",
                "evening": "Sunset boat ride. Free time.",
                "practical_notes": "Old Bazaar is best explored on foot. Remove shoes at temple entrances.",
                "primary_destination": dest_map.get("bindhyabasini"),
                "attractions": [dest_map.get("bindhyabasini")],
            },
            {
                "day_number": 8,
                "title": "Australian Camp / Dhampus Hike",
                "route": "Lakeside → Kande → Australian Camp → Dhampus",
                "travel_distance": "~25 km to Kande + hiking",
                "travel_time": "~45 min drive + 3–4 hrs hiking",
                "overnight_stay": "Pokhara or Dhampus eco-lodge",
                "morning": "Early breakfast. Private vehicle to Kande. Hike toward Australian Camp — mountain views, forest, village scenery.",
                "afternoon": "Lunch at Australian Camp. Continue toward Dhampus depending on fitness. Return to Pokhara or stay overnight in a local lodge.",
                "evening": "If in Dhampus: village walk, local dinner, stargazing.",
                "practical_notes": "This is a real hike, not a sightseeing drive. Wear proper shoes. Carry water, snacks, rain jacket.",
                "primary_destination": dest_map.get("australian"),
                "attractions": [dest_map.get("australian"), dest_map.get("dhampus")],
            },
            {
                "day_number": 9,
                "title": "Relaxation / Spa / Phewa Lake",
                "route": "Lakeside (local)",
                "travel_distance": "—",
                "travel_time": "—",
                "overnight_stay": "Lakeside hotel",
                "morning": "Sleep late. Leisurely breakfast.",
                "afternoon": "Spa/massage. Café time. Phewa Lake kayaking. Shopping.",
                "evening": "Sunset boat ride. Dinner at Lakeside.",
                "practical_notes": "Rest day after hiking. Book spa treatments through your hotel.",
                "primary_destination": pokhara,
                "attractions": [pokhara],
            },
            {
                "day_number": 10,
                "title": "Ghandruk Excursion",
                "route": "Pokhara → Nayapul → Birethanti → Ghandruk",
                "travel_distance": "~42 km to Nayapul + trek",
                "travel_time": "~2 hrs drive + 4–5 hrs trek",
                "overnight_stay": "Ghandruk local lodge",
                "morning": "Drive to Nayapul. Trek through Birethanti, terraced fields, rhododendron forests to Ghandruk.",
                "afternoon": "Gurung culture. Traditional stone houses. Local food. Village walks. Himalayan views.",
                "evening": "Sunset over Annapurna South and Machhapuchhre. Dinner at lodge.",
                "practical_notes": "Make this a 2-day/1-night excursion. Book a licensed local trekking agency/lodge. TIMS card and ACAP permit required.",
                "primary_destination": dest_map.get("ghandruk"),
                "attractions": [dest_map.get("ghandruk"), dest_map.get("birethanti")],
            },
            {
                "day_number": 11,
                "title": "Ghandruk → Pokhara",
                "route": "Ghandruk → Nayapul → Pokhara",
                "travel_distance": "~42 km + trek",
                "travel_time": "4–5 hrs trek + 2 hrs drive",
                "overnight_stay": "Lakeside hotel",
                "morning": "Sunrise over Annapurna. Breakfast. Village walk. Photography.",
                "afternoon": "Trek back to Nayapul. Drive to Pokhara.",
                "evening": "Rest at hotel. Free evening.",
                "practical_notes": "Mountain roads take longer than city driving. Allow buffer time.",
                "primary_destination": dest_map.get("ghandruk"),
                "attractions": [dest_map.get("ghandruk")],
            },
            {
                "day_number": 12,
                "title": "Sarangkot Overnight Experience",
                "route": "Lakeside → Sarangkot",
                "travel_distance": "~10–13 km",
                "travel_time": "~30–40 min",
                "overnight_stay": "Sarangkot Mountain Lodge",
                "morning": "Leisurely breakfast. Drive to Sarangkot. Check into mountain lodge.",
                "afternoon": "Sarangkot village walk. Mountain viewpoint. Relax at the lodge. Sunset.",
                "evening": "Early dinner and rest.",
                "practical_notes": "Staying overnight means no pre-dawn drive for sunrise. Book lodge in advance.",
                "primary_destination": dest_map.get("sarangkot"),
                "attractions": [dest_map.get("sarangkot")],
            },
            {
                "day_number": 13,
                "title": "Sarangkot Sunrise + Return to Pokhara",
                "route": "Sarangkot → Lakeside",
                "travel_distance": "~10–13 km",
                "travel_time": "~30–40 min",
                "overnight_stay": "Lakeside hotel",
                "morning": "Wake before sunrise. Annapurna, Machhapuchhre, Dhaulagiri, Pokhara Valley — all from the lodge doorstep.",
                "afternoon": "Breakfast. Drive back to Lakeside. Free time.",
                "evening": "Last relaxed Phewa Lake evening. Dinner at Lakeside.",
                "practical_notes": "Mountain visibility is weather-dependent. Clouds can completely hide the peaks.",
                "primary_destination": dest_map.get("sarangkot"),
                "attractions": [dest_map.get("sarangkot")],
            },
            {
                "day_number": 14,
                "title": "Bandipur Day Trip",
                "route": "Pokhara → Damauli → Dumre → Bandipur",
                "travel_distance": "~72–80 km",
                "travel_time": "~2–2.5 hrs each way",
                "overnight_stay": "Lakeside hotel",
                "morning": "Drive to Bandipur via Prithvi Highway. Explore Bandipur Bazaar — traditional Newari architecture, Tundikhel, local cafés, hilltop views.",
                "afternoon": "Lunch at a Bandipur café. Village surroundings. Photography.",
                "evening": "Drive back to Pokhara. Overnight at Lakeside.",
                "practical_notes": "Bandipur is a preserved Newari hill town — no vehicles in the bazaar. Wear comfortable walking shoes.",
                "primary_destination": dest_map.get("bandipur"),
                "attractions": [dest_map.get("bandipur")],
            },
            {
                "day_number": 15,
                "title": "Final Pokhara Day + Departure",
                "route": "Lakeside → Pokhara International Airport",
                "travel_distance": "~5 km",
                "travel_time": "~20–30 min",
                "overnight_stay": "—",
                "morning": "Breakfast. Phewa Lake. Last shopping. Souvenirs. Coffee. Photography.",
                "afternoon": "If flight is late: International Mountain Museum, Davis Falls, or one last boat ride.",
                "evening": "Transfer to airport. Allow 30–45 min buffer beyond normal transfer time.",
                "practical_notes": "Keep travel insurance covering trekking/adventure activities. Carry passport and insurance copies. Save hospital and Tourist Police numbers offline.",
                "primary_destination": pokhara,
                "attractions": [pokhara],
            },
        ]

        for day_data in days_data:
            day, day_created = TravelGuideDay.objects.update_or_create(
                guide=guide,
                day_number=day_data["day_number"],
                defaults={
                    "title": day_data["title"],
                    "route": day_data.get("route", ""),
                    "travel_distance": day_data.get("travel_distance", ""),
                    "travel_time": day_data.get("travel_time", ""),
                    "overnight_stay": day_data.get("overnight_stay", ""),
                    "morning": day_data.get("morning", ""),
                    "afternoon": day_data.get("afternoon", ""),
                    "evening": day_data.get("evening", ""),
                    "practical_notes": day_data.get("practical_notes", ""),
                    "primary_destination": day_data.get("primary_destination"),
                },
            )
            if day_data.get("attractions"):
                day.attractions.set([a for a in day_data["attractions"] if a])
            if day_data["day_number"] in (1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 14, 15):
                day.hotels.set(hotels[:3])
            if day_data["day_number"] == 1:
                day.hospitals.set(hospitals)
            self.stdout.write(f"  Day {day.day_number}: {day.title} ({'created' if day_created else 'updated'})".encode("ascii", "replace").decode("ascii"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Guide has {guide.days.count()} days, {len(hotels)} hotels, {len(hospitals)} hospitals linked."
            )
        )


def get_dest(name_part):
    return Destination.objects.filter(name__icontains=name_part).first()


def get_hotel(name_part):
    return Hotel.objects.filter(name__icontains=name_part).first()


def get_hospitals_near_pokhara(limit=5):
    from tourist.utils import haversine_distance
    pokhara = get_dest("pokhara lakeside")
    if not pokhara or not pokhara.latitude:
        return []
    rows = []
    for h in Hospital.objects.all():
        if h.latitude and h.longitude:
            d = haversine_distance(float(pokhara.latitude), float(pokhara.longitude),
                                   float(h.latitude), float(h.longitude))
            if d <= 10:
                rows.append((d, h))
    return [h for _, h in sorted(rows)[:limit]]


def seed():
    pokhara = get_dest("pokhara lakeside")
    if not pokhara:
        print("Pokhara destination not found")
        return

    guide, created = TravelGuide.objects.update_or_create(
        slug="15-day-pokhara",
        defaults={
            "title": "15-Day Pokhara & Annapurna Guide",
            "subtitle": "Relaxed lakeside base with Sarangkot sunrises, Peace Pagoda, Begnas Lake, Australian Camp hike, Ghandruk overnight and Bandipur day trip.",
            "destination": pokhara,
            "days_count": 15,
            "pace": "Relaxed",
            "best_for": "Couples, families, first-time visitors, international tourists",
            "is_published": True,
        },
    )
    print(f"Guide: {guide.title} ({'created' if created else 'updated'})")

    # Real hotels near Pokhara (from DB)
    hotel_names = [
        "Annapurna Heritage Palace", "Annapurna Himalayan Resort",
        "Bar Peepal Resort", "Fewa Grand Palace", "Pokhara Grand Heritage",
        "Pokhara Imperial Palace", "Begnas Lake Resort",
    ]
    hotels = [h for h in (get_hotel(n) for n in hotel_names) if h]
    hospitals = get_hospitals_near_pokhara(5)

    # Real destinations for each day
    dest_map = {
        "sarangkot": get_dest("sarangkot paragliding"),
        "davis": get_dest("davis falls"),
        "gupteshwar": get_dest("gupteshwar cave nallu"),
        "peace": get_dest("world peace pagoda"),
        "pumdikot": get_dest("pumdikot"),
        "begnas": get_dest("begnas lake boating"),
        "rupa": get_dest("begnas rupa view tower"),
        "bindhyabasini": get_dest("bindhyabasini temple"),
        "kande": get_dest("kande inn"),
        "australian": get_dest("australian camp guest house"),
        "dhampus": get_dest("dhampus village eco lodge"),
        "ghandruk": get_dest("ghandruk gurung"),
        "bandipur": get_dest("bandipur silktrail"),
        "birethanti": get_dest("birethanti canyoning"),
    }

    days_data = [
        {
            "day_number": 1,
            "title": "Arrive in Pokhara + Lakeside",
            "route": "Pokhara International Airport → Lakeside",
            "travel_distance": "~5 km",
            "travel_time": "~20–30 min",
            "overnight_stay": "Lakeside hotel (e.g. Annapurna Heritage Palace)",
            "morning": "Arrive at Pokhara airport. Collect luggage. Hotel transfer.",
            "afternoon": "Check in. Rest 1–2 hours. Walk around Lakeside. Visit Phewa Lake waterfront.",
            "evening": "Relaxed evening boat ride on Phewa Lake. Visit Tal Barahi Temple island. Sunset at Lakeside.",
            "practical_notes": "Pokhara International Airport (PKR) is at Prithvi Chowk. Taxis wait outside; agree fare before departure.",
            "primary_destination": dest_map.get("sarangkot"),
            "attractions": [pokhara],
        },
        {
            "day_number": 2,
            "title": "Sarangkot Sunrise + Paragliding",
            "route": "Lakeside → Sarangkot → Lakeside",
            "travel_distance": "~10–13 km each way",
            "travel_time": "~30–40 min each way",
            "overnight_stay": "Lakeside hotel",
            "morning": "4:30–5:00 AM drive to Sarangkot. Sunrise over Annapurna, Machhapuchhre (Fishtail), Dhaulagiri. Breakfast at hilltop café.",
            "afternoon": "Optional tandem paragliding (1–2 hrs including prep and transport). Return to Lakeside. Lunch. Hotel rest.",
            "evening": "Spa/massage. Lakeside walk. Phewa Lake sunset.",
            "practical_notes": "Mountain views are weather-dependent. Paragliding operators are lined up along Lakeside; book the evening before.",
            "primary_destination": dest_map.get("sarangkot"),
            "attractions": [dest_map.get("sarangkot")],
        },
        {
            "day_number": 3,
            "title": "Davis Falls + Gupteshwor Cave + Mountain Museum",
            "route": "Lakeside → Davis Falls → Gupteshwor Cave → International Mountain Museum → Lakeside",
            "travel_distance": "Short city circuit",
            "travel_time": "~10–15 min between sites",
            "overnight_stay": "Lakeside hotel",
            "morning": "Davis Falls (Patale Chhango). Gupteshwor Mahadev Cave — one of Nepal's largest caves with a Shiva lingam.",
            "afternoon": "International Mountain Museum — Himalayan mountaineering history, culture and climbing equipment exhibits.",
            "evening": "Lakeside shopping. Nepalese handicrafts. Coffee at Phewa waterfront.",
            "practical_notes": "Cave can be slippery; wear grippy shoes. Museum closed on Tuesdays.",
            "primary_destination": dest_map.get("davis"),
            "attractions": [dest_map.get("davis"), dest_map.get("gupteshwar")],
        },
        {
            "day_number": 4,
            "title": "World Peace Pagoda + Phewa Lake",
            "route": "Lakeside → Phewa Lake boat → opposite shore → hike → World Peace Pagoda",
            "travel_distance": "Boat + 30–40 min hike",
            "travel_time": "Half/full day",
            "overnight_stay": "Lakeside hotel",
            "morning": "Boat across Phewa Lake to the opposite shore. Hike up to World Peace Pagoda (Shanti Stupa) — panoramic Annapurna views.",
            "afternoon": "Boat back. Lunch at Lakeside. Rest. Optional kayaking on Phewa Lake.",
            "evening": "Sunset boat ride. Dinner at Lakeside.",
            "practical_notes": "The hike is ~300 steps; go early to avoid heat. Boat operators wait at the Pagoda base for return trips.",
            "primary_destination": dest_map.get("peace"),
            "attractions": [dest_map.get("peace")],
        },
        {
            "day_number": 5,
            "title": "Pumdikot + Damside + Relaxed Lakeside Evening",
            "route": "Lakeside → Pumdikot → Damside → Lakeside",
            "travel_distance": "~6–8 km to Pumdikot",
            "travel_time": "~20–30 min uphill",
            "overnight_stay": "Lakeside hotel",
            "morning": "Drive to Pumdikot. Large Shiva statue (135 ft) with panoramic Pokhara Valley and mountain views.",
            "afternoon": "Drive toward Damside. Relaxed lunch. International Mountain Museum area if missed on Day 3.",
            "evening": "Lakeside shopping. Nepalese handicrafts. Coffee. Phewa waterfront. Optional live cultural performance.",
            "practical_notes": "Pumdikot road is steep; taxi recommended. Best light in early morning.",
            "primary_destination": dest_map.get("pumdikot"),
            "attractions": [dest_map.get("pumdikot")],
        },
        {
            "day_number": 6,
            "title": "Begnas Lake + Rupa Lake",
            "route": "Lakeside → Prithvi Chowk → Begnas Lake → Rupa Lake → Lakeside",
            "travel_distance": "~14–15 km to Begnas",
            "travel_time": "~40–50 min by taxi/car",
            "overnight_stay": "Lakeside hotel",
            "morning": "Drive to Begnas Lake — quieter than Phewa. Boating. Village walks. Local lunch.",
            "afternoon": "Explore Rupa Lake area — terraced fields, rural Nepal. Photography.",
            "evening": "Return to Lakeside. Free evening.",
            "practical_notes": "Begnas and Rupa are among the quieter lake experiences around Pokhara. Carry water and sunscreen.",
            "primary_destination": dest_map.get("begnas"),
            "attractions": [dest_map.get("begnas"), dest_map.get("rupa")],
        },
        {
            "day_number": 7,
            "title": "Pokhara Cultural & Old City Day",
            "route": "Lakeside → Bindhyabasini Temple → Old Bazaar → Seti River Gorge → Lakeside",
            "travel_distance": "~4–5 km",
            "travel_time": "Short drives + walking",
            "overnight_stay": "Lakeside hotel",
            "morning": "Bindhyabasini Temple — Pokhara's oldest Hindu temple. Old Bazaar — traditional streets, local shops, spice markets.",
            "afternoon": "Seti River Gorge viewpoint — the river cuts deeply through the city. Lunch at a local restaurant.",
            "evening": "Sunset boat ride. Free time.",
            "practical_notes": "Old Bazaar is best explored on foot. Remove shoes at temple entrances.",
            "primary_destination": dest_map.get("bindhyabasini"),
            "attractions": [dest_map.get("bindhyabasini")],
        },
        {
            "day_number": 8,
            "title": "Australian Camp / Dhampus Hike",
            "route": "Lakeside → Kande → Australian Camp → Dhampus",
            "travel_distance": "~25 km to Kande + hiking",
            "travel_time": "~45 min drive + 3–4 hrs hiking",
            "overnight_stay": "Pokhara or Dhampus eco-lodge",
            "morning": "Early breakfast. Private vehicle to Kande. Hike toward Australian Camp — mountain views, forest, village scenery.",
            "afternoon": "Lunch at Australian Camp. Continue toward Dhampus depending on fitness. Return to Pokhara or stay overnight in a local lodge.",
            "evening": "If in Dhampus: village walk, local dinner, stargazing.",
            "practical_notes": "This is a real hike, not a sightseeing drive. Wear proper shoes. Carry water, snacks, rain jacket.",
            "primary_destination": dest_map.get("australian"),
            "attractions": [dest_map.get("australian"), dest_map.get("dhampus")],
        },
        {
            "day_number": 9,
            "title": "Relaxation / Spa / Phewa Lake",
            "route": "Lakeside (local)",
            "travel_distance": "—",
            "travel_time": "—",
            "overnight_stay": "Lakeside hotel",
            "morning": "Sleep late. Leisurely breakfast.",
            "afternoon": "Spa/massage. Café time. Phewa Lake kayaking. Shopping.",
            "evening": "Sunset boat ride. Dinner at Lakeside.",
            "practical_notes": "Rest day after hiking. Book spa treatments through your hotel.",
            "primary_destination": pokhara,
            "attractions": [pokhara],
        },
        {
            "day_number": 10,
            "title": "Ghandruk Excursion",
            "route": "Pokhara → Nayapul → Birethanti → Ghandruk",
            "travel_distance": "~42 km to Nayapul + trek",
            "travel_time": "~2 hrs drive + 4–5 hrs trek",
            "overnight_stay": "Ghandruk local lodge",
            "morning": "Drive to Nayapul. Trek through Birethanti, terraced fields, rhododendron forests to Ghandruk.",
            "afternoon": "Gurung culture. Traditional stone houses. Local food. Village walks. Himalayan views.",
            "evening": "Sunset over Annapurna South and Machhapuchhre. Dinner at lodge.",
            "practical_notes": "Make this a 2-day/1-night excursion. Book a licensed local trekking agency/lodge. TIMS card and ACAP permit required.",
            "primary_destination": dest_map.get("ghandruk"),
            "attractions": [dest_map.get("ghandruk"), dest_map.get("birethanti")],
        },
        {
            "day_number": 11,
            "title": "Ghandruk → Pokhara",
            "route": "Ghandruk → Nayapul → Pokhara",
            "travel_distance": "~42 km + trek",
            "travel_time": "4–5 hrs trek + 2 hrs drive",
            "overnight_stay": "Lakeside hotel",
            "morning": "Sunrise over Annapurna. Breakfast. Village walk. Photography.",
            "afternoon": "Trek back to Nayapul. Drive to Pokhara.",
            "evening": "Rest at hotel. Free evening.",
            "practical_notes": "Mountain roads take longer than city driving. Allow buffer time.",
            "primary_destination": dest_map.get("ghandruk"),
            "attractions": [dest_map.get("ghandruk")],
        },
        {
            "day_number": 12,
            "title": "Sarangkot Overnight Experience",
            "route": "Lakeside → Sarangkot",
            "travel_distance": "~10–13 km",
            "travel_time": "~30–40 min",
            "overnight_stay": "Sarangkot Mountain Lodge",
            "morning": "Leisurely breakfast. Drive to Sarangkot. Check into mountain lodge.",
            "afternoon": "Sarangkot village walk. Mountain viewpoint. Relax at the lodge. Sunset.",
            "evening": "Early dinner and rest.",
            "practical_notes": "Staying overnight means no pre-dawn drive for sunrise. Book lodge in advance.",
            "primary_destination": dest_map.get("sarangkot"),
            "attractions": [dest_map.get("sarangkot")],
        },
        {
            "day_number": 13,
            "title": "Sarangkot Sunrise + Return to Pokhara",
            "route": "Sarangkot → Lakeside",
            "travel_distance": "~10–13 km",
            "travel_time": "~30–40 min",
            "overnight_stay": "Lakeside hotel",
            "morning": "Wake before sunrise. Annapurna, Machhapuchhre, Dhaulagiri, Pokhara Valley — all from the lodge doorstep.",
            "afternoon": "Breakfast. Drive back to Lakeside. Free time.",
            "evening": "Last relaxed Phewa Lake evening. Dinner at Lakeside.",
            "practical_notes": "Mountain visibility is weather-dependent. Clouds can completely hide the peaks.",
            "primary_destination": dest_map.get("sarangkot"),
            "attractions": [dest_map.get("sarangkot")],
        },
        {
            "day_number": 14,
            "title": "Bandipur Day Trip",
            "route": "Pokhara → Damauli → Dumre → Bandipur",
            "travel_distance": "~72–80 km",
            "travel_time": "~2–2.5 hrs each way",
            "overnight_stay": "Lakeside hotel",
            "morning": "Drive to Bandipur via Prithvi Highway. Explore Bandipur Bazaar — traditional Newari architecture, Tundikhel, local cafés, hilltop views.",
            "afternoon": "Lunch at a Bandipur café. Village surroundings. Photography.",
            "evening": "Drive back to Pokhara. Overnight at Lakeside.",
            "practical_notes": "Bandipur is a preserved Newari hill town — no vehicles in the bazaar. Wear comfortable walking shoes.",
            "primary_destination": dest_map.get("bandipur"),
            "attractions": [dest_map.get("bandipur")],
        },
        {
            "day_number": 15,
            "title": "Final Pokhara Day + Departure",
            "route": "Lakeside → Pokhara International Airport",
            "travel_distance": "~5 km",
            "travel_time": "~20–30 min",
            "overnight_stay": "—",
            "morning": "Breakfast. Phewa Lake. Last shopping. Souvenirs. Coffee. Photography.",
            "afternoon": "If flight is late: International Mountain Museum, Davis Falls, or one last boat ride.",
            "evening": "Transfer to airport. Allow 30–45 min buffer beyond normal transfer time.",
            "practical_notes": "Keep travel insurance covering trekking/adventure activities. Carry passport and insurance copies. Save hospital and Tourist Police numbers offline.",
            "primary_destination": pokhara,
            "attractions": [pokhara],
        },
    ]

    for day_data in days_data:
        day, created = TravelGuideDay.objects.update_or_create(
            guide=guide,
            day_number=day_data["day_number"],
            defaults={
                "title": day_data["title"],
                "route": day_data.get("route", ""),
                "travel_distance": day_data.get("travel_distance", ""),
                "travel_time": day_data.get("travel_time", ""),
                "overnight_stay": day_data.get("overnight_stay", ""),
                "morning": day_data.get("morning", ""),
                "afternoon": day_data.get("afternoon", ""),
                "evening": day_data.get("evening", ""),
                "practical_notes": day_data.get("practical_notes", ""),
                "primary_destination": day_data.get("primary_destination"),
            },
        )
        if day_data.get("attractions"):
            day.attractions.set([a for a in day_data["attractions"] if a])
        if day_number := day_data["day_number"]:
            day.hotels.set(hotels[:3] if day_number in (1, 2, 3, 4, 5, 6, 7, 9, 11, 13, 14, 15) else [])
            day.hospitals.set(hospitals if day_number == 1 else [])
        print(f"  Day {day.day_number}: {day.title} ({'created' if created else 'updated'})")

    print(f"\nDone. Guide has {guide.days.count()} days, {hotels.count()} hotels, {hospitals.count()} hospitals linked.")


if __name__ == "__main__":
    seed()
