"""Idempotent demo users and marketplace offers for Playwright feature e2e & real package catalog."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from tourist.location_sync import apply_destination_locations
from tourist.models import MarketplaceListing, MarketplacePartner, User


class Command(BaseCommand):
    help = "Ensure demo logins and published marketplace packages exist for e2e and public catalog."

    def handle(self, *args, **options):
        applied = apply_destination_locations()
        if applied:
            self.stdout.write(f"Applied {applied} recorded destination locations from JSON.")
        users = [
            {
                "email": "admin@tourism.gov.np",
                "password": "Admin@12345",
                "first_name": "Nepal",
                "last_name": "Admin",
                "role": User.Role.SUPER_ADMIN,
                "city": "Kathmandu",
                "country": "Nepal",
                "latitude": Decimal("27.7172"),
                "longitude": Decimal("85.3240"),
                "location_source": "GPS",
                "managed_district": "Kathmandu",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "staff@tourism.gov.np",
                "password": "Staff@12345",
                "first_name": "Tourism",
                "last_name": "Staff",
                "role": User.Role.STAFF,
                "city": "Kathmandu",
                "country": "Nepal",
                "latitude": Decimal("27.7172"),
                "longitude": Decimal("85.3240"),
                "location_source": "GPS",
                "managed_district": "Kathmandu",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "tourist@nepaltourism.com",
                "password": "Tourist@12345",
                "first_name": "Namaste",
                "last_name": "Traveler",
                "role": User.Role.TOURIST,
                "city": "Pokhara",
                "country": "Nepal",
                "latitude": Decimal("28.2096"),
                "longitude": Decimal("83.9856"),
                "location_source": "GPS",
                "managed_district": "Kaski",
                "is_staff": False,
                "is_superuser": False,
            },
        ]
        for spec in users:
            password = spec.pop("password")
            email = spec["email"]
            user, created = User.objects.get_or_create(email=email, defaults={
                **spec,
                "is_active": True,
                "is_verified": True,
            })
            if not created:
                for key, value in spec.items():
                    setattr(user, key, value)
            user.is_active = True
            user.is_verified = True
            user.set_password(password)
            user.save()

        tourist = User.objects.get(email="tourist@nepaltourism.com")
        partner, _ = MarketplacePartner.objects.update_or_create(
            email="tourist@nepaltourism.com",
            defaults={
                "name": "Nepal Yatra Himalayan Expeditions",
                "kind": MarketplacePartner.Kind.OPERATOR,
                "status": MarketplacePartner.Status.APPROVED,
                "user": tourist,
                "city": "Kathmandu",
                "district": "Kathmandu",
                "website": "https://example.com",
                "contact_name": "Himalayan Operations",
                "description": "Official licensed Nepal travel operator and partner desk.",
            },
        )

        offers = [
            # Featured Nepal Packages
            {
                "slug": "e2e-five-day-nepal-circuit",
                "title": "Pokhara & Annapurna Heritage Circuit",
                "summary": "Published five-day Pokhara circuit with Phewa Lake boating & Sarangkot sunrise.",
                "description": "Kathmandu arrival, scenic highway trip to Pokhara, Sarangkot sunrise view, Devi's Fall, World Peace Pagoda, and Phewa boating.",
                "includes": "Licensed Trekking & Tour Guide\nLodge Accommodation & Breakfast\nPrivate Tourist Bus Transport",
                "duration_days": 5,
                "price_npr": Decimal("45000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Pokhara",
                "image_url": "/images/destinations/pokhara/fewatal.jpg",
            },
            {
                "slug": "e2e-six-day-alternative",
                "title": "Kathmandu & Pokhara 6-Day Cultural Circuit",
                "summary": "Six-day published heritage circuit across Kathmandu and Pokhara.",
                "description": "Kathmandu Durbar Square, Patan, Nagarkot sunrise, and Pokhara lakes.",
                "includes": "Licensed Heritage Guide\nHotel Stay with Breakfast\nPrivate AC Vehicle",
                "duration_days": 6,
                "price_npr": Decimal("50000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": False,
                "city": "Pokhara",
                "image_url": "/images/destinations/nagarkot/sunrise-view.jpg",
            },
            {
                "slug": "e2e-over-budget-week",
                "title": "Himalayan Luxury Panorama Week",
                "summary": "5-day luxury mountain flight to Everest & 5-star resort in Pokhara.",
                "description": "Exclusive 5-star luxury stay with Everest helicopter flight and fine dining.",
                "includes": "Helicopter Tour to EBC\n5-Star Resort Accommodations\nAll Fine Dining Meals",
                "duration_days": 5,
                "price_npr": Decimal("250000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": False,
                "city": "Kathmandu",
                "image_url": "/images/destinations/everest/base-camp.jpg",
            },
            {
                "slug": "e2e-pending-hidden-stay",
                "title": "Pokhara Eco-Lodge Pending Stay",
                "summary": "Boutique lakeside eco-lodge.",
                "description": "Pending partner offer.",
                "includes": "",
                "duration_days": 2,
                "price_npr": Decimal("1000.00"),
                "status": MarketplaceListing.Status.PENDING,
                "is_featured": False,
                "city": "Pokhara",
                "image_url": "/images/destinations/pokhara/fewatal.jpg",
            },
            # Real Authentic Nepal Travel Packages
            {
                "slug": "everest-base-camp-kala-patthar-expedition",
                "title": "Everest Base Camp Trek & Kala Patthar Expedition (14 Days)",
                "summary": "World-famous high-altitude trek through Sherpa villages, Tengboche Monastery, and Kala Patthar (5,545m) sunrise views.",
                "description": "Fly into Lukla airstrip, trek through Namche Bazaar, Tengboche, Dingboche, Gorak Shep, and stand at Everest Base Camp (5,364m) with views of Khumbu Icefall.",
                "includes": "Lukla Flights\nSherpa Guide & Porters\nTeahouse Lodging & Meals\nSagarmatha National Park Permit & TIMS",
                "duration_days": 14,
                "price_npr": Decimal("185000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Namche Bazaar / Solukhumbu",
                "image_url": "/images/destinations/everest/base-camp.jpg",
            },
            {
                "slug": "pokhara-lakes-sarangkot-annapurna-circuit",
                "title": "Pokhara Lakes, Sarangkot & Annapurna Sanctuary Circuit (7 Days)",
                "summary": "Explore Phewa & Begnas lakes, Sarangkot sunrise, World Peace Pagoda, and Poon Hill mountain vistas.",
                "description": "Scenic trip connecting Pokhara's lakeside, Mahendra Cave, Davis Falls, Sarangkot sunrise over Machhapuchhre, and Poon Hill trek.",
                "includes": "3-Star Hotel in Pokhara\nPoon Hill Lodge Accommodation\nPrivate Vehicle Transfers\nBoating on Phewa Lake",
                "duration_days": 7,
                "price_npr": Decimal("65000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Pokhara / Kaski",
                "image_url": "/images/destinations/pokhara/fewatal.jpg",
            },
            {
                "slug": "chitwan-wildlife-safari-tharu-culture",
                "title": "Chitwan Wildlife Safari & Tharu Culture Experience (4 Days)",
                "summary": "Jungle safari in UNESCO Chitwan National Park to spot one-horned rhinos, Bengal tigers, and Tharu cultural stick dance.",
                "description": "Jungle jeep safari, canoe ride on Rapti river, elephant breeding center visit, bird watching, and traditional Tharu cultural evening.",
                "includes": "Jungle Safari Resort Stay\nAll Meals (Breakfast, Lunch, Dinner)\nJeep & Canoe Safari\nNational Park Entry Permit",
                "duration_days": 4,
                "price_npr": Decimal("38000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Sauraha / Chitwan",
                "image_url": "/images/destinations/chitwan/safari.jpg",
            },
            {
                "slug": "kathmandu-valley-unesco-nagarkot-sunrise",
                "title": "Kathmandu Valley UNESCO Heritage & Nagarkot Sunrise (5 Days)",
                "summary": "Explore Swayambhu, Pashupatinath, Boudhanath, Patan & Bhaktapur Durbar Squares with Nagarkot mountain sunrise.",
                "description": "Guided heritage tour across Kathmandu, Patan, and Bhaktapur, concluding with overnight hill station stay in Nagarkot facing Everest & Langtang ranges.",
                "includes": "Heritage Hotel Stay\nNagarkot Hill Resort\nPrivate AC Vehicle & Guide\nAll Monument Entry Fees",
                "duration_days": 5,
                "price_npr": Decimal("48000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Kathmandu / Bhaktapur",
                "image_url": "/images/destinations/kathmandu/durbar-square.jpg",
            },
            {
                "slug": "upper-mustang-lo-manthang-overland-tour",
                "title": "Upper Mustang Lo Manthang Walled Kingdom Overland Tour (10 Days)",
                "summary": "4WD jeep overland expedition into the rain-shadow desert, ancient cave monasteries, and the royal palace of Lo Manthang.",
                "description": "Drive from Jomsom to Kagbeni, Muktinath, Charang, and Lo Manthang. Explore 1,000-year-old Chhoser sky caves and Mustang royal heritage.",
                "includes": "4WD Scorpio Overland Vehicle\nRestricted Area RAP Permit ($500 value)\nLocal Mustang Guide\nTeahouse & Guesthouse Stays",
                "duration_days": 10,
                "price_npr": Decimal("165000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Lo Manthang / Mustang",
                "image_url": "/images/destinations/mustang/lo-manthang.jpg",
            },
            {
                "slug": "lumbini-sacred-birthplace-buddhist-pilgrimage",
                "title": "Lumbini Sacred Birthplace & Buddhist Pilgrimage Tour (3 Days)",
                "summary": "Spiritual journey to Maya Devi Temple, Ashoka Pillar, and peaceful international monastic zone in Lumbini.",
                "description": "Visit the exact birthplace of Lord Buddha, sacred Pushkarini pond, Ashoka Pillar (249 BC), and electric Rickshaw tour of 30+ international stupas.",
                "includes": "Pilgrimage Hotel Stay\nElectric Rickshaw Tour\nKathmandu-Lumbini AC Bus / Flight Transfer\nSpiritual Guide",
                "duration_days": 3,
                "price_npr": Decimal("28000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Lumbini / Rupandehi",
                "image_url": "/images/destinations/lumbini/garden.jpg",
            },
            {
                "slug": "ilam-tea-gardens-kanyam-scenic-escape",
                "title": "Ilam Tea Gardens & Kanyam Scenic Hill Escape (4 Days)",
                "summary": "Walk through rolling green tea estates of Ilam and Kanyam, tasting organic Himalayan orthodox tea.",
                "description": "Scenic trip across Eastern Nepal visiting Kanyam tea garden, Mai Pokhari wetland, Antu Danda sunrise over Mt. Kanchenjunga, and tea factory tasting.",
                "includes": "Boutique Tea Resort\nTea Tasting & Factory Tour\nPrivate Vehicle Transfers\nLocal Cultural Dinner",
                "duration_days": 4,
                "price_npr": Decimal("32000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Ilam / Koshi",
                "image_url": "/images/destinations/ilam/tea-gardens.jpg",
            },
            {
                "slug": "rara-lake-west-nepal-wilderness-expedition",
                "title": "Rara Alpine Lake & West Nepal Wilderness Expedition (6 Days)",
                "summary": "Journey to Nepal's largest freshwater alpine lake in Mugu surrounded by pine forests and snow peaks.",
                "description": "Fly from Nepalgunj to Talcha Airstrip, trek through pine forests to Rara Lake (2,990m), boat on crystal waters, and experience Karnali culture.",
                "includes": "Nepalgunj-Talcha Flights\nLake Lodge Accommodation\nRara National Park Entry\nLocal Guide",
                "duration_days": 6,
                "price_npr": Decimal("75000.00"),
                "status": MarketplaceListing.Status.PUBLISHED,
                "is_featured": True,
                "city": "Rara / Mugu",
                "image_url": "/images/destinations/rara/alpine-lake.jpg",
            },
        ]
        for row in offers:
            MarketplaceListing.objects.update_or_create(
                slug=row["slug"],
                defaults={
                    "partner": partner,
                    "kind": MarketplaceListing.Kind.PACKAGE,
                    "title": row["title"],
                    "summary": row["summary"],
                    "description": row["description"],
                    "includes": row["includes"],
                    "duration_days": row["duration_days"],
                    "price_npr": row["price_npr"],
                    "city": row.get("city", "Pokhara"),
                    "district": "Nepal",
                    "status": row["status"],
                    "is_featured": row["is_featured"],
                    "image_url": row["image_url"],
                },
            )

        self.stdout.write(self.style.SUCCESS(
            "E2E users and marketplace packages are ready."
        ))
