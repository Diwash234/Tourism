from fastapi import APIRouter, Query
from pydantic import BaseModel


from model.route.route_engine import (
    shortest_path,
    shortest_city_route,
    find_destination_by_city,
    nearby_destinations
)


from services.itinerary_service import build_itinerary



router = APIRouter()



# ==================================================
# Route between exact tourism places
#
# Example:
# Hotel Shanker -> The Lakeside Retreat - Pokhara
#
# ==================================================

@router.get("/shortest-path")
def get_shortest_path(
    origin: str = Query(...),
    destination: str = Query(...)
):

    return shortest_path(
        origin,
        destination
    )





# ==================================================
# Route between cities
#
# Example:
# Kathmandu -> Pokhara
#
# ==================================================

@router.get("/city-route")
def get_city_route(

    from_city: str = Query(...),

    to_city: str = Query(...)

):

    return shortest_city_route(

        from_city,

        to_city

    )





# ==================================================
# Get places inside a city
#
# Example:
# Kathmandu attractions
#
# ==================================================

@router.get("/city/{city_name}")
def get_city_places(

    city_name:str

):

    places = find_destination_by_city(
        city_name
    )


    return {

        "city":city_name,

        "count":len(places),

        "places":places

    }





# ==================================================
# Nearby places
#
# Example:
# Nearby Hotel Shanker within 20 km
#
# ==================================================

@router.get("/nearby")
def get_nearby(

    name:str = Query(...),

    max_km:float = Query(150)

):

    return {

        "nearby":
        nearby_destinations(
            name,
            max_km
        )

    }





# ==================================================
# Itinerary generator
# ==================================================

class ItineraryRequest(BaseModel):

    destination_names:list[str]

    num_days:int





@router.post("/itinerary")
def post_itinerary(

    payload:ItineraryRequest

):

    return build_itinerary(

        payload.destination_names,

        payload.num_days

    )