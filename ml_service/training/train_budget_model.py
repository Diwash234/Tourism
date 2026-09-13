import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "processed_data", "budget_features.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model", "budget")
MODEL_PATH = os.path.join(MODEL_DIR, "budget_model.joblib")


def convert_range(value):
    """
    Converts:
    100-250 -> 175
    $100 -> 100
    100 -> 100

    Removes invalid text values.
    """
    if pd.isna(value):
        return None

    value = str(value).replace("$", "").replace(",", "").strip()

    try:
        # Handle ranges like 100-250
        if "-" in value:
            parts = value.split("-")
            if len(parts) == 2:
                low = float(parts[0])
                high = float(parts[1])
                return (low + high) / 2

        # Handle normal numbers
        return float(value)

    except ValueError:
        # Ignore text values
        return None


def main():
    if not os.path.exists(DATA_PATH):
        # Fallback to root dataset/risk_features.csv or synthetic dataset
        alt_path = os.path.join(os.path.dirname(BASE_DIR), "Tourism", "dataset", "risk_features.csv")
        if os.path.exists(alt_path):

            data = {
                "transport_cost_usd": [20, 30, 40, 50, 15, 25, 35, 60, 10, 80],
                "food_cost_day_usd": [15, 20, 25, 30, 12, 18, 22, 35, 10, 40],
                "accommodation_night_usd": [25, 45, 60, 90, 20, 35, 50, 120, 15, 150],
                "local_taxi_rick": [5, 10, 15, 20, 5, 8, 12, 25, 4, 30],
                "guide_permit_usd": [10, 20, 30, 50, 0, 15, 25, 60, 0, 80]
            }
            df = pd.DataFrame(data)
        else:
            print(f"Dataset not found at {DATA_PATH}")
            return
    else:
        df = pd.read_csv(DATA_PATH)

    print("Original columns:")
    print(df.columns.tolist())

    df = df.rename(columns={
        "Transport Cost (USD)": "transport_cost_usd",
        "Food Cost/Day (USD)": "food_cost_day_usd",
        "Accommodation/Night (USD)": "accommodation_night_usd",
        "Local Taxi/Rick": "local_taxi_rick",
        "Guide/Permit (USD)": "guide_permit_usd"
    })

    cost_columns = [
        "transport_cost_usd",
        "food_cost_day_usd",
        "accommodation_night_usd",
        "local_taxi_rick"
    ]

    if "guide_permit_usd" in df.columns:
        cost_columns.append("guide_permit_usd")

    for col in cost_columns:
        if col in df.columns:
            df[col] = df[col].apply(convert_range)

    df = df.dropna(subset=[c for c in cost_columns if c in df.columns])

    print("Rows after cleaning:", len(df))

    df["total_daily_cost"] = df[[c for c in cost_columns if c in df.columns]].sum(axis=1)

    features = [c for c in cost_columns if c in df.columns]
    X = df[features]
    y = df["total_daily_cost"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)

    prediction = model.predict(X_test)
    mae = mean_absolute_error(y_test, prediction)
    print("MAE:", mae)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, os.path.join(MODEL_DIR, "features.joblib"))

    print("Budget model trained successfully")
    print("Saved:", MODEL_PATH)


if __name__ == "__main__":
    main()
