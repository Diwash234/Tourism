"""
training/build_route_graph.py

Creates:
    model/route/nepal_graph.graphml

Input:
    data/destinations/nepal_destinations.csv

Expected CSV columns:

    ID
    Name
    Type
    Tourism_Category
    Latitude
    Longitude
    City
"""


import os
from math import radians, sin, cos, sqrt, atan2

import pandas as pd
import networkx as nx
import numpy as np

from sklearn.neighbors import BallTree



DESTINATIONS_PATH = "data/destinations/nepal_destinations.csv"

GRAPH_OUT = "model/route/nepal_graph.graphml"


# Number of nearby places connected
NEIGHBORS = 10




def haversine_km(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon / 2) ** 2
    )

    return 2 * R * atan2(
        sqrt(a),
        sqrt(1 - a)
    )




def main():


    print("Loading destination data...")


    df = pd.read_csv(
        DESTINATIONS_PATH
    )


    print(
        "Original columns:"
    )

    print(
        df.columns.tolist()
    )



    required_columns = [

        "Name",
        "Latitude",
        "Longitude"

    ]



    for col in required_columns:

        if col not in df.columns:

            raise Exception(
                f"Missing required column: {col}"
            )



    print(
        "Cleaning data..."
    )


    # Convert coordinates first

    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce"
    )


    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce"
    )



    # Remove bad rows

    df = df.dropna(
        subset=[
            "Name",
            "Latitude",
            "Longitude"
        ]
    )



    # Remove duplicate names
    # NetworkX cannot handle duplicate node names properly

    df = df.drop_duplicates(
        subset=[
            "Name"
        ]
    )


    # IMPORTANT
    # Reset index after cleaning

    df = df.reset_index(
        drop=True
    )



    print(
        "Destinations after cleaning:",
        len(df)
    )



    graph = nx.Graph()



    print(
        "Adding nodes..."
    )


    for _, row in df.iterrows():


        graph.add_node(

            str(row["Name"]),

            lat=float(row["Latitude"]),

            lon=float(row["Longitude"]),

            category=str(
                row.get(
                    "Tourism_Category",
                    "unknown"
                )
            ),

            city=str(
                row.get(
                    "City",
                    ""
                )
            )

        )



    print(
        "Finding nearby destinations..."
    )



    coordinates = np.radians(

        df[
            [
                "Latitude",
                "Longitude"
            ]
        ].values

    )



    total_places = len(df)



    # If only one place exists

    if total_places > 1:


        tree = BallTree(

            coordinates,

            metric="haversine"

        )



        k = min(

            NEIGHBORS + 1,

            total_places

        )



        distances, indexes = tree.query(

            coordinates,

            k=k

        )



        print(
            "Creating connections..."
        )



        for index, row in df.iterrows():


            source_name = str(
                row["Name"]
            )



            for neighbor_index in indexes[index][1:]:



                # Safety check

                if neighbor_index >= len(df):

                    continue



                target = df.iloc[
                    neighbor_index
                ]


                target_name = str(
                    target["Name"]
                )



                distance = haversine_km(

                    float(row["Latitude"]),

                    float(row["Longitude"]),

                    float(target["Latitude"]),

                    float(target["Longitude"])

                )



                graph.add_edge(

                    source_name,

                    target_name,

                    weight=round(

                        distance,

                        2

                    )

                )



            if index % 500 == 0:

                print(
                    f"Processed {index}/{total_places}"
                )



    print(
        "Saving graph..."
    )



    os.makedirs(

        os.path.dirname(GRAPH_OUT),

        exist_ok=True

    )



    nx.write_graphml(

        graph,

        GRAPH_OUT

    )



    print("\n====================")

    print(
        "Graph created successfully"
    )

    print(
        "Nodes:",
        graph.number_of_nodes()
    )

    print(
        "Edges:",
        graph.number_of_edges()
    )

    print(
        "Saved:",
        GRAPH_OUT
    )

    print("====================")




if __name__ == "__main__":

    main()