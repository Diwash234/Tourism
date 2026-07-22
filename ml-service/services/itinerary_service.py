"""
services/itinerary_service.py

Takes a list of chosen destination names and a number of days, and
produces a simple day-wise plan using the route engine to keep travel
between consecutive stops short.
"""
from model.route.route_engine import shortest_path


def build_itinerary(destination_names: list[str], num_days: int) -> dict:
    if not destination_names:
        return {"error": "No destinations provided"}

    if num_days < 1:
        num_days = 1

    # Distribute destinations across days as evenly as possible, in the
    # order given (the caller/frontend can pre-sort them by preference;
    # the route engine below just reports travel distance for context).
    per_day = max(1, len(destination_names) // num_days)
    days = []
    idx = 0
    for day_num in range(1, num_days + 1):
        stops = destination_names[idx: idx + per_day]
        if day_num == num_days:
            stops = destination_names[idx:]  # last day takes the remainder
        idx += per_day

        leg_distances = []
        for i in range(len(stops) - 1):
            leg = shortest_path(stops[i], stops[i + 1])
            if "distance_km" in leg:
                leg_distances.append({"from": stops[i], "to": stops[i + 1], "distance_km": leg["distance_km"]})

        days.append({"day": day_num, "stops": stops, "legs": leg_distances})
        if not stops:
            break

    return {"num_days": num_days, "itinerary": days}