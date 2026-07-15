import django_filters as df

from .models import Destination, Alert, EmergencyContact, Budget


class DestinationFilter(df.FilterSet):
    category = df.CharFilter(field_name="category__slug", lookup_expr="iexact")
    city = df.CharFilter(field_name="city", lookup_expr="icontains")
    country = df.CharFilter(field_name="country", lookup_expr="icontains")
    min_rating = df.NumberFilter(field_name="average_rating", lookup_expr="gte")
    max_entry_fee = df.NumberFilter(field_name="entry_fee", lookup_expr="lte")

    class Meta:
        model = Destination
        fields = ["category", "city", "country", "min_rating", "max_entry_fee", "is_active"]


class AlertFilter(df.FilterSet):
    alert_type = df.CharFilter(field_name="alert_type")
    severity = df.CharFilter(field_name="severity")
    city = df.CharFilter(field_name="city", lookup_expr="icontains")

    class Meta:
        model = Alert
        fields = ["alert_type", "severity", "city", "is_active"]


class EmergencyContactFilter(df.FilterSet):
    contact_type = df.CharFilter(field_name="contact_type")
    city = df.CharFilter(field_name="city", lookup_expr="icontains")

    class Meta:
        model = EmergencyContact
        fields = ["contact_type", "city"]


class BudgetFilter(df.FilterSet):
    category = df.CharFilter(field_name="category")
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Budget
        fields = ["category", "date_from", "date_to", "destination"]