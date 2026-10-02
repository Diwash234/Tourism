"""
Dashboard analytics and statistics endpoints.
"""
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Destination, Rating, Review, User, TravelPlan
from booking.models import Booking


class DashboardStatsView(APIView):
    """
    GET /api/v1/dashboard/stats/

    Returns key metrics for the admin dashboard.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timezone.timedelta(days=30)

        # User statistics
        total_users = User.objects.count()
        new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()

        # Destination statistics
        total_destinations = Destination.objects.count()
        published_destinations = Destination.publicly_visible().count()
        featured_destinations = Destination.objects.filter(is_featured=True).count()

        # Review statistics
        total_reviews = Review.objects.count()
        avg_rating = Rating.objects.aggregate(avg=Avg("value"))["avg"] or 0
        recent_reviews = Review.objects.filter(created_at__gte=thirty_days_ago).count()

        # Booking statistics
        total_bookings = Booking.objects.count() if hasattr(Booking, "objects") else 0
        recent_bookings = Booking.objects.filter(created_at__gte=thirty_days_ago).count() if hasattr(Booking, "objects") else 0

        # Travel plan statistics
        total_plans = TravelPlan.objects.count()
        recent_plans = TravelPlan.objects.filter(created_at__gte=thirty_days_ago).count()

        return Response({
            "users": {
                "total": total_users,
                "new_30d": new_users_30d,
                "active_30d": active_users,
            },
            "destinations": {
                "total": total_destinations,
                "published": published_destinations,
                "featured": featured_destinations,
            },
            "reviews": {
                "total": total_reviews,
                "average_rating": round(avg_rating, 2),
                "recent_30d": recent_reviews,
            },
            "bookings": {
                "total": total_bookings,
                "recent_30d": recent_bookings,
            },
            "travel_plans": {
                "total": total_plans,
                "recent_30d": recent_plans,
            },
            "generated_at": now.isoformat(),
        })


class PublicStatsView(APIView):
    """
    GET /api/v1/stats/

    Public statistics for the homepage.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "destinations": Destination.publicly_visible().count(),
            "reviews": Review.objects.count(),
            "average_rating": round(Rating.objects.aggregate(avg=Avg("value"))["avg"] or 0, 2),
            "users": User.objects.count(),
        })
