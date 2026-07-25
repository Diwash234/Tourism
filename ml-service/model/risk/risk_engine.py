import math
import os

import joblib

KATHMANDU_LAT = 27.7172
KATHMANDU_LON = 85.3240
MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.joblib")

_model = None
if os.path.exists(MODEL_PATH):
    try:
        _model = joblib.load(MODEL_PATH)
    except Exception:
        _model = None


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def predict_risk(
    latitude=None,
    longitude=None,
    city=None,
    country=None,
    elevation_m=None,
    distance_from_kathmandu_km=None,
    season_code=0,
    incident_count=0,
):
    if latitude is None or longitude is None:
        latitude = KATHMANDU_LAT
        longitude = KATHMANDU_LON

    if distance_from_kathmandu_km is None:
        distance_from_kathmandu_km = haversine_km(KATHMANDU_LAT, KATHMANDU_LON, latitude, longitude)

    elevation_m = float(elevation_m or 1200)
    season_code = int(season_code or 0)
    incident_count = int(incident_count or max(1, round(distance_from_kathmandu_km / 50)))

    if _model is not None:
        prediction = str(_model.predict([[elevation_m, distance_from_kathmandu_km, season_code, incident_count]])[0]).lower()
        risk_level = prediction
        confidence = 0.81
    else:
        score = max(0.0, min(1.0, 0.25 + (distance_from_kathmandu_km / 350) * 0.5 + (incident_count / 25) * 0.2))
        if score < 0.38:
            risk_level = "low"
        elif score < 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"
        confidence = round(score, 2)

    safety_score = round(1 - confidence, 2) if risk_level in {"low", "medium", "high"} else 0.65
    if risk_level == "low":
        safety_score = 0.78
    elif risk_level == "medium":
        safety_score = 0.62
    else:
        safety_score = 0.42

    return {
        "risk_level": risk_level,
        "safety_score": safety_score,
        "distance_from_kathmandu_km": round(float(distance_from_kathmandu_km), 2),
        "source": "model" if _model is not None else "heuristic",
        "summary": f"{risk_level.title()} risk advisory for {city or 'this destination'}.",
    }