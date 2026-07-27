import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error


DATA_PATH = "processed_data/budget_features.csv"

MODEL_PATH = "model/budget/budget_model.joblib"


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

    # ----------------------------
    # Load dataset
    # ----------------------------

    df = pd.read_csv(DATA_PATH)


    print("Original columns:")
    print(df.columns.tolist())


    # ----------------------------
    # Rename columns
    # ----------------------------

    df = df.rename(columns={

        "Transport Cost (USD)": "transport_cost_usd",

        "Food Cost/Day (USD)": "food_cost_day_usd",

        "Accommodation/Night (USD)": "accommodation_night_usd",

        "Local Taxi/Rick": "local_taxi_rick",

        "Guide/Permit (USD)": "guide_permit_usd"

    })


    # ----------------------------
    # Select cost columns
    # ----------------------------

    cost_columns = [

        "transport_cost_usd",

        "food_cost_day_usd",

        "accommodation_night_usd",

        "local_taxi_rick"

    ]


    # Add guide permit if it exists
    if "guide_permit_usd" in df.columns:

        cost_columns.append(
            "guide_permit_usd"
        )


    # ----------------------------
    # Convert all costs to numbers
    # ----------------------------

    for col in cost_columns:

        df[col] = df[col].apply(
            convert_range
        )


    # Remove rows with invalid values

    df = df.dropna(
        subset=cost_columns
    )


    print(
        "Rows after cleaning:",
        len(df)
    )


    # ----------------------------
    # Create target value
    # ----------------------------

    df["total_daily_cost"] = df[cost_columns].sum(axis=1)


    # ----------------------------
    # Prepare training data
    # ----------------------------

    features = cost_columns


    X = df[features]

    y = df["total_daily_cost"]



    # ----------------------------
    # Split dataset
    # ----------------------------

    X_train, X_test, y_train, y_test = train_test_split(

        X,

        y,

        test_size=0.2,

        random_state=42

    )


    # ----------------------------
    # Train model
    # ----------------------------

    model = RandomForestRegressor(

        n_estimators=200,

        random_state=42

    )


    model.fit(

        X_train,

        y_train

    )


    # ----------------------------
    # Test model
    # ----------------------------

    prediction = model.predict(

        X_test

    )


    mae = mean_absolute_error(

        y_test,

        prediction

    )


    print(
        "MAE:",
        mae
    )


    # ----------------------------
    # Save model
    # ----------------------------

    os.makedirs(

        "model/budget",

        exist_ok=True

    )


    joblib.dump(

        model,

        MODEL_PATH

    )


    joblib.dump(

        features,

        "model/budget/features.joblib"

    )


    print(
        "Budget model trained successfully"
    )

    print(
        "Saved:",
        MODEL_PATH
    )



if __name__ == "__main__":

    main()