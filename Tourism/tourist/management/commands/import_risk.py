import pandas as pd

from math import radians, sin, cos, sqrt, atan2

from django.core.management.base import BaseCommand

from tourist.models import Destination, RiskAnalysis



def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates in KM
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





def find_destination(name, latitude, longitude, destinations):

    """
    Find destination by:

    1. Exact name
    2. Nearest coordinate match
    """


    # Match by name first

    if isinstance(name, str) and name.strip():

        destination = Destination.objects.filter(
            name__iexact=name.strip()
        ).first()


        if destination:
            return destination



    # Match by coordinates

    if not latitude or not longitude:
        return None



    nearest_destination = None
    nearest_distance = None



    for destination in destinations:

        try:

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


        except Exception:

            continue



    # Allow 20 KM difference

    if (
        nearest_destination
        and nearest_distance <= 20
    ):

        return nearest_destination



    return None






class Command(BaseCommand):

    help = "Import tourism risk analysis data"



    def handle(self, *args, **kwargs):


        file_path = "dataset/tourism_risk_cleaned.csv"



        df = pd.read_csv(file_path)



        # Clean column names

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
        )



        self.stdout.write(
            f"CSV Columns: {df.columns.tolist()}"
        )



        imported = 0
        skipped = 0



        # LOAD DESTINATIONS ONLY ONCE

        destinations = list(

            Destination.objects.exclude(

                latitude__isnull=True,
                longitude__isnull=True

            )

        )


        self.stdout.write(
            f"Loaded {len(destinations)} destinations"
        )



        # Faster than iterrows()

        rows = df.to_dict("records")



        for row in rows:


            destination = find_destination(

                row.get("place"),

                row.get("latitude"),

                row.get("longitude"),

                destinations

            )



            if not destination:


                skipped += 1


                self.stdout.write(

                    self.style.WARNING(

                        f"Destination not found: "
                        f"{row.get('place')}"

                    )

                )


                continue




            RiskAnalysis.objects.update_or_create(

                destination=destination,


                defaults={


                    "accidents": row.get(
                        "accidents",
                        0
                    ),


                    "landslide": row.get(
                        "landslide",
                        0
                    ),


                    "avalanche": row.get(
                        "avalanche",
                        0
                    ),


                    "flood": row.get(
                        "flood",
                        0
                    ),


                    "earthquake_damage": row.get(
                        "earthquake_damage",
                        0
                    ),


                    "hospital_count": row.get(
                        "hospital",
                        0
                    ),


                    "police_count": row.get(
                        "police",
                        0
                    ),


                    "fire_station_count": row.get(
                        "fire_station",
                        0
                    ),


                    "emergency_risk": row.get(
                        "emergency_risk",
                        0
                    ),


                    "natural_disaster_risk": row.get(
                        "natural_disaster_risk",
                        0
                    ),


                    "tourism_risk_index": row.get(
                        "tourism_risk_index",
                        0
                    ),


                    "risk_category": row.get(
                        "risk_category",
                        "Unknown"
                    ),


                }

            )



            imported += 1



            self.stdout.write(

                self.style.SUCCESS(

                    f"Imported risk data: {destination.name}"

                )

            )




        self.stdout.write(

            self.style.SUCCESS(

                f"""
Completed

Imported: {imported}
Skipped: {skipped}
"""

            )

        )