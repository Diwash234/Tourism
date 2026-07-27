"""
training/train_risk_model.py

Trains a simple risk classifier (low/medium/high) from destination features.
Expects processed_data/risk_features.csv with columns:
    elevation_m, distance_from_kathmandu_km, season_code, incident_count, risk_level

If that processed file doesn't exist yet, this script falls back to building
one from data/destinations/nepal_destinations_sample.csv so you have
something runnable end to end before your real incidents.csv is ready.

Run:
    python training/train_risk_model.py
"""
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

RAW_DESTINATIONS = "data/destinations/nepal_destination_sample.csv"
PROCESSED_PATH = "processed_data/risk_features.csv"
MODEL_OUT = "model/risk/risk_model.joblib"

KATHMANDU = (27.7172, 85.3240)


def haversine_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def build_processed_from_raw():
    df = pd.read_csv(RAW_DESTINATIONS)
    df["distance_from_kathmandu_km"] = df.apply(
        lambda r: haversine_km(*KATHMANDU, r["lat"], r["lon"]), axis=1
    )
    season_map = {"all_year": 0, "oct_to_apr": 1, "oct_to_mar": 2, "mar_may_sep_nov": 3, "may_oct": 4}
    df["season_code"] = df["best_season"].map(season_map).fillna(0)
    # No real incident history yet - approximate with elevation as a proxy
    # so the pipeline is runnable; replace with real data/risk/incidents.csv
    # counts once you have them.
    df["incident_count"] = (df["elevation_m"] / 1000).round().astype(int)
    df["risk_level"] = df["risk_level"]
    os.makedirs("processed_data", exist_ok=True)
    out = df[["elevation_m", "distance_from_kathmandu_km", "season_code", "incident_count", "risk_level"]]
    out.to_csv(PROCESSED_PATH, index=False)
    return out


def main():
    if os.path.exists(PROCESSED_PATH):
        df = pd.read_csv(PROCESSED_PATH)
    else:
        print(f"{PROCESSED_PATH} not found - building it from {RAW_DESTINATIONS}")
        df = build_processed_from_raw()

    X = df[["elevation_m", "distance_from_kathmandu_km", "season_code", "incident_count"]]
    y = df["risk_level"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y if y.nunique() > 1 else None
    )

    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)

    if len(X_test) > 0:
        preds = clf.predict(X_test)
        print(classification_report(y_test, preds, zero_division=0))

    os.makedirs("model/risk", exist_ok=True)
    joblib.dump(clf, MODEL_OUT)
    print(f"Saved risk model to {MODEL_OUT}")


if __name__ == "__main__":
    main()