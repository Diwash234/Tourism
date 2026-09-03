import os
from math import radians, sin, cos, sqrt, atan2

import pandas as pd
import networkx as nx
import numpy as np

from sklearn.neighbors import BallTree

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Candidate input files
CANDIDATE_PATHS = [
    os.path.join(BASE_DIR, "processed_data", "destinations_clean.csv"),
    os.path.join(BASE_DIR, "nepal_destination_sample.csv"),
    os.path.join(BASE_DIR, "data", "destinations", "nepal_destinations.csv")
]

GRAPH_OUT = os.path.join(BASE_DIR, "model", "route", "nepal_graph.graphml")

NEIGHBORS = 10


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def main():
    print("Loading destination data...")
    df = None
    for path in CANDIDATE_PATHS:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                print(f"Loaded dataset from {path}")
                break
            except Exception as e:
                print(f"Error reading {path}: {e}")

    if df is None:
        print("No valid destination CSV dataset found.")
        return

    print("Original columns:", df.columns.tolist())

    # Map column names if necessary
    rename_map = {}
    if "latitude" in df.columns and "Latitude" not in df.columns:
        rename_map["latitude"] = "Latitude"
    if "longitude" in df.columns and "Longitude" not in df.columns:
        rename_map["longitude"] = "Longitude"
    if "name" in df.columns and "Name" not in df.columns:
        rename_map["name"] = "Name"

    if rename_map:
        df = df.rename(columns=rename_map)

    required_columns = ["Name", "Latitude", "Longitude"]
    for col in required_columns:
        if col not in df.columns:
            print(f"Missing required column: {col}")
            return

    print("Cleaning data...")
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    df = df.dropna(subset=["Name", "Latitude", "Longitude"])
    df = df.drop_duplicates(subset=["Name"])
    df = df.reset_index(drop=True)

    print("Destinations after cleaning:", len(df))

    graph = nx.Graph()

    print("Adding nodes...")
    for _, row in df.iterrows():
        graph.add_node(
            str(row["Name"]),
            lat=float(row["Latitude"]),
            lon=float(row["Longitude"]),
            category=str(row.get("Tourism_Category", row.get("Type", "unknown"))),
            city=str(row.get("City", row.get("District", "")))
        )

    print("Finding nearby destinations...")
    coordinates = np.radians(df[["Latitude", "Longitude"]].values)
    total_places = len(df)

    if total_places > 1:
        tree = BallTree(coordinates, metric="haversine")
        k = min(NEIGHBORS + 1, total_places)
        distances, indexes = tree.query(coordinates, k=k)

        print("Creating connections...")
        for index, row in df.iterrows():
            source_name = str(row["Name"])
            for neighbor_index in indexes[index][1:]:
                if neighbor_index >= len(df):
                    continue
                target = df.iloc[neighbor_index]
                target_name = str(target["Name"])

                distance = haversine_km(
                    float(row["Latitude"]),
                    float(row["Longitude"]),
                    float(target["Latitude"]),
                    float(target["Longitude"])
                )

                graph.add_edge(
                    source_name,
                    target_name,
                    weight=round(distance, 2)
                )

            if index % 2000 == 0:
                print(f"Processed {index}/{total_places}")

    print("Saving graph...")
    os.makedirs(os.path.dirname(GRAPH_OUT), exist_ok=True)
    nx.write_graphml(graph, GRAPH_OUT)

    print("\n====================")
    print("Graph created successfully")
    print("Nodes:", graph.number_of_nodes())
    print("Edges:", graph.number_of_edges())
    print("Saved:", GRAPH_OUT)
    print("====================")


if __name__ == "__main__":
    main()
