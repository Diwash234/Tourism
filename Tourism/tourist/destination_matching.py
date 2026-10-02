"""Shared destination matching for the CSV importer commands.

The importers (``import_police``, ``import_hospital``, ``import_hotels_csv``,
``import_budget`` ...) all need to answer the same question: "which catalogue
Destination does this CSV row belong to?". Each one used to answer it with its
own unindexed full-table scan, and each did it once per CSV row, so a single
import took 5-12 minutes and stalled the Render boot past its health check.

This module builds the lookup ONCE per process and answers from memory:

* a case-folded ``name -> Destination`` map, and
* an in-memory coordinate list, narrowed per row by a cheap bounding-box test
  before any distance maths.

Both are built with a single query each, so cost is O(rows * local_candidates)
instead of O(rows * catalogue).
"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .models import Destination

# Degrees of latitude per kilometre. Nepal spans 26.6-30.2 N, so a latitude
# band converted with this constant bounds the search without a proper
# projection (the distance maths below is still real haversine).
KM_PER_DEGREE_LAT = 110.574


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km between two points, or ``None`` if unusable."""
    try:
        lat1, lon1, lat2, lon2 = (float(v) for v in (lat1, lon1, lat2, lon2))
    except (TypeError, ValueError):
        return None
    if any(v != v for v in (lat1, lon1, lat2, lon2)):  # NaN
        return None

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(min(1.0, a)))


class DestinationMatcher:
    """Reusable name + coordinate lookup over the destination catalogue.

    Build one per command run, then call :meth:`match` per CSV row. Nothing here
    touches the database after construction.
    """

    def __init__(self, destinations=None):
        if destinations is None:
            # .only() keeps this to a few columns; the catalogue is 8,700+ rows.
            destinations = Destination.objects.all().only(
                "id", "name", "district", "province", "latitude", "longitude"
            )
        self._by_name: dict[str, Destination] = {}
        self._by_district: dict[str, Destination] = {}
        self._located: list[tuple[float, float, Destination]] = []

        for destination in destinations:
            name = (destination.name or "").strip().casefold()
            if name and name not in self._by_name:
                self._by_name[name] = destination
            district = (destination.district or "").strip().casefold()
            if district and district not in self._by_district:
                self._by_district[district] = destination

            lat = _as_float(destination.latitude)
            lon = _as_float(destination.longitude)
            # Only destinations with real coordinates can be matched by
            # position. The previous code selected rows with
            # `exclude(latitude__isnull=True, longitude__isnull=True)`, which
            # means "NOT (both are null)" and therefore *included* destinations
            # with a null coordinate -- those then raised TypeError inside
            # float() and aborted the whole import with a non-zero exit.
            if lat is not None and lon is not None and not (lat == 0.0 and lon == 0.0):
                self._located.append((lat, lon, destination))

    def __len__(self) -> int:
        return len(self._by_name)

    @property
    def located_count(self) -> int:
        return len(self._located)

    def by_name(self, name: str):
        key = (name or "").strip().casefold()
        return self._by_name.get(key) if key else None

    def by_district(self, district: str):
        key = (district or "").strip().casefold()
        return self._by_district.get(key) if key else None

    def nearest(self, latitude, longitude, max_km: float = 20.0, name: str | None = None):
        """Closest destination to a point, within ``max_km``.

        A coordinate match wins over a name match only when the name is absent
        or the two disagree, so a station whose own destination is recorded
        nearby is preferred.
        """
        lat = _as_float(latitude)
        lon = _as_float(longitude)

        named = self.by_name(name) if name else None

        if lat is None or lon is None:
            return named

        best = None
        best_distance = None
        lat_pad = max(0.001, float(max_km) / KM_PER_DEGREE_LAT)
        for candidate_lat, candidate_lon, destination in self._located:
            # Cheap latitude reject first; Nepal's longitude span is narrow
            # enough that this alone cuts almost every row out.
            if abs(candidate_lat - lat) > lat_pad:
                continue
            distance = haversine_km(lat, lon, candidate_lat, candidate_lon)
            if distance is None or distance > max_km:
                continue
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best = destination

        if named is None:
            return best
        if best is None:
            return named
        # Prefer the coordinate match, but keep an exact-name destination when
        # the coordinate match is far away and the names agree.
        if named.id == best.id:
            return named
        return best

    def match(self, name=None, district=None, latitude=None, longitude=None, max_km: float = 20.0):
        """Best destination for a CSV row: name, then coordinates, then district."""
        found = self.by_name(name) if name else None
        if found is not None:
            return found
        found = self.nearest(latitude, longitude, max_km=max_km, name=name)
        if found is not None:
            return found
        return self.by_district(district) if district else None


def _as_float(value):
    """Parse a coordinate cell, treating blanks and non-numbers as absent."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None
