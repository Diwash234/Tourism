"""Import hospital records and attach them to the nearest *relevant* destination.

The previous importer queried every destination for every hospital. On a Render
database with ~13k destinations that became an O(hospitals * destinations)
operation and could keep the web service from binding its port. It also only
matched an exact destination name, so perfectly valid Kathmandu/Lalitpur/etc.
hospital rows were discarded.

This importer builds small in-memory indexes for destination names, places and
coordinate grid cells. It remains idempotent and never invents a destination:
a hospital is attached only when a name/place match exists or its coordinates
are within the configured geographic radius of a real destination.
"""
import re
import unicodedata
from collections import defaultdict
from math import atan2, cos, radians, sin, sqrt

import pandas as pd
from django.core.management.base import BaseCommand

from tourist.models import Destination, Hospital


EARTH_RADIUS_KM = 6371.0
COORDINATE_MATCH_RADIUS_KM = 30.0
GRID_DEGREES = 0.25


def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * atan2(sqrt(a), sqrt(1 - a))


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    value = value.lower().strip()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def grid_key(lat, lon):
    return (int(float(lat) / GRID_DEGREES), int(float(lon) / GRID_DEGREES))


def _text_candidates(value):
    normalized = normalize(value)
    if not normalized:
        return []
    parts = normalized.split()
    # Include the full place and useful suffix-free forms. This handles values
    # such as "Maharajgunj Kathmandu" without pretending the hospital itself is
    # a destination.
    candidates = [normalized]
    if len(parts) > 1:
        candidates.append(" ".join(parts[-2:]))
        candidates.extend(parts)
    return list(dict.fromkeys(candidates))


class DestinationIndex:
    def __init__(self):
        rows = list(
            Destination.objects.values(
                "id", "name", "city", "district", "province", "latitude", "longitude"
            )
        )
        self.by_name = defaultdict(list)
        self.by_place = defaultdict(list)
        self.grid = defaultdict(list)
        self.destinations = {}

        for row in rows:
            lat, lon = row["latitude"], row["longitude"]
            if lat is None or lon is None:
                continue
            self.destinations[row["id"]] = row
            for value in (row["name"],):
                key = normalize(value)
                if key:
                    self.by_name[key].append(row)
            for value in (row["city"], row["district"], row["province"]):
                key = normalize(value)
                if key:
                    self.by_place[key].append(row)
            self.grid[grid_key(lat, lon)].append(row)

    def _nearest(self, lat, lon, candidates):
        best = None
        best_distance = None
        for row in candidates:
            distance = calculate_distance(lat, lon, row["latitude"], row["longitude"])
            if best_distance is None or distance < best_distance:
                best, best_distance = row, distance
        if best is not None and best_distance <= COORDINATE_MATCH_RADIUS_KM:
            return best
        return None

    def find(self, destination_name, district, latitude, longitude):
        for candidate in _text_candidates(destination_name):
            rows = self.by_name.get(candidate) or self.by_place.get(candidate)
            if rows:
                return self._nearest(latitude, longitude, rows) or rows[0]

        for candidate in _text_candidates(district):
            rows = self.by_place.get(candidate)
            if rows:
                return self._nearest(latitude, longitude, rows) or rows[0]

        lat_cell, lon_cell = grid_key(latitude, longitude)
        candidates = []
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                candidates.extend(self.grid.get((lat_cell + dlat, lon_cell + dlon), []))
        return self._nearest(latitude, longitude, candidates)


class Command(BaseCommand):
    help = "Import hospitals from CSV and attach them to verified nearby destinations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default="dataset/hospital_cleaned.csv",
            help="CSV path (raw dataset/hospital.csv also works — headers are normalised)",
        )

    def handle(self, *args, **kwargs):
        path = kwargs.get("csv") or "dataset/hospital_cleaned.csv"
        df = pd.read_csv(path)
        df.columns = (
            df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
        )

        required = {"hospital_name", "latitude", "longitude"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Hospital CSV is missing required columns: {sorted(missing)}")

        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])

        index = DestinationIndex()
        created = 0
        skipped = 0

        for _, row in df.iterrows():
            name = str(row.get("hospital_name") or "").strip()
            if not name:
                continue

            destination = index.find(
                row.get("destination"),
                row.get("district"),
                row["latitude"],
                row["longitude"],
            )

            if destination is None:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Destination not found for hospital: {name} "
                        f"({row.get('destination') or row.get('district') or 'no place'})"
                    )
                )
                continue

            Hospital.objects.update_or_create(
                destination_id=destination["id"],
                name=name,
                defaults={
                    "address": str(row.get("address") or ""),
                    "phone": str(row.get("phone") or ""),
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "district": str(row.get("district") or destination["district"] or ""),
                },
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported: {created}, Skipped: {skipped}, "
                f"total_hospitals={Hospital.objects.count()}"
            )
        )
