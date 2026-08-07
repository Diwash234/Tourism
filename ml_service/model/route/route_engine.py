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
from math import radians, sin, cos, sqrt, atan2, degrees

import networkx as nx

try:
    import pandas as pd
except ImportError:
    pd = None

RISK_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "processed_data", "risk_features.csv")
_risk_df = pd.read_csv(RISK_CSV_PATH) if (pd is not None and os.path.exists(RISK_CSV_PATH)) else None
RISK_MULTIPLIER = {"LOW": 1.0, "MODERATE": 1.3, "MEDIUM": 1.3, "HIGH": 1.8}


def _node_risk_multiplier(node_data):
    """Nearest risk_features.csv row to this node's lat/lon -> a weight multiplier."""
    if _risk_df is None or "lat" not in node_data or "lon" not in node_data:
        return 1.0
    df = _risk_df.copy()
    df["_d"] = ((df["latitude"] - float(node_data["lat"])) ** 2 + (df["longitude"] - float(node_data["lon"])) ** 2)
    nearest = df.loc[df["_d"].idxmin()]
    return RISK_MULTIPLIER.get(str(nearest.get("risk_category", "LOW")).upper(), 1.0)


def _weighted_graph_for_route_type(g, route_type):
    """Returns a graph (possibly a filtered subgraph or re-weighted copy) plus an optional caveat note."""
    if route_type == "trekking":
        trekking_nodes = [
            n for n, d in g.nodes(data=True)
            if "trek" in str(d.get("category", "")).lower() or "trail" in str(d.get("category", "")).lower()
        ]
        return g.subgraph(trekking_nodes).copy(), None

    if route_type == "safest":
        g2 = g.copy()
        for u, v, data in g2.edges(data=True):
            risk_u = _node_risk_multiplier(g2.nodes[u])
            risk_v = _node_risk_multiplier(g2.nodes[v])
            data["weight"] = data.get("weight", 1) * ((risk_u + risk_v) / 2)
        return g2, None

    if route_type == "cheapest":
        return g, "No per-route cost data exists yet -- returning the same result as 'fastest'."

    return g, None  # "fastest" / default


GRAPH_PATH = os.path.join(
    os.path.dirname(__file__),
    "nepal_graph.graphml"
)


_graph = None



def haversine_km(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = radians(lat2-lat1)
    dlon = radians(lon2-lon1)

    a = (
        sin(dlat/2)**2
        +
        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon/2)**2
    )

    return 2 * R * atan2(
        sqrt(a),
        sqrt(1-a)
    )



def _load_graph():

    global _graph

    if _graph is not None:
        return _graph


    if not os.path.exists(GRAPH_PATH):

        raise FileNotFoundError(
            "nepal_graph.graphml not found"
        )


    g = nx.read_graphml(
        GRAPH_PATH
    )


    # Convert distance weights back to float

    for _,_,data in g.edges(data=True):

        if "weight" in data:

            data["weight"] = float(
                data["weight"]
            )


    _graph = g

    return g





# Find all tourism places inside a city

def find_destination_by_city(city_name):

    g = _load_graph()

    results=[]


    for node,data in g.nodes(data=True):

        city=data.get(
            "city",
            ""
        )


        if city.lower()==city_name.lower():

            results.append(
                {
                    "name":node,
                    "latitude":data.get("lat"),
                    "longitude":data.get("lon"),
                    "category":data.get("category"),
                    "city":city
                }
            )


    return results





# Find shortest route between two tourism places

def shortest_path(
    origin,
    destination
):

    g=_load_graph()


    if origin not in g:

        return {
            "error":
            f"{origin} not found"
        }


    if destination not in g:

        return {
            "error":
            f"{destination} not found"
        }



    route=nx.shortest_path(
        g,
        origin,
        destination,
        weight="weight"
    )


    distance=nx.shortest_path_length(
        g,
        origin,
        destination,
        weight="weight"
    )



    return {

        "route":route,

        "distance_km":
        round(distance,2)

    }





# Calculate best route between two cities

def shortest_city_route(
    from_city,
    to_city
):


    start_places=find_destination_by_city(
        from_city
    )


    end_places=find_destination_by_city(
        to_city
    )



    if not start_places:

        return {
            "error":
            f"No places found in {from_city}"
        }



    if not end_places:

        return {
            "error":
            f"No places found in {to_city}"
        }



    shortest=None

    shortest_distance=float("inf")



    g=_load_graph()



    for start in start_places:

        for end in end_places:


            try:

                distance=nx.shortest_path_length(

                    g,

                    start["name"],

                    end["name"],

                    weight="weight"

                )


                if distance < shortest_distance:


                    shortest_distance=distance


                    shortest=nx.shortest_path(

                        g,

                        start["name"],

                        end["name"],

                        weight="weight"

                    )


            except nx.NetworkXNoPath:

                continue




    return {


        "from_city":
        from_city,


        "to_city":
        to_city,


        "fastest_route":
        shortest,


        "distance_km":
        round(
            shortest_distance,
            2
        )


    }






# Find nearby tourism places

def nearby_destinations(
    place_name,
    max_km=50
):

    g=_load_graph()



    if place_name not in g:

        return []



    current=g.nodes[place_name]


    nearby=[]



    for node,data in g.nodes(data=True):


        if node==place_name:
            continue


        distance=haversine_km(

            float(current["lat"]),

            float(current["lon"]),

            float(data["lat"]),

            float(data["lon"])

        )


        if distance <= max_km:


            nearby.append({

                "name":node,

                "city":data.get(
                    "city",
                    ""
                ),

                "distance_km":
                round(distance,2)

            })



    return sorted(

        nearby,

        key=lambda x:x["distance_km"]

    )
def _nearest_node(g, latitude, longitude):
    """Finds the graph node closest to a raw lat/lon coordinate."""
    best_node, best_distance = None, float("inf")
    for node, data in g.nodes(data=True):
        try:
            distance = haversine_km(latitude, longitude, float(data["lat"]), float(data["lon"]))
        except (KeyError, ValueError, TypeError):
            continue
        if distance < best_distance:
            best_node, best_distance = node, distance
    return best_node, best_distance
 
 
def _bearing_deg(lat1, lon1, lat2, lon2):
    """Initial bearing (0-360) from point 1 to point 2."""
    try:
        lat1, lon1, lat2, lon2 = map(radians, map(float, (lat1, lon1, lat2, lon2)))
    except (TypeError, ValueError):
        return None
    dlon = lon2 - lon1
    y = sin(dlon) * cos(lat2)
    x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360


def _compass_dir(bearing):
    if bearing is None:
        return ""
    dirs = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    idx = int((bearing + 22.5) // 45) % 8
    return dirs[idx]


def _turn_label(prev_bearing, next_bearing):
    """Google-Maps-style turn label from consecutive bearings."""
    if prev_bearing is None or next_bearing is None:
        return "straight"
    delta = (next_bearing - prev_bearing + 540) % 360 - 180  # -180..180
    if abs(delta) < 20:
        return "straight"
    if abs(delta) > 160:
        return "uturn"
    if delta > 0:
        return "right" if delta <= 100 else "sharp_right"
    return "left" if delta >= -100 else "sharp_left"


def build_steps(g, path):
    """
    Turn-by-turn steps for a graph path (Google-Maps style). Each step has
    an instruction, turn direction, and per-leg distance in km and meters.
    """
    steps = []
    if not path or len(path) < 2:
        return steps

    coords = []
    for node in path:
        d = g.nodes[node]
        try:
            coords.append((float(d["lat"]), float(d["lon"]), node))
        except (KeyError, TypeError, ValueError):
            coords.append((None, None, node))

    # Precompute bearings between consecutive points
    bearings = []
    for i in range(len(coords) - 1):
        lat1, lon1, _ = coords[i]
        lat2, lon2, _ = coords[i + 1]
        bearings.append(_bearing_deg(lat1, lon1, lat2, lon2))

    # Merge consecutive edges that go the same general direction into one step
    i = 0
    while i < len(bearings):
        start_idx = i
        # first leg always starts a step
        turn = "start"
        # find the end of this "same direction" run
        j = i
        while j < len(bearings):
            if j == i:
                j += 1
                continue
            prev_b = bearings[j - 1]
            next_b = bearings[j]
            if prev_b is not None and next_b is not None and abs((next_b - prev_b + 540) % 360 - 180) >= 20:
                break
            j += 1
        end_idx = j  # number of bearings consumed (last index inclusive = end_idx - 1)

        # distance for this step = sum of edge weights between nodes start_idx..end_idx
        dist_km = 0.0
        for e in range(start_idx, min(end_idx, len(path) - 1)):
            u, v = path[e], path[e + 1]
            w = g.edges[u, v].get("weight")
            if w is None:
                lat1, lon1, _ = coords[e]
                lat2, lon2, _ = coords[e + 1]
                if lat1 is not None and lat2 is not None:
                    w = haversine_km(lat1, lon1, lat2, lon2)
            dist_km += float(w or 0)

        # turn label for THIS step = turn at its START (i.e. between bearing i-1 and i)
        if start_idx == 0:
            turn = "start"
            prev_b = None
            next_b = bearings[0] if bearings else None
        else:
            prev_b = bearings[start_idx - 1]
            next_b = bearings[start_idx] if start_idx < len(bearings) else None
            turn = _turn_label(prev_b, next_b)

        # instruction
        if turn == "start":
            instruction = f"Head {_compass_dir(next_b)} toward {coords[min(end_idx, len(coords)-1)][2]}"
        elif turn == "straight":
            instruction = f"Continue {_compass_dir(next_b)} toward {coords[min(end_idx, len(coords)-1)][2]}"
        elif turn == "uturn":
            instruction = "Make a U-turn"
        else:
            direction_word = {"left": "left", "right": "right", "sharp_left": "sharp left", "sharp_right": "sharp right"}[turn]
            instruction = f"Turn {direction_word} toward {coords[min(end_idx, len(coords)-1)][2]}"

        steps.append({
            "instruction": instruction,
            "turn": turn,
            "distance_km": round(dist_km, 3),
            "distance_m": int(round(dist_km * 1000)),
            "from": {"lat": coords[start_idx][0], "lng": coords[start_idx][1]},
            "to": {"lat": coords[min(end_idx, len(coords)-1)][0], "lng": coords[min(end_idx, len(coords)-1)][1]},
        })
        i = end_idx

    return steps


def best_route(start_latitude, start_longitude, end_latitude, end_longitude, route_type="fastest"):
    """
    Route between two arbitrary coordinates (e.g. the user's live GPS
    position and a destination's stored lat/lon) rather than exact graph
    node names. Snaps each point to its nearest graph node, then runs the
    same shortest_path search used by /shortest-path.
    """
    g = _load_graph()

    working_graph, note = _weighted_graph_for_route_type(g, route_type)
    if working_graph.number_of_nodes() == 0:
        return {"error": f"No graph nodes match route_type={route_type!r} (e.g. no nodes tagged as trekking)."}

    start_node, start_snap_km = _nearest_node(working_graph, start_latitude, start_longitude)
    end_node, end_snap_km = _nearest_node(working_graph, end_latitude, end_longitude)
 
    if start_node is None or end_node is None:
        return {"error": "No graph nodes with valid coordinates found for this route_type."}
 
    try:
        path = nx.shortest_path(working_graph, start_node, end_node, weight="weight")
        # Real km uses the ORIGINAL unweighted graph, not the risk-adjusted
        # one -- "safest" should still report true distance, just chosen
        # via a risk-weighted path.
        distance_km = nx.shortest_path_length(g, start_node, end_node, weight="weight")
    except nx.NetworkXNoPath:
        return {"error": f"No path found between {start_node} and {end_node} for route_type={route_type!r}."}
 
    # MapView.jsx (frontend/Tourism/src/components/map/MapView.jsx) draws
    # the route with Leaflet's <Polyline positions={...}> and expects each
    # point as {lat, lng} (or [lat, lng]) -- NOT bare graph node IDs. `path`
    # below is kept for debugging/other callers, but `route` is the field
    # Django should actually forward to the frontend.
    route_coords = []
    for node in path:
        node_data = g.nodes[node]
        try:
            route_coords.append({"lat": float(node_data["lat"]), "lng": float(node_data["lon"])})
        except (KeyError, ValueError, TypeError):
            continue
 
    result = {
        "path": path,
        "route": route_coords,
        "distance_km": round(distance_km + start_snap_km + end_snap_km, 2),
        "route_type": route_type,
        "start_node": start_node,
        "end_node": end_node,
        "start_snap_km": round(start_snap_km, 2),
        "end_snap_km": round(end_snap_km, 2),
    }
    # NEW: Google-Maps-style turn-by-turn directions (left/right + km/m)
    # computed from the graphml road graph.
    steps = build_steps(g, path)
    if steps:
        result["steps"] = steps
        # Rough Nepal driving/trekking average ~30 km/h.
        result["duration_min"] = int(round((distance_km + start_snap_km + end_snap_km) / 30 * 60))
    if note:
        result["note"] = note
    return result