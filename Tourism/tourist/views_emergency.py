from django.http import JsonResponse
from .models import Hospital, PoliceStation
from math import radians, sin, cos, sqrt, atan2


def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2 +
        cos(lat1) *
        cos(lat2) *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return R * c



def nearest_emergency(request):

    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    category = request.GET.get("category")


    if not lat or not lon:
        return JsonResponse({
            "error":"latitude and longitude required"
        }, status=400)



    if category == "hospital":

        places = Hospital.objects.exclude(is_archived=True)


    elif category == "police":

        places = PoliceStation.objects.all()


    else:

        return JsonResponse({
            "error":"invalid category"
        }, status=400)



    nearest = None
    nearest_distance = None


    for place in places:


        distance = calculate_distance(
            lat,
            lon,
            place.latitude,
            place.longitude
        )


        if nearest_distance is None or distance < nearest_distance:

            nearest_distance = distance
            nearest = place



    if not nearest:

        return JsonResponse({
            "message":"details not found"
        })



    return JsonResponse({

        "name": nearest.name,

        "address": nearest.address,

        "phone": nearest.phone,

        "latitude": float(nearest.latitude),

        "longitude": float(nearest.longitude),

        "distance_km": round(nearest_distance,2)

    })