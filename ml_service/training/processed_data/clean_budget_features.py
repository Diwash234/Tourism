"""
New script: ml_service/training/processed_data/clean_budget_features.py

This is a SEPARATE dataset from travel_cost_cleaned.csv (which was
unrecoverably corrupted, see BUGS.md #3) -- Tourism/dataset/budget_features.csv
is a different file, and it's actually fine. I checked it directly: real
city names, real cost ranges, nothing shifted or zeroed out.

The reason it "mostly becomes empty" when cleaned is almost certainly one
or both of:
  1. The header row only names 8 columns, but every data row has 11
     comma-separated values. Any pd.read_csv() without explicitly telling
     pandas about the extra 3 columns will misalign them (pandas either
     errors, or silently shifts values into the wrong columns depending
     on your pandas version) -- so numeric coercion later hits garbage
     and produces NaN across almost every row.
  2. If a cleaning step does pd.to_numeric(df[col], errors="coerce") on a
     column that's still a string range like "40-120" (not converted to
     a single number first), that also produces NaN for every row, and a
     .dropna() afterward wipes out nearly the whole file.

This script names all 11 real columns explicitly, converts every
"low-high" range to its numeric midpoint BEFORE any numeric coercion, and
only drops a row if it has literally no usable cost data at all (instead
of dropping on any single NaN).
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Adjust this if your actual raw file lives elsewhere -- this matches
# Tourism/dataset/budget_features.csv as confirmed in this conversation.
INPUT_FILE = os.path.join(BASE_DIR, "..", "Tourism", "dataset", "budget_features.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "processed_data", "budget_features_clean.csv")

# The header row only has 8 names but every row has 11 values. Naming all
# 11 explicitly avoids pandas silently misaligning columns.
COLUMN_NAMES = [
    "source", "destination", "district", "province",
    "transport_cost_usd", "food_cost_day_usd", "accommodation_night_usd", "local_taxi_usd",
    # These 3 trailing columns are unlabeled in the raw file. Their values
    # are consistently larger ranges than the 4 above them, in line with
    # being an aggregate estimate -- confirm against your own source, but
    # they're kept and clearly named rather than silently dropped.
    "estimated_daily_low_usd", "estimated_daily_mid_usd", "estimated_total_budget_usd",
]


def convert_range(value):
    """'100-250' -> 175.0, '$100' -> 100.0, '100' -> 100.0, NaN/junk -> None."""
    if pd.isna(value):
        return None
    value = str(value).replace("$", "").replace(",", "").strip()
    try:
        if "-" in value:
            low, high = value.split("-", 1)
            return (float(low) + float(high)) / 2
        return float(value)
    except ValueError:
        return None


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # skiprows=1 to drop the (mismatched) original header, since we're
    # supplying the correct 11-column header ourselves.
    df = pd.read_csv(INPUT_FILE, header=None, names=COLUMN_NAMES, skiprows=1)

    cost_columns = [
        "transport_cost_usd", "food_cost_day_usd", "accommodation_night_usd", "local_taxi_usd",
        "estimated_daily_low_usd", "estimated_daily_mid_usd", "estimated_total_budget_usd",
    ]
    for col in cost_columns:
        df[col] = df[col].apply(convert_range)

    # Only drop a row if EVERY cost column ended up unusable -- not on any
    # single missing value, which is what was silently emptying the file.
    df = df.dropna(subset=cost_columns, how="all")

    df["estimated_daily_cost"] = (
        df["food_cost_day_usd"].fillna(0) + df["accommodation_night_usd"].fillna(0) + df["local_taxi_usd"].fillna(0)
    )
    df["trip_cost_3_days"] = df["transport_cost_usd"].fillna(0) + df["estimated_daily_cost"] * 3
    df["trip_cost_7_days"] = df["transport_cost_usd"].fillna(0) + df["estimated_daily_cost"] * 7

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Wrote {len(df)} usable rows (out of {sum(1 for _ in open(INPUT_FILE)) - 1} raw rows) to {OUTPUT_FILE}")
    print(df.head())


if __name__ == "__main__":
    main()