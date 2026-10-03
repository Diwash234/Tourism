"""Recompute each destination's nearest hospital / police station / hotel.

Why this is not the naive scan
------------------------------
The previous implementation compared every destination against every service
with ``min(..., key=haversine_distance)`` and then called haversine a second
time to format the winner -- so it evaluated roughly

    destinations x (hospitals + police + hotels) x 2

haversine calls. With the catalogues at their real size (6,695 destinations x
2,918 services) that is ~39 million calls and measured 4.4 minutes, plus one
``save()`` per destination (6,695 single-row UPDATEs). As a boot step on
Render that competes with live traffic for the whole window, which is exactly
why it was skipped in production and left every destination's
``nearest_*_info`` column empty.

What this does instead
----------------------
* Buckets services into a lat/lon grid once, then for each destination only
  inspects nearby cells, expanding outwards and stopping as soon as the best
  candidate found is provably closer than anything in the not-yet-visited
  rings. That is an exact nearest-neighbour search, not an approximation: the
  stopping rule only fires when every unvisited cell is farther away.
* Batches the writes with ``bulk_update`` and skips rows whose three values
  are already correct, so a re-run against an up-to-date database performs
  zero writes and finishes in a couple of seconds.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.models import Destination, Hospital, Hotel, PoliceStation
from tourist.utils import haversine_distance

# Grid resolution in degrees. 0.25 deg is ~25 km across Nepal: fine enough
# that most destinations resolve in their own cell or the eight around it,
# coarse enough that the grid stays small.
CELL_DEG = 0.25

# Conservative lower bounds on the ground distance covered by one degree of
# latitude / longitude anywhere in Nepal (26.4N-30.4N). Used only for the
# stopping rule, so erring low is always safe: it makes the search keep going
# slightly longer than strictly necessary rather than stopping too early.
KM_PER_DEG_LAT = 110.0
KM_PER_DEG_LON = 95.0

# Beyond this many rings fall back to a full scan, so a destination in a very
# sparse region still gets a correct answer instead of a wrong one.
MAX_RINGS = 40


def _cell(lat, lon):
    return int(lat // CELL_DEG), int(lon // CELL_DEG)


def _build_grid(rows):
    """rows: iterable of (label, lat, lon) -> {cell: [row, ...]}"""
    grid = {}
    for row in rows:
        grid.setdefault(_cell(row[1], row[2]), []).append(row)
    return grid


def _nearest(grid, lat, lon, fallback):
    """Exact nearest row to (lat, lon), searched outward through the grid.

    ``fallback`` is the full list, scanned linearly only if the ring search
    exhausts MAX_RINGS without proving a closest match.
    """
    if not grid:
        return None, None

    cx, cy = _cell(lat, lon)
    best = None
    best_km = None

    for ring in range(MAX_RINGS + 1):
        # At the top of round ``ring`` every cell within Chebyshev distance
        # <= ring-1 has been scanned, so the nearest unscanned cell sits at
        # Chebyshev distance ``ring``. Its closest edge is therefore at least
        # (ring-1) cells away, because our own cell already absorbs one cell
        # of that offset. Expressing that in km has to use the SMALLER
        # per-degree figure (longitude at Nepal's latitude), otherwise the
        # floor is overstated and the search stops while a genuinely closer
        # service is still unscanned.
        if best_km is not None and ring >= 1:
            floor_km = (ring - 1) * CELL_DEG * KM_PER_DEG_LON
            if best_km <= floor_km:
                return best, best_km

        found_any = False
        for dx in range(-ring, ring + 1):
            for dy in range(-ring, ring + 1):
                # Only the perimeter of the square is new this round.
                if ring and abs(dx) != ring and abs(dy) != ring:
                    continue
                bucket = grid.get((cx + dx, cy + dy))
                if not bucket:
                    continue
                found_any = True
                for row in bucket:
                    km = haversine_distance(lat, lon, row[1], row[2])
                    if km is None:
                        continue
                    if best_km is None or km < best_km:
                        best, best_km = row, km

        if not found_any and ring > 0:
            # Ran off the edge of the populated area; nothing left to expand
            # into, so this is provably the global nearest.
            break

    if best is not None:
        return best, best_km

    # Sparse region: correctness beats speed here, and this path is rare.
    best = best_km = None
    for row in fallback:
        km = haversine_distance(lat, lon, row[1], row[2])
        if km is None:
            continue
        if best_km is None or km < best_km:
            best, best_km = row, km
    return best, best_km


def format_distance(km):
    """Human-readable distance that never renders as a bare "0.0 km".

    Much of the imported data is snapped to a district or municipality
    centroid, so a hotel and the destination it belongs to frequently share
    identical coordinates and the true distance is genuinely zero or a few
    metres. Rendering that as "0.0 km" reads as broken/placeholder data
    (and is exactly the sort of placeholder the dataset is meant to be free
    of), so sub-100 m is shown as an inequality instead.
    """
    if km < 0.1:
        return "<0.1 km"
    if km < 10:
        return f"{km:.1f} km"
    return f"{round(km)} km"


class Command(BaseCommand):
    help = (
        "Enrich approved destinations with nearest hospital, police station "
        "and hotel, using a spatial grid and batched writes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Recompute every destination even when its stored values are "
                "already populated. By default only rows with a blank "
                "nearest_* field are considered, so a routine boot after the "
                "first fill is a fast no-op instead of re-deriving 6,695 rows."
            ),
        )

    def handle(self, *args, **options):
        queryset = Destination.objects.filter(
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
        ).exclude(latitude__isnull=True).exclude(longitude__isnull=True)

        if not options.get("force"):
            # Only rows that still have a gap. Re-deriving an already-correct
            # value cannot change it, so skipping them is pure saving; this is
            # what turns a routine boot into a couple of seconds instead of a
            # full recompute of every destination in the catalogue.
            queryset = queryset.filter(
                Q(nearest_hospital_info__isnull=True)
                | Q(nearest_hospital_info="")
                | Q(nearest_police_info__isnull=True)
                | Q(nearest_police_info="")
                | Q(nearest_hotel_info__isnull=True)
                | Q(nearest_hotel_info="")
            )

        destinations = list(
            queryset.only(
                "id",
                "latitude",
                "longitude",
                "nearest_hospital_info",
                "nearest_police_info",
                "nearest_hotel_info",
            )
        )
        self.stdout.write(
            f"Nearby-service enrichment: {len(destinations)} destinations to evaluate"
            + ("" if options.get("force") else " (blank fields only; pass --force to redo all)")
        )
        if not destinations:
            self.stdout.write(
                self.style.SUCCESS("  nothing to do - every public destination already has its nearest services.")
            )
            return

        hospitals = [
            (h.name, float(h.latitude), float(h.longitude))
            for h in Hospital.objects.filter(is_archived=False).exclude(
                latitude__isnull=True
            ).exclude(longitude__isnull=True)
        ]
        police = [
            (p.name, float(p.latitude), float(p.longitude))
            for p in PoliceStation.objects.filter(is_archived=False).exclude(
                latitude__isnull=True
            ).exclude(longitude__isnull=True)
        ]
        hotels = [
            (x.name, float(x.latitude), float(x.longitude))
            for x in Hotel.objects.filter(is_active=True).exclude(
                latitude__isnull=True
            ).exclude(longitude__isnull=True)
        ]

        self.stdout.write(
            f"  services: hospital={len(hospitals)} police={len(police)} hotel={len(hotels)}"
        )

        if not (hospitals or police or hotels):
            self.stdout.write(
                self.style.WARNING(
                    "  no services with coordinates - nothing to enrich. Import the "
                    "service catalogues first (import_hospital, import_police, "
                    "import_hotels_csv) or this command is a no-op."
                )
            )
            return

        grids = {
            "hospital": _build_grid(hospitals),
            "police": _build_grid(police),
            "hotel": _build_grid(hotels),
        }
        fallbacks = {
            "hospital": hospitals,
            "police": police,
            "hotel": hotels,
        }
        fields = {
            "hospital": "nearest_hospital_info",
            "police": "nearest_police_info",
            "hotel": "nearest_hotel_info",
        }

        dirty = []
        filled = {"hospital": 0, "police": 0, "hotel": 0}
        for dest in destinations:
            lat, lon = float(dest.latitude), float(dest.longitude)
            changed = False
            for kind, field in fields.items():
                rows = fallbacks[kind]
                if not rows:
                    continue
                best, km = _nearest(grids[kind], lat, lon, rows)
                if best is None:
                    continue
                value = f"{best[0]} ({format_distance(km)})"
                if getattr(dest, field) != value:
                    setattr(dest, field, value)
                    changed = True
                    filled[kind] += 1
            if changed:
                dirty.append(dest)

        self.stdout.write(
            "  updated: "
            + ", ".join(f"{k}={v}" for k, v in filled.items())
            + f" ({sum(filled.values())} field writes across {len(dirty)} destinations)"
        )

        # Batch the writes; a plain per-row save() is thousands of round trips.
        batch = 500
        for start in range(0, len(dirty), batch):
            Destination.objects.bulk_update(
                dirty[start : start + batch],
                list(fields.values()),
                batch_size=batch,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Nearby-service enrichment complete: {len(dirty)} destinations updated."
            )
        )