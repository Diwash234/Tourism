"""
services/emergency_service.py

Emergency nearby places service.
Loads hospital and police CSV datasets
and finds nearest facilities using GPS.
"""

import os
import pandas as pd

from math import radians, sin, cos, sqrt, atan2

from pathlib import Path

# --------------------------------------------------



BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
    / "Tourism"
    / "dataset"
)



HOSPITAL_FILE = BASE_DIR / "hospital_cleaned.csv"



POLICE_FILE = BASE_DIR / "police_station_cleaned.csv"



_cache = {}



# --------------------------------------------------
# Distance calculation
# --------------------------------------------------

def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):

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



# --------------------------------------------------
# CSV Loader
# --------------------------------------------------

def load_csv(
    name,
    path
):

    if name in _cache:
        return _cache[name]


    if not os.path.exists(path):

        print(
            "Missing dataset:",
            path
        )

        return []


    df = pd.read_csv(path)


    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )


    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )


    df = df.dropna(
        subset=[
            "latitude",
            "longitude"
        ]
    )


    data = df.to_dict(
        orient="records"
    )


    _cache[name] = data


    return data



# --------------------------------------------------
# Get datasets
# --------------------------------------------------

def get_hospitals():

    return load_csv(
        "hospital",
        HOSPITAL_FILE
    )



def get_police_stations():

    return load_csv(
        "police",
        POLICE_FILE
    )



# --------------------------------------------------
# Find nearest facilities
# --------------------------------------------------

def nearest_facilities(
    latitude,
    longitude,
    category=None,
    limit=5
):

    results = []


    facilities = {

        "hospital":
            get_hospitals(),

        "police_station":
            get_police_stations()

    }



    selected = facilities


    if category:

        selected = {
            category:
            facilities.get(category, [])
        }



    for facility_type, places in selected.items():

        for place in places:


            distance = haversine_km(

                latitude,
                longitude,

                place["latitude"],
                place["longitude"]

            )



            if facility_type == "hospital":

                name = place.get(
                    "hospital_name",
                    "Unknown Hospital"
                )


            else:

                name = place.get(
                    "police_station",
                    "Unknown Police Station"
                )



            results.append({

                "type": facility_type,

                "name": name,

                "phone": place.get(
                    "phone",
                    ""
                ),

                "address": place.get(
                    "address",
                    ""
                ),

                "district": place.get(
                    "district",
                    ""
                ),

                "province": place.get(
                    "province",
                    ""
                ),

                "latitude": place["latitude"],

                "longitude": place["longitude"],

                "distance_km": round(
                    distance,
                    2
                )

            })



    results.sort(
        key=lambda x:
        x["distance_km"]
    )


    return results[:limit]



# --------------------------------------------------
# Emergency contacts
# --------------------------------------------------

def get_nearest_emergency_contacts(
    latitude,
    longitude
):


    hospitals = nearest_facilities(
        latitude,
        longitude,
        category="hospital",
        limit=3
    )


    police = nearest_facilities(
        latitude,
        longitude,
        category="police_station",
        limit=3
    )


    return {

        "hospitals": hospitals,

        "police_stations": police

    }
