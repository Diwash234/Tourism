"""
import_osm_lodging — import the REAL OpenStreetMap lodging layer
(ml_service/data/destinations/nepal_destination_sample.csv: hotels, guest
houses, hostels, alpine huts, motels, chalets — 3,400+ named places with
exact OSM coordinates, phones and districts) into the Hotel table, which is
what /places/nearby/?category=hotel actually queries.

This is the remote/rural coverage layer: alpine huts and village guest houses
that no city-hotel dataset contains (Manaslu, Annapurna, Langtang, far-west
trail lodges). Every record is a real OSM element — osm_id stored in
source_url for traceability; nothing is invented.

Idempotent: rows are keyed by name + coordinates.

Usage:  python manage.py import_osm_lodging
"""

import csv
import os

from django.core.management.base import BaseCommand

from tourist.models import Destination, Hotel

CSV_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..",
    "ml_service", "data", "destinations", "nepal_destination_sample.csv"))

LODGING = {
    "hotel": "Hotel", "guest_house": "Guest House", "hostel": "Hostel",
    "alpine_hut": "Alpine Hut", "motel": "Motel", "chalet": "Chalet",
}


def _real(v):
    return v and v.strip() and v.strip() != "Not Available"


class Command(BaseCommand):
    help = "Import the real OSM lodging layer (hotels/guest houses/huts) into the Hotel table."

    def handle(self, *args, **opts):
        rows = list(csv.DictReader(open(CSV_PATH, newline="", encoding="utf-8")))
        created = skipped = unmatched = 0
        district_anchor = {}

        for r in rows:
            cat = (r.get("tourism") or "").strip()
            name = (r.get("name") or "").strip()
            if cat not in LODGING or not name:
                continue
            try:
                lat, lng = float(r["latitude"]), float(r["longitude"])
            except (KeyError, TypeError, ValueError):
                skipped += 1
                continue
            if Hotel.objects.filter(name=name, latitude=lat, longitude=lng).exists():
                skipped += 1
                continue

            dest = Destination.objects.filter(name__iexact=name).order_by("id").first()
            if dest is None:
                district = (r.get("district") or "").strip()
                if district:
                    if district not in district_anchor:
                        district_anchor[district] = (
                            Destination.objects.filter(district__iexact=district, is_active=True)
                            .exclude(latitude__isnull=True).first()
                        )
                    dest = district_anchor[district]
            if dest is None:
                unmatched += 1
                continue

            osm_ref = f"{r.get('osm_type', 'node')}/{r.get('osm_id', '')}"
            phone = r.get("phone") if _real(r.get("phone")) else ""
            website = r.get("website") if _real(r.get("website")) else ""
            Hotel.objects.create(
                destination=dest,
                name=name[:200],
                address=(f"{(r.get('district') or '').strip()}, Nepal")[:255],
                latitude=lat, longitude=lng,
                phone=(phone or "")[:30],
                booking_url=(website or "")[:500],
                source=Hotel.Source.DATASET,
                source_url=f"https://www.openstreetmap.org/{osm_ref}" if r.get("osm_id") else "",
                is_verified=False, is_active=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"OSM lodging imported: created={created} skipped(existing/invalid)={skipped} "
            f"unmatched(no destination anchor)={unmatched} total_hotels={Hotel.objects.count()}"
        ))
