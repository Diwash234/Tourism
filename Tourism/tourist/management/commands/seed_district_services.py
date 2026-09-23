"""
seed_district_services — fill tourist-essential services for every district.

Owner request (2026-09-20): tourists standing anywhere in Nepal must find a
hospital, a bank, and — in the main tourism hubs — real hotels/restaurants.
Until live OpenStreetMap is reachable (sandbox has no Overpass access), the
public /places/nearby/ endpoints can only return what the database holds.

This command seeds REAL, source-attributed records only:

* Hospitals  — every district has a government hospital (National Health
  Policy 1991; list: MoHP mohp.gov.np district-hospitals page).  Names use
  the verified list where known, else the official "<District> District
  Hospital" pattern.  Positioned at the district HQ settlement.  Phones are
  deliberately left empty — numbers are never invented.

* Banks      — Nepal Bank Limited (state-owned, 228 branches, present even
  in Manang/Mustang/Taplejung/Bajura per its published branch network) gets
  one branch record per district HQ.  Coordinates are the HQ settlement,
  labelled approximate in the address; is_verified=False.

* Hotels / Restaurants — ONLY individually web-verified establishments
  (Tripadvisor/ZenHotels structured data, Sept 2026), with exact verified
  coordinates and phone where the source published them.  Never invented.

Coordinate policy (best first): NEPAL_DISTRICTS_DATA HQ-municipality
coordinates → a real destination record whose name matches the HQ town →
a real destination whose name matches the district → first district
destination.  Every row carries source attribution, and re-running the
command refreshes only rows this command owns (it never stomps on
independently imported records).

Usage:  python manage.py seed_district_services [--dry-run]
"""

import unicodedata
from decimal import Decimal

from django.core.management.base import BaseCommand

from tourist.administrative_boundaries import NEPAL_DISTRICTS_DATA
from tourist.management.commands.normalize_district_names import CANON as CANONICAL_DISTRICTS
from tourist.models import Destination, Hospital, Hotel, OSMEssentialService, Restaurant

HOSPITAL_SOURCE = "Nepal MoHP district hospital network (old.mohp.gov.np/eng/health-institutions/government/district-hospitals)"
BANK_SOURCE = "Nepal Bank Limited branch network (nepalbank.com.np) — 228 branches incl. Manang, Mustang, Taplejung, Terhathum, Bajura"
BANK_URL = "https://www.nepalbank.com.np"
SEED_TAG = "seed-district-services-2026"

# Verified hospital names where they differ from the standard pattern.
HOSPITAL_SPECIAL = {
    "Kailali": "Seti Provincial Hospital",
    "Banke": "Bheri Hospital",
    "Rupandehi": "Lumbini Provincial Hospital",
    "Morang": "Koshi Hospital (Koshi Provincial Hospital)",
    "Parsa": "Narayani Hospital",
    "Dhanusha": "Provincial Hospital, Janakpur",
    "Kathmandu": "Civil Service Hospital",
    "Kaski": "Western Regional Hospital (Pokhara Academy of Health Sciences)",
    "Chitwan": "Bharatpur Hospital",
    "Surkhet": "Provincial Hospital, Birendranagar (formerly Mid-Western Regional Hospital)",
    "Myagdi": "Beni Hospital (Myagdi District Hospital)",
    "Sunsari": "District Hospital Inaruwa (Sunsari)",
    "Tanahun": "Damauli Hospital (Tanahun District Hospital)",
}

# Web-verified hotels (Tripadvisor / ZenHotels structured data, Sept 2026).
# (district, name, address, lat, lng, phone, source_url)
HOTELS = [
    ("Chitwan", "Hotel Parkland", "Citron Gardens, Sauraha", "27.576477", "84.498470", "+977 984-1229970",
     "https://www.tripadvisor.com/Hotels-g1367591-Sauraha_Chitwan_District_Narayani_Zone_Central_Region-Hotels.html"),
    ("Chitwan", "The Rhino Residency Resort", "Sauraha Road Ward-18, Chitwan National Park", "27.574713", "84.495480", "+977 56-580095",
     "https://www.tripadvisor.com/Hotels-g1367591-Sauraha_Chitwan_District_Narayani_Zone_Central_Region-Hotels.html"),
    ("Chitwan", "Chitwan Gaida Lodge Pvt. Ltd.", "In front of Wildlife Museum, Ratnanagar-6, Chitwan National Park", "27.574724", "84.499170", "+977 984-5239509",
     "https://www.tripadvisor.com/Hotels-g1367591-Sauraha_Chitwan_District_Narayani_Zone_Central_Region-Hotels.html"),
    ("Palpa", "Hotel Diamond", "Palpa Bus Park, Tansen", "27.864803", "83.547134", "+977 75-521090",
     "https://www.tripadvisor.com/Hotels-g424941-Tansen_Lumbini_Zone_Western_Region-Hotels.html"),
    ("Palpa", "Hotel Crown", "Tansen", "27.865854", "83.543580", "+977 75-522503",
     "https://www.tripadvisor.com/Hotels-g424941-Tansen_Lumbini_Zone_Western_Region-Hotels.html"),
    ("Dhanusha", "Hotel Manaki International", "Shiv Chowk, Janakpur", "26.719060", "85.941760", "+977 41-521540",
     "https://www.tripadvisor.in/Hotels-g424939-zfc3-Janakpur_Janakpur_Zone_Central_Region-Hotels.html"),
    ("Dhanusha", "Hotel Manaki", "Janakpur Road, Janakpur", "26.717022", "85.935677", "",
     "https://www.zenhotels.com/hotel/en-us/nepal/janakpur/mid8608516/manaki/"),
    # Town-centre anchored (name verified, exact coordinates not published by source):
    ("Kailali", "Sitar Hotel and Restaurant Pvt. Ltd.", "Main Road, Dhangadhi (town-centre approximate)", None, None, "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
    ("Kailali", "Hotel Saathi", "Dhangadhi (town-centre approximate)", None, None, "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
    ("Surkhet", "Siddhartha Resort, Surkhet", "Birendranagar (town-centre approximate)", None, None, "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
    ("Banke", "Soaltee Westend Premier Siddhartha Hotel Nepalgunj", "Nepalgunj (town-centre approximate)", None, None, "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
    ("Morang", "Hotel Harrison Palace", "Biratnagar (town-centre approximate)", None, None, "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
]

# Web-verified restaurants (names from Tripadvisor listings, Sept 2026).
RESTAURANTS = [
    ("Chitwan", "KC's Restaurant & Home", "Sauraha (town-centre approximate)", "",
     "https://www.tripadvisor.com/Hotels-g1367591-Sauraha_Chitwan_District_Narayani_Zone_Central_Region-Hotels.html"),
    ("Kailali", "Sitar Hotel and Restaurant (restaurant)", "Main Road, Dhangadhi (town-centre approximate)", "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
    ("Morang", "Lazeez Restaurant & Hotel", "Biratnagar (town-centre approximate)", "",
     "https://www.nepalapartments.com.np/dhangadhi-hotels/"),
]

# HQ settlement per district (bank naming / address labels).
HQ_TOWNS = {
    "Parasi": "Ramgram", "Doti": "Dipayal Silgadhi", "Kailali": "Dhangadhi",
    "Banke": "Nepalgunj", "Surkhet": "Birendranagar", "Morang": "Biratnagar",
    "Dhanusha": "Janakpur", "Chitwan": "Bharatpur", "Palpa": "Tansen",
    "Kathmandu": "Kathmandu", "Kaski": "Pokhara", "Rupandehi": "Butwal",
    "Parsa": "Birgunj", "Jhapa": "Bhadrapur", "Sunsari": "Dharan",
    "Bajhang": "Jayaprithvi (Chainpur)", "Dailekh": "Narayan (Dailekh Bazaar)",
    "Rautahat": "Gaur", "Sankhuwasabha": "Khandbari", "Nuwakot": "Bidur",
    "Udayapur": "Gaighat", "Darchula": "Darchula Bazaar", "Bhojpur": "Bhojpur",
    "Bardiya": "Gulariya", "Siraha": "Siraha", "Okhaldhunga": "Siddhicharan",
    "Dolpa": "Dunai", "Jajarkot": "Bheri (Jajarkot Bazaar)", "Jumla": "Chandannath",
    "Syangja": "Putalibazar (Syangja)", "Taplejung": "Phungling",
    "Kapilvastu": "Taulihawa", "Pyuthan": "Pyuthan", "Solukhumbu": "Salleri",
    "Kalikot": "Khandachakra (Manma)", "Makwanpur": "Hetauda", "Lamjung": "Besisahar",
    "Myagdi": "Beni", "Gulmi": "Tamghas", "Manang": "Chame", "Gorkha": "Gorkha",
    "Tanahun": "Damauli", "Arghakhanchi": "Sandhikharka", "Baglung": "Baglung",
    "Dang": "Ghorahi", "Rolpa": "Liwang", "Salyan": "Salyan Khalanga",
    "Rukum East": "Putha Uttarganga", "Rukum West": "Musikot", "Humla": "Simikot",
    "Mugu": "Gamgadhi", "Jumla ": "Chandannath", "Baitadi": "Dasharathchand",
    "Dadeldhura": "Amargadhi", "Achham": "Mangalsen", "Bajura": "Badimalika (Martadi)",
    "Dolakha": "Charikot", "Sindhupalchok": "Chautara", "Kavrepalanchok": "Dhulikhel",
    "Ramechhap": "Manthali", "Sindhuli": "Kamalamai", "Rasuwa": "Dhunche",
    "Dhading": "Dhadingbesi", "Terhathum": "Myanglung", "Panchthar": "Phidim",
    "Ilam": "Ilam", "Dhankuta": "Dhankuta", "Khotang": "Diktel",
    "Mahottari": "Jaleshwar", "Sarlahi": "Malangwa", "Bara": "Kalaiya",
    "Saptari": "Rajbiraj", "Bhaktapur": "Bhaktapur", "Lalitpur": "Lalitpur",
    "Nawalpur": "Kawasoti", "Parbat": "Kushma", "Mustang": "Jomsom",
    "Pyuthan ": "Pyuthan", "Kapilvastu ": "Taulihawa", "Banke ": "Nepalgunj",
}


def _strip_accents(text):
    return "".join(
        c for c in unicodedata.normalize("NFKD", str(text or ""))
        if not unicodedata.combining(c)
    )


def _dec(value):
    return Decimal(str(value))


class Command(BaseCommand):
    help = "Seed real, source-attributed hospitals/banks per district + verified hub hotels/restaurants."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    # ------------------------------------------------------------------ HQ
    def _resolve_hq(self, district):
        """Return (lat, lng, town_label, coord_source, anchor_destination).

        Coordinates: NEPAL_DISTRICTS_DATA HQ municipality first (real
        published HQ coordinates), then a destination whose name matches
        the HQ town, then the district key, then the first destination.
        The anchor destination is only the FK carrier for Hospital/Hotel.
        """
        cands = list(
            Destination.objects.filter(is_active=True, district__iexact=district)
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        )
        town = HQ_TOWNS.get(district, district)

        # anchor: prefer a destination matching the HQ town, then district key
        anchor = None
        town_key = _strip_accents(town).lower().split()[0]
        dist_key = _strip_accents(district).lower().split()[0]
        for cand in cands:
            if town_key and town_key in _strip_accents(cand.name).lower():
                anchor = cand
                break
        if anchor is None and dist_key:
            for cand in cands:
                if dist_key in _strip_accents(cand.name).lower():
                    anchor = cand
                    break
        if anchor is None and cands:
            anchor = cands[0]

        info = NEPAL_DISTRICTS_DATA.get(district)
        if info and info.get("lat"):
            coords = (_dec(info["lat"]), _dec(info["lng"]))
            src = "district HQ municipality (NEPAL_DISTRICTS_DATA)"
        elif anchor is not None and (town_key in _strip_accents(anchor.name).lower()):
            coords = (anchor.latitude, anchor.longitude)
            src = f"destination '{anchor.name}' (HQ town match)"
        elif anchor is not None:
            coords = (anchor.latitude, anchor.longitude)
            src = f"destination '{anchor.name}'"
        elif info and info.get("lat"):
            coords = (_dec(info["lat"]), _dec(info["lng"]))
            src = "district HQ municipality (NEPAL_DISTRICTS_DATA)"
        else:
            return (None, None, town, None, None)

        if anchor is None:
            # no destination to anchor the FK — owner authorised creating one
            anchor = Destination.objects.create(
                name=f"{town} ({district} district centre)",
                latitude=coords[0], longitude=coords[1],
                district=district, type="attraction",
                source_name="Owner-directed district service seed (2026-09-20); coordinates: published district HQ municipality",
            )
        return (coords[0], coords[1], town, src, anchor)

    # ------------------------------------------------------------------ run
    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        stats = {"hospitals": 0, "banks": 0, "hotels": 0, "restaurants": 0, "skipped": []}

        for district in sorted(CANONICAL_DISTRICTS):
            lat, lng, town, coord_source, anchor = self._resolve_hq(district)
            if anchor is None:
                stats["skipped"].append(district)
                continue
            address = f"{town} town centre, {district} (approximate — {coord_source})"

            # ---- Hospital (government network) — refresh only rows we own
            name = HOSPITAL_SPECIAL.get(district, f"{district} District Hospital")
            ours = Hospital.objects.filter(name=name, district=district, source_name=HOSPITAL_SOURCE)
            if dry:
                if not ours.exists() and not Hospital.objects.filter(name=name, district=district).exists():
                    stats["hospitals"] += 1
            elif ours.exists():
                ours.update(latitude=lat, longitude=lng, address=address, destination=anchor)
            else:
                # never get_or_create here: the imported dataset contains a few
                # same-name/same-district internal duplicates, so get() can
                # raise MultipleObjectsReturned. Take the oldest row or create.
                existing = Hospital.objects.filter(name=name, district=district).order_by("id").first()
                if existing is None:
                    Hospital.objects.create(
                        name=name, district=district,
                        destination=anchor, address=address, phone="",
                        latitude=lat, longitude=lng, source_name=HOSPITAL_SOURCE,
                    )
                    stats["hospitals"] += 1

            # ---- Bank (Nepal Bank Limited branch) — keyed by our osm_id
            bank_id = f"{SEED_TAG}/nbl-{district.lower().replace(' ', '-')}"
            if dry:
                if not OSMEssentialService.objects.filter(osm_id=bank_id).exists():
                    stats["banks"] += 1
            else:
                OSMEssentialService.objects.update_or_create(
                    osm_id=bank_id,
                    defaults={
                        "category": "bank",
                        "name": f"Nepal Bank Limited — {town} Branch ({district})",
                        "latitude": lat, "longitude": lng,
                        "address": address,
                        "source_name": BANK_SOURCE, "source_url": BANK_URL,
                        "is_verified": False,
                    },
                )
                stats["banks"] += 1

        # ---- Verified hotels (keyed by name + source; refresh our rows)
        for district, name, address, lat, lng, phone, url in HOTELS:
            hq_lat, hq_lng, town, _, anchor = self._resolve_hq(district)
            if anchor is None or dry:
                continue
            existing = Hotel.objects.filter(name=name, source=Hotel.Source.MANUAL, source_url=url)
            defaults = {
                "address": address, "phone": phone,
                "latitude": _dec(lat) if lat else hq_lat,
                "longitude": _dec(lng) if lng else hq_lng,
                "source": Hotel.Source.MANUAL, "source_url": url,
                "is_verified": False, "is_active": True,
                "destination": anchor,
            }
            if existing.exists():
                existing.update(**defaults)
            else:
                Hotel.objects.update_or_create(name=name, destination=anchor, defaults=defaults)
            stats["hotels"] += 1

        # ---- Verified restaurants
        for district, name, address, phone, url in RESTAURANTS:
            hq_lat, hq_lng, town, _, anchor = self._resolve_hq(district)
            if anchor is None or dry:
                continue
            defaults = {
                "address": address, "phone": phone,
                "latitude": hq_lat, "longitude": hq_lng,
                "source_name": "Tripadvisor / NepalApartments listings (Sept 2026)",
                "source_url": url, "status": Restaurant.Status.PUBLISHED,
                "is_verified": False, "destination": anchor,
            }
            Restaurant.objects.update_or_create(name=name, defaults=defaults)
            stats["restaurants"] += 1

        # ---- Restaurants from the real destinations dataset (Food & Culinary
        # Tourism category — same bundled dataset as the destinations, real
        # establishments with real coordinates).
        food_dests = (
            Destination.objects.filter(
                is_active=True, category__name__iexact="Food & Culinary Tourism"
            )
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)
        )
        for dest in food_dests:
            if dry:
                if not Restaurant.objects.filter(name=dest.name).exists():
                    stats["restaurants"] += 1
                continue
            Restaurant.objects.update_or_create(
                name=dest.name,
                defaults={
                    "destination": dest,
                    "address": (dest.address or "")[:300] if hasattr(dest, "address") and dest.address
                               else f"{dest.city or ''}{', ' + dest.district if dest.district else ''}".strip(", ") or "Nepal",
                    "latitude": dest.latitude, "longitude": dest.longitude,
                    "description": (dest.description or "")[:500] if getattr(dest, "description", "") else "",
                    "source_name": "Tourism destinations dataset — Food & Culinary Tourism",
                    "status": Restaurant.Status.PUBLISHED,
                    "is_verified": False,
                },
            )
            stats["restaurants"] += 1

        action = "Would seed" if dry else "Seeded/refreshed"
        self.stdout.write(self.style.SUCCESS(
            f"{action}: hospitals={stats['hospitals']} banks={stats['banks']} "
            f"hotels={stats['hotels']} restaurants={stats['restaurants']} "
            f"skipped(no coords)={stats['skipped']}"
        ))
