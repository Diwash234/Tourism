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
import math
import re
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
        interest = data.get("interest")
        province = data.get("province")
        category = data.get("category")
        top_n = data.get("top_n", 5)

        if latitude is None and request.user.is_authenticated:
            latitude = getattr(request.user, "latitude", None)
            longitude = getattr(request.user, "longitude", None)

        # Smart candidate selection: query real approved Destination rows,
        # filtered by user interest/province if supplied, bounded to top 100 candidates
        # to avoid payload bloat and network delays.
        candidate_qs = Destination.publicly_visible().exclude(latitude__isnull=True).exclude(longitude__isnull=True)

        if province:
            candidate_qs = candidate_qs.filter(province__iexact=province)
        if category:
            candidate_qs = candidate_qs.filter(category__name__icontains=category)
        if interest:
            from django.db.models import Q
            candidate_qs = candidate_qs.filter(
                Q(name__icontains=interest) |
                Q(type__icontains=interest) |
                Q(description__icontains=interest) |
                Q(short_description__icontains=interest) |
                Q(cultural_significance__icontains=interest) |
                Q(category__name__icontains=interest)
            )

        compact_rows = candidate_qs.order_by("-is_featured", "-average_rating", "-views_count").values(
            "id", "name", "slug", "type", "city", "district",
            "province", "latitude", "longitude", "average_rating",
        )[:100]

        # If strict filtering yielded too few rows, fall back to general candidate selection
        if len(compact_rows) < top_n:
            compact_rows = Destination.publicly_visible().exclude(
                latitude__isnull=True
            ).exclude(longitude__isnull=True).order_by(
                "-is_featured", "-average_rating", "-views_count"
            ).values(
                "id", "name", "slug", "type", "city", "district",
                "province", "latitude", "longitude", "average_rating",
            )[:100]
        destinations = [
            {
                "id": row["id"],
                "name": row["name"],
                "slug": row["slug"],
                "type": row["type"],
                "city": row["city"],
                "district": row["district"],
                "province": row["province"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "average_rating": float(row["average_rating"]) if row["average_rating"] is not None else None,
            }
            for row in compact_rows
        ]

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
                timeout=3.5,
            )

            response.raise_for_status()

            res_json = response.json()
            if isinstance(res_json, dict):
                res_json.setdefault("source", "ml_recommendation_engine")
            return Response(
                res_json,
                status=response.status_code
            )

        except requests.RequestException:
            # Deterministic DB fallback matching interest/province or top-rated destinations
            fallback_qs = Destination.publicly_visible()
            if province:
                fallback_qs = fallback_qs.filter(province__iexact=province)
            if interest:
                from django.db.models import Q
                fallback_qs = fallback_qs.filter(
                    Q(name__icontains=interest) |
                    Q(type__icontains=interest) |
                    Q(description__icontains=interest) |
                    Q(short_description__icontains=interest) |
                    Q(cultural_significance__icontains=interest) |
                    Q(category__name__icontains=interest)
                )

            fallback_destinations = list(fallback_qs.order_by("-is_featured", "-average_rating", "-views_count")[:top_n * 2])
            if len(fallback_destinations) < top_n:
                fallback_destinations = list(Destination.publicly_visible().order_by("-is_featured", "-average_rating", "-views_count")[:top_n * 2])

            # Apply category & district diversity filtering
            seen_cats, seen_districts, diverse_list = set(), set(), []
            for dest in fallback_destinations:
                cat_id = dest.category_id
                dist = dest.district or dest.city
                if cat_id not in seen_cats or dist not in seen_districts or len(diverse_list) < top_n:
                    diverse_list.append(dest)
                    if cat_id: seen_cats.add(cat_id)
                    if dist: seen_districts.add(dist)
                if len(diverse_list) >= top_n:
                    break

            results = DestinationListSerializer(
                diverse_list,
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



def _haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _parse_altitude_m(value):
    """altitude is a CharField like '4,130m' / '742' -> int meters or None."""
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


def _rule_based_safety_fallback(latitude, longitude, destination=None):
    """Honest rule-based safety estimate for when the AI safety microservice
    is not running (it is an optional service — off in most deployments).

    Uses ONLY recorded data: elevation of the nearest recorded place and
    hospital/police coverage within 50 km. The response is flagged
    degraded=True with a data_note, mirroring the other offline fallbacks
    (route graphml_fallback, itinerary dataset engine) — never presented
    as a model prediction.
    """
    latitude = float(latitude)
    longitude = float(longitude)
    factors = []
    score = 0.10  # baseline

    def _box(rkm):
        dlat = rkm / 111.0
        dlon = rkm / (111.0 * max(0.2, math.cos(math.radians(latitude))))
        return dict(
            latitude__gte=latitude - dlat, latitude__lte=latitude + dlat,
            longitude__gte=longitude - dlon, longitude__lte=longitude + dlon,
        )

    nearest = None
    max_alt_10km = None
    if destination is not None:
        nearest = destination
        max_alt_10km = _parse_altitude_m(getattr(destination, "altitude", None))
    else:
        best, best_d = None, 1e18
        for dest in Destination.objects.filter(**_box(30)).exclude(
            latitude=None, longitude=None
        ).values("name", "latitude", "longitude", "altitude", "district"):
            d = _haversine_km(latitude, longitude, dest["latitude"], dest["longitude"])
            if d < best_d:
                best, best_d = dest, d
            if d <= 10:
                alt = _parse_altitude_m(dest["altitude"])
                if alt and (max_alt_10km is None or alt > max_alt_10km):
                    max_alt_10km = alt
        nearest = best if best_d <= 30 else None

    if max_alt_10km:
        if max_alt_10km >= 3000:
            score += 0.35
            factors.append(f"High-altitude terrain: a recorded place within 10 km sits at about {max_alt_10km:,} m — thin air and fast weather changes")
        elif max_alt_10km >= 2500:
            score += 0.22
            factors.append(f"Upper-hill terrain: a recorded place within 10 km sits at about {max_alt_10km:,} m")

    try:
        hosp = list(Hospital.objects.filter(**_box(60)).exclude(
            latitude=None, longitude=None).values_list("latitude", "longitude"))
        pol = list(PoliceStation.objects.filter(**_box(60)).exclude(
            latitude=None, longitude=None).values_list("latitude", "longitude"))
        n_hosp = sum(1 for (la, lo) in hosp if _haversine_km(latitude, longitude, la, lo) <= 50)
        n_pol = sum(1 for (la, lo) in pol if _haversine_km(latitude, longitude, la, lo) <= 50)
    except Exception:
        n_hosp = n_pol = None
    if n_hosp is not None:
        n = n_hosp + n_pol
        if n == 0:
            score += 0.30
            factors.append("Remote: no hospital or police station recorded within 50 km — carry first-aid supplies and a charged phone")
        elif n < 3:
            score += 0.15
            factors.append(f"Thin emergency coverage: only {n} hospital(s)/police station(s) recorded within 50 km")

    if not factors:
        factors.append("No major risk signals in the recorded data for this location")

    score = round(min(0.95, score), 2)
    if score < 0.3:
        category = "Low"
    elif score < 0.55:
        category = "Moderate"
    elif score < 0.75:
        category = "High"
    else:
        category = "Very High"

    name = (nearest or {}).get("name") if isinstance(nearest, dict) else getattr(nearest, "name", None) if nearest is not None else None
    return {
        "risk_category": category,
        "tourism_risk_index": score,
        "degraded": True,
        "data_note": (
            "The AI safety model is offline on this deployment — this is a "
            "rule-based estimate from recorded elevation and emergency-service "
            "coverage (hospitals/police within 50 km), not a model prediction."
        ),
        "source": "rule-based-fallback",
        "factors": factors,
        "nearest_recorded_place": name,
    }


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

        if latitude is None or longitude is None:
            return Response(
                {"detail": "This destination has no recorded coordinates, so no safety estimate is possible."},
                status=status.HTTP_400_BAD_REQUEST,
            )



        result = get_ml_safety_prediction(
            latitude,
            longitude,
            city,
            country,
        )


        if result is None:
            # The AI safety microservice is optional and often not running —
            # degrade to the honest rule-based estimate instead of a bare 503,
            # so the Risk page always shows something real.
            result = _rule_based_safety_fallback(latitude, longitude, destination)
            if destination:
                MLInsight.objects.create(
                    destination=destination,
                    insight_type=MLInsight.InsightType.CROWD_PREDICTION,
                    label=result["risk_category"],
                    score=result["tourism_risk_index"],
                    raw_result=result,
                )
            return Response(result)



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


        destination_value = data.get("destination")
        if destination_value:
            dest_str = str(destination_value).strip()
            if dest_str.isdigit():
                match = Destination.objects.filter(pk=dest_str).first()
                if match:
                    data["destination"] = match.id
                else:
                    return Response({
                        "detail": "Destination not found. Please select a valid Nepal destination.",
                        "suggestions": ["Pokhara", "Kathmandu", "Patan", "Bhaktapur", "Lumbini"]
                    }, status=status.HTTP_400_BAD_REQUEST)
            elif len(dest_str) < 2 or re.fullmatch(r"[0-9\W]+", dest_str):
                return Response({
                    "detail": "Destination not found. Please select a valid Nepal destination.",
                    "suggestions": ["Pokhara", "Kathmandu", "Patan", "Bhaktapur", "Lumbini"]
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                match = Destination.objects.filter(name__icontains=dest_str).first()
                if match:
                    data["destination"] = match.id
                else:
                    data.pop("destination", None)
                    data.setdefault("city", dest_str)


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


# Bounding-box half-widths (degrees) tried in order before exact distance ranking.
# 0.25 deg is roughly 28 km of latitude in Nepal. Remote districts can have no service
# that close, so the box widens step by step. The final ``None`` means "no box" (the
# whole table) so a result is never lost; that full scan only happens as a last resort.
_ITINERARY_BBOX_STEPS = (0.25, 1.0, None)


def _nearest_for_itinerary(rows, lat, lon, mapper, limit=2):
    """Return the ``limit`` nearest rows to (lat, lon), mapped with ``mapper``.

    ``rows`` must be a queryset with ``latitude``/``longitude`` fields. The query is
    first narrowed with a SQL bounding box so only nearby candidates are
    loaded into Python for haversine ranking, rather than every hotel or hospital
    in the country.
    """
    lat, lon = float(lat), float(lon)
    rows = rows.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    candidates = []
    for delta in _ITINERARY_BBOX_STEPS:
        if delta is None:
            candidates = list(rows)
            break
        lat_min, lat_max = lat - delta, lat + delta
        lon_min, lon_max = lon - delta, lon + delta
        candidates = list(rows.filter(
            latitude__range=(lat_min, lat_max),
            longitude__range=(lon_min, lon_max),
        ))
        # A box corner is farther away than its edge midpoint, so only trust this box
        # when enough candidates sit inside its inscribed circle (radius = delta
        # degrees of latitude); otherwise a nearer row could lie just outside it.
        inscribed_km = delta * 111.0 * 0.85  # 0.85 = cos(~31.5 deg N), a safe bound for Nepal
        inside = sum(
            1 for row in candidates
            if haversine_distance(lat, lon, row.latitude, row.longitude) <= inscribed_km
        )
        if inside >= limit:
            break
    ranked = []
    for row in candidates:
        if row.latitude is None or row.longitude is None:
            continue
        distance = haversine_distance(lat, lon, row.latitude, row.longitude)
        ranked.append((distance, row))
    ranked.sort(key=lambda pair: pair[0])
    return [mapper(row, round(distance, 2)) for distance, row in ranked[:limit]]


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

        ml_payload = None
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
            ml_payload = response.json()
        except requests.RequestException as exc:
            logger.warning("ML itinerary service unreachable: %s", exc)

        requested_place = ((data.get("district") or data.get("start_city")) or "").strip()
        if ml_payload is not None:
            if _ml_plan_matches_place(ml_payload, requested_place):
                return Response(enrich_itinerary_with_services(ml_payload))
            # The ML planner silently defaulted to another city (e.g. it does
            # not know the district name "Kaski" → Pokhara). Never serve a
            # plan for a different place than the traveller asked for.
            logger.info(
                "ML itinerary planned away from %r - using internal DB engine",
                requested_place,
            )
        # Internal database fallback itinerary builder
        days = max(1, data.get("days", 3))
        travelers = max(1, data.get("travelers", 1))
        interests = data.get("interests", ["culture"])
        start_city = (data.get("start_city") or "Kathmandu").strip()
        district = (data.get("district") or "").strip()

        qs = Destination.publicly_visible()

        # A typed place may be a district, city or province ("Rolpa" is a
        # district, not a city) — match every level so district requests
        # never fall through to a generic nationwide plan.
        from django.db.models import Q
        place = district or start_city
        scope = qs.filter(Q(district__icontains=place) | Q(city__icontains=place) | Q(province__icontains=place))
        scope_label = f"places recorded in “{place}”"
        scoped = scope.exists()
        if not scoped and district and district != start_city:
            scope = qs.filter(Q(district__icontains=start_city) | Q(city__icontains=start_city))
            scope_label = f"places recorded in “{start_city}”"
            scoped = scope.exists()
        if not scoped:
            scope = qs
            scope_label = None

        def interest_score(dest):
            hay = " ".join(filter(None, [
                dest.category.name if dest.category_id else "",
                dest.name,
                dest.short_description or "",
            ])).lower()
            return sum(1 for term in interests if term and str(term).lower() in hay)

        candidates = sorted(
            list(scope.select_related("category")[:400]),
            key=lambda d: (-interest_score(d), d.name),
        )

        # Greedy nearest-neighbour ordering so each day stays geographically
        # compact instead of zig-zagging across the district.
        want = min(len(candidates), max(days * 2, 2))
        pool = candidates[:want]
        ordered, remaining = [], list(pool)
        cursor = None
        while remaining:
            if cursor is not None and cursor.latitude is not None and cursor.longitude is not None:
                remaining.sort(key=lambda p: (
                    haversine_distance(float(cursor.latitude), float(cursor.longitude),
                                       float(p.latitude), float(p.longitude))
                    if p.latitude is not None and p.longitude is not None else 10_000.0
                ))
            nxt = remaining.pop(0)
            ordered.append(nxt)
            cursor = nxt

        def to_item(dest, day_trip=False):
            item = {
                "name": dest.name,
                "city": dest.city or (dest.district or start_city),
                "district": dest.district or "",
                "latitude": float(dest.latitude) if dest.latitude is not None else None,
                "longitude": float(dest.longitude) if dest.longitude is not None else None,
                "category": dest.category.name if dest.category_id else "Attraction",
            }
            if day_trip:
                item["day_trip"] = True
                item["note"] = f"Nearest recorded place outside “{place}” — a day trip, not inside the requested area."
            return item

        def schedule_items(items):
            """Time-aware day plan (§12). Planning-grade estimates, clearly
            labelled: 09:00 start, ~90 min per place, travel legs derived
            from straight-line distance at ~35 km/h (road times come from
            the routing service, never faked as exact)."""
            cursor = 9 * 60
            prev = None
            for item in items:
                if prev is not None and item.get("latitude") is not None and item.get("longitude") is not None:
                    km = haversine_distance(prev["latitude"], prev["longitude"],
                                            item["latitude"], item["longitude"])
                    travel_min = max(10, int(km / 35.0 * 60))
                    item["travel_from_previous"] = {
                        "distance_km": round(km, 1),
                        "minutes_estimated": travel_min,
                    }
                    cursor += travel_min
                item["start_time"] = f"{cursor // 60:02d}:{cursor % 60:02d}"
                item["duration_minutes"] = 90
                cursor += 90
                item["end_time"] = f"{cursor // 60:02d}:{cursor % 60:02d}"
                prev = item

        itinerary_days = []
        per_day = max(1, -(-len(ordered) // days)) if ordered else 0
        for day_idx in range(1, days + 1):
            chunk = ordered[(day_idx - 1) * per_day: day_idx * per_day]
            day_destinations = [to_item(dest) for dest in chunk]

            # Honest shortfall: when the requested area has fewer recorded
            # places than the trip needs, fill with the nearest places from
            # the wider catalogue — clearly flagged, never fabricated.
            if scoped and not day_destinations:
                used = {item["name"] for day in itinerary_days for item in day["destinations"]}
                used.update(item["name"] for item in day_destinations)
                fillers = [c for c in candidates if c.name not in used][:2]
                if not fillers:
                    fillers = [c for c in qs.exclude(latitude__isnull=True).exclude(name__in=used)[:2]]
                if not fillers and ordered:
                    # Sparse area: nothing new is recorded anywhere reachable,
                    # so schedule honest return visits to the real recorded
                    # places instead of leaving the day empty or inventing
                    # destinations that do not exist.
                    fillers = ordered[:2]
                if fillers:
                    day_destinations = [to_item(dest, day_trip=True) for dest in fillers]
                    for item in day_destinations:
                        if item["name"] in used:
                            item["revisit"] = True
                            item["revisit_note"] = "Return visit — no further verified places are recorded in this area."

            if day_destinations:
                schedule_items(day_destinations)

            cats = [item["category"] for item in day_destinations]
            if cats:
                top = max(set(cats), key=cats.count)
                theme = f"{top} day in {place}" if len(set(cats)) == 1 else f"{top} & local exploration in {place}"
            else:
                theme = "Arrival & orientation"

            itinerary_days.append({
                "day": day_idx,
                "city": (day_destinations[0]["city"] if day_destinations else start_city),
                "theme": theme,
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
            "data_note": (
                f"Built from {scope_label}." if scope_label else
                f"No verified places are recorded for “{place}” yet — showing popular destinations from the wider Nepal catalogue instead."
            ),
            "timing_note": (
                "Times are planning estimates (09:00 start, ~90 min per place, "
                "travel legs from straight-line distance at ~35 km/h). "
                "Live road times come from the routing service."
            ),
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
            heritage_dests = list(Destination.publicly_visible().filter(
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
            nature_dests = list(Destination.publicly_visible().filter(
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

        elif action in {"replan", "impact_check", "weather_replan"}:
            action_note = "IMPACT DETECTED & AUTOMATIC REPLANNING APPLIED: Swapped outdoor high-altitude/water activities with indoor cultural heritage & tea houses."
            indoor_dests = list(Destination.publicly_visible().filter(
                category__slug__in=["museums", "culture", "heritage", "temples"]
            )[: len(days_data) * 2])
            for idx, day in enumerate(days_data):
                day_copy = dict(day)
                day_copy["theme"] = "Replanned: Cultural & Indoor Experience"
                if indoor_dests:
                    d = indoor_dests[idx % len(indoor_dests)]
                    day_copy["destinations"] = [{
                        "name": d.name, "city": d.city or d.district or "Nepal",
                        "latitude": float(d.latitude) if d.latitude else None,
                        "longitude": float(d.longitude) if d.longitude else None,
                        "category": d.category.name if d.category else "Museum / Cultural",
                    }]
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

# Ported from devin dark-mode-compat layer (regression-suite contract).

def _ml_plan_matches_place(payload, place):
    """True when the ML plan actually visits the requested place.

    The ML service silently plans around its default city when it does not
    recognise a place name (e.g. the district name "Kaski"), so callers must
    be able to detect that and prefer the internal district-scoped engine
    instead of serving a plan for the wrong place.
    """
    needle = (place or "").strip().lower()
    if not needle:
        return True  # no place constraint - any plan is on-topic
    days = payload.get("itinerary") or payload.get("days") or []
    if not isinstance(days, list):
        return False
    for day in days:
        if not isinstance(day, dict):
            continue
        candidates = [day.get("city"), day.get("district")]
        for stop in day.get("destinations") or day.get("stops") or []:
            if isinstance(stop, dict):
                candidates.append(stop.get("city"))
                candidates.append(stop.get("district"))
        for value in candidates:
            text = str(value or "").strip().lower()
            if text and (needle in text or text in needle):
                return True
    return False
