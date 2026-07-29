from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
from tourist.models import Destination
import time


class Command(BaseCommand):

    help = "Update missing latitude and longitude for destinations"


    def handle(self, *args, **kwargs):

        geolocator = Nominatim(
            user_agent="nepal_tourism_system"
        )

        destinations = Destination.objects.filter(
            latitude__isnull=True
        )

        self.stdout.write(
            f"Found {destinations.count()} places"
        )


        for destination in destinations:

            try:

                search = f"{destination.name}, Nepal"

                location = geolocator.geocode(search)


                if location:

                    destination.latitude = location.latitude
                    destination.longitude = location.longitude
                    destination.save()


                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated {destination.name}: "
                            f"{location.latitude}, {location.longitude}"
                        )
                    )

                else:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Not found: {destination.name}"
                        )
                    )


                # Respect OpenStreetMap rate limit
                time.sleep(1)


            except Exception as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"{destination.name}: {e}"
                    )
                )
