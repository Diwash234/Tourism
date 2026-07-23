"""
training/build_route_graph.py

Builds model/route/nepal_graph.graphml.

IMPORTANT - what this graph actually is right now: a complete graph over
the destinations in data/destinations/nepal_destinations_sample.csv, with
edge weights = straight-line (haversine) distance in km. That's a
reasonable stand-in for "roughly how far apart are these places" but it
is NOT real road routing.

To get real road distances/turn-by-turn routing, replace the graph-build
section below with osmnx reading data/routes/nepal.osm.pbf, e.g.:

    import osmnx as ox
    g = ox.graph_from_xml("data/routes/nepal.osm.pbf")

...and keep saving to the same nepal_graph.graphml path - route_engine.py
already checks for this file first and only falls back to the in-memory
haversine graph if it's missing, so nothing downstream has to change.

Run:
    python training/build_route_graph.py
"""
import os
from math import radians, sin, cos, sqrt, atan2
import networkx as nx
import pandas as pd

DESTINATIONS_PATH = "data/destinations/nepal_destination_sample.csv"
GRAPH_OUT = "model/route/nepal_graph.graphml"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def main():
    df = pd.read_csv(DESTINATIONS_PATH)
    g = nx.Graph()

    for _, row in df.iterrows():
        g.add_node(row["name"], lat=float(row["lat"]), lon=float(row["lon"]), category=row["category"])

    names = df["name"].tolist()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = df.iloc[i], df.iloc[j]
            dist = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            g.add_edge(a["name"], b["name"], weight=round(dist, 2))

    os.makedirs(os.path.dirname(GRAPH_OUT), exist_ok=True)
    nx.write_graphml(g, GRAPH_OUT)
    print(f"Saved graph ({g.number_of_nodes()} nodes, {g.number_of_edges()} edges) to {GRAPH_OUT}")


if __name__ == "__main__":
    main()