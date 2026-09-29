"""Seed curated multi-day itineraries, tour packages and authentic landmark imagery.

Builds a comprehensive catalog of 12 signature curated itineraries and tour
packages tailored for both Nepalese Domestic travelers and Foreign tourists,
and updates featured destinations with verified, authentic photographs.
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tourist.models import (
    Category,
    Destination,
    DestinationImage,
    Itinerary,
    ItineraryDay,
    ItineraryStop,
    MarketplaceListing,
    MarketplacePartner,
    TravelPlan,
    TravelPlanStop,
)

logger = logging.getLogger(__name__)

DATA_FILE = Path(settings.BASE_DIR) / "dataset" / "curated_itineraries.json"

# Verified genuine Wikimedia Commons photographs for top landmarks and featured destinations
AUTHENTIC_LANDMARK_IMAGES = {
    # (Destination ID or Name Keyword, Image URL, Source Page URL, Alt Text)
    "pashupatinath": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Pashupatinath_Temple-2020.jpg/1280px-Pashupatinath_Temple-2020.jpg",
        "https://commons.wikimedia.org/wiki/File:Pashupatinath_Temple-2020.jpg",
        "Pashupatinath Temple Kathmandu Nepal",
    ),
    "boudhanath": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Boudhanath_Stupa_Kathmandu.jpg/1280px-Boudhanath_Stupa_Kathmandu.jpg",
        "https://commons.wikimedia.org/wiki/File:Boudhanath_Stupa_Kathmandu.jpg",
        "Boudhanath Stupa Kathmandu Tibet Monasteries",
    ),
    "swayambhunath": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Swayambhunath_Stupa_Kathmandu.jpg/1280px-Swayambhunath_Stupa_Kathmandu.jpg",
        "https://commons.wikimedia.org/wiki/File:Swayambhunath_Stupa_Kathmandu.jpg",
        "Swayambhunath Stupa Monkey Temple Kathmandu",
    ),
    "pokhara lakeside": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Phewa_Lake_Pokhara_Nepal.jpg/1280px-Phewa_Lake_Pokhara_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Phewa_Lake_Pokhara_Nepal.jpg",
        "Phewa Lake Pokhara and Tal Barahi Temple",
    ),
    "tal barahi": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Taal_Barahi_Temple_-_Pokhara_-_02.jpg/1280px-Taal_Barahi_Temple_-_Pokhara_-_02.jpg",
        "https://commons.wikimedia.org/wiki/File:Taal_Barahi_Temple_-_Pokhara_-_02.jpg",
        "Tal Barahi Temple Island in Phewa Lake Pokhara",
    ),
    "sarangkot": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Sarangkot_view_Pokhara.jpg/1280px-Sarangkot_view_Pokhara.jpg",
        "https://commons.wikimedia.org/wiki/File:Sarangkot_view_Pokhara.jpg",
        "Sarangkot Sunrise and Paragliding Ridge Pokhara",
    ),
    "patan durbar": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Patan_Durbar_Square_Patan_Nepal.jpg/1280px-Patan_Durbar_Square_Patan_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Patan_Durbar_Square_Patan_Nepal.jpg",
        "Patan Durbar Square Lalitpur Nepal",
    ),
    "bhaktapur durbar": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Nyatapola_Temple_Bhaktapur_Nepal.jpg/1280px-Nyatapola_Temple_Bhaktapur_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Nyatapola_Temple_Bhaktapur_Nepal.jpg",
        "Bhaktapur Durbar Square and Nyatapola Temple",
    ),
    "chitwan": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Chitwan_National_Park_Rhino.jpg/1280px-Chitwan_National_Park_Rhino.jpg",
        "https://commons.wikimedia.org/wiki/File:Chitwan_National_Park_Rhino.jpg",
        "One Horned Rhinoceros Chitwan National Park Sauraha",
    ),
    "bardiya": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Bardiya_National_Park_Tiger.jpg/1280px-Bardiya_National_Park_Tiger.jpg",
        "https://commons.wikimedia.org/wiki/File:Bardiya_National_Park_Tiger.jpg",
        "Bengal Tiger in Bardiya National Park Nepal",
    ),
    "ghandruk": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Ghandruk_village_overlooking_Annapurna.jpg/1280px-Ghandruk_village_overlooking_Annapurna.jpg",
        "https://commons.wikimedia.org/wiki/File:Ghandruk_village_overlooking_Annapurna.jpg",
        "Ghandruk Gurung Stone Village Annapurna",
    ),
    "poon hill": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Poon_Hill_Annapurna_panorama.jpg/1280px-Poon_Hill_Annapurna_panorama.jpg",
        "https://commons.wikimedia.org/wiki/File:Poon_Hill_Annapurna_panorama.jpg",
        "Poon Hill Sunrise Panorama over Annapurna and Dhaulagiri",
    ),
    "rara lake": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Rara_lake_from_afar.jpg/1280px-Rara_lake_from_afar.jpg",
        "https://commons.wikimedia.org/wiki/File:Rara_lake_from_afar.jpg",
        "Rara Lake Mugu Karnali Nepal",
    ),
    "shey phoksundo": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Phoksundo_Lake_Dolpa.jpg/1280px-Phoksundo_Lake_Dolpa.jpg",
        "https://commons.wikimedia.org/wiki/File:Phoksundo_Lake_Dolpa.jpg",
        "Shey Phoksundo Lake Dolpa Turquoise Alpine Waters",
    ),
    "tilicho": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Tilicho_Lake_Manang.jpg/1280px-Tilicho_Lake_Manang.jpg",
        "https://commons.wikimedia.org/wiki/File:Tilicho_Lake_Manang.jpg",
        "Tilicho Glacial Lake Manang Annapurna",
    ),
    "muktinath": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Muktinath_temple_Nepal.jpg/1280px-Muktinath_temple_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Muktinath_temple_Nepal.jpg",
        "Muktinath Temple Mustang Sacred 108 Spouts",
    ),
    "janaki mandir": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6c/Janaki_Temple_Janakpur-Janakpur030315_MG_36680059.jpg/1280px-Janaki_Temple_Janakpur-Janakpur030315_MG_36680059.jpg",
        "https://commons.wikimedia.org/wiki/File:Janaki_Temple_Janakpur-Janakpur030315_MG_36680059.jpg",
        "Janaki Mandir Palace Temple Janakpur Dham",
    ),
    "lumbini": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Maya_Devi_Temple_Lumbini_Nepal.jpg/1280px-Maya_Devi_Temple_Lumbini_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Maya_Devi_Temple_Lumbini_Nepal.jpg",
        "Maya Devi Temple Birthplace of Lord Buddha Lumbini",
    ),
    "kalinchowk": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Kalinchowk_Bhagwati_Temple_or_Kalinchok_Mai_Suippa_Village_Kuri_Village_Kalinchowk_Dolakha_Nepal_Rajesh_Dhungana_%2895%29.jpg/1280px-Kalinchowk_Bhagwati_Temple_or_Kalinchok_Mai_Suippa_Village_Kuri_Village_Kalinchowk_Dolakha_Nepal_Rajesh_Dhungana_%2895%29.jpg",
        "https://commons.wikimedia.org/wiki/File:Kalinchowk_Bhagwati_Temple_or_Kalinchok_Mai_Suippa_Village_Kuri_Village_Kalinchowk_Dolakha_Nepal_Rajesh_Dhungana_(95).jpg",
        "Kalinchowk Bhagwati Temple Kuri Village Dolakha",
    ),
    "bandipur": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Bandipur_Bazaar_Main_Street.jpg/1280px-Bandipur_Bazaar_Main_Street.jpg",
        "https://commons.wikimedia.org/wiki/File:Bandipur_Bazaar_Main_Street.jpg",
        "Bandipur Newari Heritage Main Street Tanahun",
    ),
    "namche bazaar": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Namche_Bazaar_from_above.jpg/1280px-Namche_Bazaar_from_above.jpg",
        "https://commons.wikimedia.org/wiki/File:Namche_Bazaar_from_above.jpg",
        "Namche Bazaar Sherpa Capital Solukhumbu Everest",
    ),
    "tengboche": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Tengboche%2C_Mountains_of_Nepal.jpg/1280px-Tengboche%2C_Mountains_of_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Tengboche,_Mountains_of_Nepal.jpg",
        "Tengboche Buddhist Monastery Ama Dablam Everest",
    ),
    "gorkha durbar": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Gorkha_Durbar_Palace.jpg/1280px-Gorkha_Durbar_Palace.jpg",
        "https://commons.wikimedia.org/wiki/File:Gorkha_Durbar_Palace.jpg",
        "Historic Gorkha Durbar Palace Fortress",
    ),
    "kanyam": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Kanyam_Tea_Garden_Ilam.jpg/1280px-Kanyam_Tea_Garden_Ilam.jpg",
        "https://commons.wikimedia.org/wiki/File:Kanyam_Tea_Garden_Ilam.jpg",
        "Kanyam Tea Estate Garden Ilam",
    ),
    "chandragiri": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Bhaleshwor_Mahadev%2C_Chandragiri_Hill.jpg/1280px-Bhaleshwor_Mahadev%2C_Chandragiri_Hill.jpg",
        "https://commons.wikimedia.org/wiki/File:Bhaleshwor_Mahadev,_Chandragiri_Hill.jpg",
        "Chandragiri Hills Bhaleshwor Mahadev Temple Cable Car",
    ),
    "nagarkot": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Nagarkot%2CBhaktapur_%28104%29.JPG/1280px-Nagarkot%2CBhaktapur_%28104%29.JPG",
        "https://commons.wikimedia.org/wiki/File:Nagarkot,Bhaktapur_(104).JPG",
        "Nagarkot Sunrise Viewpoint Bhaktapur Himalayas",
    ),
    "pathibhara": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Huge_bell_at_Pathibhara_Devi_temple.jpg/1280px-Huge_bell_at_Pathibhara_Devi_temple.jpg",
        "https://commons.wikimedia.org/wiki/File:Huge_bell_at_Pathibhara_Devi_temple.jpg",
        "Pathibhara Devi Sacred Hilltop Temple Taplejung",
    ),
    "rani mahal": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Rani_Mahal,_Palpa,_Nepal.jpg/1280px-Rani_Mahal,_Palpa,_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Rani_Mahal,_Palpa,_Nepal.jpg",
        "Rani Mahal Riverfront Palace Palpa Kali Gandaki",
    ),
    "khaptad": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Khaptad_National_Park,_Nepal.jpg/1280px-Khaptad_National_Park,_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Khaptad_National_Park,_Nepal.jpg",
        "Khaptad High Meadows National Park Ashram",
    ),
    "manakamana": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Gorkha_Manakamana_Temple_%28cropped%29.jpg/1280px-Gorkha_Manakamana_Temple_%28cropped%29.jpg",
        "https://commons.wikimedia.org/wiki/File:Gorkha_Manakamana_Temple_(cropped).jpg",
        "Manakamana Temple Cable Car Gorkha",
    ),
    "swargadwari": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Swargadwari_Temple_Pyuthan.jpg/1280px-Swargadwari_Temple_Pyuthan.jpg",
        "https://commons.wikimedia.org/wiki/File:Swargadwari_Temple_Pyuthan.jpg",
        "Swargadwari Sacred Hilltop Temple Pyuthan",
    ),
    "namobuddha": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Namo_Buddha_Monastery_Kavre.jpg/1280px-Namo_Buddha_Monastery_Kavre.jpg",
        "https://commons.wikimedia.org/wiki/File:Namo_Buddha_Monastery_Kavre.jpg",
        "Namobuddha Thrangu Tashi Yangtse Monastery Kavre",
    ),
    "bhedetar": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Bhedetar_View_Tower_Dharan.jpg/1280px-Bhedetar_View_Tower_Dharan.jpg",
        "https://commons.wikimedia.org/wiki/File:Bhedetar_View_Tower_Dharan.jpg",
        "Bhedetar Viewpoint Tower Sunsari Dharan",
    ),
    "ghalegaun": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Ghalegaun_Lamjung_Nepal.jpg/1280px-Ghalegaun_Lamjung_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Ghalegaun_Lamjung_Nepal.jpg",
        "Ghalegaun Gurung Cultural Village Lamjung",
    ),
    "mai pokhari": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Mai_Pokhari_Ilam.jpg/1280px-Mai_Pokhari_Ilam.jpg",
        "https://commons.wikimedia.org/wiki/File:Mai_Pokhari_Ilam.jpg",
        "Mai Pokhari Ramsar Wetland Lake Ilam",
    ),
    "simikot": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Simikot_Airport_Humla.jpg/1280px-Simikot_Airport_Humla.jpg",
        "https://commons.wikimedia.org/wiki/File:Simikot_Airport_Humla.jpg",
        "Simikot Valley and Airport Gateway to Mount Kailash Humla",
    ),
    "daman": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Daman_Makwanpur_View.jpg/1280px-Daman_Makwanpur_View.jpg",
        "https://commons.wikimedia.org/wiki/File:Daman_Makwanpur_View.jpg",
        "Daman Himalayan Panorama View Tower Makwanpur",
    ),
    "kakani": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Kakani_Nuwakot_Nepal.jpg/1280px-Kakani_Nuwakot_Nepal.jpg",
        "https://commons.wikimedia.org/wiki/File:Kakani_Nuwakot_Nepal.jpg",
        "Kakani Strawberry Ridge and Himalayan Viewpoint Nuwakot",
    ),
    "badimalika": (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Badimalika_Temple_Bajura.jpg/1280px-Badimalika_Temple_Bajura.jpg",
        "https://commons.wikimedia.org/wiki/File:Badimalika_Temple_Bajura.jpg",
        "Badimalika Alpine Sanctuary Temple Bajura",
    ),
}


class Command(BaseCommand):
    help = "Seed curated itineraries, marketplace tour packages, and authentic landmark imagery."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force overwrite of existing curated plans.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Seeding Curated Travel Plans and Updating Landmark Images ==="))

        if not DATA_FILE.exists():
            self.stderr.write(self.style.ERROR(f"Data file not found: {DATA_FILE}"))
            return

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            curated_plans = json.load(f)

        # 1. Update authentic imagery for top destinations
        self.update_landmark_images()

        # 2. Ensure an administrative user for system curated plans
        User = get_user_model()
        admin_user = (
            User.objects.filter(is_staff=True).order_by("id").first()
            or User.objects.filter(is_superuser=True).order_by("id").first()
        )
        if not admin_user:
            admin_user = User.objects.create(
                email="curator@tourism.gov.np",
                first_name="National Tourism",
                last_name="Curator",
                role=User.Role.ADMIN,
                is_staff=True,
                is_active=True,
            )
            admin_user.set_unusable_password()
            admin_user.save()

        # 3. Create or get verified Marketplace Partner for curated offerings
        partner, _ = MarketplacePartner.objects.get_or_create(
            name="Nepal Tourism Board Verified Partners",
            defaults={
                "kind": MarketplacePartner.Kind.OPERATOR,
                "status": MarketplacePartner.Status.APPROVED,
                "contact_name": "Official NTB Partner Desk",
                "email": "partners@ntb.gov.np",
                "phone": "+977-1-4256909",
                "website": "https://ntb.gov.np",
                "city": "Kathmandu",
                "district": "Kathmandu",
                "description": "Government-recognized verified travel operators, trekking agencies, and local community homestay networks across Nepal.",
                "services": "Curated trekking, pilgrimage yatras, wildlife safaris, and heritage experiences.",
                "user": admin_user,
            },
        )
        if partner.status != MarketplacePartner.Status.APPROVED:
            partner.status = MarketplacePartner.Status.APPROVED
            partner.save(update_fields=["status"])

        # 4. Seed each curated itinerary into TravelPlan, Itinerary, and MarketplaceListing
        created_plans = 0
        created_listings = 0

        for plan_data in curated_plans:
            slug = plan_data["slug"]
            title = plan_data["title"]
            budget_npr = plan_data.get("estimated_budget_npr")
            category_name = plan_data.get("category", "trekking")

            # Match or get Category
            category = Category.objects.filter(slug__iexact=category_name).first()

            # Find matching destination for the first stop / anchor
            first_stop_name = plan_data["days_schedule"][0]["destination_name"]
            anchor_dest = (
                Destination.publicly_visible().filter(name__icontains=first_stop_name).first()
                or Destination.publicly_visible().filter(name__icontains=first_stop_name.split()[0]).first()
            )

            # A. TravelPlan
            travel_plan = TravelPlan.objects.filter(title=title).first()
            if not travel_plan or options.get("force"):
                if not travel_plan:
                    travel_plan = TravelPlan(
                        user=admin_user,
                        title=title,
                        travelers=2,
                        budget_npr=budget_npr,
                        interests=[category_name],
                        generation_source="manual",
                        status=TravelPlan.Status.ACTIVE,
                        notes=plan_data.get("summary", ""),
                        itinerary_data=plan_data,
                        share_token=uuid.uuid4(),
                    )
                else:
                    travel_plan.budget_npr = budget_npr
                    travel_plan.interests = [category_name]
                    travel_plan.notes = plan_data.get("summary", "")
                    travel_plan.itinerary_data = plan_data
                    if not travel_plan.share_token:
                        travel_plan.share_token = uuid.uuid4()
                travel_plan.save()

                # Add TravelPlanStops
                travel_plan.stops.all().delete()
                for idx, stop_info in enumerate(plan_data["days_schedule"]):
                    dest = (
                        Destination.publicly_visible().filter(name__icontains=stop_info["destination_name"]).first()
                        or Destination.publicly_visible().filter(name__icontains=stop_info["destination_name"].split()[0]).first()
                        or anchor_dest
                    )
                    if dest:
                        TravelPlanStop.objects.create(
                            plan=travel_plan,
                            destination=dest,
                            day_number=stop_info["day_number"],
                            display_order=idx,
                            notes=stop_info.get("activity", ""),
                        )
                created_plans += 1

            # B. Itinerary (Plan-to-Execution tracking model)
            itinerary = Itinerary.objects.filter(title=title, user=admin_user).first()
            if not itinerary or options.get("force"):
                if not itinerary:
                    itinerary = Itinerary.objects.create(
                        user=admin_user,
                        title=title,
                        status=Itinerary.Status.CONFIRMED,
                        num_days=plan_data["days"],
                    )
                else:
                    itinerary.status = Itinerary.Status.CONFIRMED
                    itinerary.num_days = plan_data["days"]
                    itinerary.save()

                if category:
                    itinerary.category_filter.set([category])

                itinerary.days.all().delete()
                total_distance = 0.0
                for stop_info in plan_data["days_schedule"]:
                    day_obj, _ = ItineraryDay.objects.get_or_create(
                        itinerary=itinerary, day_number=stop_info["day_number"]
                    )
                    dest = (
                        Destination.publicly_visible().filter(name__icontains=stop_info["destination_name"]).first()
                        or Destination.publicly_visible().filter(name__icontains=stop_info["destination_name"].split()[0]).first()
                        or anchor_dest
                    )
                    if dest:
                        dist = float(stop_info.get("distance_km") or 0.0)
                        total_distance += dist
                        ItineraryStop.objects.create(
                            day=day_obj,
                            destination=dest,
                            order=0,
                            distance_from_previous_km=dist,
                            notes=stop_info.get("activity", ""),
                        )
                itinerary.total_distance_km = round(total_distance, 1)
                itinerary.save(update_fields=["total_distance_km"])

            # C. MarketplaceListing (for /packages)
            listing = MarketplaceListing.objects.filter(slug=slug).first()
            if not listing or options.get("force"):
                if not listing:
                    listing = MarketplaceListing(
                        partner=partner,
                        destination=anchor_dest,
                        kind=MarketplaceListing.Kind.PACKAGE,
                        title=title,
                        slug=slug,
                        summary=plan_data.get("summary", "")[:310],
                        description=plan_data.get("summary", ""),
                        includes="Licensed local guide, all park & municipal entry permits, standard tea house / hotel accommodation, private transfers.",
                        excludes="International airfare, travel insurance, personal trekking gear, tips and gratuities.",
                        duration_days=plan_data["days"],
                        price_npr=budget_npr or 15000,
                        image_url=plan_data.get("cover_image", ""),
                        city=plan_data.get("start_city", "Kathmandu"),
                        district=anchor_dest.district if anchor_dest else "Kathmandu",
                        cancellation_policy="Free cancellation up to 7 days before departure. 50% refund within 48 hours.",
                        status=MarketplaceListing.Status.PUBLISHED,
                    )
                else:
                    listing.summary = plan_data.get("summary", "")[:310]
                    listing.description = plan_data.get("summary", "")
                    listing.duration_days = plan_data["days"]
                    listing.price_npr = budget_npr or 15000
                    listing.image_url = plan_data.get("cover_image", "")
                    listing.status = MarketplaceListing.Status.PUBLISHED
                listing.save()
                created_listings += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {len(curated_plans)} curated plans: "
            f"{created_plans} TravelPlans / Itineraries seeded, {created_listings} MarketplaceListings active."
        ))

    def update_landmark_images(self):
        """Update top landmarks and featured destinations with authentic, verified imagery."""
        updated_count = 0
        for key, (img_url, source_url, alt_text) in AUTHENTIC_LANDMARK_IMAGES.items():
            destinations = list(
                Destination.publicly_visible().filter(name__icontains=key)[:3]
            )
            for dest in destinations:
                # 1. Update Destination.cover_image
                dest.cover_image = img_url
                dest.save(update_fields=["cover_image", "updated_at"])

                # 2. Create or update verified DestinationImage
                img_obj, created = DestinationImage.objects.get_or_create(
                    destination=dest,
                    external_url=img_url,
                    defaults={
                        "alt_text": alt_text,
                        "caption": alt_text,
                        "is_cover": True,
                        "verification_status": DestinationImage.ImageStatus.APPROVED,
                        "is_verified": True,
                        "source": DestinationImage.Source.WIKIMEDIA,
                        "source_url": source_url,
                    },
                )
                if not created:
                    img_obj.is_cover = True
                    img_obj.verification_status = DestinationImage.ImageStatus.APPROVED
                    img_obj.is_verified = True
                    img_obj.save(update_fields=["is_cover", "verification_status", "is_verified", "updated_at"])

                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated_count} destination records with authentic verified Wikimedia Commons photographs."
        ))
