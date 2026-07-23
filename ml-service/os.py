import osmnx as ox
import pandas as pd
import geopandas as gpd
import numpy as np
import time


# ==========================================
# OSM SETTINGS (Fix timeout problem)
# ==========================================

ox.settings.timeout = 600

ox.settings.overpass_url = (
    "https://overpass.kumi.systems/api/interpreter"
)


# ==========================================
# Nepal Provinces
# ==========================================

places = [

    "Koshi Province, Nepal",
    "Madhesh Province, Nepal",
    "Bagmati Province, Nepal",
    "Gandaki Province, Nepal",
    "Lumbini Province, Nepal",
    "Karnali Province, Nepal",
    "Sudurpashchim Province, Nepal"

]


# ==========================================
# OSM Tourism Tags
# ==========================================

tags = {

    "tourism":[
        "attraction",
        "viewpoint",
        "museum",
        "camp_site",
        "guest_house",
        "hotel",
        "information"
    ],

    "historic":True,

    "natural":[
        "peak",
        "water",
        "valley",
        "forest"
    ]

}



# ==========================================
# Download OSM Data
# ==========================================

all_data=[]


for place in places:

    print("\nDownloading:",place)

    try:

        data = ox.features_from_place(
            place,
            tags=tags
        )


        data["Province"] = place


        all_data.append(data)


        print(
            "Records:",
            len(data)
        )


        time.sleep(5)


    except Exception as e:

        print(
            "Error:",
            place,
            e
        )



# Combine

if len(all_data)==0:

    raise Exception(
        "No OSM data downloaded"
    )


gdf = pd.concat(
    all_data,
    ignore_index=True
)


print(
"\nTotal OSM records:",
len(gdf)
)



# ==========================================
# Extract Coordinates
# ==========================================


gdf = gpd.GeoDataFrame(
    gdf,
    geometry="geometry",
    crs="EPSG:4326"
)



gdf["Latitude"] = (
    gdf.geometry.centroid.y
)


gdf["Longitude"] = (
    gdf.geometry.centroid.x
)



# ==========================================
# Clean Dataset
# ==========================================


df=pd.DataFrame()


df["Place_Name"] = (
    gdf["name"]
    if "name" in gdf
    else "Unknown"
)


df["Latitude"]=gdf["Latitude"]

df["Longitude"]=gdf["Longitude"]

df["Province"]=gdf["Province"]



if "tourism" in gdf:

    df["Tourism_Type"]=(
        gdf["tourism"]
    )

else:

    df["Tourism_Type"]="Natural/Historic"



# Remove duplicates

df=df.drop_duplicates(
    subset=[
        "Place_Name",
        "Latitude",
        "Longitude"
    ]
)



# ==========================================
# Generate Risk Parameters
# (Replace later with real disaster data)
# ==========================================


np.random.seed(42)


df["Accident_History"] = np.random.randint(
    0,
    30,
    len(df)
)


df["Landslide_Risk"] = np.random.randint(
    0,
    100,
    len(df)
)


df["Flood_Risk"] = np.random.randint(
    0,
    100,
    len(df)
)


df["Earthquake_Risk"] = np.random.randint(
    0,
    100,
    len(df)
)



# ==========================================
# Emergency Availability
# ==========================================


df["Hospital_Distance_km"] = np.random.randint(
    1,
    100,
    len(df)
)


df["Police_Distance_km"] = np.random.randint(
    1,
    80,
    len(df)
)


df["FireStation_Distance_km"] = np.random.randint(
    1,
    100,
    len(df)
)



# ==========================================
# Risk Calculation
# ==========================================


df["Risk_Score"]=(

    df["Accident_History"]*2

    +

    df["Landslide_Risk"]*0.35

    +

    df["Flood_Risk"]*0.25

    +

    df["Earthquake_Risk"]*0.30

    +

    df["Hospital_Distance_km"]*0.20

)



def risk_category(score):

    if score < 40:

        return "LOW"

    elif score < 70:

        return "MEDIUM"

    else:

        return "HIGH"



df["Risk_Category"] = (
    df["Risk_Score"]
    .apply(risk_category)
)



# ==========================================
# Keep 5000+ records
# ==========================================


if len(df) >= 5000:

    final=df.head(5000)

else:

    print(
        "Only",
        len(df),
        "OSM records found"
    )

    final=df



# ==========================================
# Export
# ==========================================


final.to_csv(
    "Nepal_Tourism_Risk_5000.csv",
    index=False
)


print("\nFinished")

print(
"Generated rows:",
len(final)
)

print(
"Saved file: Nepal_Tourism_Risk_5000.csv"
)