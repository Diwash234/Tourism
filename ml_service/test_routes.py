"""
test_routes.py

Tests route engine functionality.

Run:

python test_routes.py
"""


from model.route.route_engine import (
    shortest_path,
    shortest_city_route,
    nearby_destinations,
    find_destination_by_city
)


from services.itinerary_service import build_itinerary





# =====================================================
# 1. TEST CITY TO CITY ROUTE
# =====================================================

print("\n")
print("=" * 50)
print("CITY ROUTE TEST")
print("=" * 50)


from_city = "Kathmandu"
to_city = "Pokhara"


try:

    result = shortest_city_route(
        from_city,
        to_city
    )


    print("\nFROM:")
    print(from_city)


    print("TO:")
    print(to_city)


    print("\nRESULT:")
    print("-" * 30)


    print(result)



except Exception as e:

    print("City route error:")
    print(e)





# =====================================================
# 2. TEST EXACT PLACE ROUTE
# =====================================================

print("\n")
print("=" * 50)
print("EXACT PLACE ROUTE TEST")
print("=" * 50)



origin = "Hotel Shanker"

destination = "The Lakeside Retreat - Pokhara"



try:


    result = shortest_path(

        origin,

        destination

    )


    print("\nFROM:")
    print(origin)


    print("TO:")
    print(destination)


    print("\nRESULT:")
    print("-" * 30)


    print(result)



except Exception as e:

    print("Exact route error:")
    print(e)





# =====================================================
# 3. TEST CITY DESTINATIONS
# =====================================================


print("\n")
print("=" * 50)
print("CITY PLACES TEST")
print("=" * 50)



city = "Kathmandu"



try:


    places = find_destination_by_city(
        city
    )


    print("\nCity:")
    print(city)


    print(
        "Total places:",
        len(places)
    )


    print("\nFirst 10 places:")


    for place in places[:10]:

        print(
            "-",
            place
        )



except Exception as e:

    print("City places error:")
    print(e)






# =====================================================
# 4. TEST NEARBY DESTINATIONS
# =====================================================


print("\n")
print("=" * 50)
print("NEARBY PLACES TEST")
print("=" * 50)



place = "Hotel Shanker"



try:


    nearby = nearby_destinations(

        place,

        20

    )


    print("\nAround:")
    print(place)


    print("\nNearby places:")


    if nearby:

        for item in nearby[:10]:

            print(item)


    else:

        print(
            "No nearby places found"
        )



except Exception as e:

    print("Nearby error:")
    print(e)







# =====================================================
# 5. TEST ITINERARY
# =====================================================


print("\n")
print("=" * 50)
print("ITINERARY TEST")
print("=" * 50)



try:


    itinerary = build_itinerary(

        [
            "Kathmandu",
            "Pokhara"
        ],

        3

    )


    print(itinerary)



except Exception as e:


    print("Itinerary error:")
    print(e)





print("\n")
print("=" * 50)
print("TEST COMPLETE")
print("=" * 50)