from fastapi import APIRouter
from pydantic import BaseModel

from model.risk.risk_engine import predict_risk

router = APIRouter()


class RiskRequest(BaseModel):
    elevation_m: float | None = None
    distance_from_kathmandu_km: float | None = None
    season_code: int = 0
    incident_count: int = 0
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    country: str | None = None


@router.post("/predict")
def predict(payload: RiskRequest):
    return predict_risk(
        latitude=payload.latitude,
        longitude=payload.longitude,
        city=payload.city,
        country=payload.country,
        elevation_m=payload.elevation_m,
        distance_from_kathmandu_km=payload.distance_from_kathmandu_km,
        season_code=payload.season_code,
        incident_count=payload.incident_count,
    )


@router.post("/predict-safety")
def predict_safety(payload: RiskRequest):
    return predict_risk(
        latitude=payload.latitude,
        longitude=payload.longitude,
        city=payload.city,
        country=payload.country,
        elevation_m=payload.elevation_m,
        distance_from_kathmandu_km=payload.distance_from_kathmandu_km,
        season_code=payload.season_code,
        incident_count=payload.incident_count,
    )