import pandas as pd
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "destinations",
    "nepal_destinations.csv"
)


OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "destinations_clean.csv"
)


CACHE_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "geocode_cache.csv"
)


headers = {
    "User-Agent": "NepalTourismAI/1.0"
}


def get_location_details(lat, lon):

    key = f"{lat},{lon}"

    url = "https://nominatim.openstreetmap.org/reverse"


    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 14,
        "addressdetails": 1
    }


    try:

        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=5
        )


        data = r.json()

        address = data.get(
            "address",
            {}
        )


        return {

            "city":
                address.get("city")
                or address.get("town")
                or address.get("municipality")
                or address.get("village")
                or "",


            "area":
                address.get("suburb")
                or address.get("neighbourhood")
                or address.get("quarter")
                or "",


            "district":
                address.get("county")
                or address.get("state_district")
                or "",


            "province":
                address.get("state")
                or "",


            "display_name":
                data.get("display_name","")

        }


    except Exception as e:

        print(
            "Error:",
            lat,
            lon,
            e
        )

        return {
            "city":"",
            "area":"",
            "district":"",
            "province":"",
            "display_name":""
        }



# Load data

df = pd.read_csv(INPUT_FILE)



# Load previous cache

if os.path.exists(CACHE_FILE):

    cache = pd.read_csv(
        CACHE_FILE
    )

    cache_dict = cache.set_index(
        "key"
    ).to_dict(
        "index"
    )

else:

    cache_dict = {}



results = {}



tasks = []


for _,row in df.iterrows():

    key = f"{row.Latitude},{row.Longitude}"

    if key not in cache_dict:

        tasks.append(
            (
                key,
                row.Latitude,
                row.Longitude
            )
        )



print(
    "New locations:",
    len(tasks)
)



# Faster parallel requests

with ThreadPoolExecutor(
    max_workers=10
) as executor:


    futures = {

        executor.submit(
            get_location_details,
            lat,
            lon
        ): key

        for key,lat,lon in tasks

    }


    for future in as_completed(futures):

        key = futures[future]

        results[key] = future.result()

        print(
            "Completed:",
            key
        )



# update cache

cache_dict.update(
    results
)



cache_df = pd.DataFrame(
    [
        {
            "key":k,
            **v
        }

        for k,v in cache_dict.items()

    ]
)


cache_df.to_csv(
    CACHE_FILE,
    index=False
)



# Add searchable fields

cities = []
areas = []
districts = []
provinces = []
search_text = []



for _,row in df.iterrows():

    key=f"{row.Latitude},{row.Longitude}"


    location = cache_dict.get(
        key,
        {}
    )


    city = (
        row.get("City","")
        if pd.notna(row.get("City",""))
        else ""
    )


    city = city or location.get(
        "city",
        ""
    )


    area = location.get(
        "area",
        ""
    )


    district = location.get(
        "district",
        ""
    )


    province = location.get(
        "province",
        ""
    )


    cities.append(city)
    areas.append(area)
    districts.append(district)
    provinces.append(province)



    # Search keywords
    # Example:
    # "Pokhara Sarangkot Kaski Gandaki Nepal"

    search_text.append(
        " ".join(
            [
                str(row["Name"]),
                city,
                area,
                district,
                province,
                "Nepal"
            ]
        )
        .lower()
    )



df["City"] = cities
df["Area"] = areas
df["District"] = districts
df["Province"] = provinces

df["search_text"] = search_text



df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "Destination cleaning completed"
)