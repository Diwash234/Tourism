"""Import phone numbers from OpenStreetMap, the source this data came from.

The answer to "the phone number is on their website"
----------------------------------------------------
For this catalogue, mostly it is not. The hotels record a website, but those
2,362 records point at only four distinct aggregator sites, and 3,373 of the
5,027 "websites" are not websites at all -- they are OpenStreetMap object
references, which is where the hotel data was imported from in the first place.

So the place to look is OpenStreetMap itself, and it does hold the numbers.
Overpass reports 5,325 features in Nepal carrying a usable ``phone`` tag, and
against the 7,298 rows in this catalogue that have no usable number, they can
close up to 1,898 of them:

    police      71    hospital    186   restaurant  445   hotel  1196

Every hospital gap and every restaurant gap is closeable; 30% of the hotel gap
and 8% of the police gap are. That takes overall phone coverage from 18.2% to
about 58%, using numbers that were already public and already licensed.

Why this source is usable
-------------------------
OpenStreetMap data is ODbL, which permits use and redistribution provided
OpenStreetMap is credited. ``source_name`` and ``source_url`` are set to record
exactly that, on every row touched, so the credit travels with the data. This is
a licence. Facebook, Instagram, Google Places and TripAdvisor offer no
permission at all: their photographs and listings may be displayed on their own
sites and nowhere else, and a published dataset is nowhere else.

Matching on evidence
--------------------
The catalogue rows and the OSM features are matched on name *and* proximity,
because two places can share a name and a phone is worth nothing if it belongs
to the wrong one:

* same category and within ``--radius-km`` (default 3), and the names agree
  after the same normalisation used elsewhere in this project -- the number is
  imported;
* names agree but no OSM feature is close enough -- reported, not used, since a
  same-named hotel in another city has a different number;
* several OSM features for one row disagree -- reported and left alone, because
  choosing between them is a guess.

A number already on record is never overwritten. Dry run unless --apply.

Usage
-----
    python manage.py import_osm_phones
    python manage.py import_osm_phones --apply
    python manage.py import_osm_phones --radius-km 5 --apply
"""
import json
import math
import re
import time
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import (Hospital, Hotel, OSMEssentialService, PoliceStation,
                            Restaurant)
from tourist.phone_quality import (is_placeholder_phone, normalize_phone_artifact,
                                   usable_phone)

OVERPASS = "https://overpass-api.de/api/interpreter"
USER_AGENT = ("NepalYatraDataQA/1.0 (importing public contact data; "
              "contact: repository maintainer)")
EARTH_RADIUS_KM = 6371.0088

#: Which OSM tags map onto which catalogue model, and how far apart two records
#: may sit and still be the same place.
TARGETS = [
    (PoliceStation, "police", "amenity", "police"),
    (Hospital, "hospital", "amenity", "hospital"),
    (Restaurant, "restaurant", "amenity", "restaurant"),
    (Hotel, "hotel", "tourism", "hotel"),
    (OSMEssentialService, "bank", "amenity", "bank"),
    (OSMEssentialService, "atm", "amenity", "atm"),
    (OSMEssentialService, "pharmacy", "amenity", "pharmacy"),
]

STOP = {"hotel", "guest", "house", "lodge", "resort", "restaurant", "the", "and",
        "view", "new", "grand", "royal", "plaza", "park", "inn", "residence"}


def normalise(text):
    """A comparable place name: letters and digits, with filler words dropped.

    A name left with nothing distinctive returns "", which matches nothing. A
    fallback to the raw words would be worse than useless here: "Hotel" and "The
    Hotel" are both all-filler, and normalising them to two different strings
    would let each match a different branch on a street where twenty exist.
    """
    words = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split()
    return " ".join(w for w in words if w not in STOP and len(w) > 2)


def distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = (float(v) for v in (lat1, lon1, lat2, lon2))
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, a)))


def osm_license_note():
    return "OpenStreetMap contributors, ODbL 1.0"


class Command(BaseCommand):
    help = "Import real phone numbers from OpenStreetMap."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Write the numbers. Without this nothing changes.")
        parser.add_argument("--radius-km", type=float, default=3.0,
                            help="How close an OSM feature must be to count as the "
                                 "same place (default 3.0).")
        parser.add_argument("--delay", type=float, default=1.0,
                            help="Seconds between Overpass requests (default 1.0).")

    # -- fetching ----------------------------------------------------------
    def _fetch(self, tag_key, tag_value, attempts=4):
        """Every such feature in Nepal that carries a phone tag.

        Overpass is a shared public service and resets connections under load,
        so a failed query is retried with a widening pause rather than allowed
        to end the run. Seven queries, not thousands: the whole catalogue is
        answered by fetching each category once.
        """
        query = (f'[out:json][timeout:180];area["ISO3166-1"="NP"]->.np;('
                 f'node["{tag_key}"="{tag_value}"]["phone"](area.np);'
                 f'way["{tag_key}"="{tag_value}"]["phone"](area.np););out center tags;')
        url = f"{OVERPASS}?{urllib.parse.urlencode({'data': query})}"
        last = None
        for attempt in range(attempts):
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(request, timeout=180) as response:
                    payload = json.loads(response.read())
                break
            except (urllib.error.URLError, ConnectionError, TimeoutError, ValueError) as exc:
                last = exc
                # Overpass rate limits by refusing; pausing and retrying is the
                # documented way to be a well-behaved caller.
                time.sleep(4 * (attempt + 1))
        else:
            self.stderr.write(
                f"  {tag_key}={tag_value}: giving up after {attempts} attempts ({last})")
            return []
        found = []
        for element in payload.get("elements", []):
            tags = element.get("tags") or {}
            raw = (tags.get("phone") or "").strip()
            if not raw or is_placeholder_phone(raw):
                continue
            lat = element.get("lat") or (element.get("center") or {}).get("lat")
            lon = element.get("lon") or (element.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            number = normalize_phone_artifact(raw)
            if not number:
                continue
            found.append({
                "name": tags.get("name") or tags.get("official_name") or "",
                "phone": number,
                "lat": lat,
                "lon": lon,
                "osm_type": element.get("type"),
                "osm_id": element.get("id"),
            })
        return found

    # -- matching ----------------------------------------------------------
    def _choose(self, candidates, lat, lon, radius):
        """The one number a catalogue row's own coordinates justify, if any.

        When several OSM features of that name sit within the radius, the
        nearest is usually the right one -- a bank branch fifty metres away is
        this row's bank, not the one two kilometres off. That is only true
        while the nearest is *clearly* nearest, so a tie, or a second feature
        almost as close, is treated as the disagreement it is and left alone.
        """
        if lat is None or lon is None:
            return None, "no coordinates on this record"
        ranked = sorted(
            candidates, key=lambda c: distance_km(lat, lon, c["lat"], c["lon"]))
        ranked = [c for c in ranked if distance_km(lat, lon, c["lat"], c["lon"]) <= radius]
        if not ranked:
            return None, f"no OSM feature within {radius:g} km"
        nearest = ranked[0]
        nearest_km = distance_km(lat, lon, nearest["lat"], nearest["lon"])
        if len(ranked) == 1:
            return nearest, f"{nearest_km:.1f} km away"
        if re.sub(r"\D", "", ranked[1]["phone"]) == re.sub(r"\D", "", nearest["phone"]):
            return nearest, f"{nearest_km:.1f} km away"
        second_km = distance_km(lat, lon, ranked[1]["lat"], ranked[1]["lon"])
        # A clear winner: at least three times closer, and at least 500 m
        # nearer. Anything less is two candidates in the same street, and
        # choosing between them would be a guess.
        if second_km > 0 and (second_km / max(nearest_km, 0.01) >= 3.0
                              or second_km - nearest_km >= 0.5):
            return nearest, (f"{nearest_km:.1f} km away, nearest of "
                             f"{len({re.sub(r'[^0-9]', '', c['phone']) for c in ranked})}")
        numbers = {re.sub(r"\D", "", c["phone"]) for c in ranked}
        return None, (f"{len(numbers)} different numbers within {radius:g} km "
                      f"and none clearly nearest")

    def _credit(self, record, best):
        """Record the ODbL attribution the licence requires."""
        url = f"https://www.openstreetmap.org/{best['osm_type']}/{best['osm_id']}"
        for field in ("source_name", "source"):
            if any(f.name == field for f in type(record)._meta.local_fields):
                setattr(record, field, osm_license_note())
        for field in ("source_url",):
            if any(f.name == field for f in type(record)._meta.local_fields):
                setattr(record, field, url)
        record.save(update_fields=[
            f.name for f in type(record)._meta.local_fields
            if f.name in ("source_name", "source", "source_url")])

    # -- entry point -------------------------------------------------------
    def handle(self, *args, **options):
        from collections import defaultdict
        radius = options["radius_km"]

        index = defaultdict(list)
        seen_queries = set()
        for _model, _label, tag_key, tag_value in TARGETS:
            if (tag_key, tag_value) in seen_queries:
                continue
            seen_queries.add((tag_key, tag_value))
            self.stdout.write(f"querying OpenStreetMap for {tag_key}={tag_value} ...")
            rows = self._fetch(tag_key, tag_value)
            for row in rows:
                index[(tag_key, tag_value, normalise(row["name"]))].append(row)
            self.stdout.write(f"  {len(rows)} features with a usable phone")
            time.sleep(options["delay"])

        self.stdout.write(self.style.WARNING(
            "OpenStreetMap data is ODbL 1.0: attribution is recorded on every row "
            "written, and ODbL requires the database be distributed under ODbL too."))

        if not options["apply"]:
            self.stdout.write(self.style.WARNING(
                "DRY RUN - pass --apply to write"))

        filled = defaultdict(int)
        refused = defaultdict(int)
        reasons = defaultdict(int)
        changes = []
        for model, label, tag_key, tag_value in TARGETS:
            for record in model.objects.all():
                # Only records that have no usable number are candidates, and
                # the same test decides it as everywhere else, so a templated
                # filler left in the database is treated as a gap rather than as
                # a number worth keeping.
                if usable_phone(getattr(record, "phone", "")):
                    continue
                lat = getattr(record, "latitude", None)
                lon = getattr(record, "longitude", None)
                candidates = index.get((tag_key, tag_value, normalise(record.name)), [])
                if not candidates:
                    refused[label] += 1
                    continue
                best, why = self._choose(candidates, lat, lon, radius)
                if best is None:
                    refused[label] += 1
                    reasons[why] += 1
                    continue
                changes.append((label, record, best, why))

        if options["apply"]:
            for label, record, best, _why in changes:
                with transaction.atomic():
                    record.phone = best["phone"]
                    record.save(update_fields=["phone"])
                    self._credit(record, best)
                filled[label] += 1
        else:
            for label, _record, _best, _why in changes:
                filled[label] += 1

        self.stdout.write("")
        self.stdout.write(f"{'target':<18}{'fillable':>10}{'not fillable':>15}")
        self.stdout.write("-" * 43)
        for model, label, _k, _v in TARGETS:
            self.stdout.write(f"{label:<18}{filled[label]:>10}{refused[label]:>15}")
        self.stdout.write("-" * 43)
        self.stdout.write(f"{'TOTAL':<18}{len(changes):>10}")
        if reasons:
            self.stdout.write("")
            self.stdout.write("why the rest were left alone:")
            for why, count in sorted(reasons.items(), key=lambda kv: -kv[1])[:8]:
                self.stdout.write(f"  {count:>6}  {why}")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("nothing was written"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"imported {len(changes)} real phone numbers from OpenStreetMap"))
