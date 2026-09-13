"""
ml_service/api/itinerary.py

FastAPI router for itinerary planning powered by the dataset destinations
and road graph distance calculations.
"""
from typing import List, Optional, Union
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from services.itinerary_service import build_rich_itinerary, build_itinerary

router = APIRouter()


class RichItineraryRequest(BaseModel):
    days: Optional[int] = 3
    travelers: Optional[int] = 1
    budget_npr: Optional[float] = None
    budget_level: Optional[str] = "mid"
    travel_style: Optional[str] = "leisure"
    travel_type: Optional[str] = "solo"
    interests: Optional[List[str]] = None
    start_city: Optional[str] = "Kathmandu"
    destination_names: Optional[List[str]] = None
    num_days: Optional[int] = None


@router.post("/generate")
def generate_rich_itinerary(payload: RichItineraryRequest):
    days = payload.days or payload.num_days or 3
    return build_rich_itinerary(
        days=days,
        travelers=payload.travelers or 1,
        budget_npr=payload.budget_npr,
        budget_level=payload.budget_level or "mid",
        travel_style=payload.travel_style or "leisure",
        travel_type=payload.travel_type or "solo",
        interests=payload.interests or ["culture"],
        start_city=payload.start_city or "Kathmandu",
    )


@router.post("/build")
def generate_build_itinerary(payload: RichItineraryRequest):
    if payload.destination_names and not payload.interests:
        num_days = payload.num_days or payload.days or 3
        return build_itinerary(payload.destination_names, num_days)
    days = payload.days or payload.num_days or 3
    return build_rich_itinerary(
        days=days,
        travelers=payload.travelers or 1,
        budget_npr=payload.budget_npr,
        budget_level=payload.budget_level or "mid",
        travel_style=payload.travel_style or "leisure",
        travel_type=payload.travel_type or "solo",
        interests=payload.interests or ["culture"],
        start_city=payload.start_city or "Kathmandu",
    )


@router.get("/suggest")
def suggest_itinerary(
    days: int = Query(3, ge=1, le=30),
    travelers: int = Query(1, ge=1, le=50),
    budget_npr: Optional[float] = Query(None),
    interests: Optional[str] = Query("culture,nature"),
    start_city: Optional[str] = Query("Kathmandu"),
):
    interest_list = [i.strip() for i in interests.split(",") if i.strip()] if interests else ["culture"]
    return build_rich_itinerary(
        days=days,
        travelers=travelers,
        budget_npr=budget_npr,
        interests=interest_list,
        start_city=start_city,
    )
