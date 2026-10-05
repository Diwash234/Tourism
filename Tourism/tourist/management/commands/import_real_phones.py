"""Fill missing phone numbers from the project's own source files.

Why this exists
---------------
Measured honestly (sentinel-aware, so a literal "Not Available" is not counted
as a number), the catalogue holds 1,620 usable phone numbers across 8,918 rows
that carry a phone field: 18.2% coverage. Of the 7,298 rows with no usable
number, exactly 441 have a genuine, verifiable number sitting unused in the
repository's own CSV exports. This command supplies those 441 and nothing else.

The alternative numbers that would reach 100% do not exist. They would have to
be invented, and an invented number that a traveller dials does not fail
quietly -- it reaches a stranger's telephone.

Matching on evidence, not resemblance
-------------------------------------
Matching by name alone would attach a number to the wrong place whenever two
destinations share a name, and the source files carry coordinates, so proximity
is used as the primary evidence:

* **Within 2 km** of the destination, the two records describe the same place
  and the source row's number is used. This is the rule that does the work.
* **Name match, coordinates too far apart or absent** -- used only when the
  name resolves to exactly one distinct real number. A name shared by several
  different numbers is ambiguous, and ambiguity is left alone.
* Anything else is left without a number and reported.

Safety rules
------------
1. A number already present is never overwritten.
2. Only numbers that pass :func:`usable_phone` are used, so stringified nulls
   ("nan", "Not Available") and templated filler are rejected, not imported.
3. A real number held by more than one source row is treated as ambiguous.
4. Nothing is guessed and nothing is invented.
5. Dry run unless ``--apply`` is passed, so the changes can be read first.

Usage
-----
    python manage.py import_real_phones
    python manage.py import_real_phones --apply
    python manage.py import_real_phones --radius-km 5 --apply
"""
import csv
import math
import os
import re
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import (Hospital, Hotel, OSMEssentialService, PoliceStation,
                            Restaurant)
from tourist.phone_quality import is_null_sentinel, usable_phone

#: The repository's own exports, and the columns they use.
#:
#: Paths are the ones the files actually occupy. Several near-identical exports
#: exist in more than one place, and an earlier pass that looked for
#: ``nepal_hotels_cleaned.csv`` under ``ml_service/data/emergency/`` silently
#: found nothing -- which is how a file holding 1,597 real numbers went unread.
#:
#: What each source really holds, measured with the sentinel-aware filter:
#:
#:   Tourism/dataset/hotel.csv                  2,104 rows, 2,097 real, all located
#:   ml_service/nepal_hotels_cleaned.csv         1,603 rows, 1,597 real, all located
#:   ml_service/data/emergency/hospital.csv     2,071 rows, 1,300 real, 713 filler
#:   ml_service/data/emergency/emergency_s...    3,293 rows,   541 real, 2,752 "Not Available"
#:   Tourism/dataset/police_station_cleaned.csv   792 rows,    10 real
#:   ml_service/data/emergency/nearbypolice.csv  2,601 rows,     0 real
#:
#: The police exports are the reason police-station phone coverage cannot be
#: improved: after 3,393 rows across two files, ten real numbers survive.
SOURCES = [
    ("dataset/hotel.csv",
     os.path.join("Tourism", "dataset", "hotel.csv"),
     {"name": "Hotel Name", "phone": "Phone", "lat": "Latitude", "lon": "Longitude"}),
    ("ml_service/nepal_hotels_cleaned.csv",
     os.path.join("ml_service", "nepal_hotels_cleaned.csv"),
     {"name": "hotel_name", "phone": "phone", "lat": "latitude", "lon": "longitude"}),
    ("emergency/hospital.csv",
     os.path.join("ml_service", "data", "emergency", "hospital.csv"),
     {"name": "Hospital Name", "phone": "Phone", "lat": "Latitude", "lon": "Longitude"}),
    ("emergency/hospital_cleaned.csv",
     os.path.join("ml_service", "data", "emergency", "hospital_cleaned.csv"),
     {"name": "Hospital Name", "phone": "Phone", "lat": "Latitude", "lon": "Longitude"}),
    ("ml_service/nepal_hospitals.csv",
     os.path.join("ml_service", "nepal_hospitals.csv"),
     {"name": "Hospital Name", "phone": "Phone", "lat": None, "lon": None}),
    ("emergency_services.csv",
     os.path.join("ml_service", "data", "emergency", "emergency_services.csv"),
     {"name": "name", "phone": "phone", "lat": "latitude", "lon": "longitude"}),
    ("dataset/police_station_cleaned.csv",
     os.path.join("Tourism", "dataset", "police_station_cleaned.csv"),
     {"name": "police_station", "phone": "phone", "lat": "latitude", "lon": "longitude"}),
    ("emergency/nearbypolice.csv",
     os.path.join("ml_service", "data", "emergency", "nearbypolice.csv"),
     {"name": "name", "phone": "phone", "lat": "latitude", "lon": "longitude"}),
]

TARGETS = [
    (Hospital, "hospital"),
    (PoliceStation, "police station"),
    (Hotel, "hotel"),
    (Restaurant, "restaurant"),
    (OSMEssentialService, "essential service"),
]

KM_PER_DEGREE = 111.0
EARTH_RADIUS_KM = 6371.0088


def normalise(text):
    """Case- and punctuation-insensitive key for a place name."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def number_key(value):
    """Identity of a phone number, independent of how it is punctuated.

    The hotel exports record the same number twice, once dashed and once plain:
    ``+977-1-4479488`` and ``+97714479488`` are one number, not two. Comparing
    the strings made 1,573 hotels look ambiguous and withheld the number, when
    the sources in fact agreed completely. Comparing digits instead is what
    "do these records agree?" actually means.
    """
    return re.sub(r"\D", "", str(value or ""))


def _as_float(value):
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometres.

    Haversine rather than a flat approximation: one degree of longitude is
    111 km only at the equator, and at Nepal's 27 degrees north it is nearer
    99. Treating a degree as 111 km in both directions overstated every
    east-west separation here by about 12%, which is wide enough to let a
    source record from the next district satisfy a 2 km proximity test.

    Coordinates are Decimal on some models and float on others, so both sides
    are coerced before use.
    """
    lat1, lon1, lat2, lon2 = (float(v) for v in (lat1, lon1, lat2, lon2))
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, a)))


def repository_root():
    """The checkout that holds ml_service/, i.e. the parent of Tourism/."""
    here = os.path.abspath(os.getcwd())
    for candidate in (here, os.path.dirname(here)):
        if os.path.isdir(os.path.join(candidate, "ml_service")):
            return candidate
    return os.path.dirname(here)


def read_source_rows(root):
    """name -> list of (lat, lon, usable_phone, source) across every file."""
    index = defaultdict(list)
    for filename, relative, columns in SOURCES:
        path = os.path.join(root, relative)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace", newline="") as handle:
            for row in csv.DictReader(handle):
                name = normalise(row.get(columns["name"]))
                raw = (row.get(columns["phone"]) or "").strip()
                if not name or not raw or is_null_sentinel(raw):
                    continue
                number = usable_phone(raw)
                if not number:
                    continue
                index[name].append({
                    "phone": number,
                    "lat": _as_float(row.get(columns["lat"])),
                    "lon": _as_float(row.get(columns["lon"])),
                    "source": filename,
                })
    return index


def choose_number(candidates, lat, lon, radius_km):
    """Pick the one number a destination's own coordinates justify.

    Returns (phone, source, reason) or (None, None, reason-for-refusal).
    """
    if lat is not None and lon is not None:
        nearby = [c for c in candidates
                  if c["lat"] is not None and c["lon"] is not None
                  and distance_km(lat, lon, c["lat"], c["lon"]) <= radius_km]
        if nearby:
            keys = {number_key(c["phone"]) for c in nearby}
            if len(keys) == 1:
                best = min(nearby, key=lambda c: distance_km(lat, lon, c["lat"], c["lon"]))
                return best["phone"], best["source"], (
                    f"{distance_km(lat, lon, best['lat'], best['lon']):.1f} km away")
            return None, None, f"{len(keys)} different numbers within {radius_km:g} km"

    keys = {number_key(c["phone"]) for c in candidates}
    if not keys:
        return None, None, "no usable number"
    if len(keys) == 1:
        only = next(iter(keys))
        winner = next(c for c in candidates if number_key(c["phone"]) == only)
        # Say plainly when this is a name match rather than a location match,
        # so the weaker evidence is visible in the run's own report.
        located = lat is not None and lon is not None
        reason = ("unique number for this name" if not located else
                  "unique number for this name, though no source record was nearby")
        return winner["phone"], winner["source"], reason
    return None, None, f"{len(keys)} different numbers share this name"


class Command(BaseCommand):
    help = "Fill missing phone numbers from the project's own source exports."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Write the numbers. Without this, nothing changes.")
        parser.add_argument("--radius-km", type=float, default=2.0,
                            help="How close a source record must be to count as the "
                                 "same place (default 2.0).")

    def handle(self, *args, **options):
        root = repository_root()
        index = read_source_rows(root)
        radius = options["radius_km"]

        self.stdout.write(f"source repository: {root}")
        self.stdout.write(
            f"read {len(index)} distinct place names carrying a real number")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING(
                "DRY RUN - pass --apply to write. No number below is invented; "
                "each one already exists in the repository's own exports."))

        filled = defaultdict(int)
        refused = defaultdict(int)
        reasons = defaultdict(int)
        total = 0
        changes = []

        for model, label in TARGETS:
            queryset = model.objects.all()
            for record in queryset.iterator():
                if usable_phone(getattr(record, "phone", "")):
                    continue  # never overwrite a real number
                total += 1
                candidates = index.get(normalise(record.name))
                if not candidates:
                    refused[label] += 1
                    reasons["no source record for this name"] += 1
                    continue
                number, source, reason = choose_number(
                    candidates,
                    getattr(record, "latitude", None),
                    getattr(record, "longitude", None),
                    radius,
                )
                if not number:
                    refused[label] += 1
                    reasons[reason] += 1
                    continue
                changes.append((model, label, record, number, source, reason))

        if options["apply"]:
            for model, label, record, number, source, reason in changes:
                with transaction.atomic():
                    # Re-read under the guard: another process may have filled it.
                    fresh = model.objects.get(pk=record.pk)
                    if usable_phone(fresh.phone):
                        continue
                    fresh.phone = number
                    fresh.save(update_fields=["phone", "updated_at"]
                               if _has_updated_at(model) else ["phone"])
                filled[label] += 1
        else:
            for model, label, record, number, source, reason in changes:
                filled[label] += 1

        self.stdout.write("")
        self.stdout.write(f"rows with no usable phone: {total}")
        self.stdout.write(f"rows a source file can genuinely supply: {len(changes)}")
        self.stdout.write("")
        for model, label in TARGETS:
            self.stdout.write(
                f"  {label:<22} fillable={filled[label]:>5}  "
                f"not fillable={refused[label]:>5}")
        self.stdout.write("")
        self.stdout.write("why the rest were left alone:")
        for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1])[:8]:
            self.stdout.write(f"  {count:>6}  {reason}")

        if not options["apply"]:
            self.stdout.write(self.style.WARNING(
                "\nnothing was written; re-run with --apply to make these changes"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nfilled {len(changes)} phone numbers with real, sourced values"))


def _has_updated_at(model):
    return any(f.name == "updated_at" for f in model._meta.local_fields)
