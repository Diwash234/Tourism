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
    serializer_class = None
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


import json
from pathlib import Path
from django.conf import settings
from .serializers import public_destination_cover
from .views_ml import _with_readiness, enrich_itinerary_with_services
from .curated_planning import (
    calculate_cost_breakdown,
    calculate_altitude_safety,
    compare_curated_itineraries,
    generate_packing_checklist,
)


CURATED_DATA_FILE = Path(settings.BASE_DIR) / "dataset" / "curated_itineraries.json"


def _load_curated_data():
    if not CURATED_DATA_FILE.exists():
        return []
    try:
        with open(CURATED_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


class CuratedItineraryListView(APIView):
    """
    GET /api/v1/curated-itineraries/
    Public curated itineraries tailored for Foreign, Domestic Nepali, and SAARC travelers.
    Query params: persona (nepali|foreign|saarc|all), category, days, q
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        items = _load_curated_data()
        persona = (request.query_params.get("persona") or "").strip().lower()
        category = (request.query_params.get("category") or "").strip().lower()
        days_param = request.query_params.get("days")
        query = (request.query_params.get("q") or "").strip().lower()

        results = []
        for it in items:
            it_persona = it.get("persona", "all")
            if persona and persona != "all":
                if persona == "nepali" and it_persona not in ("nepali", "all"):
                    continue
                elif persona == "foreign" and it_persona not in ("foreign", "all"):
                    continue
                elif persona == "saarc" and it_persona not in ("saarc", "all"):
                    continue
            if category and category != "all" and it.get("category") != category:
                continue
            if days_param:
                try:
                    d_int = int(days_param)
                    if it.get("days") != d_int and it.get("days") > d_int:
                        continue
                except ValueError:
                    pass
            if query:
                haystack = f"{it.get('title','')} {it.get('title_nepali','')} {it.get('summary','')} {it.get('summary_nepali','')} {it.get('category','')} {it.get('start_city','')} {it.get('end_city','')}".lower()
                if query not in haystack:
                    continue

            results.append({
                "slug": it["slug"],
                "title": it["title"],
                "title_nepali": it.get("title_nepali", ""),
                "persona": it.get("persona", "all"),
                "persona_label": "Nepalese Domestic Explorer" if it.get("persona") == "nepali" else ("International Traveler" if it.get("persona") == "foreign" else "All Travelers"),
                "category": it.get("category", "trekking"),
                "days": it.get("days", 3),
                "difficulty": it.get("difficulty", "moderate"),
                "start_city": it.get("start_city", "Kathmandu"),
                "end_city": it.get("end_city", "Kathmandu"),
                "best_seasons": it.get("best_seasons", []),
                "max_elevation_m": it.get("max_elevation_m"),
                "estimated_budget_npr": it.get("estimated_budget_npr"),
                "estimated_budget_usd": it.get("estimated_budget_usd"),
                "cover_image": it.get("cover_image", ""),
                "summary": it.get("summary", ""),
                "summary_nepali": it.get("summary_nepali", ""),
                "highlights": it.get("highlights", []),
                "highlights_nepali": it.get("highlights_nepali", []),
                "permits_info": it.get("permits_info", {}),
                "transport_info": it.get("transport_info", ""),
                "local_food_recommendations": it.get("local_food_recommendations", ""),
                "stops_count": len(it.get("days_schedule", [])),
            })

        return Response({
            "count": len(results),
            "results": results,
            "meta": {
                "categories": ["trekking", "pilgrimage", "heritage", "wildlife", "weekend", "adventure"],
                "personas": [
                    {"key": "all", "label": "All Travelers (सबैका लागि)"},
                    {"key": "nepali", "label": "Nepali Domestic Explorer (नेपाली आन्तरिक पर्यटक)"},
                    {"key": "foreign", "label": "International Explorer (विदेशी पर्यटक)"},
                    {"key": "saarc", "label": "SAARC National (सार्क देशहरू)"},
                ]
            }
        })


class CuratedItineraryDetailView(APIView):
    """
    GET /api/v1/curated-itineraries/<slug>/
    Returns full day-by-day curated itinerary.
    If ?format=planner is passed, formats into the full interactive planner schema
    ready to display in the frontend Travel Planner with altitude profile, maps,
    hospitals, police stations, hotels and permits checklist.
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        items = _load_curated_data()
        target = next((it for it in items if it.get("slug") == slug), None)
        if not target:
            return Response({"detail": "Curated itinerary not found."}, status=status.HTTP_404_NOT_FOUND)

        travelers = max(1, int(request.query_params.get("travelers", 1)))
        nationality = request.query_params.get("nationality", target.get("persona", "foreign"))
        if nationality not in ("foreign", "saarc", "chinese", "nepali"):
            nationality = "foreign" if target.get("persona") == "foreign" else ("nepali" if target.get("persona") == "nepali" else "foreign")
        style = request.query_params.get("style", "standard")

        cost_breakdown = calculate_cost_breakdown(target, nationality=nationality, style=style, travelers=travelers)
        altitude_safety = calculate_altitude_safety(target)
        packing_detailed = generate_packing_checklist(target)

        mode = request.query_params.get("mode") or request.query_params.get("schema") or request.query_params.get("as")
        if mode != "planner":
            enriched_raw = dict(target)
            enriched_raw["cost_breakdown"] = cost_breakdown
            enriched_raw["altitude_safety"] = altitude_safety
            enriched_raw["packing_checklist_detailed"] = packing_detailed
            return Response(enriched_raw)

        days_schedule = target.get("days_schedule", [])
        itinerary_days = []
        dest_cache = {}

        total_distance_km = 0.0
        for day_item in days_schedule:
            dest_name = day_item.get("destination_name", "")
            dest_obj = None
            if dest_name:
                if dest_name not in dest_cache:
                    dest_obj = (
                        Destination.publicly_visible().filter(name__icontains=dest_name).first()
                        or Destination.publicly_visible().filter(name__icontains=dest_name.split()[0]).first()
                    )
                    dest_cache[dest_name] = dest_obj
                else:
                    dest_obj = dest_cache[dest_name]

            dest_data = {
                "id": dest_obj.id if dest_obj else None,
                "name": dest_name,
                "city": dest_obj.city if dest_obj else target.get("start_city"),
                "district": dest_obj.district if dest_obj else "",
                "latitude": float(dest_obj.latitude) if dest_obj and dest_obj.latitude else None,
                "longitude": float(dest_obj.longitude) if dest_obj and dest_obj.longitude else None,
                "elevation_m": day_item.get("elevation_m") or (dest_obj.elevation_m if dest_obj else None),
                "cover_image_url": public_destination_cover(dest_obj, request) if dest_obj else target.get("cover_image"),
                "short_description": day_item.get("activity") or (dest_obj.short_description if dest_obj else ""),
            }

            dist = float(day_item.get("distance_km") or 0.0)
            total_distance_km += dist

            daily_budget = round(float(target.get("estimated_budget_npr") or 10000) / max(1, target.get("days", 1)))

            itinerary_days.append({
                "day_number": day_item.get("day_number", 1),
                "day": day_item.get("day_number", 1),
                "title": day_item.get("title", f"Day {day_item.get('day_number')}"),
                "city": dest_data["city"],
                "destinations": [dest_data],
                "daily_budget_npr": daily_budget,
                "activity": day_item.get("activity", ""),
                "stay": day_item.get("stay", ""),
                "legs": [
                    {
                        "from": "Start",
                        "to": dest_name,
                        "distance_km": dist,
                        "duration_min": round(dist * 2.5),
                        "mode": "surface / trek",
                    }
                ] if dist > 0 else [],
            })

        total_budget_npr = target.get("estimated_budget_npr", 25000) * travelers
        total_budget_usd = target.get("estimated_budget_usd", 190) * travelers

        plan_payload = {
            "title": target["title"],
            "title_nepali": target.get("title_nepali", ""),
            "days": target.get("days", len(days_schedule)),
            "travelers": travelers,
            "nationality": nationality,
            "persona": target.get("persona", "all"),
            "category": target.get("category", "trekking"),
            "total_budget_npr": total_budget_npr,
            "total_estimated_npr": total_budget_npr,
            "total_estimated_usd": total_budget_usd,
            "estimated_budget_npr": total_budget_npr,
            "estimated_budget_usd": total_budget_usd,
            "total_distance_km": round(total_distance_km, 1),
            "cover_image": target.get("cover_image", ""),
            "summary": target.get("summary", ""),
            "highlights": target.get("highlights", []),
            "permits_info": target.get("permits_info", {}),
            "transport_info": target.get("transport_info", ""),
            "local_food_recommendations": target.get("local_food_recommendations", ""),
            "packing_checklist": target.get("packing_checklist", []),
            "itinerary": itinerary_days,
            "source": "curated_master_catalog",
            "why_this_itinerary": [
                f"Curated signature itinerary for {target['title']} with certified Nepal route milestones.",
                f"Sourced elevation profiles ({target.get('max_elevation_m', 'High')}m maximum altitude) and safety intervals.",
                "Permits and fees calculated from Department of Immigration and Nepal Tourism Board official rate schedules.",
            ],
        }

        # Enrich with live nearest emergency services (hospitals, police, hotels)
        plan_payload = enrich_itinerary_with_services(plan_payload)

        # Enrich with trip readiness (acclimatization checks, permits, readiness checklist)
        month_param = request.query_params.get("travel_month")
        plan_payload = _with_readiness(
            plan_payload,
            {"nationality": nationality, "travel_month": int(month_param) if month_param and month_param.isdigit() else None}
        )

        plan_payload["cost_breakdown"] = cost_breakdown
        plan_payload["altitude_safety"] = altitude_safety
        plan_payload["packing_checklist_detailed"] = packing_detailed

        return Response(plan_payload)


class CuratedItineraryCompareView(APIView):
    """
    GET /api/v1/curated-itineraries/compare/?slugs=slug1,slug2&nationality=nepali&style=standard&travelers=1
    Returns side-by-side comparative matrix of up to 4 curated itineraries.
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        items = _load_curated_data()
        slugs_param = request.query_params.get("slugs", "").strip()
        if slugs_param:
            req_slugs = [s.strip() for s in slugs_param.split(",") if s.strip()][:4]
            matched = [it for it in items if it.get("slug") in req_slugs]
        else:
            # Default to comparing top 2 signature itineraries
            matched = items[:2] if len(items) >= 2 else items

        if not matched:
            return Response({"detail": "No matching itineraries found for comparison."}, status=status.HTTP_404_NOT_FOUND)

        nationality = request.query_params.get("nationality", "nepali")
        style = request.query_params.get("style", "standard")
        travelers = max(1, int(request.query_params.get("travelers", 1)))

        matrix = compare_curated_itineraries(matched, nationality=nationality, style=style, travelers=travelers)
        return Response(matrix)


class CuratedItinerarySafetyView(APIView):
    """
    GET /api/v1/curated-itineraries/<slug>/safety/
    Returns high-altitude risk evaluation, Lake Louise AMS rubric, and emergency rescue directory.
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        items = _load_curated_data()
        target = next((it for it in items if it.get("slug") == slug), None)
        if not target:
            return Response({"detail": "Curated itinerary not found."}, status=status.HTTP_404_NOT_FOUND)
        safety = calculate_altitude_safety(target)
        return Response({
            "slug": target["slug"],
            "title": target["title"],
            "title_nepali": target.get("title_nepali", ""),
            "safety": safety,
        })


class CuratedItineraryPackingView(APIView):
    """
    GET /api/v1/curated-itineraries/<slug>/packing/
    Returns structured gear checklist and local gear rental guidance (Kathmandu & Pokhara).
    """
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        items = _load_curated_data()
        target = next((it for it in items if it.get("slug") == slug), None)
        if not target:
            return Response({"detail": "Curated itinerary not found."}, status=status.HTTP_404_NOT_FOUND)
        packing = generate_packing_checklist(target)
        return Response({
            "slug": target["slug"],
            "title": target["title"],
            "title_nepali": target.get("title_nepali", ""),
            "packing": packing,
        })


class City15DayItineraryListView(APIView):
    """Public index of the additive 200-city, 15-day planner."""
    # This view assembles its response from CITY_CATALOG rather than a model, so
    # there is no serializer to infer. Declaring it explicitly stops
    # drf-spectacular logging "unable to guess serializer" and dropping the
    # operation from the OpenAPI document. Matches the other curated-* views.
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from .city_15_day_planner import CITY_CATALOG
        return Response({
            "count": len(CITY_CATALOG), "days": 15, "cities": CITY_CATALOG,
            "data_policy": "Existing curated itineraries and database records are preserved; missing facts are never invented.",
        })


class City15DayItineraryDetailView(APIView):
    """Build one 15-day city plan from the project's real database records."""
    # See City15DayItineraryListView: response is a hand-built dict, so declare
    # the absence of a serializer rather than letting spectacular guess and warn.
    serializer_class = None
    permission_classes = [permissions.AllowAny]

    def get(self, request, city):
        from .city_15_day_planner import build_city_15_day
        payload = build_city_15_day(city, request=request)
        if payload is None:
            return Response({"detail": "City is not in the 200-city planning catalog."}, status=status.HTTP_404_NOT_FOUND)
        return Response(payload)
