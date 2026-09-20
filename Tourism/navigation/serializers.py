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
