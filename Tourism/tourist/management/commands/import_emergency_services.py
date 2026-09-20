"""
import_emergency_services — import the REAL OSM amenity layer
(ml_service/data/emergency/emergency_services.csv: 762 bank branches,
346 ATMs, 141 hospitals, 225 clinics, 351 pharmacies, 81 police — real
Nepali banks like Himalaya Bank, Everest Bank, Nabil, KIST with exact OSM
coordinates and phones).

Rows go into OSMEssentialService, which is what /places/nearby/ falls back
to for bank/atm/hospital/pharmacy/police categories. Nothing invented:
rows without a recorded name are labelled "name not recorded in OSM".
Idempotent via a stable synthetic osm_id keyed on coordinates + name.

Usage:  python manage.py import_emergency_services
"""

import csv
import hashlib
import os

from django.core.management.base import BaseCommand

from tourist.models import OSMEssentialService

CSV_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ml_service", "data", "emergency", "emergency_services.csv"))

# csv amenity -> OSMEssentialService category (only categories the model +
# nearby endpoint support)
CATEGORY = {
    "bank": "bank", "atm": "atm",
    "hospital": "hospital", "clinic": "hospital", "doctors": "hospital",
    "pharmacy": "pharmacy", "police": "police",
}


def _real(v):
    return v and v.strip() and v.strip() != "Not Available"


class Command(BaseCommand):
    help = "Import real OSM banks/ATMs/clinics/pharmacies/police into OSMEssentialService."

    def handle(self, *args, **opts):
        rows = list(csv.DictReader(open(CSV_PATH, newline="", encoding="utf-8")))
        created = skipped = 0
        for r in rows:
            amenity = (r.get("amenity") or "").strip().lower()
            cat = CATEGORY.get(amenity)
            if not cat:
                continue
            try:
                lat, lng = float(r["latitude"]), float(r["longitude"])
            except (KeyError, TypeError, ValueError):
                skipped += 1
                continue
            name = (r.get("name") or "").strip()
            if not _real(name):
                name = f"{cat.title()} (name not recorded in OSM)"
            # deterministic across runs (hash() is salted per process)
            digest = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]
            osm_id = f"seed/emergency-services/{cat}/{lat:.6f},{lng:.6f},{digest}"
            addr_bits = [r.get("addr:street"), r.get("addr:city"), r.get("addr:postcode")]
            address = ", ".join(b.strip() for b in addr_bits if _real(b)) or "Nepal"
            _, was_created = OSMEssentialService.objects.get_or_create(
                osm_id=osm_id,
                defaults={
                    "category": cat,
                    "name": name[:160],
                    "latitude": lat, "longitude": lng,
                    "address": address[:255],
                    "phone": (r.get("phone") if _real(r.get("phone")) else "")[:50],
                    "opening_hours": (r.get("opening_hours") if _real(r.get("opening_hours")) else "")[:160],
                    "source_name": "OpenStreetMap amenity extract (ml_service/data/emergency/emergency_services.csv)",
                    "is_verified": False,
                },
            )
            created += 1 if was_created else 0
            skipped += 0 if was_created else 1
        self.stdout.write(self.style.SUCCESS(
            f"Emergency/amenity services imported: created={created} existing_skipped={skipped} "
            f"total_osm_services={OSMEssentialService.objects.count()}"
        ))
