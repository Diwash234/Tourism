from rest_framework import serializers


class PointSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class RouteRequestSerializer(serializers.Serializer):
    start = PointSerializer()
    destination = PointSerializer()
    mode = serializers.ChoiceField(
        choices=["driving", "motorcycle", "walking", "hiking", "cycling"],
        default="driving")
    alternatives = serializers.BooleanField(default=False)


class ProgressRequestSerializer(serializers.Serializer):
    route_id = serializers.CharField(max_length=32)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    heading = serializers.FloatField(required=False, allow_null=True,
                                     min_value=0, max_value=360)
    accuracy = serializers.FloatField(required=False, allow_null=True, min_value=0)


class StopSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class ItineraryRouteRequestSerializer(serializers.Serializer):
    start = PointSerializer()
    stops = StopSerializer(many=True)
    mode = serializers.ChoiceField(
        choices=["driving", "motorcycle", "walking", "hiking", "cycling"],
        default="driving")

    def validate_stops(self, value):
        if not value or len(value) > 12:
            raise serializers.ValidationError("Provide between 1 and 12 stops.")
        return value


class SelectAlternativeSerializer(serializers.Serializer):
    route_id = serializers.CharField(max_length=32)
    index = serializers.IntegerField(min_value=0, max_value=2)
