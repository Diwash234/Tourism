from fastapi import APIRouter, Query

from services.hotel_service import nearest_hotels, search_hotels

router = APIRouter()


@router.get("/nearest")
def hotels_nearest(lat: float = Query(...), lon: float = Query(...), limit: int = Query(10)):
    return {"hotels": nearest_hotels(lat, lon, limit)}


@router.get("/search")
def hotels_search(query: str = Query(..., description='e.g. "Pokhara", "Lakeside", or a hotel name'), limit: int = Query(10)):
    """
    New endpoint -- didn't exist before. Lets the frontend search hotels by
    city/area/name text (e.g. "Pokhara", "Lakeside") instead of only by
    exact coordinates.
    """
    return {"query": query, "hotels": search_hotels(query, limit)}