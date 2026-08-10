"""
Risk prediction engine.

The risk model uses real location-based features from
risk_features.csv instead of hardcoded placeholder values.

Location matching works in this order:

1. Match by city/place/district name when available.
2. Otherwise find the nearest location using latitude/longitude.
3. If no location information is available, use a fallback
   based on the incident_count supplied by the caller.

Expected CSV:
    ml_service/processed_data/risk_features.csv

Expected model:
    ml_service/model/risk/risk_model.joblib
"""

import os
from math import radians, sin, cos, sqrt, atan2

import joblib
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(__file__)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "risk_model.joblib",
)

FEATURES_CSV_PATH = os.path.join(
    BASE_DIR,
    "..",
    "..",
    "processed_data",
    "risk_features.csv",
)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURE_COLUMNS = [
    "accidents",
    "landslide",
    "avalanche",
    "flood",
    "earthquake_damage",
    "hospital",
    "police",
    "fire_station",
    "emergency_risk",
    "natural_disaster_risk",
    "tourism_risk_index",
]


# ============================================================
# LOAD MODEL
# ============================================================

model = None

if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as exc:
        print(
            f"Warning: Could not load risk model: {exc}"
        )


# ============================================================
# LOAD RISK FEATURES
# ============================================================

_features_df = None

if os.path.exists(FEATURES_CSV_PATH):
    try:
        _features_df = pd.read_csv(
            FEATURES_CSV_PATH
        )

        # Remove accidental whitespace from CSV column names.
        _features_df.columns = (
            _features_df.columns
            .str.strip()
        )

    except Exception as exc:
        print(
            f"Warning: Could not load risk features CSV: {exc}"
        )


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def _haversine_km(
    lat1,
    lon1,
    lat2,
    lon2,
):
    """
    Calculate distance between two GPS coordinates
    in kilometers.
    """

    R = 6371.0

    dlat = radians(
        lat2 - lat1
    )

    dlon = radians(
        lon2 - lon1
    )

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    return (
        2
        * R
        * atan2(
            sqrt(a),
            sqrt(1 - a),
        )
    )


# ============================================================
# LOCATION LOOKUP
# ============================================================

def _lookup_nearest_place(
    latitude=None,
    longitude=None,
    city=None,
):
    """
    Find the best matching location from risk_features.csv.

    Priority:

    1. City/place/district name
    2. Nearest latitude/longitude

    Returns:
        dict or None
    """

    if (
        _features_df is None
        or _features_df.empty
    ):
        return None

    df = _features_df

    # --------------------------------------------------------
    # CITY / PLACE / DISTRICT MATCH
    # --------------------------------------------------------

    if city:
        city = str(city).strip()

        if city:
            text_match = pd.Series(
                False,
                index=df.index,
            )

            # Match "place" if the column exists.
            if "place" in df.columns:
                text_match |= (
                    df["place"]
                    .astype(str)
                    .str.contains(
                        city,
                        case=False,
                        na=False,
                        regex=False,
                    )
                )

            # Match "district" if the column exists.
            if "district" in df.columns:
                text_match |= (
                    df["district"]
                    .astype(str)
                    .str.contains(
                        city,
                        case=False,
                        na=False,
                        regex=False,
                    )
                )

            matches = df[text_match]

            if not matches.empty:
                return matches.iloc[0].to_dict()

    # --------------------------------------------------------
    # LATITUDE / LONGITUDE MATCH
    # --------------------------------------------------------

    if (
        latitude is not None
        and longitude is not None
        and "latitude" in df.columns
        and "longitude" in df.columns
    ):
        try:
            latitude = float(latitude)
            longitude = float(longitude)

            location_df = df.copy()

            location_df["latitude"] = pd.to_numeric(
                location_df["latitude"],
                errors="coerce",
            )

            location_df["longitude"] = pd.to_numeric(
                location_df["longitude"],
                errors="coerce",
            )

            # Remove rows with invalid coordinates.
            location_df = location_df.dropna(
                subset=[
                    "latitude",
                    "longitude",
                ]
            )

            if not location_df.empty:

                location_df["_distance_km"] = (
                    location_df.apply(
                        lambda row:
                        _haversine_km(
                            latitude,
                            longitude,
                            row["latitude"],
                            row["longitude"],
                        ),
                        axis=1,
                    )
                )

                nearest = location_df.loc[
                    location_df["_distance_km"].idxmin()
                ]

                return nearest.to_dict()

        except (
            TypeError,
            ValueError,
        ):
            pass

    return None


# ============================================================
# RISK PREDICTION
# ============================================================

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
    """
    Predict travel risk for a location.

    The model uses the real features found in
    risk_features.csv whenever a location can be matched.

    Parameters such as elevation_m, distance_from_kathmandu_km,
    and season_code are kept for API compatibility with the
    existing application.
    """

    # --------------------------------------------------------
    # MODEL CHECK
    # --------------------------------------------------------

    if model is None:
        return {
            "risk": "unknown",
            "message": "Risk model not trained",
        }

    # --------------------------------------------------------
    # FIND LOCATION
    # --------------------------------------------------------

    place_row = _lookup_nearest_place(
        latitude=latitude,
        longitude=longitude,
        city=city,
    )

    # --------------------------------------------------------
    # USE REAL CSV FEATURES
    # --------------------------------------------------------

    if place_row is not None:

        feature_values = []

        for column in FEATURE_COLUMNS:
            value = place_row.get(
                column,
                0,
            )

            # Safely convert numeric features.
            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
            ):
                value = 0

            feature_values.append(value)

        data = pd.DataFrame(
            [feature_values],
            columns=FEATURE_COLUMNS,
        )

        matched_place = place_row.get(
            "place"
        )

        matched_district = place_row.get(
            "district"
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    else:

        try:
            incident_count = float(
                incident_count or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            incident_count = 0

        data = pd.DataFrame(
            [[
                incident_count,
                0,  # landslide
                0,  # avalanche
                0,  # flood
                0,  # earthquake_damage
                1,  # hospital
                1,  # police
                1,  # fire_station
                0,  # emergency_risk
                0,  # natural_disaster_risk
                0,  # tourism_risk_index
            ]],
            columns=FEATURE_COLUMNS,
        )

        matched_place = None
        matched_district = None

    # --------------------------------------------------------
    # MODEL PREDICTION
    # --------------------------------------------------------

    try:
        result = model.predict(data)[0]

    except Exception as exc:
        return {
            "risk": "unknown",
            "message": (
                f"Risk prediction failed: {exc}"
            ),
            "features_used": (
                data.iloc[0].to_dict()
            ),
        }

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "location": (
            city
            or matched_place
        ),

        "country": country,

        "matched_place": matched_place,

        "matched_district": matched_district,

        "risk_category": result,

        "features_used": (
            data.iloc[0].to_dict()
        ),
    }