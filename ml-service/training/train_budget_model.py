"""
training/train_budget_model.py

Trains a regression model that predicts total trip cost (USD) from:
    num_destinations, num_days, avg_daily_cost_usd, travel_style_code

Expects processed_data/budget_features.csv. Falls back to synthesizing
a small training set from trip_expenses.csv-style logic if it's missing,
so the pipeline runs end to end before your real expense data is ready.

Run:
    python training/train_budget_model.py
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib

PROCESSED_PATH = "processed_data/budget_features.csv"
MODEL_OUT = "model/budget/budget_model.joblib"

STYLE_MAP = {"budget": 0, "mid_range": 1, "luxury": 2}


def synthesize_training_data(n=300, seed=42):
    rng = np.random.default_rng(seed)
    num_destinations = rng.integers(1, 8, size=n)
    num_days = num_destinations * rng.integers(1, 3, size=n)
    avg_daily_cost = rng.uniform(10, 80, size=n)
    travel_style_code = rng.integers(0, 3, size=n)

    style_multiplier = np.array([0.8, 1.0, 1.8])[travel_style_code]
    total_cost = num_days * avg_daily_cost * style_multiplier + rng.normal(0, 15, size=n)
    total_cost = np.clip(total_cost, 20, None)

    df = pd.DataFrame({
        "num_destinations": num_destinations,
        "num_days": num_days,
        "avg_daily_cost_usd": avg_daily_cost,
        "travel_style_code": travel_style_code,
        "total_cost_usd": total_cost,
    })
    os.makedirs("processed_data", exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    return df


def main():
    if os.path.exists(PROCESSED_PATH):
        df = pd.read_csv(PROCESSED_PATH)
    else:
        print(f"{PROCESSED_PATH} not found - synthesizing training data")
        df = synthesize_training_data()

    X = df[["num_destinations", "num_days", "avg_daily_cost_usd", "travel_style_code"]]
    y = df["total_cost_usd"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    reg = RandomForestRegressor(n_estimators=200, random_state=42)
    reg.fit(X_train, y_train)

    preds = reg.predict(X_test)
    print(f"MAE: {mean_absolute_error(y_test, preds):.2f} USD")

    os.makedirs("model/budget", exist_ok=True)
    joblib.dump(reg, MODEL_OUT)
    print(f"Saved budget model to {MODEL_OUT}")


if __name__ == "__main__":
    main()