from fastapi import APIRouter
from services.hotel_service import nearest_hotels


router=APIRouter()



@router.get("/nearest")
def hotels(
    lat:float,
    lon:float
):

    return {
        "hotels":
        nearest_hotels(
            lat,
            lon
        )
    }