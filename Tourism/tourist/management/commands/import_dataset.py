import requests
import time

from django.core.management.base import BaseCommand

from tourist.models import Destination



def get_city_from_coordinates(latitude, longitude):

    if not latitude or not longitude:
        return "", ""


    url = "https://nominatim.openstreetmap.org/reverse"


    params = {
        "lat": latitude,
        "lon": longitude,
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
            timeout=5
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


        return city, city



    except Exception as e:

        print(
            "Error:",
            e
        )

        return "", ""





class Command(BaseCommand):

    help = "Update destination city from latitude longitude"


    def handle(self,*args,**options):


        destinations = Destination.objects.filter(
            city_english=""
        )


        total = destinations.count()


        self.stdout.write(
            f"Total remaining: {total}"
        )


        updated = 0



        for index, destination in enumerate(
            destinations,
            start=1
        ):


            print(
                f"{index}/{total}: {destination.latitude},{destination.longitude}"
            )



            city_nepali, city_english = get_city_from_coordinates(

                destination.latitude,

                destination.longitude

            )



            if city_english:


                destination.city_nepali = city_nepali

                destination.city_english = city_english


                destination.save(
                    update_fields=[
                        "city_nepali",
                        "city_english"
                    ]
                )


                updated += 1


                self.stdout.write(

                    self.style.SUCCESS(

                        f"Updated: {city_english}"

                    )

                )



            else:

                self.stdout.write(

                    self.style.WARNING(

                        "City not found"

                    )

                )



            # Only small delay for Nominatim

            time.sleep(0.2)




        self.stdout.write(

            self.style.SUCCESS(

                f"""
Finished

Updated: {updated}
"""

            )

        )