"""
training/clean_risk.py

Clean risk dataset before training
"""

import os
import pandas as pd


INPUT_FILE = "data/risk/risk_data.csv"

OUTPUT_FILE = "processed_data/risk_features.csv"


def main():

    print("Loading risk data...")

    df = pd.read_csv(INPUT_FILE)


    # remove spaces from column names

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )


    print("Columns:")
    print(df.columns.tolist())


    # Fill missing values

    numeric_columns = [
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
        "data_quality_score",
        "latitude",
        "longitude",
    ]


    for col in numeric_columns:

        if col in df.columns:
            df[col] = (
                pd.to_numeric(
                    df[col],
                    errors="coerce"
                )
                .fillna(0)
            )


    # Text cleanup

    text_columns = [
        "place",
        "district",
        "province",
        "risk_category"
    ]


    for col in text_columns:

        if col in df.columns:
            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.strip()
            )


    # Remove duplicates

    df = df.drop_duplicates()


    # Save cleaned data

    os.makedirs(
        "processed_data",
        exist_ok=True
    )


    df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print("Risk cleaned successfully")
    print(
        "Saved:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()