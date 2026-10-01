# Shared catalogue classification rules. These are deliberately kept in one module
# because public destination listing, mood recommendations and media discovery
# must agree on what is an attraction versus accommodation/service content.
ACCOMMODATION_SLUGS = frozenset({
    "hotel", "resort", "lodge", "guest_house", "guesthouse", "hostel", "motel",
    "homestay", "home_stay", "alpine_hut", "camp_site", "camp_pitch", "chalet",
    "apartment", "wilderness_hut", "cottage",
})
ACCOMMODATION_NAME_HINTS = (
    "hotel", "resort", "lodge", "guest house", "guesthouse", "homestay",
    "home stay", "backpackers", "hostel", "motel", "cottage", "tea house",
    "teahouse", "inn",
)

# Categories that represent services/settlements rather than a visitor
# attraction. Keep this conservative: unknown categories remain visible.
NON_ATTRACTION_SLUGS = frozenset({
    "restaurants", "restaurant", "food-culinary", "shopping", "transportation",
    "bus-stations", "airports", "hospitals", "police", "pharmacies", "atm",
    "fuel", "cities", "towns", "villages",
})
NON_ATTRACTION_NAME_HINTS = (
    "restaurant", "cafe", "hospital", "police station", "pharmacy", "bus park",
    "bus station", "airport", "petrol pump", "fuel station", "atm",
)

"""
Advanced filtering, search, and ordering for the Tourism API.
"""
import django_filters
from django.db.models import Q
from rest_framework.filters import SearchFilter, OrderingFilter


class DestinationFilter(django_filters.FilterSet):
    """Advanced filtering for destinations."""
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    province = django_filters.CharFilter(field_name="province", lookup_expr="iexact")
    district = django_filters.CharFilter(field_name="district", lookup_expr="iexact")
    min_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr="lte")
    has_images = django_filters.BooleanFilter(method="filter_has_images")
    is_featured = django_filters.BooleanFilter(field_name="is_featured")
    is_published = django_filters.BooleanFilter(field_name="is_published")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        from .models import Destination
        model = Destination
        fields = [
            "category", "province", "district", "is_featured",
            "status",
        ]

    def filter_has_images(self, queryset, name, value):
        if value:
            return queryset.filter(gallery__isnull=False).distinct()
        return queryset.filter(gallery__isnull=True)

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(district__icontains=value)
            | Q(province__icontains=value)
            | Q(category__name__icontains=value)
        ).distinct()


class AlertFilter(django_filters.FilterSet):
    """Filtering for alerts."""
    severity = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()
    province = django_filters.CharFilter(lookup_expr="iexact")
    district = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        from .models import Alert
        model = Alert
        fields = ["severity", "is_active", "province", "district", "alert_type"]


class EmergencyContactFilter(django_filters.FilterSet):
    """Filtering for emergency contacts."""
    district = django_filters.CharFilter(lookup_expr="iexact")
    province = django_filters.CharFilter(lookup_expr="iexact")
    contact_type = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()

    class Meta:
        from .models import EmergencyContact
        model = EmergencyContact
        fields = ["district", "province", "contact_type", "is_active"]


class BudgetFilter(django_filters.FilterSet):
    """Filtering for budgets."""
    min_amount = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    currency = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        from .models import Budget
        model = Budget
        fields = ["currency", "min_amount", "max_amount"]
