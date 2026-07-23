import random


def calculate_budget(row):

    name = row["name"]

    lat, lon = get_location(name)

    if not lat:
        return None


    osm = get_osm_features(
        lat,
        lon
    )


    distance = city_distance(
        lat,
        lon
    )


    road_factor = osm["road_count"]
    hotel_factor = osm["hotel_count"]
    restaurant_factor = osm["restaurant_count"]


    # Remote score
    remoteness = (
        distance * 2
        - road_factor * 0.5
        - hotel_factor * 10
    )


    # Base Nepal travel cost

    if remoteness > 300:

        location_type = "extreme_remote"

        transport = random.randint(
            50000,
            250000
        )

        accommodation = random.randint(
            20000,
            100000
        )

        food = random.randint(
            10000,
            50000
        )


    elif remoteness > 150:

        location_type = "remote"

        transport = random.randint(
            15000,
            80000
        )

        accommodation = random.randint(
            8000,
            50000
        )

        food = random.randint(
            5000,
            25000
        )


    elif distance > 50:

        location_type = "rural"

        transport = random.randint(
            5000,
            30000
        )

        accommodation = random.randint(
            3000,
            20000
        )

        food = random.randint(
            2000,
            10000
        )


    else:

        location_type = "town"

        transport = random.randint(
            1000,
            10000
        )

        accommodation = random.randint(
            2000,
            15000
        )

        food = random.randint(
            1000,
            8000
        )


    # Extra tourism costs

    guide = random.randint(
        2000,
        50000
    )


    activities = random.randint(
        1000,
        100000
    )


    emergency_buffer = random.randint(
        1000,
        50000
    )


    total_budget = (
        transport
        + accommodation
        + food
        + guide
        + activities
        + emergency_buffer
    )


    # Force range
    total_budget = max(
        1000,
        min(
            total_budget,
            1000000
        )
    )


    return {

        "destination": name,

        "latitude": lat,

        "longitude": lon,

        "location_type": location_type,

        "distance_from_city_km":
            round(distance,2),

        "road_count":
            road_factor,

        "hotel_count":
            hotel_factor,

        "restaurant_count":
            restaurant_factor,


        "transport_cost":
            transport,

        "food_cost":
            food,

        "accommodation_cost":
            accommodation,

        "guide_cost":
            guide,

        "activity_cost":
            activities,

        "emergency_cost":
            emergency_buffer,


        "daily_budget":
            total_budget
    }
