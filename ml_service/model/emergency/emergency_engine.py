import pandas as pd
import math
import os


HOSPITAL_FILE = os.path.join(
    os.path.dirname(__file__),
    "../../data/emergency/hospital_cleaned.csv"
)

POLICE_FILE = os.path.join(
    os.path.dirname(__file__),
    "../../../tourism/dataset/police_station_cleaned.csv"
)


def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = math.radians(float(lat1))
    lat2 = math.radians(float(lat2))

    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c



def clean_coordinates(df):

    # Remove duplicate header rows
    df = df[
        df["latitude"].astype(str).str.lower() != "latitude"
    ]

    df = df[
        df["longitude"].astype(str).str.lower() != "longitude"
    ]

    # Convert coordinates
    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # Remove invalid rows
    df = df.dropna(
        subset=[
            "latitude",
            "longitude"
        ]
    )

    return df



def get_nearest_places(
        latitude,
        longitude,
        limit=5
):

    hospitals = pd.read_csv(
        HOSPITAL_FILE
    )

    police = pd.read_csv(
        POLICE_FILE
    )


    hospitals = clean_coordinates(
        hospitals
    )

    police = clean_coordinates(
        police
    )


    results = []


    # --------------------
    # Hospitals
    # --------------------

    for _, row in hospitals.iterrows():

        distance = haversine(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"]
        )


        results.append({

            "type": "hospital",

            "name": row["hospital_name"],

            "address": row["address"],

            "phone": row["phone"],

            "district": row["district"],

            "province": row["province"],

            "latitude": row["latitude"],

            "longitude": row["longitude"],

            "distance_km": round(distance,2)

        })



    # --------------------
    # Police Stations
    # --------------------

    for _, row in police.iterrows():

        distance = haversine(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"]
        )


        results.append({

            "type": "police",

            "name": row["police_station"],

            "address": row["address"],

            "phone": row["phone"],

            "district": row["district"],

            "province": row["province"],

            "latitude": row["latitude"],

            "longitude": row["longitude"],

            "distance_km": round(distance,2)

        })


    results.sort(
        key=lambda x:x["distance_km"]
    )


    return results[:limit]



if __name__ == "__main__":

    results = get_nearest_places(
        latitude=27.7172,
        longitude=85.3240,
        limit=5
    )


    print(f"Found {len(results)} places")


    for place in results:
        print(place)
