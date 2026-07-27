import osmnx as ox
import networkx as nx
import pandas as pd
from tqdm import tqdm

# -----------------------------
# USER LOCATION
# -----------------------------
user_lat = 27.7172
user_lon = 85.3240

# -----------------------------
# LOAD DESTINATIONS
# -----------------------------
df = pd.read_csv("nepal_destination_sample.csv")

# -----------------------------
# DOWNLOAD ROAD NETWORK
# -----------------------------
print("Downloading Nepal road network...")

graph = ox.graph_from_place(
    "Nepal",
    network_type="drive"
)

graph = ox.add_edge_speeds(graph)
graph = ox.add_edge_travel_times(graph)

print("Road network downloaded.")

# -----------------------------
# USER NODE
# -----------------------------
origin = ox.distance.nearest_nodes(
    graph,
    X=user_lon,
    Y=user_lat
)

results = []

# -----------------------------
# ROUTE TO EACH DESTINATION
# -----------------------------
for _, row in tqdm(df.iterrows(), total=len(df)):

    try:

        destination = ox.distance.nearest_nodes(
            graph,
            X=row["longitude"],
            Y=row["latitude"]
        )

        route = nx.shortest_path(
            graph,
            origin,
            destination,
            weight="travel_time"
        )

        distance = 0
        travel_time = 0

        for u, v in zip(route[:-1], route[1:]):

            edge = min(
                graph.get_edge_data(u, v).values(),
                key=lambda x: x["length"]
            )

            distance += edge["length"]

            travel_time += edge.get(
                "travel_time",
                edge["length"] / 11.11
            )

        results.append({
            "Destination ID": row["id"],
            "Destination": row["name"],
            "User Latitude": user_lat,
            "User Longitude": user_lon,
            "Destination Latitude": row["latitude"],
            "Destination Longitude": row["longitude"],
            "Distance (km)": round(distance / 1000, 2),
            "Travel Time (min)": round(travel_time / 60, 1)
        })

    except Exception:

        results.append({
            "Destination ID": row["id"],
            "Destination": row["name"],
            "User Latitude": user_lat,
            "User Longitude": user_lon,
            "Destination Latitude": row["latitude"],
            "Destination Longitude": row["longitude"],
            "Distance (km)": None,
            "Travel Time (min)": None
        })

# -----------------------------
# SAVE CSV
# -----------------------------
result = pd.DataFrame(results)

result.to_csv(
    "routes_dataset.csv",
    index=False
)

print(result.head())

print("Dataset saved as routes_dataset.csv")