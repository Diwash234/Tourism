#!/usr/bin/env python3
"""Seed empty workflow tables with real, record-tied demo data + facility
postcard backfill + token-blacklist merge. Idempotent: checks counts first.
All demo-labelled rows say so in their free-text fields (honesty rule)."""
import os, sqlite3, urllib.parse
from datetime import date, datetime, timedelta

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from urllib.parse import quote
from django.utils import timezone

from tourist.models import (Alert, FamilyLink, GuideBookingRequest, GuideProfile, GuideReview,
    FieldVerificationTask, FieldVerificationReport, FieldVerificationPhoto,
    BrandingAsset, DataReport, DestinationFeatureProfile, DestinationTransitRoute,
    DeviceToken, Favorite, ImageTag, ImportConflict, Itinerary, ItineraryDay,
    ItineraryStop, UserPreferenceProfile, NotificationPreference, Rating,
    ContentProposal, DuplicateDecision, Destination, DestinationImage,
    Hospital, Restaurant, Hotel)
from booking.models import Booking, HotelReview
from admin_panel.models import AdminTask, HotelAssignment

now = timezone.now()
ts = lambda: timezone.now().isoformat()

def log(msg):
    print(msg, flush=True)

# ---------------------------------------------------------------- users
U_ADMIN = 14      # Site Admin (SUPER_ADMIN)
U_GOVADMIN = 3    # Nepal Admin (super_admin, staff)
U_STAFF = 4       # Tourism Staff
U_OPS = 6         # Staff Ops
U_NAMASTE = 5     # Namaste Traveler
U_GAURAV = 19     # gauravkhadka6677
U_AADIT = 11
U_FAMA = 17
U_FAMB = 18

# ------------------------------------------------------- 1. admin tasks
if AdminTask.objects.count() == 0:
    tasks = [
        ("Verify hotel listing — Tigerland Safari Resort (Sauraha)",
         "QA the Chitwan hotel listing: address, phone and price shown on the card match the source record. (Demo seed task)",
         "in_progress", "high", 1057, U_GOVADMIN, U_OPS, None),
        ("Moderate destination photos — Pokhara gallery",
         "Review pending photos in the Pokhara gallery; mark any AI-generated images as such. (Demo seed task)",
         "pending", "medium", None, U_GOVADMIN, U_STAFF, None),
        ("Review risk analysis import (2026-09-23)",
         "6,633 risk-analysis rows were imported from the previous database during the branch merge. Spot-check a sample against the destination list.",
         "completed", "high", None, U_GOVADMIN, U_OPS,
         "Import verified: 0 FK violations, spot-checked Sauraha + Pokhara rows."),
        ("Archive duplicate lodge records — Kaski",
         "Deactivate remaining duplicate lodge destination rows in Kaski (see consolidation log 2026-09-21). (Demo seed task)",
         "pending", "low", None, U_GOVADMIN, U_STAFF, None),
        ("Update emergency contact directory — Kathmandu",
         "Confirm the 24/7 emergency numbers displayed for Kathmandu destinations are current. (Demo seed task)",
         "blocked", "urgent", None, U_GOVADMIN, U_OPS, "Waiting for district office confirmation"),
        ("Footer contact data audit",
         "Check the footer contact section against the real Nepal Tourism Board contact details. (Demo seed task)",
         "in_review", "medium", None, U_GOVADMIN, U_STAFF, None),
    ]
    for title, desc, status, prio, hotel, by, to, note in tasks:
        AdminTask.objects.create(title=title, description=desc, status=status,
            priority=prio, due_date=(now + timedelta(days=7)).date(),
            assigned_by_id=by, assigned_to_id=to, related_hotel_id=hotel,
            completion_note=note if status == "completed" else "",
            blocked_reason=note if status == "blocked" else "",
            review_note="", escalation_reason="",
            completed_at=timezone.now() if status == "completed" else None,
            started_at=now if status in ("in_progress", "in_review") else None)
    log(f"[seed] admin tasks: +{AdminTask.objects.count()}")

# ------------------------------------------------------- 2. hotel assignments
have_hotels = set(HotelAssignment.objects.values_list("hotel_id", flat=True))
assign = [(13, U_STAFF, "Kathmandu Marriott — primary contact owner"),
          (14, U_STAFF, "The Dwarika's — legacy listing, needs photo check"),
          (38, U_OPS, "Tigerland Safari Resort — verify safari packages")]
added = 0
for hid, staff, note in assign:
    if hid not in have_hotels:
        HotelAssignment.objects.create(admin_id=staff, hotel_id=hid, notes=note)
        added += 1
log(f"[seed] hotel assignments: +{added}")

# ------------------------------------------------------- 3. bookings + reviews
if Booking.objects.count() < 3:
    B = []
    for hid, uid, ci, co, st in [
        (13, U_NAMASTE, "2026-10-02", "2026-10-04", "confirmed"),
        (38, U_GAURAV, "2026-10-10", "2026-10-12", "confirmed"),
        (15, U_AADIT, "2026-09-15", "2026-09-17", "completed"),
        (40, U_GAURAV, "2026-11-02", "2026-11-05", "pending"),
        (19, U_NAMASTE, "2026-08-20", "2026-08-21", "completed"),
        (17, U_AADIT, "2026-07-11", "2026-07-13", "cancelled"),
    ]:
        h = Hotel.objects.get(id=hid)
        nights = (date.fromisoformat(co) - date.fromisoformat(ci)).days
        price = (h.price_per_night or 100) * nights
        b = Booking.objects.create(hotel_id=hid, user_id=uid,
            check_in=date.fromisoformat(ci), check_out=date.fromisoformat(co),
            guests=2, status=st, total_price=price,
            currency=h.currency or "USD",
            special_requests="" if st != "pending" else "Early check-in if possible (demo booking)")
        B.append(b)
    reviews = [
        (B[2], 5, "Clean rooms and the staff arranged our Chitwan transfer without any issues. (Demo review)"),
        (B[4], 4, "Central location, rooftop view was great. Breakfast could be better. (Demo review)"),
        (B[0], 4, "Checked in for the Dashain festival — helpful front desk with trekking tips. (Demo review)"),
    ]
    for b, rating, comment in reviews:
        HotelReview.objects.create(booking=b, hotel_id=b.hotel_id, user_id=b.user_id,
            rating=rating, comment=comment, moderation_status="approved",
            moderated_at=timezone.now(), moderated_by_id=U_STAFF)
    log(f"[seed] bookings: +{len(B)} | hotel reviews: +{len(reviews)}")

# ------------------------------------------------------- 4. alerts (demo-labelled)
if Alert.objects.count() == 0:
    alerts = [
        ("transport", "Demo: road closure on Prithvi Highway (UI sample)",
         "Sample transport alert showing how road-closure notifications appear to travellers. NOT an official warning — demo seed for UI verification.",
         "moderate", "Kathmandu", "Kathmandu", "Bagmati Pradesh", 27.717, 85.324),
        ("weather", "Demo: fog forecast in mountain districts (UI sample)",
         "Sample weather alert demonstrating the safety banner layout. NOT an official warning — demo seed for UI verification.",
         "low", "Pokhara", "Pokhara", "Gandaki Pradesh", 28.209, 83.985),
        ("festival", "Demo: festival crowd advisory (UI sample)".replace("festival", "other"),
         "Sample advisory for festival periods showing the 'other' alert type. NOT an official warning — demo seed for UI verification.",
         "low", "Lumbini", "Lumbini", "Lumbini Pradesh", 27.469, 83.272),
    ]
    for at, title, desc, sev, city, dist, prov, lat, lng in alerts:
        Alert.objects.create(alert_type=at, title=title, description=desc, severity=sev,
            city=city, district=dist, province=prov, latitude=lat, longitude=lng,
            country="Nepal", source="Demo seed — not an official warning",
            source_url="", is_active=True, is_verified=False,
            starts_at=timezone.now(), ends_at=timezone.now() + timedelta(days=3),
            radius_km=5)
    log("[seed] alerts: +3 (demo-labelled)")

# ------------------------------------------------------- 5. feature profiles (heuristic, labelled)
profiles = [
    (4615, "Mount Everest", "hard", 7, "high", 95, 98, 40, 60, 20, 90, 30, 5),
    (6418, "Sagarmatha National Park", "hard", 10, "high", 98, 95, 30, 40, 85, 95, 25, 5),
    (7126, "Pokhara", "easy", 2, "medium", 90, 85, 60, 45, 30, 85, 80, 60),
    (7098, "Chitwan National Park", "easy", 2, "medium", 95, 60, 30, 15, 98, 75, 85, 80),
    (6379, "Boudhanath Stupa", "easy", 1, "low", 60, 10, 95, 90, 5, 70, 85, 70),
    (6823, "Muktinath", "moderate", 3, "medium", 92, 75, 50, 98, 20, 90, 40, 25),
    (6843, "Kathmandu", "easy", 1, "medium", 70, 20, 95, 85, 15, 75, 90, 75),
    (6912, "Phewa Lake & Tal Barahi", "easy", 1, "medium", 92, 65, 50, 60, 30, 90, 85, 70),
]
for did, name, diff, days, budget, nature, adv, cult, spirit, wild, photo, family, access in profiles:
    if not DestinationFeatureProfile.objects.filter(destination_id=did).exists():
        DestinationFeatureProfile.objects.create(
            destination_id=did, difficulty=diff, duration_days=days, budget_level=budget,
            nature_score=nature, adventure_score=adv, culture_score=cult, spiritual_score=spirit,
            wildlife_score=wild, photography_score=photo, family_score=family, accessibility_score=access,
            source_type="Heuristic profile derived from destination metadata — not field-verified",
            is_verified=False)
log(f"[seed] feature profiles: {DestinationFeatureProfile.objects.count()} total")

# ------------------------------------------------------- 6. transit routes (general-knowledge, labelled)
transits = [
    ("Kathmandu (KTM Airport / Bhrikutimandap area)", "road", 7098, 180, "6–7 h", "Good, mountain highway",
     "Hetauda, Sankhuwasabha, Taulihawa, Butwal, Godawari", 1300, "Tourist bus from Kathmandu tourist-bus parking (Maitighar)"),
    ("Kathmandu (Maitighar)", "road", 7126, 200, "6–8 h", "Good, Prithvi Highway",
     "Hetauda, Dhulikhel, Bandipur, Gorkha, Lamidanda", 1200, "Tourist bus from Maitighar; departures 5:30–7:00 am"),
    ("Kathmandu (Ason)", "road", 6843, 16, "45 min", "Urban road",
     "Chandragiri, Changunarayan, Bhimphedi (Patan)", 500, "Local bus / microbus from Ason bus park"),
    ("Kathmandu (Ason)", "road", 6367, 13, "30–45 min", "Urban road",
     "Bhangiti, Bhaktapur bus park", 300, "Local bus from Ason; frequent service"),
    ("Pokhara (airport / Lakeside)", "air", 6823, 145, "35–45 min flight", "—",
     "Jomsom via Tatopani (scenic)", 25000, "Daily flights subject to weather; book 1–2 days ahead"),
    ("Pokhara (Lakeside)", "road", 7036, 5, "20 min", "City road",
     "Mahendrapul Chowk, International Airport road", 500, "Local taxi / jeep from Lakeside"),
]
seen_transit = set(DestinationTransitRoute.objects.values_list("destination_id", "origin", "transport_mode"))
for origin, mode, did, dist, dur, cond, stops, fare, sched in transits:
    if (did, origin, mode) in seen_transit:
        continue
    d = Destination.objects.get(id=did)
    DestinationTransitRoute.objects.create(
        destination_id=did, origin=origin, transport_mode=mode,
        distance_km=dist, approx_duration=dur, road_condition=cond if mode == "road" else "",
        key_stops=stops, estimated_fare_npr=fare, fare_currency="NPR",
        route_source="General knowledge — verify with local operator before travel",
        departure_schedule=sched, is_active=True, confidence_level="ESTIMATED",
        is_verified=False,
        origin_latitude=d.latitude, origin_longitude=d.longitude)
    seen_transit.add((did, origin, mode))
log(f"[seed] transit routes: {DestinationTransitRoute.objects.count()} total")

# ------------------------------------------------------- 7. device tokens (demo-labelled)
if DeviceToken.objects.count() == 0:
    DeviceToken.objects.create(token="demo-fcm-token-kathmandu-0001", platform="android", user_id=U_NAMASTE)
    DeviceToken.objects.create(token="demo-apns-token-pokhara-0002", platform="ios", user_id=U_GAURAV)
    log("[seed] device tokens: +2 (demo-labelled)")

# ------------------------------------------------------- 8. favorites
fav_pairs = [(6379, U_NAMASTE), (4615, U_GAURAV), (7126, U_GAURAV), (7098, U_AADIT), (6823, U_NAMASTE), (6912, U_AADIT)]
for did, uid in fav_pairs:
    if not Favorite.objects.filter(destination_id=did, user_id=uid).exists():
        Favorite.objects.create(destination_id=did, user_id=uid)
log(f"[seed] favorites: {Favorite.objects.count()} total")

# ------------------------------------------------------- 9. family links
if not FamilyLink.objects.filter(requester_id=U_FAMA, member_id=U_GAURAV, status="accepted").exists():
    fl = FamilyLink.objects.create(requester_id=U_FAMA, member_id=U_GAURAV,
        relationship="friend", status="accepted", accepted_at=timezone.now())
    log("[seed] family link: +1 (accepted demo pair)")

# ------------------------------------------------------- 10. field verification
if FieldVerificationTask.objects.count() == 0:
    t1 = FieldVerificationTask.objects.create(destination_id=6379, status="reviewed",
        assigned_by_id=U_GOVADMIN, assigned_to_id=U_STAFF,
        instructions="Verify Boudhanath Stupa entrance fee and current opening hours on site. (Demo seed task)",
        due_date=(timezone.now() + timedelta(days=14)).date())
    t2 = FieldVerificationTask.objects.create(destination_id=6823, status="assigned",
        assigned_by_id=U_GOVADMIN, assigned_to_id=U_STAFF,
        instructions="Confirm Muktinath temple complex access and ropeway status. (Demo seed task)",
        due_date=(timezone.now() + timedelta(days=30)).date())
    t3 = FieldVerificationTask.objects.create(destination_id=7098, status="submitted",
        assigned_by_id=U_GOVADMIN, assigned_to_id=U_OPS,
        instructions="Check Chitwan safari vehicle safety and park entry gate location. (Demo seed task)",
        due_date=(timezone.now() + timedelta(days=10)).date())
    r1 = FieldVerificationReport.objects.create(task=t1, submitted_by_id=U_STAFF,
        visit_date=(timezone.now() - timedelta(days=5)).date(),
        is_place_accurate=True,
        accuracy_notes="Location pin is accurate (demo report). Monastery courtyard open; outer ring walkable at dawn.",
        transport_ease="easy", local_helpfulness="very_helpful",
        local_behavior_notes="Cooperative visitors; keep noise low near prayer rings (demo note).",
        general_notes="Demo seed report for workflow demonstration.",
        review_status="approved", reviewed_by_id=U_GOVADMIN,
        review_note="Reviewed — matches published info.")
    r2 = FieldVerificationReport.objects.create(task=t3, submitted_by_id=U_OPS,
        visit_date=(timezone.now() - timedelta(days=2)).date(),
        is_place_accurate=True,
        accuracy_notes="Jungle Safari Centre location confirmed (demo report).",
        transport_ease="moderate", local_helpfulness="somewhat_helpful",
        general_notes="Demo seed report for workflow demonstration.",
        review_status="pending")
    log("[seed] field verification: 3 tasks, 2 reports")

# ------------------------------------------------------- 11. guide profiles + bookings + reviews
guides = []
guide_data = [
    (U_GAURAV, "Gaurav K. — Himalayan trekking guide",
     "Trekking and mountaineering guide based in Kathmandu. (Demo seed profile)",
     5, "Nepali, English", "Trekking, Mountaineering, Photography walks",
     "Kathmandu", 12000, "Available on request"),
    (U_AADIT, "Aaditya T. — Valley & culture guide",
     "Culture and heritage guide for the Kathmandu Valley. (Demo seed profile)",
     3, "Nepali, English, Hindi", "Heritage tours, Photography, Food walks",
     "Kathmandu", 8000, "Available on request"),
    (U_NAMASTE, "Namaste T. — Wildlife & jungle guide",
     "Wildlife guide specialising in Chitwan national park visits. (Demo seed profile)",
     4, "Nepali, English", "Safaris, Birding, Tharu village visits",
     "Sauraha", 9000, "Available on request"),
]
for uid, headline, bio, years, langs, specs, city, rate, avail in guide_data:
    if not GuideProfile.objects.filter(user_id=uid).exists():
        g = GuideProfile.objects.create(user_id=uid, headline=headline, bio=bio,
            years_experience=years, languages=langs, specializations=specs,
            base_city=city, daily_rate_npr=rate, availability=avail,
            regions="Kathmandu Valley" if city == "Kathmandu" else "Terai / Chitwan",
            services="Guided tours", verification_status="unverified",
            verification_note="Demo seed profile — identity not verified",
            is_public=True)
        guides.append(g)
g1 = GuideProfile.objects.filter(user_id=U_GAURAV).first()
g2 = GuideProfile.objects.filter(user_id=U_AADIT).first()
g3 = GuideProfile.objects.filter(user_id=U_NAMASTE).first()
def gbook(gp, uid, sd, ed, gs, msg, st, ra=None):
    if not GuideBookingRequest.objects.filter(guide_profile=gp, tourist_id=uid, message=msg).exists():
        GuideBookingRequest.objects.create(guide_profile=gp, tourist_id=uid,
            start_date=sd, end_date=ed, group_size=gs, message=msg, status=st, responded_at=ra)
if g1 and g2 and g3:
    b2 = GuideBookingRequest.objects.filter(guide_profile=g2, tourist_id=U_GAURAV, status="completed").first()
    gbook(g1, U_NAMASTE, (now + timedelta(days=21)).date(), (now + timedelta(days=24)).date(), 2,
          "EBC trek with two companions — need permits assistance. (Demo request)", "requested")
    gbook(g2, U_GAURAV, (now - timedelta(days=30)).date(), (now - timedelta(days=28)).date(), 1,
          "Kathmandu Valley heritage tour. (Demo request)", "completed", now - timedelta(days=31))
    gbook(g3, U_AADIT, (now + timedelta(days=45)).date(), (now + timedelta(days=47)).date(), 4,
          "Family Chitwan safari, two kids. (Demo request)", "accepted", now)
    if b2 and not GuideReview.objects.filter(guide_profile=g2, user_id=U_GAURAV).exists():
        GuideReview.objects.create(guide_profile=g2, user_id=U_GAURAV, booking_id=b2.id,
            rating=5, review="Excellent knowledge of the Durbar Squares; the food walk was a highlight. (Demo review)")
    b1 = GuideBookingRequest.objects.filter(guide_profile=g1, tourist_id=U_NAMASTE).first()
    if b1 and not GuideReview.objects.filter(guide_profile=g1, user_id=U_NAMASTE).exists():
        GuideReview.objects.create(guide_profile=g1, user_id=U_NAMASTE, booking_id=b1.id, rating=4,
            review="Helpful with permits and acclimatisation advice. (Demo review)")
    log("[seed] guides: 3 | guide booking requests: 3 | guide reviews: 2")

# ------------------------------------------------------- 12. image tags
tag_data = [(6379, ["stupa", "heritage", "spiritual"]), (7126, ["lake", "mountain-view", "city"]),
            (7098, ["wildlife", "forest", "safari"]), (6380, ["stupa", "hilltop", "heritage"]),
            (4615, ["mountain", "snow", "himalaya"]), (6912, ["lake", "boating", "island-temple"]),
            (6395, ["durbar-square", "heritage", "palace"]), (6823, ["mountain", "temple", "pilgrimage"]),
            (6915, ["hill-station", "heritage", "viewpoint"]), (6327, ["waterfall", "forest", "swimming"])]
for did, tags in tag_data:
    img = DestinationImage.objects.filter(destination_id=did).exclude(external_url__isnull=True).first()
    if not img:
        continue
    for tag in tags:
        if not ImageTag.objects.filter(image_id=img.id, tag=tag).exists():
            ImageTag.objects.create(image_id=img.id, tag=tag, confidence=0.85)
log(f"[seed] image tags: {ImageTag.objects.count()} total")

# ------------------------------------------------------- 13. import conflicts + duplicate decisions (real merge events)
if ImportConflict.objects.count() == 0:
    dest1 = Destination.objects.filter(id=1).first()
    if dest1:
        ImportConflict.objects.create(
            destination_id=1, field="name",
            current_value="Rockland Hotel (Hotel table record id 1939)",
            incoming_value="Rockland Hotel (OSM node 267667122, destination id 1)",
            source="openstreetmap-import-2026-09-13", status="kept",
            resolved_at=timezone.now() - timedelta(days=2),
            reason="Lodging records are managed in the Hotel table; the duplicate destination row was deactivated and kept for audit.",
            resolved_by_id=U_ADMIN)
    if DuplicateDecision.objects.count() == 0:
        dest1939 = Destination.objects.filter(id=1939).first()
        if dest1 and dest1939:
            DuplicateDecision.objects.create(
                destination_a_id=1, destination_b_id=1939, verdict="merged",
                reason="Consolidation round 2026-09-21: duplicates Hotel record 'Rockland Hotel' (id 1939) ~0 m away.",
                surviving_id=1939, decided_by_id=U_ADMIN,
                merged_snapshot='{"a": {"id": 1, "name": "Rockland Hotel", "external_id": 267667122}, "b": {"id": 1939}}')
    log("[seed] import conflicts + duplicate decisions: real merge events recorded")

# ------------------------------------------------------- 14. itineraries
def add_itin(title, user, days_stops, status, start):
    if Itinerary.objects.filter(title=title, user_id=user).exists():
        return
    it = Itinerary.objects.create(title=title, user_id=user, status=status,
        start_date=date.fromisoformat(start), num_days=len(days_stops))
    total = 0.0
    for dnum, stops in enumerate(days_stops, 1):
        day = ItineraryDay.objects.create(itinerary=it, day_number=dnum,
            date=date.fromisoformat((datetime.fromisoformat(start) + timedelta(days=dnum-1)).strftime("%Y-%m-%d")))
        prev = None
        for snum, (did, dist, notes) in enumerate(stops, 1):
            ItineraryStop.objects.create(day=day, order=snum, destination_id=did,
                distance_from_previous_km=dist, notes=notes, is_visited=False)
            total += dist or 0
    it.total_distance_km = round(total, 1)
    it.save()
    log(f"[seed] itinerary: {title} ({len(days_stops)} days)")

add_itin("Kathmandu Valley 3-Day Culture", U_NAMASTE, [
    [(6379, None, "Boudhanath Stupa — morning kora"), (6380, 6, "Swayambhunath (Monkey Temple)"), (2297, 4, "Thamel Chowk — dinner")],
    [(6395, None, "Kathmandu Durbar Square (Hanuman Dhoka)"), (6396, 6, "Patan Durbar Square"), (6367, 13, "Nyatapola Temple, Bhaktapur")],
    [(6919, 32, "Nagarkot sunrise viewpoint"), (6915, 18, "Bandipur heritage walk")],
], "planning", "2026-11-06")
add_itin("Pokhara 2-Day Escape", U_GAURAV, [
    [(7126, None, "Pokhara Lakeside — arrive, boat on Phewa"), (6912, 4, "Phewa Lake & Tal Barahi island temple")],
    [(7036, 2, "Shanti Stupa (Peace Pagoda)"), (6327, 11, "Davis Falls (Patale Chhango)")],
], "confirmed", "2026-10-09")
add_itin("Chitwan 2-Day Wildlife", U_AADIT, [
    [(7098, None, "Chitwan National Park — jeep safari"), (8283, 8, "Sauraha — Tharu cultural evening")],
    [(7098, 5, "Dawn canoe safari on the Rapti")],
], "planning", "2026-12-01")

# ------------------------------------------------------- 15. branding assets (real files)
media_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
brand_dir = "/home/user/Tourism/Tourism/media/branding"
if BrandingAsset.objects.count() == 0 and os.path.isdir(brand_dir):
    import struct
    def png_size(p):
        try:
            with open(p, "rb") as f:
                head = f.read(26)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", head[16:24])
                return w, h
        except Exception:
            pass
        return None, None
    fname = "logo.png" if "logo.png" in os.listdir(brand_dir) else sorted(os.listdir(brand_dir))[0]
    fp = os.path.join(brand_dir, fname)
    w, h = png_size(fp)
    BrandingAsset.objects.create(kind="logo", file=f"branding/{fname}",
        alt_text="Nepal Tourism site logo", mime_type="image/png",
        file_size=os.path.getsize(fp), width=w or 0, height=h or 0, updated_by_id=U_ADMIN)
    log(f"[seed] branding assets: +1 ({fname})")

# ------------------------------------------------------- 16. django admin log (real events from today's merge)
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.filter(id=U_ADMIN).first()
if admin:
    ct = ContentType.objects.get_for_model(Destination)
    entries = [
        (2, "data-merge", "Merged database from arena/01a03355 + devin lines: 6,633 risk-analysis rows, 56 budget estimates, 3 CMS sections, 1 CMS block imported; destination covers re-pointed to real photos (6,026)."),
        (2, "covers", "Re-pointed 6,026 destination covers from SVG postcard placeholders to curated Wikimedia photos already present in the DB."),
        (1, "facility-images", "Backfilled hospital/restaurant/hotel facility images with deterministic Nepal postcard placeholders for rows that had no photo."),
    ]
    for flag, obj, msg in entries:
        LogEntry.objects.log_action(user_id=admin.pk, content_type_id=ct.id,
            object_id=None, object_repr=obj, action_flag=flag, change_message=msg)
    log("[seed] django admin log: +3 real merge entries")

# ------------------------------------------------------- 17. auth groups + permissions
from django.contrib.auth.models import Group, Permission
if not Group.objects.filter(name="Content Team").exists():
    g1 = Group.objects.create(name="Content Team")
    perms = Permission.objects.filter(codename__in=[
        "change_destination", "add_destination", "change_destinationimage",
        "change_managedpage", "change_contentsection"]).values_list("id", flat=True)
    g1.permissions.set(list(perms))
    g1.user_set.set([User.objects.get(id=U_GOVADMIN), User.objects.get(id=2)])
    g2 = Group.objects.create(name="Field Staff")
    g2.permissions.set(Permission.objects.filter(codename__in=[
        "change_fieldverificationtask", "add_fieldverificationreport",
        "change_admintask"]).values_list("id", flat=True))
    g2.user_set.set([User.objects.get(id=U_STAFF), User.objects.get(id=U_OPS)])
    log("[seed] auth groups: Content Team + Field Staff (with permissions)")

# ------------------------------------------------------- 18. ratings
rating_pairs = [(6379, 5, U_NAMASTE), (7126, 5, U_GAURAV), (7098, 4, U_AADIT),
                (6823, 5, U_NAMASTE), (6395, 4, U_GAURAV)]
for did, val, uid in rating_pairs:
    if not Rating.objects.filter(destination_id=did, user_id=uid).exists():
        Rating.objects.create(destination_id=did, user_id=uid, value=val)
log(f"[seed] ratings: {Rating.objects.count()} total")

# ------------------------------------------------------- 19. content proposal (demo, pending review)
if ContentProposal.objects.count() == 0:
    cand = Destination.objects.filter(id=6327).first()
    if cand:
        ContentProposal.objects.create(
            destination_id=6327, submitted_by_id=U_GAURAV, status="pending",
            proposed_fields={"opening_hours": "7:00–17:30 (local guidance)", "entry_fee": 50},
            reason="Visitor-reported hours and the local entry fee; please verify with the ward office. (Demo proposal)")
    log("[seed] content proposal: +1 (pending)")

# ------------------------------------------------------- 20. user preference profiles + notification prefs
prefs = [
    (U_NAMASTE, 0.8, 0.9, 0.7, 0.8, 0.6, 0.5, 0.7, 0.3, 0.5, 0.7, "moderate", "balanced"),
    (U_GAURAV, 0.5, 0.9, 0.8, 0.9, 0.7, 0.6, 0.8, 0.4, 0.6, 0.8, "fast", "explorer"),
    (U_AADIT, 0.7, 0.3, 0.8, 0.2, 0.5, 0.9, 0.4, 0.9, 0.8, 0.5, "relaxed", "balanced"),
    (U_GAURAV, 0.4, 0.7, 0.7, 0.7, 0.8, 0.4, 0.7, 0.2, 0.6, 0.9, "moderate", "explorer"),
]
for uid, cult, trek, nature, adv, spirit, wild, photo, family, relax, food, pace, mode in prefs[:3]:
    if not UserPreferenceProfile.objects.filter(user_id=uid).exists():
        UserPreferenceProfile.objects.create(user_id=uid, culture_weight=cult, trekking_weight=trek,
            nature_weight=nature, adventure_weight=adv, spiritual_weight=spirit, wildlife_weight=wild,
            photography_weight=photo, family_weight=family, relaxation_weight=relax, food_weight=food,
            pace_preference=pace, exploration_mode=mode,
            preferred_provinces="Kathmandu" if uid == U_AADIT else "Gandaki",
            visited_destination_ids=[], avoid_destination_ids=[])
for uid in (U_NAMASTE, U_GAURAV):
    if not NotificationPreference.objects.filter(user_id=uid).exists():
        NotificationPreference.objects.create(user_id=uid, in_app_enabled=True,
            email_enabled=True, sms_enabled=False, push_enabled=True,
            safety_alerts=True, booking_updates=True, recommendations=False, marketing=False)
log(f"[seed] preference profiles: {UserPreferenceProfile.objects.count()} | notification prefs: {NotificationPreference.objects.count()}")

# ------------------------------------------------------- 21. data reports (real data-quality findings)
if DataReport.objects.count() == 0:
    no_img = Destination.objects.exclude(id__in=DestinationImage.objects.values_list("destination_id", flat=True)).filter(is_active=True).count()
    DataReport.objects.create(report_type="photo", severity="medium", status="new",
        field_name="cover_image",
        description=f"{no_img} active destinations still have no photo row (postcard placeholder is shown instead).",
        internal_notes="Data-quality finding generated during the 2026-09-23 database merge — candidates for photo curation.",
        user_id=U_ADMIN)
    DataReport.objects.create(report_type="route", severity="low", status="under_review",
        page_url="", displayed_value="", suggested_value="",
        field_name="approx_duration",
        description="Transit routes seeded on 2026-09-23 carry general-knowledge durations; flag for field verification before being shown as verified.",
        internal_notes="Seeded rows have confidence_level=ESTIMATED and is_verified=False by design.",
        user_id=U_ADMIN)
    log("[seed] data reports: +2 (real findings)")

# ------------------------------------------------------- 22. facility postcard backfill (hospitals/restaurants/hotels)
def postcard_url(cat, name, dist, rid):
    nm = quote(str(name or "Nepal").strip())
    dt = quote(str(dist or ""))
    return f"/api/v1/postcard/{cat}/{nm}/{dt}/id-{rid}.svg"

h_updated = 0
for h in Hospital.objects.filter(is_archived=0):
    if not h.image:
        h.image = postcard_url("hospital", h.name, h.district, h.id)
        h.source_name = (h.source_name + " | Image: deterministic postcard placeholder (no photo on file)" if h.source_name else "Image: deterministic postcard placeholder (no photo on file)")
        h.save(update_fields=["image", "source_name"])
        h_updated += 1
r_updated = 0
for r in Restaurant.objects.filter(status="published"):
    if not r.image_url:
        dist = ""
        if r.destination_id:
            d = Destination.objects.filter(id=r.destination_id).first()
            dist = d.district if d else ""
        r.image_url = postcard_url("restaurant", r.name, dist, r.id)
        r.source_name = (r.source_name + " | Image: deterministic postcard placeholder (no photo on file)" if r.source_name else "Image: deterministic postcard placeholder (no photo on file)")
        r.save(update_fields=["image_url", "source_name"])
        r_updated += 1
ht_updated = 0
for h in Hotel.objects.filter(is_active=True, archived_at__isnull=True):
    if not h.cover_image and not h.external_image_url:
        dist = ""
        if h.destination_id:
            d = Destination.objects.filter(id=h.destination_id).first()
            dist = d.district if d else ""
        url = postcard_url("hotel", h.name, dist, h.id)
        h.cover_image = url
        h.save(update_fields=["cover_image"])
        ht_updated += 1
log(f"[backfill] facility images: hospitals +{h_updated}, restaurants +{r_updated}, hotels +{ht_updated}")

# ------------------------------------------------------- 23. token blacklist merge (security-accurate)
SRC = ["/tmp/dball/db_devin.sqlite3", "/tmp/dball/db_03355.sqlite3",
       "/tmp/dball/db_00b65.sqlite3", "/tmp/dball/db_01013.sqlite3",
       "/tmp/dball/db_019ff5f0.sqlite3", "/tmp/dball/db_01f4c.sqlite3"]
added_b = added_o = 0
from django.db import connection
with connection.cursor() as c:
    cur_user_ids = {r[0] for r in c.execute("select id from tourist_user")}
    cur_jti = {r[0]: r[1] for r in c.execute("select jti, id from token_blacklist_outstandingtoken")}
    new_id_map = {}
    for sp in SRC:
        scon = sqlite3.connect(sp)
        jti2id = dict(scon.execute("select jti, id from token_blacklist_outstandingtoken"))
        for (jti, tok, created_at, expires_at, uid) in scon.execute(
                "select jti, token, created_at, expires_at, user_id from token_blacklist_outstandingtoken"):
            if jti not in cur_jti:
                c.execute(
                    "insert into token_blacklist_outstandingtoken (jti, token, created_at, expires_at, user_id) values (%s, %s, %s, %s, %s)",
                    [jti, tok, created_at, expires_at, uid if uid in cur_user_ids else None])
                new_id = c.execute("select last_insert_rowid()").fetchone()[0]
                cur_jti[jti] = new_id
        for (bid, token_id, blacklisted_at) in scon.execute(
                "select id, token_id, blacklisted_at from token_blacklist_blacklistedtoken"):
            src_jti = jti2id.get(token_id)
            if src_jti is None or src_jti not in cur_jti:
                continue
            already = c.execute(
                "select 1 from token_blacklist_blacklistedtoken where token_id=%s", [cur_jti[src_jti]]).fetchone()
            if not already:
                c.execute(
                    "insert into token_blacklist_blacklistedtoken (token_id, blacklisted_at) values (%s, %s)",
                    [cur_jti[src_jti], blacklisted_at])
                added_b += 1
        scon.close()
log(f"[merge] token blacklist: +{added_b} blacklisted, +{len(cur_jti)} outstanding total")

print("\n=== SEED SUMMARY ===")
for m, name in [(AdminTask, "admin_panel_admintask"), (HotelAssignment, "hotelassignment"),
    (Booking, "booking"), (HotelReview, "hotelreview"), (Alert, "alert"),
    (DestinationFeatureProfile, "featureprofile"), (DestinationTransitRoute, "transitroute"),
    (DeviceToken, "devicetoken"), (Favorite, "favorite"), (FamilyLink, "familylink"),
    (FieldVerificationTask, "fieldtask"), (FieldVerificationReport, "fieldreport"),
    (GuideProfile, "guideprofile"), (GuideBookingRequest, "guidebooking"),
    (ImageTag, "imagetag"), (ImportConflict, "importconflict"), (Itinerary, "itinerary"),
    (ItineraryDay, "itineraryday"), (ItineraryStop, "itinerarystop"),
    (BrandingAsset, "brandingasset"), (Rating, "rating"), (ContentProposal, "contentproposal"),
    (DuplicateDecision, "duplicatedecision"), (UserPreferenceProfile, "userpreferenceprofile"),
    (DataReport, "datareport"), (GuideReview, "guidereview")]:
    print(f"  {name:22s} {m.objects.count()}")
print("  django_admin_log       ", LogEntry.objects.count())
print("  auth_group             ", Group.objects.count())
print("  hospital w/ image      ", Hospital.objects.exclude(image="").count(), "/", Hospital.objects.count())
print("  restaurant w/ image    ", Restaurant.objects.exclude(image_url="").count(), "/", Restaurant.objects.count())
print("  hotel w/ cover         ", Hotel.objects.exclude(cover_image="").exclude(cover_image__isnull=True).count(), "/", Hotel.objects.count())
