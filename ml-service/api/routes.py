from fastapi import APIRouter, Query
from pydantic import BaseModel

from model.route.route_engine import shortest_path, nearby_destinations
from services.itinerary_service import build_itinerary

router = APIRouter()


@router.get("/shortest-path")
def get_shortest_path(origin: str = Query(...), destination: str = Query(...)):
    return shortest_path(origin, destination)


@router.get("/nearby")
def get_nearby(name: str = Query(...), max_km: float = Query(150)):
    return {"nearby": nearby_destinations(name, max_km)}


class ItineraryRequest(BaseModel):
    destination_names: list[str]
    num_days: int


@router.post("/itinerary")
def post_itinerary(payload: ItineraryRequest):
    return build_itinerary(payload.destination_names, payload.num_days)