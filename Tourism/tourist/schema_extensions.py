"""
drf-spectacular schema helpers.

These endpoints are plain `APIView` subclasses that build their responses from
ML/risk services rather than from a single serializer, so drf-spectacular cannot
guess their shape. Without an explicit declaration it logs
`unable to guess serializer` errors and drops the operation from the OpenAPI
document, which broke `/api/v1/models/`, `/api/schema/`, `/api/docs/` and
`/api/redoc/` accuracy.

Each `Serializer` below describes the real response the view already returns —
they are documentation only and are never used to validate incoming data.
"""
from rest_framework import serializers


# ---------------------------------------------------------------------------
# Risk prediction (POST /api/v1/ml/risk-prediction/)
# ---------------------------------------------------------------------------
class RiskTrendSerializer(serializers.Serializer):
    """Direction of travel of the risk indicator, not a price/forecast."""

    direction = serializers.ChoiceField(
        choices=["increasing", "decreasing", "stable"], required=False
    )
    change_pct = serializers.FloatField(required=False, allow_null=True)
    incidents_last_30d = serializers.IntegerField(required=False, allow_null=True)


class RiskNavigationSerializer(serializers.Serializer):
    route_safety_score = serializers.FloatField(required=False)
    recommended = serializers.BooleanField(required=False)
    caution_advised = serializers.BooleanField(required=False)
    avoid_recommended = serializers.BooleanField(required=False)
    specific_warnings = serializers.ListField(
        child=serializers.CharField(), required=False
    )


class RiskDayPredictionSerializer(serializers.Serializer):
    date = serializers.CharField(required=False)
    day_name = serializers.CharField(required=False)
    predicted_score = serializers.FloatField(required=False)
    level = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False)
    key_factors = serializers.ListField(child=serializers.CharField(), required=False)


class RiskRequestSerializer(serializers.Serializer):
    """Body accepted by RiskPredictionView."""

    destination_id = serializers.IntegerField(required=False)
    destination_slug = serializers.CharField(required=False)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    days_ahead = serializers.IntegerField(required=False, default=7, min_value=1, max_value=30)


class RiskPredictionResponseSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField(required=False, allow_null=True)
    destination_name = serializers.CharField(required=False, allow_null=True)
    base_score = serializers.FloatField(required=False, allow_null=True)
    trend = RiskTrendSerializer(required=False)
    predictions = RiskDayPredictionSerializer(many=True, required=False)
    summary = serializers.CharField(required=False, allow_null=True)
    navigation_risk = RiskNavigationSerializer(required=False)
    current_conditions = serializers.DictField(required=False)
    category_risk = serializers.DictField(required=False)
    detail = serializers.CharField(required=False)


# ---------------------------------------------------------------------------
# Route risk assessment (POST /api/v1/ml/route-risk/)
# ---------------------------------------------------------------------------
class RouteRiskSegmentSerializer(serializers.Serializer):
    segment = serializers.CharField(required=False)
    score = serializers.FloatField(required=False)
    level = serializers.CharField(required=False)
    factors = serializers.ListField(child=serializers.CharField(), required=False)


class RouteRiskRequestSerializer(serializers.Serializer):
    """Body accepted by RouteRiskAssessmentView. All four coordinates required."""

    origin_latitude = serializers.FloatField()
    origin_longitude = serializers.FloatField()
    destination_latitude = serializers.FloatField()
    destination_longitude = serializers.FloatField()
    destination_id = serializers.IntegerField(required=False)


class RouteRiskResponseSerializer(serializers.Serializer):
    overall_score = serializers.FloatField(required=False)
    level = serializers.CharField(required=False)
    warnings = serializers.ListField(child=serializers.CharField(), required=False)
    recommendations = serializers.ListField(child=serializers.CharField(), required=False)
    segment_risks = RouteRiskSegmentSerializer(many=True, required=False)
    destination_risk = serializers.DictField(required=False)
    disclaimer = serializers.CharField(required=False, allow_null=True)
    detail = serializers.CharField(required=False)


# ---------------------------------------------------------------------------
# Admin multi-source image search (POST /api/v1/admin/images/multi-search/)
# Mirrors ImageHit.to_dict() in tourist/services/image_search/search.py.
# ---------------------------------------------------------------------------
class ImageSearchHitSerializer(serializers.Serializer):
    url = serializers.CharField()
    thumbnail = serializers.CharField(required=False)
    source = serializers.CharField(required=False)
    source_title = serializers.CharField(required=False)
    source_page = serializers.CharField(required=False, allow_blank=True)
    source_page_url = serializers.CharField(required=False, allow_blank=True)
    author = serializers.CharField(required=False)
    license = serializers.CharField(required=False)
    attribution_requirement = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    location_match = serializers.IntegerField(required=False)
    keyword_match = serializers.IntegerField(required=False)
    confidence_score = serializers.IntegerField(required=False)
    match_score = serializers.FloatField(required=False)


class ImageSearchDestinationSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False)
    slug = serializers.CharField(required=False)
    district = serializers.CharField(required=False, allow_blank=True)
    province = serializers.CharField(required=False, allow_blank=True)


class MultiSourceImageSearchRequestSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField(required=False)
    query = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    province = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    sources = serializers.ListField(child=serializers.CharField(), required=False)
    limit = serializers.IntegerField(required=False, default=24)


class MultiSourceImageSearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField(required=False)
    district = serializers.CharField(required=False, allow_blank=True)
    province = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False)
    destination = ImageSearchDestinationSerializer(required=False, allow_null=True)
    total_found = serializers.IntegerField(required=False)
    results = ImageSearchHitSerializer(many=True, required=False)
    detail = serializers.CharField(required=False)


# ---------------------------------------------------------------------------
# Admin image import from media (POST /api/v1/admin/images/import-media/)
# ---------------------------------------------------------------------------
class ImageImportRequestSerializer(serializers.Serializer):
    destination_id = serializers.IntegerField()
    image_url = serializers.CharField()
    thumbnail_url = serializers.CharField(required=False, allow_blank=True)
    caption = serializers.CharField(required=False, allow_blank=True)
    source_platform = serializers.CharField(required=False, allow_blank=True)
    source_url = serializers.CharField(required=False, allow_blank=True)
    photographer = serializers.CharField(required=False, allow_blank=True)
    license_type = serializers.CharField(required=False, allow_blank=True)
    confidence_score = serializers.FloatField(required=False)
    is_cover = serializers.BooleanField(required=False, default=False)


class ImageImportResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(required=False)
    message = serializers.CharField(required=False)
    image_id = serializers.IntegerField(required=False)
    image_url = serializers.CharField(required=False)
    is_cover = serializers.BooleanField(required=False)
    destination_id = serializers.IntegerField(required=False)
    destination_name = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)


# ---------------------------------------------------------------------------
# AI itinerary modification (POST /api/v1/ml/itinerary/modify/)
# Mirrors the ``action in {...}`` branches in tourist.views_ml.
# ---------------------------------------------------------------------------
# Every value the view actually branches on. An unknown value is not an error:
# the view falls through to "Custom adjustment applied: <action>" and echoes the
# itinerary back unchanged, so this is documented as a free-form string rather
# than a ChoiceField to keep the published contract honest.
ITINERARY_MODIFY_ACTIONS = (
    "cheaper",
    "make_cheaper",
    "luxurious",
    "make_luxurious",
    "more_culture",
    "culture",
    "more_nature",
    "more_trekking",
    "hidden_gems",
    "slower_pace",
    "relaxed",
    "replan",
    "impact_check",
    "weather_replan",
)


class ItineraryModifyRequestSerializer(serializers.Serializer):
    """Body accepted by AIItineraryModificationView.

    ``itinerary_data`` is the structured plan to rewrite; ``itinerary`` is
    accepted as an alias. ``itinerary_data.itinerary`` must be a non-empty list
    of day objects, otherwise the view answers 400.
    """

    action = serializers.CharField(required=False, allow_blank=True)
    itinerary_data = serializers.DictField(required=False)
    itinerary = serializers.DictField(required=False)