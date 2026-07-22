from fastapi import APIRouter
from pydantic import BaseModel

from model.risk.risk_engine import predict_risk

router = APIRouter()


class RiskRequest(BaseModel):
    elevation_m: float
    distance_from_kathmandu_km: float
    season_code: int = 0
    incident_count: int = 0


@router.post("/predict")
def predict(payload: RiskRequest):
    return predict_risk(
        payload.elevation_m,
        payload.distance_from_kathmandu_km,
        payload.season_code,
        payload.incident_count,
    )