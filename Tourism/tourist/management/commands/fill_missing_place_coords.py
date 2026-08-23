"""Fill missing destination city/coords from other recorded destinations.

Does not invent coordinates. Uses:
  1. another destination with the same name that already has coords
  2. the mean of recorded destinations in the same district
  3. the mean of recorded destinations in the same city
Also computes distance_from_kathmandu_km from stored coordinates.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Avg

from tourist.models import Destination
from tourist.utils import haversine_distance

KTM = (27.7172, 85.3240)


def _in_nepal(lat, lng):
    try:
        latitude, longitude = float(lat), float(lng)
    except (TypeError, ValueError):
        return False
    return 26 <= latitude <= 31 and 80 <= longitude <= 89


class Command(BaseCommand):
    help = "Fill missing destination coordinates from other recorded places."

    def handle(self, *args, **options):
        filled_coords = 0
        filled_city = 0
        filled_distance = 0
        qs = Destination.objects.filter(is_active=True)

        missing = qs.filter(latitude__isnull=True) | qs.filter(longitude__isnull=True)
        for dest in missing.distinct():
            lat = lng = None
            twin = Destination.objects.filter(
                name__iexact=dest.name, latitude__isnull=False, longitude__isnull=False,
            ).exclude(pk=dest.pk).first()
            if twin and _in_nepal(twin.latitude, twin.longitude):
                lat, lng = twin.latitude, twin.longitude
            else:
                tokens = []
                for raw in (dest.district, dest.city, dest.province):
                    for part in str(raw or "").replace(",", "/").split("/"):
                        token = part.strip()
                        if token and token.lower() not in {"nepal", "province"} and token not in tokens:
                            tokens.append(token)
                for token in tokens:
                    agg = Destination.objects.filter(
                        district__iexact=token, latitude__isnull=False, longitude__isnull=False,
                    ).aggregate(lat=Avg("latitude"), lng=Avg("longitude"))
                    if agg["lat"] is None:
                        agg = Destination.objects.filter(
                            city__iexact=token, latitude__isnull=False, longitude__isnull=False,
                        ).aggregate(lat=Avg("latitude"), lng=Avg("longitude"))
                    if agg["lat"] is not None and agg["lng"] is not None:
                        lat, lng = agg["lat"], agg["lng"]
                        break
            if lat is None or lng is None or not _in_nepal(lat, lng):
                continue
            dest.latitude = Decimal(str(round(float(lat), 6)))
            dest.longitude = Decimal(str(round(float(lng), 6)))
            dest.save(update_fields=["latitude", "longitude", "updated_at"])
            filled_coords += 1

        for dest in qs.filter(city__isnull=True) | qs.filter(city=""):
            if dest.district:
                dest.city = dest.district
                dest.save(update_fields=["city", "updated_at"])
                filled_city += 1

        for dest in qs.exclude(latitude__isnull=True).exclude(longitude__isnull=True):
            if dest.distance_from_kathmandu_km:
                continue
            km = haversine_distance(KTM[0], KTM[1], float(dest.latitude), float(dest.longitude))
            if km is None:
                continue
            dest.distance_from_kathmandu_km = Decimal(str(round(km, 2)))
            dest.save(update_fields=["distance_from_kathmandu_km", "updated_at"])
            filled_distance += 1

        remaining = Destination.objects.filter(is_active=True, latitude__isnull=True).count()
        self.stdout.write(self.style.SUCCESS(
            f"Filled coords={filled_coords}, city={filled_city}, ktm_distance={filled_distance}. "
            f"Still missing coords: {remaining}."
        ))
