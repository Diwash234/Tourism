"""
Add real missing Nepal tourist destinations (heritage sites, temples,
caves, lakes, trekking areas, mountains, etc.) that weren't in the OSM
import. Also filter out hotel/lodge/guest_house entries that aren't
real tourist destinations from the default listing.

Usage:
    python manage.py add_missing_destinations
    python manage.py add_missing_destinations --filter-hotels   # also mark hotel-category destinations as not real attractions
"""
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction

from django.conf import settings

from tourist.models import (
    Destination, Category, DestinationImage,
)


def settings_base():
    return os.path.normpath(os.path.join(settings.BASE_DIR, ".."))


# (name, category_slug, lat, lon, district, province, short_description, image_path, aliases)
MISSING = [
    # ---- Pokhara ----
    ("Mahendra Cave", "attraction", 28.2467, 83.9742, "Kaski", "Gandaki",
     "Famous limestone cave in Pokhara with stalactites, stalagmites and a Shiva statue.",
     None, ["mahindra cave", "pokhara cave"]),
    ("Davis Falls (Patale Chhango)", "attraction", 28.2344, 83.9664, "Kaski", "Gandaki",
     "Powerful waterfall that disappears into an underground tunnel, feeding Gupteshwor Cave.",
     None, ["davis fall", "patale chhango", "patale chhanga"]),
    ("Gupteshwor Mahadev Cave", "religious-sites", 28.2353, 83.9660, "Kaski", "Gandaki",
     "Sacred cave temple dedicated to Lord Shiva, opposite Davis Falls in Pokhara.",
     None, ["gupteshwor cave", "gupteshwar cave"]),
    ("Bindhyabasini Temple", "heritage-temples", 28.2406, 83.9887, "Kaski", "Gandaki",
     "Historic Hindu temple on a hillock in Pokhara bazaar, dedicated to Goddess Bindhyabasini.",
     None, ["bindabashini", "bindhyabasini"]),
    ("World Peace Pagoda Pokhara", "heritage-temples", 28.2072, 83.9674, "Kaski", "Gandaki",
     "White Buddhist stupa on Anadu Hill with panoramic views of Pokhara, Phewa Lake, and the Annapurna range.",
     None, ["shanti stupa", "peace pagoda pokhara"]),
    ("Begnas Lake", "lakes-water-activities", 28.1785, 84.0564, "Kaski", "Gandaki",
     "Second largest lake in Pokhara valley; peaceful freshwater lake popular for boating and angling.",
     None, ["begnas tal"]),
    ("Rupa Lake", "lakes-water-activities", 28.1676, 84.0863, "Kaski", "Gandaki",
     "Freshwater lake in Lekhnath, known for lotus blooms and migratory birds.",
     None, ["rupa tal"]),
    ("Sarangkot Viewpoint", "photography-spots", 28.2533, 83.9467, "Kaski", "Gandaki",
     "Popular hilltop viewpoint at 1600m — best sunrise spot for Annapurna range, Phewa Lake, and Pokhara.",
     None, ["sarangkot"]),
    ("International Mountain Museum", "museum", 28.2146, 83.9744, "Kaski", "Gandaki",
     "Museum documenting the Himalayas, mountaineering history, and the people of Nepal's mountains.",
     None, []),

    # ---- Kathmandu Valley ----
    ("Pashupatinath Temple", "religious-sites", 27.7105, 85.3485, "Kathmandu", "Bagmati",
     "UNESCO World Heritage sacred Hindu temple complex on the Bagmati River, dedicated to Lord Shiva.",
     "/images/destinations/kathmandu/durbar-square.jpg", ["pashupati", "pashupatinath"]),
    ("Boudhanath Stupa", "heritage-temples", 27.7215, 85.3620, "Kathmandu", "Bagmati",
     "UNESCO World Heritage — one of the largest spherical stupas in the world, center of Tibetan Buddhism in Nepal.",
     "/images/destinations/kathmandu/durbar-square.jpg", ["boudha", "boudhanath", "baudhanath"]),
    ("Swayambhunath Stupa (Monkey Temple)", "heritage-temples", 27.7150, 85.2916, "Kathmandu", "Bagmati",
     "UNESCO World Heritage ancient hilltop stupa with the all-seeing eyes of the Buddha; panoramic Kathmandu views.",
     "/images/destinations/kathmandu/durbar-square.jpg", ["swayambhu", "monkey temple", "swayambhunath"]),
    ("Dharahara (Bhimsen Tower)", "heritage-temples", 27.7015, 85.3128, "Kathmandu", "Bagmati",
     "Iconic 72-metre white tower at Sundhara; rebuilt after the 2015 earthquake with an observation deck.",
     None, ["bhimsen tower", "dharahara tower"]),
    ("Garden of Dreams", "attraction", 27.7139, 85.3149, "Kathmandu", "Bagmati",
     "Neo-classical historical garden in the heart of Kathmandu (Kaiser Mahal), restored with pavilions and fountains.",
     None, ["garden of dreams kathmandu", "kaiser mahal garden"]),
    ("Thamel", "attraction", 27.7153, 85.3123, "Kathmandu", "Bagmati",
     "Vibrant tourist district in Kathmandu — trekking gear shops, restaurants, nightlife, traveler gathering point.",
     None, []),
    ("Narayanhiti Palace Museum", "museum", 27.7159, 85.3201, "Kathmandu", "Bagmati",
     "Former royal palace, now a public museum showcasing the monarchy's history and artifacts.",
     None, ["narayanhiti darbar", "royal palace kathmandu"]),
    ("Hanuman Dhoka Durbar Square", "heritage-temples", 27.7042, 85.3064, "Kathmandu", "Bagmati",
     "UNESCO-listed ancient royal palace complex with Hanuman Gate, Kumari Ghar, and Taleju Temple.",
     "/images/destinations/kathmandu/durbar-square.jpg", ["hanuman dhoka", "basantapur"]),
    ("Kopan Monastery", "heritage-temples", 27.7375, 85.3681, "Kathmandu", "Bagmati",
     "Tibetan Buddhist monastery on a hill north of Boudha; famous for meditation courses.",
     None, ["kopan"]),
    ("Phulchowki Hill", "nature-trekking", 27.5578, 85.3947, "Lalitpur", "Bagmati",
     "Highest hill (2782m) surrounding Kathmandu Valley; botanical garden, hiking, snow in winter.",
     None, ["phulchoki", "phul chowki"]),
    ("Chandragiri Hill", "photography-spots", 27.7130, 85.2050, "Kathmandu", "Bagmati",
     "Hilltop at 2551m with cable car ride, Bhaleshwor Mahadev temple, and panoramic Himalayan views.",
     None, ["chandragiri"]),
    ("Nagarkot View Tower", "photography-spots", 27.7237, 85.5217, "Bhaktapur", "Bagmati",
     "Tower at Nagarkot ridge with 360-degree views of Everest, Langtang, Manaslu, and Ganesh Himal.",
     "/images/destinations/nagarkot/sunrise-view.jpg", []),

    # ---- Langtang & Helambu ----
    ("Langtang Valley Trek", "nature-trekking", 28.2167, 85.5167, "Rasuwa", "Bagmati",
     "Alpine valley trek north of Kathmandu near the Tibetan border; Tamang villages, glaciers, Kyanjin Gompa.",
     "/images/destinations/gosaikunda/glacial-lake.jpg", ["langtang", "langtang national park"]),
    ("Kyanjin Gompa", "religious-sites", 28.2456, 85.6072, "Rasuwa", "Bagmati",
     "Ancient Buddhist monastery at 3870m in Langtang; viewpoints for Langtang Lirung and glaciers.",
     None, ["kyanjin gompa"]),
    ("Gosaikunda Lake Trek", "nature-trekking", 28.2000, 85.4000, "Rasuwa", "Bagmati",
     "Sacred alpine lake at 4380m and trekking route in Langtang National Park; pilgrimage site.",
     "/images/destinations/gosaikunda/glacial-lake.jpg", ["gosainkunda", "gosaikunda"]),
    ("Helambu Trek", "nature-trekking", 28.0500, 85.5000, "Sindhupalchok", "Bagmati",
     "Short scenic trek north-east of Kathmandu through Sherpa and Tamang villages, rhododendron forests.",
     None, ["helambu"]),
    ("Panch Pokhari", "lakes-water-activities", 28.0720, 85.7070, "Sindhupalchok", "Bagmati",
     "Group of five sacred high-altitude lakes at ~4100m; less crowded pilgrimage and trekking destination.",
     None, ["five lakes", "pancha pokhari"]),

    # ---- Solukhumbu / Everest ----
    ("Tengboche Monastery", "religious-sites", 27.8350, 86.7660, "Solukhumbu", "Province 1",
     "Largest Tibetan Buddhist gompa in Khumbu at 3867m; mani walls, prayer flags, Everest backdrop.",
     "/images/destinations/everest/base-camp.jpg", ["thyangboche", "tengboche"]),
    ("Namche Bazaar", "attraction", 27.8069, 86.7136, "Solukhumbu", "Province 1",
     "Sherpa trading town at 3440m; gateway to Everest with teahouses, bakeries, and weekend markets.",
     None, ["namche"]),
    ("Kala Patthar Viewpoint", "photography-spots", 27.9940, 86.8280, "Solukhumbu", "Province 1",
     "5545m peak above Gorakshep — famous for the best sunrise view of Mount Everest.",
     None, ["kala patthar", "kalapathar"]),
    ("Gokyo Lakes", "lakes-water-activities", 27.9360, 86.7080, "Solukhumbu", "Province 1",
     "Series of six turquoise glacial lakes in Sagarmatha National Park, with Gokyo Ri viewpoint.",
     None, ["gokyo"]),

    # ---- Annapurna region ----
    ("Poon Hill Viewpoint", "photography-spots", 28.4030, 83.7060, "Myagdi", "Gandaki",
     "3210m Ghorepani viewpoint — famous for sunrise over Dhaulagiri, Annapurna South, Machhapuchhre.",
     "/images/destinations/annapurna/trek.jpg", ["poonhill", "poon hill ghorepani"]),
    ("Machhapuchhre (Fishtail Mountain)", "nature-trekking", 28.4667, 83.9450, "Kaski", "Gandaki",
     "Iconic 6993m sacred peak shaped like a fish tail; never officially summited; dominates Pokhara skyline.",
     None, ["fishtail mountain", "machhapuchhre", "machhapuchhre"]),
    ("Tilicho Base Camp", "nature-trekking", 28.6600, 83.9000, "Manang", "Gandaki",
     "High camp on the Annapurna Circuit near Tilicho Lake at 4150m.",
     "/images/destinations/tilicho/himalayan-lake.jpg", []),
    ("Thorong La Pass", "nature-trekking", 28.7878, 83.9597, "Manang/Mustang", "Gandaki",
     "5416m high pass — the highest point on the Annapurna Circuit, linking Manang to Mustang.",
     None, ["thorung la", "thorong pass"]),
    ("Muktinath Temple", "religious-sites", 28.8167, 83.8750, "Mustang", "Gandaki",
     "Sacred pilgrimage site for both Hindus and Vishnu worshippers at 3710m in Lower Mustang; 108 waterspouts.",
     None, ["muktinath", "mukti chhetra"]),
    ("Kagbeni", "heritage-temples", 28.8570, 83.7760, "Mustang", "Gandaki",
     "Medieval walled village on the Kali Gandaki river; gateway to Upper Mustang and centuries-old monastery.",
     "/images/destinations/mustang/lo-manthang.jpg", []),

    # ---- Chitwan & Terai ----
    ("Sauraha (Chitwan NP Entry)", "wildlife", 27.5761, 84.4954, "Chitwan", "Bagmati",
     "Main tourist hub for Chitwan National Park; elephant safaris, canoe rides, jungle walks start here.",
     "/images/destinations/chitwan/safari.jpg", ["sauraha"]),
    ("Lumbini Sacred Garden", "religious-sites", 27.4696, 83.2761, "Rupandehi", "Lumbini",
     "UNESCO World Heritage — birthplace of Buddha; Maya Devi Temple, sacred Bodhi tree, monastic zone.",
     "/images/destinations/lumbini/garden.jpg", ["lumbini", "mayadevi"]),
    ("Bardiya National Park HQ (Thakurdwara)", "wildlife", 28.4700, 81.5200, "Bardiya", "Lumbini",
     "Entrance point to Bardiya National Park; jungle safaris, wild elephant and tiger tracking.",
     "/images/destinations/bardiya/tiger-reserve.jpg", ["thakurdwara"]),

    # ---- Far west / Far east ----
    ("Khaptad National Park", "nature-trekking", 29.4000, 80.9333, "Doti/Bajhang", "Sudurpashchim",
     "High-altitude plateau national park; Khaptad Baba ashram, meadows, forests, Himalayan views.",
     None, ["khaptad"]),
    ("Pathibhara Devi Temple", "religious-sites", 27.4200, 87.7300, "Taplejung", "Province 1",
     "Sacred hilltop shrine at 3794m in Taplejung; pilgrimage, Kanchenjunga views, popular among Nepalis.",
     None, ["pathibhara", "pathivara"]),
    ("Kanyam Tea Gardens", "photography-spots", 26.8300, 87.9600, "Ilam", "Province 1",
     "Rolling green tea plantations in Ilam district; popular picnic and photography spot.",
     "/images/destinations/ilam/tea-gardens.jpg", ["kanyam", "ilam tea garden"]),
    ("Shree Antu Viewpoint", "photography-spots", 26.8300, 88.0800, "Ilam", "Province 1",
     "Easternmost hill viewpoint in Ilam, Nepal — famous for sunrise over Kanchenjunga and the tea estates.",
     None, ["shreeantu", "sri antu"]),
    ("Halesi Mahadev Cave", "religious-sites", 27.1800, 86.6200, "Khotang", "Province 1",
     "Sacred cave temple of Lord Shiva in eastern Nepal; known as the Pashupatinath of the east.",
     None, ["halesi", "halesi mahadev"]),
    ("Janaki Mandir Janakpur", "religious-sites", 26.7300, 85.9250, "Dhanusha", "Madhesh",
     "Grand pink-white Hindu temple dedicated to Goddess Sita at Janakpur, the birthplace of Sita.",
     "/images/destinations/janakpur/janaki-mandir.jpg", ["janaki mandir", "janakpur dham"]),
    ("Manakamana Temple", "religious-sites", 27.8550, 84.5900, "Gorkha", "Gandaki",
     "Sacred Bhagwati temple at 1302m above the Trisuli river; accessed by cable car from Kurintar.",
     None, ["manakamana", "manakamana cable car"]),
    ("Gorkha Durbar", "heritage-temples", 28.0000, 84.6320, "Gorkha", "Gandaki",
     "Historic palace of Prithvi Narayan Shah — birthplace of modern Nepal; hilltop fort, Kalika temple.",
     None, ["gorkha palace", "gorkha durbar"]),
    ("Bandipur Newari Bazaar", "heritage-temples", 27.9380, 84.4150, "Tanahun", "Gandaki",
     "Preserved 18th-century Newari trading town on a ridge; cobbled streets, pagoda temples, Himalayan views.",
     "/images/destinations/bandipur/hilltop-village.jpg", ["bandipur bazaar"]),
    ("Tansen Palpa Durbar", "heritage-temples", 27.8689, 83.5469, "Palpa", "Lumbini",
     "Historic hill town in Palpa; Rani Mahal, traditional Newari architecture, Srinagar Danda viewpoint.",
     None, ["tansen", "palpa durbar"]),
    ("Rani Mahal Palpa", "heritage-temples", 27.7994, 83.5275, "Palpa", "Lumbini",
     "19th-century palace on the banks of the Kali Gandaki, known as the Taj Mahal of Nepal.",
     None, ["rani mahal"]),
    ("Bhaktapur Durbar Square", "heritage-temples", 27.6720, 85.4280, "Bhaktapur", "Bagmati",
     "UNESCO-listed royal square with 55-window palace, Nyatapola temple, Golden Gate, and Peacock Window.",
     "/images/destinations/bhaktapur/durbar.jpg", ["bhaktapur durbar", "khwopa"]),
    ("Patan Durbar Square", "heritage-temples", 27.6735, 85.3250, "Lalitpur", "Bagmati",
     "UNESCO-listed ancient palace complex in Lalitpur with Krishna Mandir, Golden Temple, and Patan Museum.",
     "/images/destinations/patan/durbar.jpg", ["patan durbar", "lalitpur durbar"]),
    ("Chitwan National Park Visitor Center", "wildlife", 27.5450, 84.5100, "Chitwan", "Bagmati",
     "Main entry and visitor center for Chitwan National Park; jeep safari, elephant rides, one-horned rhino.",
     "/images/destinations/chitwan/safari.jpg", []),
]

# Key destinations whose names are hotels/lodges that we want to HIDE
# from the default destination listing (they are accommodations, not places to visit):
ACCOMMODATION_CATEGORIES = [
    "hotel", "guest_house", "hostel", "alpine_hut", "motel",
    "apartment", "camp_pitch", "camp_site", "chalet", "resort",
    "wilderness_hut", "home_stay", "homestay",
]


class Command(BaseCommand):
    help = "Add missing real Nepal destinations (temples, caves, lakes, viewpoints, heritage sites)."

    def add_arguments(self, parser):
        parser.add_argument("--filter-hotels", action="store_true",
                            help="Mark hotel/lodge/guest_house destinations as inactive so they don't clutter listings.")
        parser.add_argument("--no-photos", action="store_true",
                            help="Don't try to attach local photos.")

    def handle(self, *args, **options):
        filter_hotels = options["filter_hotels"]
        no_photos = options["no_photos"]

        # Ensure categories exist / cache them
        cat_cache = {c.slug: c for c in Category.objects.all()}
        # Map missing slug variants
        cat_aliases = {
            "nature-trekking": "nature-trekking",
            "religious-sites": "religious-sites",
            "heritage-temples": "heritage-temples",
            "lakes-water-activities": "lakes-water-activities",
            "wildlife": "wildlife",
            "photography-spots": "photography-spots",
            "museum": "museum",
            "attraction": "attraction",
            "viewpoint": "viewpoint",
        }
        default_cat = cat_cache.get("attraction")
        if default_cat is None:
            default_cat, _ = Category.objects.get_or_create(
                slug="attraction",
                defaults={"name": "Attractions", "icon": "star", "description": "Tourist attractions and points of interest"},
            )
            cat_cache["attraction"] = default_cat

        added = 0
        skipped = 0
        for (name, cslug, lat, lon, district, province, desc, photo, aliases) in MISSING:
            # Check if destination exists (by name)
            if Destination.objects.filter(name__iexact=name).exists():
                skipped += 1
                continue
            # Check aliases
            found = False
            for a in aliases:
                if Destination.objects.filter(name__icontains=a).exists():
                    found = True; break
            if found:
                skipped += 1
                continue

            cat = cat_cache.get(cat_aliases.get(cslug, cslug), default_cat)
            with transaction.atomic():
                d = Destination.objects.create(
                    name=name,
                    category=cat,
                    latitude=str(lat),
                    longitude=str(lon),
                    city=district,
                    district=district,
                    province=province,
                    country="Nepal",
                    short_description=desc,
                    description=desc,
                    is_active=True,
                    is_user_submitted=False,
                    status=Destination.SubmissionStatus.APPROVED,
                    aliases=", ".join(aliases),
                    best_time_to_visit="Sep–Nov / Mar–May",
                )
                # Attach local photo if we have one
                if photo and not no_photos:
                    full = os.path.join(
                        settings_base(),
                        "frontend", "Tourism", "public", photo.lstrip("/")
                    )
                    if os.path.exists(full):
                        with open(full, "rb") as f:
                            data = f.read()
                        di = DestinationImage(
                            destination=d,
                            caption=name,
                            source=DestinationImage.Source.REFERENCE,
                            photographer="Nepal Tourism Platform (AI)",
                            license_type="Platform-generated (royalty-free)",
                            source_url=f"static://{photo}",
                            image_category="attraction",
                            is_cover=True,
                            verification_status=DestinationImage.ImageStatus.APPROVED,
                            is_verified=True,
                            authenticity_score=0.9,
                            attribution="AI-generated for Nepal Tourism",
                            external_url=photo,
                        )
                        # Save without touching ImageField (use external_url = static path)
                        di.save()
            added += 1
            self.stdout.write(self.style.SUCCESS(f"  + {name}"))

        self.stdout.write(self.style.SUCCESS(f"Added {added} new destinations (skipped {skipped} already exist)."))

        # Optionally mark accommodation-type "destinations" as is_active=False so they
        # don't appear in the destination discovery pages
        if filter_hotels:
            cats = Category.objects.filter(slug__in=ACCOMMODATION_CATEGORIES)
            ids = list(cats.values_list("id", flat=True))
            updated = Destination.objects.filter(category_id__in=ids, is_active=True).update(is_active=False)
            self.stdout.write(self.style.SUCCESS(
                f"Marked {updated} accommodation-type Destinations as inactive "
                f"(they remain accessible via Hotels page, not destination listings)."
            ))

        self.stdout.write(f"Final destination count: {Destination.objects.count()}")
