from fastapi import APIRouter, Query

from services.emergency_service import (
    get_national_hotlines,
    get_languages,
    get_region,
    get_facilities,
    nearest_facilities,
    FACILITY_FILES,
)

router = APIRouter()


@router.get("/hotlines")
def hotlines():
    return {"hotlines": get_national_hotlines()}


@router.get("/languages")
def languages():
    return {"languages": get_languages()}


@router.get("/categories")
def categories():
    """List the valid category values for /emergency/{category} and
    the ?category= filter on /emergency/nearest."""
    return {"categories": list(FACILITY_FILES.keys())}


@router.get("/region/{city}")
def region(city: str):
    return get_region(city)


@router.get("/nearest")
def nearest(
    lat: float = Query(...),
    lon: float = Query(...),
    category: str | None = Query(None, description="hospital | pharmacy | bank | police_station | embassy | local_government | hotel"),
    limit: int = Query(5),
):
    return {"facilities": nearest_facilities(lat, lon, category, limit)}


@router.get("/{category}")
def by_category(category: str):
    """All entries in one category file, e.g. /emergency/hospital,
    /emergency/pharmacy, /emergency/hotel."""
    facilities = get_facilities(category)
    if not facilities:
        return {"error": f"Unknown category '{category}'. See /emergency/categories."}
    return {"category": category, "facilities": facilities}