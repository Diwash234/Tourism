import pandas as pd
import sqlite3
import os


# CSV dataset location
input_file = "../../data/destinations/nepal_destinations.csv"


# SQLite database location
database_file = r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\db.sqlite3"


# Table name in database
table_name = "tourist_destination"


# Read raw CSV
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


# Standardize text fields
df["Name"] = df["Name"].str.strip()

df["Tourism_Category"] = (
    df["Tourism_Category"]
    .str.strip()
    .str.lower()
)

df["Type"] = (
    df["Type"]
    .str.strip()
    .str.lower()
)


# Connect to SQLite database
conn = sqlite3.connect(database_file)


# Save cleaned dataset into db.sqlite3
df.to_sql(
    table_name,
    conn,
    if_exists="replace",
    index=False
)


# Close connection
conn.close()


print(
    f"Cleaned successfully. Saved {len(df)} destinations into '{database_file}' table '{table_name}'"
)
