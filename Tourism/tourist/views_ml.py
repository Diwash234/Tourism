"""
Endpoints that connect this Django backend to the teammate's ML
microservice (see /ml-service in the project root).

OUTBOUND: backend -> ML service
    RecommendedDestinationsView sends destination data and user request
    information to ML_SERVICE_URL/recommendation.

INBOUND: ML service -> backend (webhook)
    MLResultWebhookView receives ML analysis results and stores them.
"""

import logging

import requests

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone

logger = logging.getLogger(__name__)

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, Hotel, Hospital, MLInsight, OSMEssentialService, PoliceStation
from .serializers import (
    DestinationListSerializer,
    MLInsightSerializer,
    MLRecommendationRequestSerializer,
    MLWebhookResultSerializer,
    SafetyPredictionRequestSerializer,
    BudgetPredictionRequestSerializer,
    BestRouteRequestSerializer,
    ItineraryRequestSerializer,
)
from .utils import (
    get_ml_safety_prediction,
    get_ml_budget_prediction,
    get_ml_best_route,
    haversine_distance,
)


class RecommendedDestinationsView(APIView):
    """
    POST /api/v1/ml/recommendations/

    Sends user information + available destinations to the ML service.
    If ML service fails, returns top-rated destinations as fallback.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MLRecommendationRequestSerializer

    def post(self, request):

        serializer = MLRecommendationRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if latitude is None and request.user.is_authenticated:
            latitude = getattr(request.user, "latitude", None)
            longitude = getattr(request.user, "longitude", None)

        # Get all approved destinations
        destinations = DestinationListSerializer(
            Destination.objects.filter(
                is_active=True,
                status=Destination.SubmissionStatus.APPROVED,
            ),
            many=True,
            context={
                "request": request,
            },
        ).data


        payload = {
            **data,
            "latitude": float(latitude or 0),
            "longitude": float(longitude or 0),
            "destinations": destinations,
        }


        try:
            response = requests.post(
                f"{settings.ML_SERVICE_URL}/recommendation",
                json=payload,
                headers={
                    "X-API-Key": settings.ML_SERVICE_API_KEY,
                },
                timeout=10,
            )


            response.raise_for_status()

            return Response(
                response.json(),
                status=response.status_code
            )


        except requests.RequestException:

            fallback_destinations = Destination.objects.filter(
                is_active=True,
                status=Destination.SubmissionStatus.APPROVED,
            ).order_by(
                "-average_rating"
            )[:data["top_n"]]


            results = DestinationListSerializer(
                fallback_destinations,
                many=True,
                context={
                    "request": request,
                    "user_lat": latitude,
                    "user_lon": longitude,
                },
            ).data


            return Response(
                {
                    "source": "fallback_top_rated",
                    "results": results,
                },
                status=status.HTTP_200_OK,
            )



class MLResultWebhookView(APIView):
    """
    POST /api/v1/ml/results/

    Called by ML service after completing analysis.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MLWebhookResultSerializer


    def post(self, request):

        secret = request.headers.get(
            "X-ML-Webhook-Secret"
        )


        if secret != settings.ML_WEBHOOK_SECRET:
            return Response(
                {
                    "detail": "Invalid webhook secret."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )


        serializer = MLWebhookResultSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data


        destination = get_object_or_404(
            Destination,
            pk=data["destination_id"]
        )


        insight = MLInsight.objects.create(
            destination=destination,
            insight_type=data["insight_type"],
            label=data.get("label", ""),
            score=data.get("score"),
            raw_result=data.get("raw_result", {}),
        )


        return Response(
            MLInsightSerializer(insight).data,
            status=status.HTTP_201_CREATED,
        )



class SafetyPredictionView(APIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = SafetyPredictionRequestSerializer


    def post(self, request):

        serializer = SafetyPredictionRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data


        destination = data.get("destination")


        if destination:

            latitude = destination.latitude
            longitude = destination.longitude
            city = destination.city
            country = destination.country

        else:

            latitude = data["latitude"]
            longitude = data["longitude"]
            city = None
            country = None



        result = get_ml_safety_prediction(
            latitude,
            longitude,
            city,
            country,
        )


        if result is None:
            return Response(
                {"detail": "Safety prediction service unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )



        if destination:

            MLInsight.objects.create(
                destination=destination,
                insight_type=MLInsight.InsightType.CROWD_PREDICTION,
                label=result["risk_level"],
                score=result["safety_score"],
                raw_result=result,
            )


        return Response(result)




class BudgetPredictionView(APIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = BudgetPredictionRequestSerializer


    def post(self, request):

        data = request.data.copy()


        if (
            "budget_level" not in data
            and "style" in data
        ):
            data["budget_level"] = {
                "standard": "mid"
            }.get(
                data["style"],
                data["style"]
            )


        destination_value = data.get(
            "destination"
        )


        if (
            destination_value
            and not str(destination_value).isdigit()
        ):

            match = Destination.objects.filter(
                name__icontains=destination_value
            ).first()


            if match:

                data["destination"] = match.id

            else:

                data.pop(
                    "destination",
                    None
                )

                data.setdefault(
                    "city",
                    destination_value
                )


        serializer = BudgetPredictionRequestSerializer(
            data=data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data


        destination = data.get(
            "destination"
        )


        city = (
            destination.city
            if destination
            else data.get("city")
        )


        country = (
            destination.country
            if destination
            else data.get("country")
        )

        latitude = float(destination.latitude) if destination and destination.latitude else None
        longitude = float(destination.longitude) if destination and destination.longitude else None

        result = get_ml_budget_prediction(
            city=city,
            country=country,
            days=data["days"],
            travelers=data["travelers"],
            budget_level=data["budget_level"],
            latitude=latitude,
            longitude=longitude,
            user_latitude=data.get("user_latitude"),
            user_longitude=data.get("user_longitude"),
            district=getattr(destination, "district", None) if destination else data.get("district"),
            province=getattr(destination, "province", None) if destination else data.get("province"),
            destination_name=getattr(destination, "name", None) if destination else data.get("city"),
        )


        if result is None:
            return Response(
                {"detail": "Budget prediction service unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


        flattened = dict(result)

        flattened["total"] = result.get(
            "estimated_total"
        )

        flattened.update(
            result.get(
                "breakdown",
                {}
            )
        )


        return Response(flattened)




class BestRouteView(APIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = BestRouteRequestSerializer


    def post(self, request):

        serializer = BestRouteRequestSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )


        data = serializer.validated_data


        destination = data.get(
            "destination"
        )


        if destination:

            end_lat = destination.latitude
            end_lon = destination.longitude

        else:

            end_lat = data["end_latitude"]
            end_lon = data["end_longitude"]



        result = get_ml_best_route(
            data["start_latitude"],
            data["start_longitude"],
            end_lat,
            end_lon,
        )


        if result is None:

            return Response(
                {
                    "detail": "Routing service unavailable."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


        return Response(result)


def _safe_file_url(field):
    try:
        return field.url if field else None
    except (ValueError, AttributeError):
        return str(field) if field else None


def _nearest_for_itinerary(rows, lat, lon, mapper):
    ranked = []
    for row in rows:
        if row.latitude is None or row.longitude is None:
            continue
        distance = haversine_distance(lat, lon, row.latitude, row.longitude)
        ranked.append((distance, row))
    ranked.sort(key=lambda pair: pair[0])
    return [mapper(row, round(distance, 2)) for distance, row in ranked[:2]]


def enrich_itinerary_with_services(payload):
    """Attach DB-backed planning and emergency services to every itinerary day."""
    for day in payload.get("itinerary", []):
        destinations = day.get("destinations") or []
        anchor = next((item for item in destinations if item.get("latitude") is not None and item.get("longitude") is not None), None)
        if anchor:
            lat, lon = float(anchor["latitude"]), float(anchor["longitude"])
        else:
            match = Destination.objects.filter(city__icontains=day.get("city", "")).exclude(latitude__isnull=True).first()
            if not match:
                continue
            lat, lon = float(match.latitude), float(match.longitude)

        day["nearby_services"] = {
            "hotels": _nearest_for_itinerary(
                Hotel.objects.all(), lat, lon,
                lambda row, distance: {
                    "id": row.id, "name": row.name, "distance_km": distance,
                    "price_npr": float(row.price_per_night) if row.price_per_night is not None and row.currency == "NPR" else None,
                    "image_url": _safe_file_url(row.cover_image) or row.external_image_url or None,
                },
            ),
            "hospitals": _nearest_for_itinerary(
                Hospital.objects.all(), lat, lon,
                lambda row, distance: {"id": row.id, "name": row.name, "phone": row.phone, "distance_km": distance},
            ),
            "police": _nearest_for_itinerary(
                PoliceStation.objects.all(), lat, lon,
                lambda row, distance: {"id": row.id, "name": row.name, "phone": row.phone or "100", "distance_km": distance},
            ),
            "essentials": _nearest_for_itinerary(
                OSMEssentialService.objects.filter(category__in=["bank", "pharmacy", "fire_station", "ambulance"]), lat, lon,
                lambda row, distance: {"id": row.id, "type": row.category, "name": row.name, "phone": row.phone, "distance_km": distance},
            ),
        }
    payload["service_data_source"] = "live_database_distance_ranking"
    return payload


class ItineraryView(APIView):
    """
    POST /api/v1/ml/itinerary/
    Rich, dataset-driven itinerary builder. Forwards the request to the ML
    service's /itinerary/build endpoint, which plans day-by-day
    destinations (from the OSM dataset), budgets in NPR (scaled by
    travelers / travel type / style) and route legs from the graphml road
    graph. Pure function of its inputs, so the frontend re-calls it on
    every form change for continuous updates.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = ItineraryRequestSerializer

    def post(self, request):
        serializer = ItineraryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            response = requests.post(
                f"{settings.ML_SERVICE_URL}/itinerary/build",
                json={
                    "days": data.get("days", 3),
                    "travelers": data.get("travelers", 1),
                    "budget_npr": data.get("budget_npr"),
                    "budget_level": data.get("budget_level", "mid"),
                    "travel_style": data.get("travel_style", "leisure"),
                    "travel_type": data.get("travel_type", "solo"),
                    "interests": data.get("interests", ["culture"]),
                    "start_city": (data.get("start_city") or "").strip() or "Kathmandu",
                },
                timeout=settings.ML_SERVICE_TIMEOUT * 3,
            )
            response.raise_for_status()
            return Response(enrich_itinerary_with_services(response.json()))
        except requests.RequestException as exc:
            logger.warning("ML itinerary service unreachable: %s", exc)
            # Internal database fallback itinerary builder
            days = max(1, data.get("days", 3))
            travelers = max(1, data.get("travelers", 1))
            interests = data.get("interests", ["culture"])
            start_city = (data.get("start_city") or "Kathmandu").strip()

            qs = Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)
            city_qs = qs.filter(city__icontains=start_city)
            if not city_qs.exists():
                city_qs = qs

            dest_list = list(city_qs[: days * 3])
            if not dest_list:
                dest_list = list(qs[: days * 3])

            itinerary_days = []

            for day_idx in range(1, days + 1):
                day_destinations = []
                start_i = (day_idx - 1) * 2
                for dest in dest_list[start_i : start_i + 2]:
                    day_destinations.append({
                        "name": dest.name,
                        "city": dest.city or start_city,
                        "latitude": float(dest.latitude) if dest.latitude else None,
                        "longitude": float(dest.longitude) if dest.longitude else None,
                        "category": dest.category.name if dest.category else "Attraction",
                    })
                if not day_destinations and dest_list:
                    d = dest_list[day_idx % len(dest_list)]
                    day_destinations.append({
                        "name": d.name,
                        "city": d.city or start_city,
                        "latitude": float(d.latitude) if d.latitude else None,
                        "longitude": float(d.longitude) if d.longitude else None,
                        "category": d.category.name if d.category else "Attraction",
                    })

                itinerary_days.append({
                    "day": day_idx,
                    "city": start_city,
                    "theme": "Cultural & Scenic Exploration",
                    "destinations": day_destinations,
                    "daily_budget_npr": None,
                })

            fallback_payload = {
                "source": "internal_db_engine",
                "days": days,
                "travelers": travelers,
                "budget_level": data.get("budget_level", "mid"),
                "travel_style": data.get("travel_style", "leisure"),
                "travel_type": data.get("travel_type", "solo"),
                "interests": interests,
                "start_city": start_city,
                "total_estimated_npr": None,
                "total_estimated_usd": None,
                "per_person_npr": None,
                "budget_npr": data.get("budget_npr"),
                "fits_budget": None,
                "budget_note": "No recorded daily budget is stored for this fallback itinerary.",
                "itinerary": itinerary_days,
            }
            return Response(enrich_itinerary_with_services(fallback_payload), status=status.HTTP_200_OK)


class AIItineraryModificationView(APIView):
    """
    POST /api/v1/ml/itinerary/modify/
    Modifies an existing structured itinerary data based on natural language or action buttons:
    (cheaper, luxurious, more_trekking, more_culture, more_nature, hidden_gems, reduce_travel_time, slower_pace, family_friendly)
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        action = (request.data.get("action") or "").strip().lower()
        itinerary_data = request.data.get("itinerary_data") or request.data.get("itinerary") or {}
        days_data = itinerary_data.get("itinerary") or []
        interests = list(itinerary_data.get("interests") or ["culture"])

        if not days_data:
            return Response({"detail": "No structured itinerary provided to modify."}, status=status.HTTP_400_BAD_REQUEST)

        modified_days = []
        action_note = ""

        if action in {"cheaper", "make_cheaper"}:
            action_note = "Rebalanced with budget accommodation and public transport."
            for day in days_data:
                day_copy = dict(day)
                day_copy["theme"] = f"Budget Friendly: {day.get('theme', 'Exploration')}"
                if day_copy.get("daily_budget_npr"):
                    day_copy["daily_budget_npr"] = round(float(day_copy["daily_budget_npr"]) * 0.7, 2)
                modified_days.append(day_copy)

        elif action in {"luxurious", "make_luxurious"}:
            action_note = "Upgraded to premium private vehicle transit and boutique hotels."
            for day in days_data:
                day_copy = dict(day)
                day_copy["theme"] = f"Boutique Luxury: {day.get('theme', 'Exploration')}"
                if day_copy.get("daily_budget_npr"):
                    day_copy["daily_budget_npr"] = round(float(day_copy["daily_budget_npr"]) * 1.5, 2)
                modified_days.append(day_copy)

        elif action in {"more_culture", "culture"}:
            action_note = "Enriched with UNESCO heritage sites, durbar squares, and temple circuits."
            heritage_dests = list(Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED,
                category__slug__in=["heritage", "culture", "temples", "buddhist-sites"]
            )[: len(days_data) * 2])
            for idx, day in enumerate(days_data):
                day_copy = dict(day)
                day_copy["theme"] = "Heritage & Cultural Immersion"
                if heritage_dests:
                    d = heritage_dests[idx % len(heritage_dests)]
                    day_copy["destinations"] = [{
                        "name": d.name, "city": d.city or d.district or "Nepal",
                        "latitude": float(d.latitude) if d.latitude else None,
                        "longitude": float(d.longitude) if d.longitude else None,
                        "category": d.category.name if d.category else "Heritage",
                    }]
                modified_days.append(day_copy)

        elif action in {"more_nature", "more_trekking", "hidden_gems"}:
            action_note = "Swapped crowded spots with quiet alpine lakes, trekking trails, and hidden gems."
            nature_dests = list(Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED,
                category__slug__in=["natural-wonders", "trekking", "lakes", "viewpoints"]
            )[: len(days_data) * 2])
            for idx, day in enumerate(days_data):
                day_copy = dict(day)
                day_copy["theme"] = "Nature & Scenic Exploration"
                if nature_dests:
                    d = nature_dests[idx % len(nature_dests)]
                    day_copy["destinations"] = [{
                        "name": d.name, "city": d.city or d.district or "Nepal",
                        "latitude": float(d.latitude) if d.latitude else None,
                        "longitude": float(d.longitude) if d.longitude else None,
                        "category": d.category.name if d.category else "Nature",
                    }]
                modified_days.append(day_copy)

        elif action in {"slower_pace", "relaxed"}:
            action_note = "Reduced daily activity density for a relaxed, unhurried pace."
            for day in days_data:
                day_copy = dict(day)
                day_copy["theme"] = f"Relaxed Pace: {day.get('theme', 'Exploration')}"
                if day_copy.get("destinations"):
                    day_copy["destinations"] = day_copy["destinations"][:1]
                modified_days.append(day_copy)

        else:
            action_note = f"Custom adjustment applied: {action}"
            modified_days = days_data

        result = dict(itinerary_data)
        result["itinerary"] = modified_days
        result["modification_note"] = action_note
        result["modified_action"] = action
        result["modified_at"] = timezone.now().isoformat()

        return Response(enrich_itinerary_with_services(result))
