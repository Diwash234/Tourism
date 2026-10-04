"""
ML-powered Risk Prediction API Views
"""
import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination
from .ml_risk import risk_predictor, get_route_risk_assessment
from .risk_service import build_destination_risk
from .schema_extensions import (
    RiskPredictionResponseSerializer,
    RiskRequestSerializer,
    RouteRiskRequestSerializer,
    RouteRiskResponseSerializer,
)

logger = logging.getLogger(__name__)


class RiskPredictionView(APIView):
    """
    POST /api/v1/ml/risk-prediction/
    
    Predicts risk scores for a destination for the next 7 days using ML.
    Uses historical incidents, seasonal patterns, current hazards, weather data, and trends.
    
    Request:
    {
        "destination_id": 123,  // or destination_slug
        "latitude": 27.7172,     // optional, uses destination coords if not provided
        "longitude": 85.3240,    // optional
        "days_ahead": 7          // optional, default 7
    }
    
    Response:
    {
        "destination_id": 123,
        "destination_name": "Pokhara",
        "base_score": 45.2,
        "trend": {"direction": "increasing", "change_pct": 15.0, "incidents_last_30d": 3},
        "predictions": [
            {"date": "2026-10-04", "day_name": "Sunday", "predicted_score": 48.5, "level": "moderate", "confidence": 0.82, "key_factors": [...]}
        ],
        "summary": "MODERATE: Average risk 47/100..."
    }
    """
    
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        operation_id="ml_risk_prediction",
        summary="Predict destination risk for the next N days",
        description=(
            "ML risk indicator for a destination. Weighted from verified "
            "historical incidents, traveler records, seasonal patterns and "
            "active observations. This is **not** an official DHM/BIPAD warning."
        ),
        request=RiskRequestSerializer,
        responses={
            200: RiskPredictionResponseSerializer,
            400: RiskPredictionResponseSerializer,
            404: RiskPredictionResponseSerializer,
        },
    )
    def post(self, request):
        destination_id = request.data.get("destination_id")
        destination_slug = request.data.get("destination_slug")
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")
        days_ahead = request.data.get("days_ahead", 7)
        
        destination = None
        
        if destination_id:
            destination = Destination.objects.filter(pk=destination_id).first()
        elif destination_slug:
            destination = Destination.publicly_visible().filter(slug=destination_slug).first()
        
        if not destination and latitude and longitude:
            # Find nearest destination
            destinations = Destination.publicly_visible().exclude(latitude=None).exclude(longitude=None)
            best = None
            best_dist = float('inf')
            for d in destinations:
                from .routing_service import haversine_distance_km
                dist = haversine_distance_km(latitude, longitude, float(d.latitude), float(d.longitude))
                if dist < best_dist:
                    best_dist = dist
                    best = d
            destination = best
        
        if not destination:
            return Response(
                {"detail": "Destination not found. Provide destination_id, destination_slug, or coordinates."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Use destination coordinates if not provided
        if latitude is None:
            latitude = float(destination.latitude) if destination.latitude else None
        if longitude is None:
            longitude = float(destination.longitude) if destination.longitude else None
        
        if latitude is None or longitude is None:
            return Response(
                {"detail": "Destination has no recorded coordinates for risk prediction."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get ML prediction
        prediction = risk_predictor.predict_risk(destination, days_ahead=days_ahead)
        
        # Add navigation-specific risk assessment
        nav_risk = build_destination_risk(destination)
        prediction["navigation_risk"] = nav_risk.get("navigation_risk", {})
        prediction["current_conditions"] = nav_risk.get("current_conditions", {})
        prediction["category_risk"] = nav_risk.get("category_risk", {})
        
        return Response(prediction)


class RouteRiskAssessmentView(APIView):
    """
    POST /api/v1/ml/route-risk/
    
    Assesses risk along a navigation route between two points.
    
    Request:
    {
        "origin_latitude": 27.7172,
        "origin_longitude": 85.3240,
        "destination_latitude": 28.2096,
        "destination_longitude": 83.9856,
        "destination_id": 123  // optional
    }
    
    Response:
    {
        "overall_score": 42.5,
        "warnings": ["High risk area - consider alternative routes"],
        "recommendations": ["Carry emergency supplies", "Check weather before departure"],
        "segment_risks": [
            {"segment": "Kathmandu to Dhading", "score": 35, "level": "moderate", "factors": [...]}
        ]
    }
    """
    
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        operation_id="ml_route_risk_assessment",
        summary="Assess risk along a route between two coordinates",
        description=(
            "Segments a route between two points and scores the hazard level of "
            "each segment. Advisory only; confirm conditions with DHM/BIPAD."
        ),
        request=RouteRiskRequestSerializer,
        responses={
            200: RouteRiskResponseSerializer,
            400: RouteRiskResponseSerializer,
        },
    )
    def post(self, request):
        origin_lat = request.data.get("origin_latitude")
        origin_lng = request.data.get("origin_longitude")
        dest_lat = request.data.get("destination_latitude")
        dest_lng = request.data.get("destination_longitude")
        destination_id = request.data.get("destination_id")
        
        if None in (origin_lat, origin_lng, dest_lat, dest_lng):
            return Response(
                {"detail": "origin_latitude, origin_longitude, destination_latitude, destination_longitude are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        destination = None
        if destination_id:
            destination = Destination.objects.filter(pk=destination_id).first()
        
        # Get destination risk if available
        dest_risk = None
        if destination:
            dest_risk = build_destination_risk(destination)
        
        # Get route risk assessment
        route_risk = get_route_risk_assessment(
            float(origin_lat), float(origin_lng),
            float(dest_lat), float(dest_lng),
            destination
        )
        
        # Add destination risk if available
        if dest_risk:
            route_risk["destination_risk"] = {
                "overall_score": dest_risk["overall"]["score"],
                "level": dest_risk["overall"]["level"],
                "navigation_risk": dest_risk["navigation_risk"],
                "current_conditions": dest_risk["current_conditions"],
            }
        
        return Response(route_risk)