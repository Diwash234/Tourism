import os
import pandas as pd


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)


INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "budget",
    "travel_cost_cleaned.csv"
)


OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "budget_features.csv"
)


os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


df = pd.read_csv(INPUT_FILE)


df = df.fillna(
    {
        "source":"",
        "destination":"",
        "district":"",
        "province":"",
        "transport_cost_usd":0,
        "food_cost_day_usd":0,
        "accommodation_night_usd":0,
        "local_taxi_rick":0,
        "data_quality_score":0
    }
)


# Create total daily estimated cost

df["estimated_daily_cost"] = (
    df["food_cost_day_usd"]
    +
    df["accommodation_night_usd"]
    +
    df["local_taxi_rick"]
)


# Create 3 day and 7 day trip cost

df["trip_cost_3_days"] = (
    df["transport_cost_usd"]
    +
    df["estimated_daily_cost"] * 3
)


df["trip_cost_7_days"] = (
    df["transport_cost_usd"]
    +
    df["estimated_daily_cost"] * 7
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("Budget preprocessing completed")
print(df.head())

# python training/preprocess/clean_budget.py
# python training/train_budget_model.py
# ml-service/test_budget.py
