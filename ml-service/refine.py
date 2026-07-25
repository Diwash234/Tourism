import pandas as pd

# ==============================
# LOAD DATA
# ==============================

input_file = "../Tourism/dataset/budget_features.csv"
output_file = "../Tourism/dataset/travel_cost_cleaned.csv"

df = pd.read_csv(input_file)

print("Original rows:", len(df))

# ==============================
# CLEAN COLUMN NAMES
# ==============================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("/", "_")
    .str.replace("(", "")
    .str.replace(")", "")
)

print("Columns:", df.columns.tolist())

# ==============================
# REMOVE DUPLICATES
# ==============================

df = df.drop_duplicates()

df = df.drop_duplicates(
    subset=["source", "destination"],
    keep="first"
)

# ==============================
# CLEAN TEXT COLUMNS
# ==============================

text_cols = df.select_dtypes(include="object").columns

for col in text_cols:
    df[col] = (
        df[col]
        .fillna("")
        .astype(str)
        .str.strip()
    )

# ==============================
# STANDARDIZE TEXT
# ==============================

for col in [
    "source",
    "destination",
    "district",
    "province"
]:
    if col in df.columns:
        df[col] = df[col].str.title()

# ==============================
# CLEAN NUMERIC COLUMNS
# ==============================

numeric_cols = [
    "transport_cost_usd",
    "food_cost_day_usd",
    "accommodation_night_usd",
    "local_taxi_rickshaw_usd"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        df[col] = df[col].fillna(0)

        # Remove negative values
        df = df[df[col] >= 0]

# ==============================
# REMOVE EMPTY REQUIRED FIELDS
# ==============================

required = [
    "source",
    "destination",
    "district",
    "province"
]

for col in required:
    df = df[df[col].notna()]
    df = df[df[col] != ""]

# ==============================
# TOTAL ESTIMATED DAILY COST
# ==============================

if all(col in df.columns for col in [
    "food_cost_day_usd",
    "accommodation_night_usd",
    "local_taxi_rickshaw_usd"
]):
    df["estimated_daily_cost_usd"] = (
        df["food_cost_day_usd"] +
        df["accommodation_night_usd"] +
        df["local_taxi_rickshaw_usd"]
    ).round(2)

# ==============================
# DATA QUALITY SCORE
# ==============================

df["data_quality_score"] = (
    df.notnull().sum(axis=1)
    / len(df.columns)
    * 100
).round(2)

# ==============================
# SORT DATA
# ==============================

df = df.sort_values(
    by=[
        "province",
        "district",
        "destination"
    ]
)

# ==============================
# SAVE
# ==============================

df.to_csv(output_file, index=False)

print("Cleaned rows:", len(df))
print("Saved:", output_file)