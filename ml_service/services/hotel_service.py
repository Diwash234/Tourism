import pandas as pd
import math


HOTEL_FILE="data/hotel/hotel.csv"


def distance(lat1,lon1,lat2,lon2):

    return math.sqrt(
        (lat1-lat2)**2+
        (lon1-lon2)**2
    )



def nearest_hotels(
    lat,
    lon,
    limit=5
):

    df=pd.read_csv(
        HOTEL_FILE
    )


    results=[]


    for _,row in df.iterrows():

        d=distance(
            lat,
            lon,
            row["Latitude"],
            row["Longitude"]
        )


        results.append({

            "hotel_name":row["Hotel Name"],
            "address":row["Address"],
            "phone":row["Phone"],
            "rating":row["Rating"],
            "price":row["Price Per Night"],
            "booking_url":row["Booking URL"],
            "distance":round(d,2)

        })


    results.sort(
        key=lambda x:x["distance"]
    )


    return results[:limit]