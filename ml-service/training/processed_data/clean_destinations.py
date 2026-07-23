import pandas as pd

input_file = "../../data/destinations/nepal_destinations.csv"
output_file = "processed_data/destinations_clean.csv"


df = pd.read_csv(input_file)


# Remove duplicates
df = df.drop_duplicates()


# Remove missing important values
df = df.dropna(
    subset=[
        "Name",
        "Latitude",
        "Longitude",
        "Tourism_Category"
    ]
)


# Standardize text
df["Name"] = df["Name"].str.strip()
df["Tourism_Category"] = df["Tourism_Category"].str.lower()
df["Type"] = df["Type"].str.lower()


df.to_csv(
    output_file,
    index=False
)

print("Cleaned successfully")
