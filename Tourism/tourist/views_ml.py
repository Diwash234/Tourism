"""
Endpoints that connect this Django backend to the teammate's ML
microservice (see /ml-service in the project root).

OUTBOUND: backend -> ML service
    RecommendedDestinationsView sends destination data and user request
    information to ML_SERVICE_URL/recommendation.

INBOUND: ML service -> backend (webhook)
    MLResultWebhookView receives ML analysis results and stores them.
"""

import requests

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
from .utils import (
    get_ml_safety_prediction,
    get_ml_budget_prediction,
    get_ml_best_route,
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
            "latitude": latitude,
            "longitude": longitude,
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
                {
                    "detail": "Safety prediction service unavailable."
                },
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


        result = get_ml_budget_prediction(
            city=city,
            country=country,
            days=data["days"],
            travelers=data["travelers"],
            budget_level=data["budget_level"],
        )


        if result is None:

            return Response(
                {
                    "detail": "Budget prediction service unavailable."
                },
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
