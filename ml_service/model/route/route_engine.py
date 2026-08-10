"""
model/route/route_engine.py

Builds/loads a graph of destinations and computes shortest paths between
them.

Loads model/route/nepal_graph.graphml if it exists.

The graph currently uses straight-line distance between destinations,
not real road routing. Turn-by-turn instructions are therefore based
on the graph's coordinate sequence and should be treated as approximate
navigation instructions rather than real road-level directions.

Supported route types:
    fastest   -> normal shortest-distance route
    safest    -> risk-weighted route using risk_features.csv
    cheapest  -> currently falls back to fastest because no route-cost
                 data exists yet
    trekking  -> route using nodes categorized as trekking/trails
"""

import os
from math import radians, degrees, sin, cos, sqrt, atan2

import networkx as nx

try:
    import pandas as pd
except ImportError:
    pd = None


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)

GRAPH_PATH = os.path.join(
    BASE_DIR,
    "nepal_graph.graphml"
)

RISK_CSV_PATH = os.path.join(
    BASE_DIR,
    "..",
    "..",
    "processed_data",
    "risk_features.csv"
)


# ---------------------------------------------------------------------------
# Risk configuration
# ---------------------------------------------------------------------------

RISK_MULTIPLIER = {
    "LOW": 1.0,
    "MODERATE": 1.3,
    "MEDIUM": 1.3,
    "HIGH": 1.8,
}


_risk_df = None

if (
    pd is not None
    and os.path.exists(RISK_CSV_PATH)
):
    try:
        _risk_df = pd.read_csv(RISK_CSV_PATH)
    except Exception:
        _risk_df = None


# Cached graph
_graph = None


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calculate straight-line distance between two latitude/longitude
    coordinates in kilometers.
    """

    R = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    return 2 * R * atan2(
        sqrt(a),
        sqrt(1 - a)
    )


# ---------------------------------------------------------------------------
# Graph loading
# ---------------------------------------------------------------------------

def _load_graph():
    """
    Load the Nepal tourism graph once and cache it.

    GraphML stores edge weights as strings, so they are converted
    back to floats.
    """

    global _graph

    if _graph is not None:
        return _graph

    if not os.path.exists(GRAPH_PATH):
        raise FileNotFoundError(
            f"nepal_graph.graphml not found at: {GRAPH_PATH}"
        )

    g = nx.read_graphml(GRAPH_PATH)

    # Convert edge weights to floats.
    for _, _, data in g.edges(data=True):

        if "weight" in data:

            try:
                data["weight"] = float(data["weight"])
            except (ValueError, TypeError):

                # If the weight is invalid, use 1 as a safe fallback.
                data["weight"] = 1.0

    _graph = g

    return g


# ---------------------------------------------------------------------------
# Risk calculation
# ---------------------------------------------------------------------------

def _node_risk_multiplier(node_data):
    """
    Find the nearest risk_features.csv row to a graph node and return
    the corresponding risk multiplier.
    """

    if _risk_df is None:
        return 1.0

    if "lat" not in node_data or "lon" not in node_data:
        return 1.0

    try:
        node_lat = float(node_data["lat"])
        node_lon = float(node_data["lon"])
    except (ValueError, TypeError):
        return 1.0

    required_columns = {
        "latitude",
        "longitude",
        "risk_category",
    }

    if not required_columns.issubset(_risk_df.columns):
        return 1.0

    try:

        df = _risk_df.copy()

        df["_d"] = (
            (df["latitude"] - node_lat) ** 2
            +
            (df["longitude"] - node_lon) ** 2
        )

        nearest = df.loc[df["_d"].idxmin()]

        category = str(
            nearest.get("risk_category", "LOW")
        ).upper()

        return RISK_MULTIPLIER.get(
            category,
            1.0
        )

    except Exception:
        return 1.0


# ---------------------------------------------------------------------------
# Route type handling
# ---------------------------------------------------------------------------

def _weighted_graph_for_route_type(g, route_type):
    """
    Return the graph that should be used for the requested route type.

    Returns:
        (graph, optional_note)
    """

    route_type = str(
        route_type or "fastest"
    ).lower().strip()

    # ---------------------------------------------------------------
    # Trekking
    # ---------------------------------------------------------------

    if route_type == "trekking":

        trekking_nodes = [
            node
            for node, data in g.nodes(data=True)
            if (
                "trek" in str(
                    data.get("category", "")
                ).lower()
                or
                "trail" in str(
                    data.get("category", "")
                ).lower()
            )
        ]

        trekking_graph = g.subgraph(
            trekking_nodes
        ).copy()

        return trekking_graph, None

    # ---------------------------------------------------------------
    # Safest
    # ---------------------------------------------------------------

    if route_type == "safest":

        g2 = g.copy()

        for u, v, data in g2.edges(data=True):

            try:
                original_weight = float(
                    data.get("weight", 1.0)
                )
            except (
                ValueError,
                TypeError
            ):
                original_weight = 1.0

            risk_u = _node_risk_multiplier(
                g2.nodes[u]
            )

            risk_v = _node_risk_multiplier(
                g2.nodes[v]
            )

            data["weight"] = (
                original_weight
                *
                ((risk_u + risk_v) / 2.0)
            )

        return g2, None

    # ---------------------------------------------------------------
    # Cheapest
    # ---------------------------------------------------------------

    if route_type == "cheapest":

        return (
            g,
            "No per-route cost data exists yet -- "
            "returning the same result as 'fastest'."
        )

    # ---------------------------------------------------------------
    # Fastest / default
    # ---------------------------------------------------------------

    return g, None


# ---------------------------------------------------------------------------
# Find destinations by city
# ---------------------------------------------------------------------------

def find_destination_by_city(city_name):
    """
    Find all tourism destinations inside a city.
    """

    g = _load_graph()

    if city_name is None:
        return []

    requested_city = str(
        city_name
    ).strip().lower()

    results = []

    for node, data in g.nodes(data=True):

        city = str(
            data.get("city", "")
        ).strip()

        if city.lower() == requested_city:

            results.append({
                "name": node,
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "category": data.get("category"),
                "city": city,
            })

    return results


# ---------------------------------------------------------------------------
# Shortest path between two tourism places
# ---------------------------------------------------------------------------

def shortest_path(origin, destination):
    """
    Find the shortest path between two exact graph nodes.
    """

    g = _load_graph()

    if origin not in g:
        return {
            "error": f"{origin} not found"
        }

    if destination not in g:
        return {
            "error": f"{destination} not found"
        }

    try:

        route = nx.shortest_path(
            g,
            origin,
            destination,
            weight="weight"
        )

        distance = nx.shortest_path_length(
            g,
            origin,
            destination,
            weight="weight"
        )

    except nx.NetworkXNoPath:

        return {
            "error": (
                f"No path found between "
                f"{origin} and {destination}"
            )
        }

    return {
        "route": route,
        "distance_km": round(
            float(distance),
            2
        ),
    }


# ---------------------------------------------------------------------------
# Shortest route between cities
# ---------------------------------------------------------------------------

def shortest_city_route(from_city, to_city):
    """
    Find the shortest route between any tourism destination in one city
    and any tourism destination in another city.
    """

    start_places = find_destination_by_city(
        from_city
    )

    end_places = find_destination_by_city(
        to_city
    )

    if not start_places:

        return {
            "error": f"No places found in {from_city}"
        }

    if not end_places:

        return {
            "error": f"No places found in {to_city}"
        }

    g = _load_graph()

    shortest = None
    shortest_distance = float("inf")

    for start in start_places:

        for end in end_places:

            try:

                distance = nx.shortest_path_length(
                    g,
                    start["name"],
                    end["name"],
                    weight="weight"
                )

                if distance < shortest_distance:

                    shortest_distance = distance

                    shortest = nx.shortest_path(
                        g,
                        start["name"],
                        end["name"],
                        weight="weight"
                    )

            except nx.NetworkXNoPath:
                continue

    if shortest is None:

        return {
            "error": (
                f"No route found between "
                f"{from_city} and {to_city}"
            )
        }

    return {
        "from_city": from_city,
        "to_city": to_city,
        "fastest_route": shortest,
        "distance_km": round(
            float(shortest_distance),
            2
        ),
    }


# ---------------------------------------------------------------------------
# Nearby destinations
# ---------------------------------------------------------------------------

def nearby_destinations(
    place_name,
    max_km=50
):
    """
    Find tourism destinations within max_km of a named place.
    """

    g = _load_graph()

    if place_name not in g:
        return []

    current = g.nodes[place_name]

    try:

        current_lat = float(
            current["lat"]
        )

        current_lon = float(
            current["lon"]
        )

    except (
        KeyError,
        ValueError,
        TypeError
    ):

        return []

    nearby = []

    for node, data in g.nodes(data=True):

        if node == place_name:
            continue

        try:

            distance = haversine_km(
                current_lat,
                current_lon,
                float(data["lat"]),
                float(data["lon"])
            )

        except (
            KeyError,
            ValueError,
            TypeError
        ):

            continue

        if distance <= max_km:

            nearby.append({
                "name": node,
                "city": data.get(
                    "city",
                    ""
                ),
                "distance_km": round(
                    distance,
                    2
                ),
            })

    return sorted(
        nearby,
        key=lambda x: x["distance_km"]
    )


# ---------------------------------------------------------------------------
# Find nearest graph node to coordinates
# ---------------------------------------------------------------------------

def _nearest_node(
    g,
    latitude,
    longitude
):
    """
    Find the graph node closest to a raw latitude/longitude coordinate.

    Returns:
        (node_name, distance_km)
    """

    best_node = None
    best_distance = float("inf")

    for node, data in g.nodes(data=True):

        try:

            distance = haversine_km(
                latitude,
                longitude,
                float(data["lat"]),
                float(data["lon"])
            )

        except (
            KeyError,
            ValueError,
            TypeError
        ):

            continue

        if distance < best_distance:

            best_node = node
            best_distance = distance

    return best_node, best_distance


# ---------------------------------------------------------------------------
# Bearing
# ---------------------------------------------------------------------------

def _bearing(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate compass bearing.

    0   = North
    90  = East
    180 = South
    270 = West
    """

    lat1_r = radians(lat1)
    lat2_r = radians(lat2)

    dlon = radians(
        lon2 - lon1
    )

    x = (
        sin(dlon)
        *
        cos(lat2_r)
    )

    y = (
        cos(lat1_r)
        *
        sin(lat2_r)
        -
        sin(lat1_r)
        *
        cos(lat2_r)
        *
        cos(dlon)
    )

    return (
        degrees(
            atan2(x, y)
        )
        + 360
    ) % 360


# ---------------------------------------------------------------------------
# Turn classification
# ---------------------------------------------------------------------------

def _turn_label(bearing_change):
    """
    Convert a bearing change into a human-readable instruction.
    """

    if -15 <= bearing_change <= 15:
        return "Continue straight"

    if 15 < bearing_change <= 45:
        return "Slight right"

    if 45 < bearing_change <= 135:
        return "Turn right"

    if 135 < bearing_change <= 180:
        return "Sharp right, near U-turn"

    if -45 <= bearing_change < -15:
        return "Slight left"

    if -135 <= bearing_change < -45:
        return "Turn left"

    return "Sharp left, near U-turn"


# ---------------------------------------------------------------------------
# Distance phrase
# ---------------------------------------------------------------------------

def _format_distance_phrase(
    distance_km
):
    """
    Format a navigation distance.

    Examples:
        In 250m
        In 720m
        In 1.2km
    """

    meters = distance_km * 1000

    if meters < 1000:

        rounded = int(
            round(meters / 10) * 10
        )

        return f"In {rounded}m"

    return f"In {round(distance_km, 1)}km"


# ---------------------------------------------------------------------------
# Turn-by-turn navigation
# ---------------------------------------------------------------------------

def build_turn_by_turn(route_coords):
    """
    Build approximate turn-by-turn instructions from route coordinates.

    Input:

        [
            {"lat": 27.7, "lng": 85.3},
            {"lat": 27.71, "lng": 85.31},
            ...
        ]

    Output:

        [
            {
                "instruction": "Head Northeast",
                "distance_phrase": "In 800m",
                "distance_km": 0.8,
                "lat": 27.7,
                "lng": 85.3
            },
            ...
        ]

    Important:
        These are coordinate-based directions, not real road-level
        navigation instructions.
    """

    if not route_coords:
        return []

    if len(route_coords) < 2:

        return [
            {
                "instruction": "Arrive at destination",
                "distance_phrase": "",
                "distance_km": 0,
                "lat": route_coords[0]["lat"],
                "lng": route_coords[0]["lng"],
            }
        ]

    steps = []

    previous_bearing = None

    compass = [
        "North",
        "Northeast",
        "East",
        "Southeast",
        "South",
        "Southwest",
        "West",
        "Northwest",
    ]

    for i in range(
        len(route_coords) - 1
    ):

        a = route_coords[i]
        b = route_coords[i + 1]

        try:

            seg_bearing = _bearing(
                float(a["lat"]),
                float(a["lng"]),
                float(b["lat"]),
                float(b["lng"])
            )

            seg_distance = haversine_km(
                float(a["lat"]),
                float(a["lng"]),
                float(b["lat"]),
                float(b["lng"])
            )

        except (
            KeyError,
            ValueError,
            TypeError
        ):

            continue

        # First segment
        if previous_bearing is None:

            direction = compass[
                round(
                    seg_bearing / 45
                ) % 8
            ]

            instruction = (
                f"Head {direction}"
            )

        else:

            change = (
                (
                    seg_bearing
                    -
                    previous_bearing
                    +
                    180
                )
                % 360
            ) - 180

            instruction = _turn_label(
                change
            )

        steps.append({
            "instruction": instruction,
            "distance_phrase": _format_distance_phrase(
                seg_distance
            ),
            "distance_km": round(
                seg_distance,
                2
            ),
            "lat": float(a["lat"]),
            "lng": float(a["lng"]),
        })

        previous_bearing = seg_bearing

    # Final arrival step
    final_point = route_coords[-1]

    steps.append({
        "instruction": "Arrive at destination",
        "distance_phrase": "",
        "distance_km": 0,
        "lat": float(final_point["lat"]),
        "lng": float(final_point["lng"]),
    })

    return steps


# ---------------------------------------------------------------------------
# Calculate actual distance along a selected path
# ---------------------------------------------------------------------------

def _path_distance(
    g,
    path
):
    """
    Calculate the actual graph weight/distance along a specific path.

    This is important for the 'safest' route because the safest path may
    not be the same path as the normal shortest-distance path.
    """

    if not path or len(path) < 2:
        return 0.0

    total = 0.0

    for u, v in zip(
        path[:-1],
        path[1:]
    ):

        try:

            edge_data = g.get_edge_data(
                u,
                v
            )

            if edge_data is None:
                continue

            # Normal Graph
            if "weight" in edge_data:

                total += float(
                    edge_data["weight"]
                )

            # MultiGraph / MultiDiGraph
            elif isinstance(
                edge_data,
                dict
            ):

                weights = []

                for edge in edge_data.values():

                    if isinstance(edge, dict):

                        try:

                            weights.append(
                                float(
                                    edge.get(
                                        "weight",
                                        1.0
                                    )
                                )
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            pass

                if weights:

                    total += min(weights)

        except Exception:

            continue

    return total


# ---------------------------------------------------------------------------
# Best route between arbitrary coordinates
# ---------------------------------------------------------------------------

def best_route(
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
    route_type="fastest"
):
    """
    Route between two arbitrary coordinates.

    The coordinates are snapped to their nearest graph nodes and then
    shortest-path routing is performed.

    Supported route types:

        fastest
        safest
        cheapest
        trekking
    """

    g = _load_graph()

    route_type = str(
        route_type or "fastest"
    ).lower().strip()

    # Validate coordinates
    try:

        start_latitude = float(
            start_latitude
        )

        start_longitude = float(
            start_longitude
        )

        end_latitude = float(
            end_latitude
        )

        end_longitude = float(
            end_longitude
        )

    except (
        ValueError,
        TypeError
    ):

        return {
            "error": "Invalid start or destination coordinates."
        }

    # Get route-specific graph
    working_graph, note = (
        _weighted_graph_for_route_type(
            g,
            route_type
        )
    )

    if working_graph.number_of_nodes() == 0:

        return {
            "error": (
                f"No graph nodes match "
                f"route_type={route_type!r}."
            )
        }

    # Snap start coordinate
    start_node, start_snap_km = (
        _nearest_node(
            working_graph,
            start_latitude,
            start_longitude
        )
    )

    # Snap destination coordinate
    end_node, end_snap_km = (
        _nearest_node(
            working_graph,
            end_latitude,
            end_longitude
        )
    )

    if start_node is None:

        return {
            "error": (
                "No graph node found near "
                "the starting coordinates."
            )
        }

    if end_node is None:

        return {
            "error": (
                "No graph node found near "
                "the destination coordinates."
            )
        }

    # ---------------------------------------------------------------
    # Find route
    # ---------------------------------------------------------------

    try:

        path = nx.shortest_path(
            working_graph,
            start_node,
            end_node,
            weight="weight"
        )

    except nx.NetworkXNoPath:

        return {
            "error": (
                f"No path found between "
                f"{start_node} and {end_node} "
                f"for route_type={route_type!r}."
            )
        }

    except nx.NodeNotFound as exc:

        return {
            "error": str(exc)
        }

    # ---------------------------------------------------------------
    # Convert graph nodes to frontend coordinates
    # ---------------------------------------------------------------

    route_coords = []

    for node in path:

        node_data = g.nodes[node]

        try:

            route_coords.append({
                "lat": float(
                    node_data["lat"]
                ),
                "lng": float(
                    node_data["lon"]
                ),
            })

        except (
            KeyError,
            ValueError,
            TypeError
        ):

            continue

    if not route_coords:

        return {
            "error": "Route nodes do not contain valid coordinates."
        }

    # ---------------------------------------------------------------
    # Calculate distance along the selected route
    # ---------------------------------------------------------------

    route_distance_km = _path_distance(
        g,
        path
    )

    total_distance_km = (
        route_distance_km
        +
        start_snap_km
        +
        end_snap_km
    )

    # ---------------------------------------------------------------
    # Build turn-by-turn directions
    # ---------------------------------------------------------------

    directions = build_turn_by_turn(
        route_coords
    )

    # ---------------------------------------------------------------
    # Build response
    # ---------------------------------------------------------------

    result = {
        "path": path,

        # Frontend should use this field for Leaflet Polyline.
        "route": route_coords,

        # Turn-by-turn instructions.
        "directions": directions,

        "distance_km": round(
            total_distance_km,
            2
        ),

        "route_type": route_type,

        "start_node": start_node,

        "end_node": end_node,

        "start_snap_km": round(
            start_snap_km,
            2
        ),

        "end_snap_km": round(
            end_snap_km,
            2
        ),
    }

    if note:

        result["note"] = note

    return result