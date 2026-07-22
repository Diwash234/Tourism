"""
Endpoints that connect this Django backend to the teammate's ML
microservice (see /ml-service in the project root).

  OUTBOUND: backend -> ML service
    RecommendedDestinationsView calls ML_SERVICE_URL/recommend and maps
    the returned destination IDs back to full Destination records. If the
    ML service is down, it falls back to top-rated destinations instead of
    failing the request.

  INBOUND: ML service -> backend (webhook)
    MLResultWebhookView is what the ML service calls (with a shared-secret
    header) once it finishes analyzing something (e.g. a submitted photo),
    storing the result as an MLInsight row.
"""
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, MLInsight
from .serializers import (
    DestinationListSerializer,
    MLInsightSerializer,
    MLRecommendationRequestSerializer,
    MLWebhookResultSerializer,
    SafetyPredictionRequestSerializer,
    BudgetPredictionRequestSerializer,
    BestRouteRequestSerializer,
)
from .utils import get_ml_recommendations, get_ml_safety_prediction, get_ml_budget_prediction, get_ml_best_route


class RecommendedDestinationsView(APIView):
    """
    GET/POST /api/v1/ml/recommendations/
    Personalized "you might also like" results, powered by the ML service.
    Accepts optional latitude/longitude/top_n to bias recommendations by
    location (falls back to the user's saved profile location, then to
    simple top-rated destinations if the ML service can't be reached).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MLRecommendationRequestSerializer

    def post(self, request):
        serializer = MLRecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        lat = data.get("latitude")
        lon = data.get("longitude")
        if lat is None and request.user.is_authenticated:
            lat, lon = request.user.latitude, request.user.longitude

        recommendations = get_ml_recommendations(
            user=request.user, latitude=lat, longitude=lon, top_n=data["top_n"]
        )

        if recommendations:
            ordered_ids = [r["destination_id"] for r in recommendations]
            score_by_id = {r["destination_id"]: r.get("score") for r in recommendations}
            destinations = list(
                Destination.objects.filter(
                    id__in=ordered_ids, is_active=True, status=Destination.SubmissionStatus.APPROVED
                )
            )
            destinations.sort(key=lambda d: ordered_ids.index(d.id))
            source = "ml_service"
        else:
            # Graceful fallback so the endpoint still returns something
            # useful if the ML teammate's service isn't running.
            destinations = list(
                Destination.objects.filter(is_active=True, status=Destination.SubmissionStatus.APPROVED)
                .order_by("-average_rating")[: data["top_n"]]
            )
            score_by_id = {}
            source = "fallback_top_rated"

        context = {"request": request, "user_lat": lat, "user_lon": lon}
        results = DestinationListSerializer(destinations, many=True, context=context).data
        for item in results:
            item["ml_score"] = score_by_id.get(item["id"])

        return Response({"source": source, "results": results})


class MLResultWebhookView(APIView):
    """
    POST /api/v1/ml/results/
    Called BY the ML microservice once it finishes analyzing something.
    Protected with a shared secret (X-ML-Webhook-Secret header) rather than
    user JWT auth, since the caller is a backend service, not a person.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = MLWebhookResultSerializer

    def post(self, request):
        secret = request.headers.get("X-ML-Webhook-Secret")
        if secret != settings.ML_WEBHOOK_SECRET:
            return Response({"detail": "Invalid webhook secret."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = MLWebhookResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        destination = get_object_or_404(Destination, pk=data["destination_id"])
        insight = MLInsight.objects.create(
            destination=destination,
            insight_type=data["insight_type"],
            label=data.get("label", ""),
            score=data.get("score"),
            raw_result=data.get("raw_result", {}),
        )
        return Response(MLInsightSerializer(insight).data, status=status.HTTP_201_CREATED)


class SafetyPredictionView(APIView):
    """
    POST /api/v1/ml/safety/
    Proxies to the ML service's /predict-safety for a location risk score.
    Pass either `destination` (its own coordinates/city/country are used)
    or `latitude`/`longitude` directly. Returns 503 if the ML service is
    unreachable, so the frontend can show "safety info unavailable" instead
    of a wrong/stale score.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = SafetyPredictionRequestSerializer

    def post(self, request):
        serializer = SafetyPredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        destination = data.get("destination")
        if destination:
            lat, lon = destination.latitude, destination.longitude
            city, country = destination.city, destination.country
        else:
            lat, lon = data["latitude"], data["longitude"]
            city, country = None, None

        result = get_ml_safety_prediction(lat, lon, city, country)
        if result is None:
            return Response(
                {"detail": "Safety prediction service is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Cache it against the destination (if one was given) so it shows up
        # in admin / can be reused without re-calling the ML service.
        if destination:
            MLInsight.objects.create(
                destination=destination, insight_type=MLInsight.InsightType.CROWD_PREDICTION,
                label=result["risk_level"], score=result["safety_score"], raw_result=result,
            )

        return Response(result)


class BudgetPredictionView(APIView):
    """
    POST /api/v1/ml/budget/
    Proxies to the ML service's /predict-budget for an estimated trip cost.
    Pass either `destination` (its city/country are used) or `city`/`country`
    directly, plus `days`, `travelers`, and `budget_level`.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = BudgetPredictionRequestSerializer

    def post(self, request):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

        # Accept `style` as an alias for `budget_level` (BudgetEstimator.jsx
        # sends "style": "budget"|"standard"|"luxury" — map "standard" -> "mid").
        if "budget_level" not in data and "style" in data:
            data["budget_level"] = {"standard": "mid"}.get(data["style"], data["style"])

        # `destination` may be a real PK (int) OR free text like "Pokhara"
        # (BudgetEstimator.jsx sends the destination NAME, not an ID).
        # Resolve free text against real Destination rows; if no match,
        # just use it directly as the city so the estimate still runs.
        destination_value = data.get("destination")
        if destination_value and not str(destination_value).isdigit():
            from .models import Destination

            match = Destination.objects.filter(name__icontains=destination_value).first()
            if match:
                data["destination"] = match.id
            else:
                data.pop("destination", None)
                data.setdefault("city", destination_value)

        serializer = BudgetPredictionRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        destination = data.get("destination")
        city = destination.city if destination else data.get("city")
        country = destination.country if destination else data.get("country")

        result = get_ml_budget_prediction(
            city=city, country=country, days=data["days"],
            travelers=data["travelers"], budget_level=data["budget_level"],
        )
        if result is None:
            return Response(
                {"detail": "Budget prediction service is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Flatten so BudgetEstimator.jsx's `estimate.total` / `estimate.accommodation`
        # etc. work directly, while keeping the original nested shape too
        # (`estimated_total`, `breakdown`) for any other caller.
        flattened = dict(result)
        flattened["total"] = result["estimated_total"]
        flattened.update(result.get("breakdown", {}))
        return Response(flattened)


class BestRouteView(APIView):
    """
    POST /api/v1/ml/best-route/
    Proxies to the ML service's /best-route for a routed path (OSM-based
    once the ML teammate's road graph exists; straight-line fallback until
    then — same response shape either way). Pass `start_latitude`/
    `start_longitude` (always required — it's the tourist's current
    location) plus either `destination` (its coordinates are used) or
    `end_latitude`/`end_longitude` directly.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = BestRouteRequestSerializer

    def post(self, request):
        serializer = BestRouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        destination = data.get("destination")
        end_lat = destination.latitude if destination else data["end_latitude"]
        end_lon = destination.longitude if destination else data["end_longitude"]

        result = get_ml_best_route(data["start_latitude"], data["start_longitude"], end_lat, end_lon)
        if result is None:
            return Response(
                {"detail": "Routing service is currently unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(result)
