"""Batch-resolve not-found owner places from the repo's OWN sourced data.
Run via: python manage.py shell < batch_find_40.py
Creates up to 40 destinations, each with coordinates traceable to an
in-repo source (municipality index, landmarks, cleaned CSVs, hotel table,
OSM services) and a district-hub sanity check (<=60 km)."""
import csv
import difflib
import json
import math
import os
import re
import statistics

import django  # noqa: F401  (shell already set up)
from django.db import connection
from django.utils.text import slugify

from tourist.models import Destination, Hotel, OSMEssentialService

GENERIC = (r"\b(temple|mandir|stupa|lake|pokhari|pond|river|waterfall|jharana|"
           r"jharna|falls|hills|hill|danda|daha|cave|gufa|durbar|palace|park|"
           r"viewpoint|base camp|trek|dham|deurali|bazaar|bazar|himal|monastery|"
           r"gompa|kot|garhi|ghat|dhunga|bunga|kot|chhetra)\b")


def norm(s):
    s = re.sub(GENERIC, "", str(s).lower())
    return re.sub(r"[^a-z0-9]", "", s)


def hav(a, b):
    R = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


ft = json.load(open("../reports/tourist_field_test.json"))
not_found = [(r["place"], dist) for dist, b in ft["districts"].items()
             for r in b["rows"] if r.get("search") == "not-found"]
hubs = {dist: tuple(b["hub_coords"]) for dist, b in ft["districts"].items() if b.get("hub_coords")}
print(f"not-found pool: {len(not_found)}; hubs: {len(hubs)}")

# ---------- source loaders ----------
from tourist.location.search_service import MUNICIPALITY_COORDINATES, NEPAL_LANDMARKS  # noqa: E402

muni = {}
for key, v in MUNICIPALITY_COORDINATES.items():
    muni[norm(key)] = (v["lat"], v["lng"], f"project municipality coordinate index ('{key}')")
land = {}
for key, v in NEPAL_LANDMARKS.items():
    land[norm(key)] = (v["lat"], v["lng"], f"project Nepal landmark index ('{key}')")

csv_rows = []
with open("dataset/destinations_clean.csv", newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        try:
            csv_rows.append((norm(row.get("Name", "")), row.get("Name", ""),
                             float(row["Latitude"]), float(row["Longitude"]),
                             "dataset/destinations_clean.csv", row.get("City", "")))
        except (ValueError, KeyError, TypeError):
            pass
with open("dataset/community_services.csv", newline="", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        try:
            csv_rows.append((norm(row.get("name", "")), row.get("name", ""),
                             float(row["latitude"]), float(row["longitude"]),
                             "dataset/community_services.csv", row.get("district", "")))
        except (ValueError, KeyError, TypeError):
            pass

hotel_rows = [(h.name, h.address or "", float(h.latitude), float(h.longitude))
              for h in Hotel.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True).iterator()]
osm_rows = [(s.name, s.address or "", float(s.latitude), float(s.longitude))
            for s in OSMEssentialService.objects.exclude(is_archived=True)
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)]

existing = [(d.id, d.name, float(d.latitude), float(d.longitude))
            for d in Destination.objects.filter(is_active=True)
            .exclude(latitude__isnull=True).exclude(longitude__isnull=True)]
existing_names = [norm(n) for _, n, _, _ in existing]

taken_names = set()
created = []

for place, district in not_found:
    if len(created) >= 40:
        break
    np_ = norm(place)
    if not np_ or len(np_) < 4 or np_ in taken_names:
        continue
    # already represented by an existing destination?
    if np_ in existing_names:
        continue
    hub = hubs.get(district)
    cand = None  # (lat, lng, source_note, accuracy)

    if np_ in muni:
        lat, lng, src = muni[np_]
        cand = (lat, lng, src, "Town centre (municipality index)", "VERIFIED")
    elif np_ in land:
        lat, lng, src = land[np_]
        cand = (lat, lng, src, "Site-level (landmark index)", "VERIFIED")
    else:
        # CSV exact-normalized matches
        hits = [r for r in csv_rows if r[0] == np_]
        if hits:
            lat = statistics.median(r[2] for r in hits)
            lng = statistics.median(r[3] for r in hits)
            cand = (lat, lng, f"{hits[0][4]} ('{hits[0][1]}', {len(hits)} row(s))",
                    "From project dataset", "APPROXIMATE")
    if cand is None:
        # hotels whose address mentions the place name
        hits = [(la, lo) for nm, addr, la, lo in hotel_rows
                if np_ and np_ in norm(addr)]
        if hits:
            lat = statistics.median(h[0] for h in hits)
            lng = statistics.median(h[1] for h in hits)
            cand = (lat, lng, f"in-repo hotel dataset: median of {len(hits)} hotel coords "
                              f"addressing '{place}'",
                    f"Hotel-cluster median ({len(hits)} hotels)", "APPROXIMATE")
    if cand is None:
        hits = [(la, lo) for nm, addr, la, lo in osm_rows if np_ in norm(addr) or np_ in norm(nm)]
        if hits:
            lat = statistics.median(h[0] for h in hits)
            lng = statistics.median(h[1] for h in hits)
            cand = (lat, lng, f"in-repo OSM essential services: median of {len(hits)} row(s) "
                              f"matching '{place}'",
                    f"OSM-cluster median ({len(hits)} rows)", "APPROXIMATE")
    if cand is None:
        continue

    lat, lng, src, acc, status = cand
    if hub and hav(hub, (lat, lng)) > 60:
        continue  # sanity: candidate too far from the owner's district
    # dedupe: an existing destination with a close name nearby already covers it
    dup = False
    for eid, ename, elat, elng in existing:
        if (norm(ename) == np_ or difflib.SequenceMatcher(None, norm(ename), np_).ratio() >= 0.92) \
                and hav((elat, elng), (lat, lng)) <= 15:
            dup = True
            break
    if dup:
        continue

    base = slugify(place)[:100]
    slug = base
    k = 2
    while Destination.objects.filter(slug=slug).exists():
        slug = f"{base}-{k}"
        k += 1
    d = Destination.objects.create(
        name=place, slug=slug,
        latitude=str(round(lat, 6)), longitude=str(round(lng, 6)),
        district=district, province="", city=place,
        type="attraction", status="approved", is_active=True, provenance="imported",
        description=f"{place}, {district} — resolved {'' if status == 'VERIFIED' else 'approximately '}"
                    f"from project-owned source data. Owner field-list addition 2026-09-21.",
        source=src,
        coordinate_source=src,
        coordinate_accuracy=acc,
        coordinate_status=status,
    )
    existing.append((d.id, d.name, lat, lng))
    existing_names.append(np_)
    taken_names.add(np_)
    created.append((d.id, place, district, round(lat, 4), round(lng, 4), status, src[:70]))

with connection.cursor() as c:
    c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    print("checkpoint:", c.fetchone())

print(f"CREATED {len(created)}:")
for row in created:
    print("  ", row)
