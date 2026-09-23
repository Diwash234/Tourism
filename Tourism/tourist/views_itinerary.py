"""
Tourism/tourist/views_itinerary.py
"""
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Itinerary, ItineraryDay, ItineraryStop, Destination, Category
from .serializers_itinerary import ItinerarySerializer, ItineraryCreateSerializer
from .utils import haversine_distance


class ItineraryViewSet(viewsets.ModelViewSet):
    """
    Standard CRUD, scoped to the logged-in user's own itineraries.
    Create uses ItineraryCreateSerializer's flat shape; everything else
    (list/retrieve/update/delete) uses the nested ItinerarySerializer.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Itinerary.objects.none()
        return Itinerary.objects.filter(user=self.request.user).prefetch_related("days__stops__destination")

    def get_serializer_class(self):
        if self.action == "create":
            return ItineraryCreateSerializer
        return ItinerarySerializer

    def create(self, request, *args, **kwargs):
        serializer = ItineraryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        destinations = list(Destination.objects.filter(id__in=data["destination_ids"]))
        # Preserve the order the frontend sent them in (the ID filter
        # above doesn't guarantee order) -- the frontend's ordering is
        # the user's chosen visit order.
        destinations.sort(key=lambda d: data["destination_ids"].index(d.id))

        itinerary = Itinerary.objects.create(
            user=request.user,
            title=data.get("title") or f"{destinations[0].name} trip",
            num_days=data["num_days"],
            start_date=data.get("start_date"),
        )
        if data.get("category_ids"):
            itinerary.category_filter.set(Category.objects.filter(id__in=data["category_ids"]))

        # Distribute destinations across days as evenly as possible, same
        # spirit as ml_service's itinerary_service.py, but this version
        # actually PERSISTS the result and computes REAL distances
        # (haversine between consecutive stops -- straight-line, not a
        # routed path; deliberately not calling ml_service's graph-based
        # route engine per-pair here, since that's a heavier synchronous
        # call multiplied by every consecutive stop pair in the whole
        # trip -- straight-line distance is a fast, always-available
        # approximation for trip-planning purposes. If you want routed
        # distances specifically, that's a scoped follow-up, not a
        # silent shortcut here).
        num_days = data["num_days"]
        per_day = max(1, len(destinations) // num_days)
        idx = 0
        total_distance = 0.0
        previous_stop_destination = None

        for day_num in range(1, num_days + 1):
            day_destinations = destinations[idx: idx + per_day]
            if day_num == num_days:
                day_destinations = destinations[idx:]
            idx += per_day
            if not day_destinations:
                break

            day = ItineraryDay.objects.create(itinerary=itinerary, day_number=day_num)

            for order, destination in enumerate(day_destinations):
                distance = None
                if previous_stop_destination and destination.latitude and destination.longitude and \
                   previous_stop_destination.latitude and previous_stop_destination.longitude:
                    distance = haversine_distance(
                        float(previous_stop_destination.latitude), float(previous_stop_destination.longitude),
                        float(destination.latitude), float(destination.longitude),
                    )
                    total_distance += distance

                ItineraryStop.objects.create(
                    day=day, destination=destination, order=order,
                    distance_from_previous_km=round(distance, 2) if distance is not None else None,
                )
                previous_stop_destination = destination

        itinerary.total_distance_km = round(total_distance, 2)
        itinerary.save(update_fields=["total_distance_km"])

        return Response(ItinerarySerializer(itinerary).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def advance_status(self, request, pk=None):
        """
        POST /itineraries/{id}/advance-status/
        Moves the itinerary one step through planning -> confirmed ->
        in_progress -> completed. This IS the "plan to execution"
        progression at the itinerary level (per-stop progression is
        ItineraryStopViewSet.visit below).
        """
        itinerary = self.get_object()
        order = [Itinerary.Status.PLANNING, Itinerary.Status.CONFIRMED,
                  Itinerary.Status.IN_PROGRESS, Itinerary.Status.COMPLETED]
        try:
            next_index = order.index(itinerary.status) + 1
        except ValueError:
            return Response({"detail": "Cancelled itineraries can't be advanced."}, status=400)

        if next_index >= len(order):
            return Response({"detail": "Already completed."}, status=400)

        itinerary.status = order[next_index]
        itinerary.save(update_fields=["status"])
        return Response(ItinerarySerializer(itinerary).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        itinerary = self.get_object()
        itinerary.status = Itinerary.Status.CANCELLED
        itinerary.save(update_fields=["status"])
        return Response(ItinerarySerializer(itinerary).data)


class ItineraryStopVisitView(APIView):
    """
    POST /itinerary-stops/{id}/visit/
    The actual per-stop execution tracking -- marks a single stop as
    visited as the trip actually happens, independent of the overall
    itinerary status above.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        stop = ItineraryStop.objects.filter(id=pk, day__itinerary__user=request.user).first()
        if not stop:
            return Response({"detail": "Not found."}, status=404)

        stop.is_visited = True
        stop.visited_at = timezone.now()
        stop.save(update_fields=["is_visited", "visited_at"])

        # If every stop in the itinerary is now visited, auto-advance to
        # completed -- the execution progress driving the plan's status,
        # not just a manual button.
        itinerary = stop.day.itinerary
        all_stops = ItineraryStop.objects.filter(day__itinerary=itinerary)
        if all_stops.exists() and not all_stops.filter(is_visited=False).exists():
            itinerary.status = Itinerary.Status.COMPLETED
            itinerary.save(update_fields=["status"])

        from .serializers_itinerary import ItineraryStopSerializer
        return Response(ItineraryStopSerializer(stop).data)