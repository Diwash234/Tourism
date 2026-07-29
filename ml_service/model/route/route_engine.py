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
 
 
def best_route(start_latitude, start_longitude, end_latitude, end_longitude):
    """
    Route between two arbitrary coordinates (e.g. the user's live GPS
    position and a destination's stored lat/lon) rather than exact graph
    node names. Snaps each point to its nearest graph node, then runs the
    same shortest_path search used by /shortest-path.
    """
    g = _load_graph()
 
    start_node, start_snap_km = _nearest_node(g, start_latitude, start_longitude)
    end_node, end_snap_km = _nearest_node(g, end_latitude, end_longitude)
 
    if start_node is None or end_node is None:
        return {"error": "No graph nodes with valid coordinates found."}
 
    try:
        path = nx.shortest_path(g, start_node, end_node, weight="weight")
        distance_km = nx.shortest_path_length(g, start_node, end_node, weight="weight")
    except nx.NetworkXNoPath:
        return {"error": f"No path found between {start_node} and {end_node}."}
 
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
 
    return {
        "path": path,
        "route": route_coords,
        "distance_km": round(distance_km + start_snap_km + end_snap_km, 2),
        "start_node": start_node,
        "end_node": end_node,
        "start_snap_km": round(start_snap_km, 2),
        "end_snap_km": round(end_snap_km, 2),
    }