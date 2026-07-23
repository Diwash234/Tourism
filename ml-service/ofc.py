#pip install pandas geopy requests tqdm
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time


# Load your CSV file
# Example columns:
# Source,Destination,District,Province

df = pd.read_csv("nepal_tourist_places.csv")


# OpenStreetMap geocoder
geolocator = Nominatim(
    user_agent="nepal_tourism_distance_calculator"
)


def get_coordinates(place, province="Nepal"):
    """
    Get latitude longitude from OSM
    """

    try:
        query = f"{place}, {province}, Nepal"

        location = geolocator.geocode(
            query,
            timeout=10
        )

        if location:
            return location.latitude, location.longitude

        else:
            return None, None

    except Exception:
        return None, None



def get_osrm_distance(lat1, lon1, lat2, lon2):
    """
    Driving distance from OSM road network
    """

    try:

        url = (
            f"https://router.project-osrm.org/"
            f"route/v1/driving/"
            f"{lon1},{lat1};{lon2},{lat2}"
            f"?overview=false"
        )

        response = requests.get(url)

        data = response.json()

        distance = data["routes"][0]["distance"]

        # meter to kilometer
        return round(distance / 1000,2)


    except Exception:
        return 0



results = []


for index,row in tqdm(df.iterrows(), total=len(df)):

    source = row["Source"]
    destination = row["Destination"]
    province = row["Province"]


    # Source coordinates
    s_lat,s_lon = get_coordinates(
        source,
        province
    )

    time.sleep(1)


    # Destination coordinates
    d_lat,d_lon = get_coordinates(
        destination,
        province
    )

    time.sleep(1)


    if None not in [
        s_lat,
        s_lon,
        d_lat,
        d_lon
    ]:

        distance = get_osrm_distance(
            s_lat,
            s_lon,
            d_lat,
            d_lon
        )

    else:

        distance = 0



    results.append(
        {
        "Source":source,
        "Destination":destination,
        "Province":province,
        "Source_Lat":s_lat,
        "Source_Lon":s_lon,
        "Destination_Lat":d_lat,
        "Destination_Lon":d_lon,
        "Road_Distance_KM":distance
        }
    )



# Save output

output = pd.DataFrame(results)

output.to_csv(
    "nepal_osm_distances.csv",
    index=False
)


print("Completed!")
