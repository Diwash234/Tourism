from fastapi import APIRouter, Query
from pydantic import BaseModel


from model.route.route_engine import (
    shortest_path,
    shortest_city_route,
    find_destination_by_city,
    nearby_destinations,
    best_route,          # <-- new, see route_engine_addition.py
)


from services.itinerary_service import build_itinerary



router = APIRouter()


@router.get("/shortest-path")
def get_shortest_path(origin: str = Query(...), destination: str = Query(...)):
    return shortest_path(origin, destination)


@router.get("/city-route")
def get_city_route(from_city: str = Query(...), to_city: str = Query(...)):
    return shortest_city_route(from_city, to_city)


@router.get("/city/{city_name}")
def get_city_places(city_name: str):
    places = find_destination_by_city(city_name)
    return {"city": city_name, "count": len(places), "places": places}


@router.get("/nearby")
def get_nearby(name: str = Query(...), max_km: float = Query(150)):
    return {"nearby": nearby_destinations(name, max_km)}


class ItineraryRequest(BaseModel):
    destination_names: list[str]
    num_days: int


@router.post("/itinerary")
def post_itinerary(payload: ItineraryRequest):
    return build_itinerary(payload.destination_names, payload.num_days)


# ==================================================
# NEW: route between raw coordinates (live GPS -> a destination), used by
# Django's NavigationRouteView / Navigation.jsx. This was missing entirely
# -- Django was calling POST /routes/best-route and always getting a 404.
# ==================================================
class BestRouteRequest(BaseModel):
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float
    # "fastest" (default), "safest", "trekking", or "cheapest" -- see
    # route_engine_route_types.py for what each actually does and the
    # honest caveat on "cheapest" (no real per-route cost data exists yet).
    route_type: str = "fastest"


@router.post("/best-route")
def post_best_route(payload: BestRouteRequest):
    return best_route(
        payload.start_latitude,
        payload.start_longitude,
        payload.end_latitude,
        payload.end_longitude,
        payload.route_type,
    )