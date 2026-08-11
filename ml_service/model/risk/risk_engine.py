"""
Drop-in replacement for ml_service/model/risk/risk_engine.py.

What was wrong: predict_risk() built the model's input DataFrame with
hardcoded placeholder values for 10 of its 11 features (landslide=0,
avalanche=0, flood=0, earthquake_damage=0, hospital=1, police=1,
fire_station=1, emergency_risk=0, natural_disaster_risk=0,
tourism_risk_index=0) -- only `incident_count` (mapped to `accidents`)
came from the actual request. So regardless of where the user actually
was, the model saw nearly the same input every time and the risk
category barely changed. risk_features.csv (which has real per-place
values for every one of those columns) was never read at all.

Fix: look up the nearest place in risk_features.csv to the given
lat/lon (or match by city name if given), and feed the model ITS real
feature values. Falls back to the previous heuristic only if the CSV
is missing or no location info was given at all.
"""
import os
from math import radians, sin, cos, sqrt, atan2

import joblib
import pandas as pd


MODEL_PATH = os.path.join(os.path.dirname(__file__), "risk_model.joblib")
# Adjust this if your actual path differs -- this matches what you showed
# earlier: ml_service/processed_data/risk_features.csv
FEATURES_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "processed_data", "risk_features.csv"
)

FEATURE_COLUMNS = [
    "accidents", "landslide", "avalanche", "flood", "earthquake_damage",
    "hospital", "police", "fire_station", "emergency_risk",
    "natural_disaster_risk", "tourism_risk_index",
]

_loaded = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
if isinstance(_loaded, dict):
    model = _loaded.get("model")
    FEATURE_COLUMNS = _loaded.get("features", FEATURE_COLUMNS)
else:
    model = _loaded
_features_df = pd.read_csv(FEATURES_CSV_PATH) if os.path.exists(FEATURES_CSV_PATH) else None


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _lookup_nearest_place(latitude=None, longitude=None, city=None):
    """Returns the matching risk_features.csv row (as a dict) or None."""
    if _features_df is None or _features_df.empty:
        return None

    df = _features_df
    if city:
        # Prefer an exact-ish city/district/place-name match first.
        match = df[
            df["place"].str.contains(city, case=False, na=False)
            | df["district"].str.contains(city, case=False, na=False)
        ]
        if not match.empty:
            return match.iloc[0].to_dict()

    if latitude is not None and longitude is not None:
        df = df.copy()
        df["_distance_km"] = df.apply(
            lambda row: _haversine_km(latitude, longitude, row["latitude"], row["longitude"]), axis=1
        )
        nearest = df.loc[df["_distance_km"].idxmin()]
        return nearest.to_dict()

    return None


def predict_risk(
    latitude=None,
    longitude=None,
    city=None,
    country=None,
    elevation_m=0,
    distance_from_kathmandu_km=0,
    season_code=0,
    incident_count=0,
):
    if model is None:
        return {"risk": "unknown", "message": "Risk model not trained"}

    place_row = _lookup_nearest_place(latitude, longitude, city)

    if place_row is not None:
        data = pd.DataFrame([[place_row.get(col, 0) for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
        matched_place = place_row.get("place")
        matched_district = place_row.get("district")
    else:
        # No CSV / no location given at all -- fall back to the previous
        # placeholder behaviour rather than crashing, but at least use the
        # real incident_count the caller sent.
        data = pd.DataFrame(
            [[incident_count, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0]], columns=FEATURE_COLUMNS
        )
        matched_place = None
        matched_district = None

    result = model.predict(data)[0]

    return {
        "location": city or matched_place,
        "matched_place": matched_place,
        "matched_district": matched_district,
        "risk_category": result,
        "features_used": data.iloc[0].to_dict(),
    }