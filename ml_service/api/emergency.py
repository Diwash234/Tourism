from fastapi import APIRouter, Query

from services.emergency_service import nearest_facilities


# FIX: the router no longer declares its own prefix. app.py mounts it with
# prefix="/emergency", so the previous declaration doubled the path to
# /emergency/emergency/... while the frontend (and Django chatbot) call
# /emergency/... — every request 404'd.
router = APIRouter(
    tags=["Emergency"]
)


# -----------------------------------------
# Available categories
# -----------------------------------------

@router.get("/categories")
def categories():

    return {
        "categories": [
            "hospital",
            "police_station"
        ]
    }



# -----------------------------------------
# Main nearby emergency search
# -----------------------------------------

@router.get("/nearest")
def nearest(
    lat: float = Query(...),
    lon: float = Query(...),
    category: str | None = Query(
        None,
        description="hospital or police_station"
    ),
    limit: int = Query(5)
):

    facilities = nearest_facilities(
        latitude=lat,
        longitude=lon,
        category=category,
        limit=limit
    )


    return {
        "latitude": lat,
        "longitude": lon,
        "category": category,
        "count": len(facilities),
        "facilities": facilities
    }



# -----------------------------------------
# Hospital search
# -----------------------------------------

@router.get("/hospitals")
def hospitals(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(5)
):

    facilities = nearest_facilities(
        latitude=lat,
        longitude=lon,
        category="hospital",
        limit=limit
    )


    return {
        "type": "hospital",
        "facilities": facilities
    }



# -----------------------------------------
# Police search
# -----------------------------------------

@router.get("/police")
def police(
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(5)
):

    facilities = nearest_facilities(
        latitude=lat,
        longitude=lon,
        category="police_station",
        limit=limit
    )


    return {
        "type": "police_station",
        "facilities": facilities
    }



# -----------------------------------------
# Search by category
# -----------------------------------------

@router.get("/{category}")
def by_category(
    category: str,
    lat: float = Query(...),
    lon: float = Query(...),
    limit: int = Query(5)
):

    allowed = [
        "hospital",
        "police_station"
    ]


    if category not in allowed:

        return {
            "error": "Invalid category",
            "available": allowed
        }


    facilities = nearest_facilities(
        latitude=lat,
        longitude=lon,
        category=category,
        limit=limit
    )


    return {
        "category": category,
        "facilities": facilities
    }
