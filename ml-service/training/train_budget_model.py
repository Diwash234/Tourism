"""
training/train_budget_model.py

Train travel budget prediction model
"""

import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


DATA_PATH = "processed_data/budget_features.csv"
MODEL_OUT = "model/budget/budget_model.joblib"


def convert_range(value):
    """
    Convert values like:
    8-20 -> 14
    50-150 -> 100
    """
    if isinstance(value, str):
        value = value.strip()

        if "-" in value:
            parts = value.split("-")

            try:
                low = float(parts[0])
                high = float(parts[1])
                return (low + high) / 2
            except:
                return None

        try:
            return float(value)

        except:
            return None

    return value


def main():

    df = pd.read_csv(DATA_PATH)

    # Clean column names
    df.columns = df.columns.str.strip()

    print("Columns found:")
    print(df.columns.tolist())


    # Columns containing cost ranges
    cost_columns = df.columns[4:]


    # Convert ranges to numbers
    for col in cost_columns:
        df[col] = df[col].apply(convert_range)


    # Remove invalid rows
    df = df.dropna()


    # Create total cost target
    df["total_cost_usd"] = df[cost_columns].sum(axis=1)


    # Select features
    X = df[cost_columns]

    # Target
    y = df["total_cost_usd"]


    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )


    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )


    model.fit(X_train, y_train)


    prediction = model.predict(X_test)

    error = mean_absolute_error(
        y_test,
        prediction
    )

    print(f"MAE: {error:.2f} USD")


    os.makedirs(
        "model/budget",
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_OUT
    )


    print("Model saved:")
    print(MODEL_OUT)



if __name__ == "__main__":
    main()
