"""
model/route/route_engine.py

Builds/loads a graph of destinations and computes shortest paths between
them.

Loads model/route/nepal_graph.graphml if it exists (generate it with
training/build_route_graph.py). Falls back to building the same kind of
graph in memory from data/destinations/nepal_destinations_sample.csv if
the file isn't there yet, so this never breaks the API.

Note: right now that graph (whether loaded from disk or built in memory)
uses straight-line distance between destinations, not real road routing -
see the docstring in training/build_route_graph.py for how to swap in
real OSM-based routing later without changing these function signatures.
"""
import os
from math import radians, sin, cos, sqrt, atan2
import networkx as nx
import pandas as pd

GRAPH_PATH = os.path.join(os.path.dirname(__file__), "nepal_graph.graphml")
DESTINATIONS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "destinations", "nepal_destinations_sample.csv"
)

_graph = None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def _build_graph_in_memory() -> nx.Graph:
    df = pd.read_csv(DESTINATIONS_PATH)
    g = nx.Graph()
    for _, row in df.iterrows():
        g.add_node(row["name"], lat=row["lat"], lon=row["lon"], category=row["category"])

    names = df["name"].tolist()
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = df.iloc[i], df.iloc[j]
            dist = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            g.add_edge(a["name"], b["name"], weight=dist)
    return g


def _load_graph() -> nx.Graph:
    global _graph
    if _graph is not None:
        return _graph

    if os.path.exists(GRAPH_PATH):
        g = nx.read_graphml(GRAPH_PATH)
        # graphml stores edge weights as strings - cast back to float
        for _, _, data in g.edges(data=True):
            if "weight" in data:
                data["weight"] = float(data["weight"])
        _graph = g
    else:
        _graph = _build_graph_in_memory()

    return _graph


def shortest_path(origin: str, destination: str) -> dict:
    g = _load_graph()
    if origin not in g or destination not in g:
        return {"error": "Unknown destination name", "known_names": list(g.nodes)}

    path = nx.shortest_path(g, origin, destination, weight="weight")
    distance_km = nx.shortest_path_length(g, origin, destination, weight="weight")
    return {"path": path, "distance_km": round(distance_km, 1)}


def nearby_destinations(name: str, max_km: float = 150) -> list:
    g = _load_graph()
    if name not in g:
        return []
    return sorted(
        [
            {"name": n, "distance_km": round(g[name][n]["weight"], 1)}
            for n in g.neighbors(name)
            if g[name][n]["weight"] <= max_km
        ],
        key=lambda x: x["distance_km"],
    )