"""Public weather endpoint.

Returns real provider data or an explicit "unavailable" with a reason. It never
returns a substituted, averaged or invented reading, and it never 500s because
an upstream provider is down.
"""
from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .weather_service import fetch_weather, provider_config


class PublicWeatherView(APIView):
    """GET /api/v1/weather/?lat=27.7172&lon=85.3240&days=3

    Coordinates are optional: when omitted, the authenticated user's own stored
    position is used, and only if that position passed GPS validation.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat") or request.query_params.get("latitude")
        lon = request.query_params.get("lon") or request.query_params.get("longitude")
        source_note = "requested"

        if lat is None or lon is None:
            user = getattr(request, "user", None)
            if user is not None and getattr(user, "latitude", None) is not None:
                lat, lon = user.latitude, user.longitude
                source_note = "user_position"
            else:
                return Response(
                    {
                        "available": False,
                        "reason": "no_coordinates",
                        "detail": "Pass lat and lon, or sign in with a validated position.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            days = int(request.query_params.get("days", 3))
        except (TypeError, ValueError):
            days = 3

        result = fetch_weather(lat, lon, forecast_days=days)
        payload = result.as_dict()
        payload["coordinates_source"] = source_note
        if not payload["available"]:
            # An unreachable provider is a 200 with an honest payload, not a
            # 500: the rest of the page must still render.
            return Response(payload, status=status.HTTP_200_OK)
        return Response(payload, status=status.HTTP_200_OK)


class WeatherProviderStatusView(APIView):
    """Whether a weather provider is configured, without exposing its key."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        config = provider_config()
        return Response(
            {
                "configured": config["enabled"],
                "reason": config["reason"],
                "source": config["source"],
                "commercial_use_required": False,
                "note": (
                    "The default provider is Open-Meteo's free tier: non-commercial "
                    "use only. Commercial deployment needs a customer-prefixed URL and "
                    "an API key."
                ),
            }
        )
