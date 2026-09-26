"""Traveller-facing official data: NRB exchange rates and entry/permit requirements."""

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import fx
from . import travel_requirements as tr
from .models import Destination


def _int(value, lo, hi):
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


class ForexRatesView(APIView):
    """GET /api/v1/fx/rates/ -- latest official NRB rates (never a fixed fallback)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        payload = fx.rates_payload()
        code = status.HTTP_200_OK if payload.get("available") else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response(payload, status=code)


class TravelRequirementsView(APIView):
    """GET /api/v1/travel-requirements/?nationality=foreign|saarc|chinese|nepali"""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(tr.general_requirements(request.query_params.get("nationality")))


class DestinationRequirementsView(APIView):
    """GET /api/v1/travel-requirements/destination/<id>/?nationality=&days=&month=&travelers="""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, pk):
        dest = get_object_or_404(Destination, pk=pk, status=Destination.SubmissionStatus.APPROVED, is_active=True)
        qp = request.query_params
        travelers = _int(qp.get("travelers"), 1, 50) or 1
        result = tr.destination_requirements(
            dest,
            nationality=qp.get("nationality"),
            days=_int(qp.get("days"), 1, 120),
            month=_int(qp.get("month"), 1, 12),
            travelers=travelers,
        )
        result["fee_totals"] = tr.fee_totals(result["fees"], travelers)
        return Response(result)
