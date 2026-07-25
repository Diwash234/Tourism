import time
import requests

from django.core.management.base import BaseCommand
from tourist.models import Destination



# Nepal local body English names
MUNICIPALITY_TRANSLATION = {

    "महाकुलुङ गाउँपालिका": "Mahakulung Rural Municipality",
    "खुम्बु पासाङल्हामु गाउँपालिका": "Khumbu Pasang Lhamu Rural Municipality",
    "सोलुदुधकुण्ड नगरपालिका": "Solududhkunda Municipality",
    "माप्य दुधकोशी गाउँपालिका": "Mapya Dudhkoshi Rural Municipality",
    "लिखु पिके गाउँपालिका": "Likhu Pike Rural Municipality",
    "गोकुलगङ्गा गाउँपालिका": "Gokulganga Rural Municipality",

}



def reverse_location(lat, lon):

    try:

        response = requests.get(

            "https://nominatim.openstreetmap.org/reverse",

            params={

                "lat": float(lat),
                "lon": float(lon),
                "format": "json",
                "addressdetails": 1,
                "zoom": 12,
                "accept-language": "ne"

            },

            headers={

                "User-Agent":
                "Tourism-Django-App"

            },

            timeout=10

        )


        data=response.json()


        address=data.get(
            "address",
            {}
        )


        return address



    except Exception as e:

        print(
            "ERROR:",
            e
        )

        return {}





class Command(BaseCommand):

    help="Update Nepal destination city municipality district province"



    def handle(self,*args,**kwargs):


        destinations = Destination.objects.filter(

            latitude__isnull=False,
            longitude__isnull=False

        ).filter(

            city_nepali__isnull=True

        ) | Destination.objects.filter(

            latitude__isnull=False,
            longitude__isnull=False

        ).filter(

            city_english__isnull=True

        )



        total=destinations.count()


        print(
            "Processing:",
            total
        )


        updated=0



        for index,d in enumerate(
            destinations.distinct(),
            start=1
        ):


            print(
                f"{index}/{total}",
                d.name
            )


            address = reverse_location(

                d.latitude,
                d.longitude

            )


            if not address:

                continue



            changed=False



            # -------------------------
            # Municipality / City
            # -------------------------

            municipality = (

                address.get("municipality")
                or
                address.get("city")
                or
                address.get("town")
                or
                address.get("village")
                or ""

            )



            if municipality:


                if not d.city_nepali:

                    d.city_nepali = municipality

                    changed=True



                if not d.city_english:


                    english = MUNICIPALITY_TRANSLATION.get(

                        municipality,

                        municipality

                    )


                    d.city_english = english

                    changed=True




            # -------------------------
            # District
            # -------------------------

            district = (

                address.get("county")
                or
                address.get("state_district")
                or ""

            )


            if district:


                district=district.replace(
                    " जिल्ला",
                    ""
                )


                if d.district != district:

                    d.district=district

                    changed=True





            # -------------------------
            # Province
            # -------------------------

            province = address.get(
                "state",
                ""
            )


            if province:


                province=province.replace(
                    "प्रदेश",
                    "Province"
                )


                if d.province != province:

                    d.province=province

                    changed=True





            # -------------------------
            # Address
            # -------------------------

            if not d.address:


                d.address=", ".join(

                    filter(

                        None,

                        [

                        municipality,
                        district,
                        province,
                        "Nepal"

                        ]

                    )

                )


                changed=True





            # -------------------------
            # Description
            # -------------------------

            if not d.description:


                place = (

                    d.city_english
                    or
                    d.city_nepali
                    or
                    "Nepal"

                )


                d.description=(

                    f"{d.name} is a tourist destination "
                    f"located in {place}, Nepal. "
                    f"This area belongs to {d.district or ''} "
                    f"district in {d.province or ''}. "
                    "Visitors can explore local culture, "
                    "nature, landscapes and tourism activities."

                )


                changed=True





            if changed:


                d.save()

                updated += 1


                print(

                    "UPDATED:",
                    d.city_nepali,
                    "/",
                    d.city_english

                )



            time.sleep(1)



        print("================")
        print("FINISHED")
        print(
            "UPDATED:",
            updated
        )