import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "processed_data", "risk_features.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model", "risk")
MODEL_PATH = os.path.join(MODEL_DIR, "risk_model.joblib")


def main():
    if not os.path.exists(DATA_PATH):
        alt_path = os.path.join(os.path.dirname(BASE_DIR), "Tourism", "dataset", "risk_features.csv")
        if os.path.exists(alt_path):
            df = pd.read_csv(alt_path)
        else:
            print(f"Risk dataset not found at {DATA_PATH}")
            return
    else:
        df = pd.read_csv(DATA_PATH)

    print("Original columns:")
    print(df.columns)

    features = [
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
        "tourism_risk_index"
    ]

    target = "risk_category"

    available_features = [col for col in features if col in df.columns]

    for col in available_features:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df[available_features] = df[available_features].fillna(0)

    if target not in df.columns:
        # Create risk category target if missing
        df[target] = "Low Risk"
        if "tourism_risk_index" in df.columns:
            df.loc[df["tourism_risk_index"] > 5, target] = "Medium Risk"
            df.loc[df["tourism_risk_index"] > 8, target] = "High Risk"

    df = df.dropna(subset=[target])

    print("Rows after cleaning:", len(df))

    X = df[available_features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    prediction = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, prediction))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "features": available_features}, MODEL_PATH)

    print("Saved:", MODEL_PATH)


if __name__ == "__main__":
    main()
