import time
import requests

from django.core.management.base import BaseCommand

from tourist.models import Destination



def get_english_city(latitude, longitude):

    """
    Get English city name using latitude and longitude
    """

    if not latitude or not longitude:
        return ""


    url = "https://nominatim.openstreetmap.org/reverse"


    params = {
        "lat": float(latitude),
        "lon": float(longitude),
        "format": "json",
        "zoom": 10,
        "accept-language": "en"
    }


    headers = {
        "User-Agent": "Tourism-Django-App"
    }


    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )


        data = response.json()


        address = data.get(
            "address",
            {}
        )


        city = (

            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("village")
            or address.get("county")
            or ""

        )


        return city



    except Exception as e:

        print(
            "API Error:",
            e
        )

        return ""





class Command(BaseCommand):

    help = "Update destination city names using coordinates"



    def handle(self, *args, **kwargs):


        destinations = Destination.objects.filter(

            latitude__isnull=False,

            longitude__isnull=False

        )


        total = destinations.count()


        self.stdout.write(

            self.style.SUCCESS(

                f"Found {total} destinations"

            )

        )



        updated = 0
        failed = 0



        for index, destination in enumerate(
            destinations,
            start=1
        ):


            self.stdout.write(

                f"{index}/{total}: {destination.name}"

            )



            changed = False



            # Existing Nepali city

            if destination.city:

                destination.city_nepali = destination.city

                changed = True



            # Get English city

            english_city = get_english_city(

                destination.latitude,

                destination.longitude

            )



            if english_city:

                destination.city_english = english_city

                changed = True

            else:

                failed += 1



            if changed:

                destination.save(

                    update_fields=[

                        "city_nepali",

                        "city_english"

                    ]

                )


                updated += 1



                self.stdout.write(

                    self.style.SUCCESS(

                        f"{destination.city_nepali} -> {destination.city_english}"

                    )

                )

            else:

                self.stdout.write(

                    self.style.WARNING(

                        "No city information"

                    )

                )



            # avoid overloading Nominatim

            time.sleep(0.3)



        self.stdout.write(

            self.style.SUCCESS(

                f"""
Completed

Updated: {updated}
Failed: {failed}
"""

            )

        )