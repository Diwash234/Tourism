import pandas as pd
from math import radians, sin, cos, sqrt, atan2

from django.core.management.base import BaseCommand

from tourist.models import Destination, PoliceStation



def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two GPS points in KM
    """

    R = 6371

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))


    dlat = lat2 - lat1
    dlon = lon2 - lon1


    a = (
        sin(dlat / 2) ** 2
        +
        cos(lat1)
        *
        cos(lat2)
        *
        sin(dlon / 2) ** 2
    )


    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )


    return R * c




def find_destination(
    name,
    latitude,
    longitude
):

    # 1. Match destination name

    if name:

        try:

            return Destination.objects.get(
                name__iexact=name.strip()
            )

        except Destination.DoesNotExist:

            pass



    # 2. Match by coordinates

    if not latitude or not longitude:
        return None



    nearest_destination = None
    nearest_distance = None



    destinations = Destination.objects.exclude(
        latitude__isnull=True,
        longitude__isnull=True
    )



    for destination in destinations:


        distance = calculate_distance(

            latitude,

            longitude,

            destination.latitude,

            destination.longitude

        )



        if (
            nearest_distance is None
            or distance < nearest_distance
        ):

            nearest_distance = distance
            nearest_destination = destination



    # Accept within 20 KM

    if nearest_distance and nearest_distance <= 20:

        return nearest_destination



    return None





class Command(BaseCommand):

    help = "Import police stations from CSV"



    def handle(self, *args, **kwargs):


        df = pd.read_csv(
            "dataset/police_station_cleaned.csv"
        )


        # normalize columns

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )


        imported = 0
        skipped = 0



        for _, row in df.iterrows():


            destination = find_destination(

                row.get("destination"),

                row.get("latitude"),

                row.get("longitude")

            )



            if not destination:


                skipped += 1


                self.stdout.write(

                    self.style.WARNING(

                        f"Destination not found for police station: "
                        f"{row['police_station']}"

                    )

                )

                continue





            PoliceStation.objects.update_or_create(

                destination=destination,

                name=row["police_station"],


                defaults={

                    "address": row.get(
                        "address",
                        ""
                    ),


                    "phone": row.get(
                        "phone",
                        ""
                    ),


                    "latitude": row.get(
                        "latitude"
                    ),


                    "longitude": row.get(
                        "longitude"
                    ),

                }

            )


            imported += 1




        self.stdout.write(

            self.style.SUCCESS(

                f"Imported: {imported}, Skipped: {skipped}"

            )

        )