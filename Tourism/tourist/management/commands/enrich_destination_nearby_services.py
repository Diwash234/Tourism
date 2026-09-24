from django.core.management.base import BaseCommand
from tourist.models import Destination, Hospital, PoliceStation, Hotel
from tourist.utils import haversine_distance

class Command(BaseCommand):
    help = "Enrich all approved destinations with nearest hospital, police, and hotel distance info"

    def handle(self, *args, **options):
        approved = Destination.objects.filter(status=Destination.SubmissionStatus.APPROVED).exclude(latitude=None).exclude(longitude=None)
        self.stdout.write(f"Enriching nearby services for {approved.count()} destinations...")

        hospitals = [(h.name, float(h.latitude), float(h.longitude)) for h in Hospital.objects.filter(is_archived=False) if h.latitude and h.longitude]
        police_list = [(p.name, float(p.latitude), float(p.longitude)) for p in PoliceStation.objects.filter(is_archived=False) if p.latitude and p.longitude]
        hotel_list = [(ht.name, float(ht.latitude), float(ht.longitude)) for ht in Hotel.objects.filter(is_active=True) if ht.latitude and ht.longitude]

        count = 0
        for dest in approved:
            d_lat, d_lng = float(dest.latitude), float(dest.longitude)

            if hospitals:
                best_h = min(hospitals, key=lambda x: haversine_distance(d_lat, d_lng, x[1], x[2]) or 9999)
                dist_h = round(haversine_distance(d_lat, d_lng, best_h[1], best_h[2]) or 0, 1)
                dest.nearest_hospital_info = f"{best_h[0]} ({dist_h} km)"

            if police_list:
                best_p = min(police_list, key=lambda x: haversine_distance(d_lat, d_lng, x[1], x[2]) or 9999)
                dist_p = round(haversine_distance(d_lat, d_lng, best_p[1], best_p[2]) or 0, 1)
                dest.nearest_police_info = f"{best_p[0]} ({dist_p} km)"

            if hotel_list:
                best_ht = min(hotel_list, key=lambda x: haversine_distance(d_lat, d_lng, x[1], x[2]) or 9999)
                dist_ht = round(haversine_distance(d_lat, d_lng, best_ht[1], best_ht[2]) or 0, 1)
                dest.nearest_hotel_info = f"{best_ht[0]} ({dist_ht} km)"

            dest.save(update_fields=["nearest_hospital_info", "nearest_police_info", "nearest_hotel_info"])
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully enriched nearby services for {count} destinations."))
