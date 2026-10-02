import pandas as pd

from django.core.management.base import BaseCommand

from tourist.models import Destination, BudgetEstimation


def parse_range(value):
    """
    Convert values like:
    '40-120' -> 80
    '20' -> 20
    """

    if pd.isna(value):
        return 0

    value = str(value).strip()

    if "-" in value:
        try:
            low, high = value.split("-")
            return (float(low) + float(high)) / 2
        except ValueError:
            return 0

    try:
        return float(value)

    except ValueError:
        return 0



    # 1. Match destination name

    if isinstance(name, str) and name.strip():

        try:
            return Destination.objects.get(
                name__iexact=name.strip()
            )

        except Destination.DoesNotExist:
            pass



    # 2. Match district

    if isinstance(district, str) and district.strip():

        destination = (
            Destination.objects
            .filter(
                district__iexact=district.strip()
            )
            .first()
        )

        if destination:
            return destination


    return None
def find_destination(name, district, latitude=None, longitude=None):

    # 1. Exact destination name match

    if isinstance(name, str) and name.strip():

        destination = (
            Destination.objects
            .filter(name__iexact=name.strip())
            .first()
        )

        if destination:
            return destination


    # 2. Match by district

    if isinstance(district, str) and district.strip():

        destination = (
            Destination.objects
            .filter(district__iexact=district.strip())
            .first()
        )

        if destination:
            return destination


    # 3. Create new destination with coordinates

    if isinstance(name, str) and name.strip():

        destination, created = Destination.objects.get_or_create(

            name=name.strip(),

            defaults={

                "district": district,

                "latitude": latitude,

                "longitude": longitude,

            }

        )


        if created:
            print(
                f"Created destination: {name}"
            )


        return destination


    return None

class Command(BaseCommand):

    help = "Import budget estimation data"



    def handle(self, *args, **kwargs):


        df = pd.read_csv(
            "dataset/budget_features.csv",
            index_col=False
        )


        # Clean column names

        df.columns = (
            df.columns
            .str.strip()
        )


        df = df.reset_index(drop=True)


        print(df.columns.tolist())
        print(df.head())


        imported = 0
        skipped = 0



        for _, row in df.iterrows():


            destination = find_destination(

                row.get("Destination"),

                row.get("District")

            )



            if not destination:


                skipped += 1


                self.stdout.write(

                    self.style.WARNING(

                        f"Destination not found: "
                        f"{row.get('Destination')}"

                    )

                )

                continue



            transport = parse_range(
                row["Transport Cost (USD)"]
            )


            food = parse_range(
                row["Food Cost/Day (USD)"]
            )


            accommodation = parse_range(
                row["Accommodation/Night (USD)"]
            )


            local_transport = parse_range(
                row["Local Taxi/Rick"]
            )



            daily_budget = (
                food
                +
                accommodation
                +
                local_transport
            )



            BudgetEstimation.objects.update_or_create(

                destination=destination,


                defaults={

                    "district": row.get(
                        "District",
                        ""
                    ),


                    "province": row.get(
                        "Province",
                        ""
                    ),


                    "transport_cost": transport,


                    "food_cost_per_day": food,


                    "accommodation_per_night": accommodation,


                    "local_transport": local_transport,


                    "entry_fee": 0,


                    "estimated_daily_budget": daily_budget,


                    "estimated_trip_budget": (
                        daily_budget * 3
                    ),

                }

            )


            imported += 1



        self.stdout.write(

            self.style.SUCCESS(

                f"Imported: {imported}, Skipped: {skipped}"

            )

        )