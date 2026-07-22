import django_filters as df

from .models import Destination, Alert, EmergencyContact, Budget
from django.contrib.auth.base_user import BaseUserManager


class DestinationFilter(df.FilterSet):
    category = df.CharFilter(field_name="category__slug", lookup_expr="iexact")
    city = df.CharFilter(field_name="city", lookup_expr="icontains")
    country = df.CharFilter(field_name="country", lookup_expr="icontains")
    min_rating = df.NumberFilter(field_name="average_rating", lookup_expr="gte")
    max_entry_fee = df.NumberFilter(field_name="entry_fee", lookup_expr="lte")
    featured = df.BooleanFilter(method="filter_featured")

    class Meta:
        model = Destination
        fields = ["category", "city", "country", "min_rating", "max_entry_fee", "is_active", "featured"]

    def filter_featured(self, queryset, name, value):
        """?featured=true -> highly-rated destinations, for homepage widgets."""
        if value:
            return queryset.filter(average_rating__gte=4.0).order_by("-average_rating")
        return queryset


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
    ward_number = df.NumberFilter(field_name="ward_number")

    class Meta:
        model = EmergencyContact
        fields = ["contact_type", "city", "ward_number"]


class BudgetFilter(df.FilterSet):
    category = df.CharFilter(field_name="category")
    date_from = df.DateFilter(field_name="date", lookup_expr="gte")
    date_to = df.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Budget
        fields = ["category", "date_from", "date_to", "destination"]
        
class UserManager(BaseUserManager):
    """Custom manager for the email-based User model."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)
