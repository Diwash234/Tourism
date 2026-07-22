"""
tourist/views_osm.py — endpoints backed by tourist/services/overpass.py.

  POST /api/v1/osm/essential-services/sync/   {latitude, longitude, radius_m}
  GET  /api/v1/osm/essential-services/nearby/ ?latitude=&longitude=&radius_km=&category=
  POST /api/v1/osm/tourism-places/sync/       {latitude, longitude, radius_m}
  GET  /api/v1/osm/tourism-places/nearby/     ?latitude=&longitude=&radius_km=&category=

`sync/` fetches fresh data from Overpass and saves it (see services/overpass.py);
`nearby/` reads straight from the database — fast, no repeated Overpass calls.
Call sync/ once per area (e.g. on first visit, or via a scheduled task), then
nearby/ for every subsequent read.
"""
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OSMEssentialService, OSMTourismPlace
from .serializers import OSMEssentialServiceSerializer, OSMTourismPlaceSerializer
from .services.overpass import sync_essential_services, sync_tourism_places
from .utils import haversine_distance


def _parse_coords(params):
    try:
        lat = float(params.get("latitude") or params.get("lat"))
        lon = float(params.get("longitude") or params.get("lng"))
        return lat, lon
    except (TypeError, ValueError):
        return None, None


class OSMEssentialServiceSyncView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lat, lon = _parse_coords(request.data)
        if lat is None:
            return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)
        radius_m = int(request.data.get("radius_m", 5000))
        created, updated = sync_essential_services(lat, lon, radius_m)
        return Response({"created": created, "updated": updated})


class OSMEssentialServiceNearbyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat, lon = _parse_coords(request.query_params)
        if lat is None:
            return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)
        radius_km = float(request.query_params.get("radius_km", 10))
        category = request.query_params.get("category")

        qs = OSMEssentialService.objects.all()
        if category:
            qs = qs.filter(category=category)

        results = []
        for obj in qs:
            distance = haversine_distance(lat, lon, obj.latitude, obj.longitude)
            if distance <= radius_km:
                results.append((distance, obj))
        results.sort(key=lambda pair: pair[0])

        data = OSMEssentialServiceSerializer([o for _, o in results], many=True).data
        for item, (distance, _) in zip(data, results):
            item["distance_km"] = round(distance, 2)
        return Response(data)


class OSMTourismPlaceSyncView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        lat, lon = _parse_coords(request.data)
        if lat is None:
            return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)
        radius_m = int(request.data.get("radius_m", 5000))
        created, updated = sync_tourism_places(lat, lon, radius_m)
        return Response({"created": created, "updated": updated})


class OSMTourismPlaceNearbyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat, lon = _parse_coords(request.query_params)
        if lat is None:
            return Response({"detail": "latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)
        radius_km = float(request.query_params.get("radius_km", 10))
        category = request.query_params.get("category")

        qs = OSMTourismPlace.objects.all()
        if category:
            qs = qs.filter(category=category)

        results = []
        for obj in qs:
            distance = haversine_distance(lat, lon, obj.latitude, obj.longitude)
            if distance <= radius_km:
                results.append((distance, obj))
        results.sort(key=lambda pair: pair[0])

        data = OSMTourismPlaceSerializer([o for _, o in results], many=True).data
        for item, (distance, _) in zip(data, results):
            item["distance_km"] = round(distance, 2)
        return Response(data)
