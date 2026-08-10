from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Avg, Count

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from tourist.models import (
    Hotel,
    Destination,
    Alert,
    Budget,
    VisitHistory,
)

from .models import HotelAssignment, AdminTask
from .permissions import IsSuperAdmin, IsSuperAdminOrAssignedAdmin
from .serializers import (
    HotelAssignmentSerializer,
    AdminTaskSerializer,
)


# ============================================================
# HOTEL ASSIGNMENT VIEWSET
# ============================================================

class HotelAssignmentViewSet(viewsets.ModelViewSet):
    """
    Only super admins can create/delete/update assignments
    (who manages which hotel).

    Staff admins can list/view their own assignments.
    """

    serializer_class = HotelAssignmentSerializer
    filterset_fields = ["hotel", "admin"]

    def get_permissions(self):
        if self.action in (
            "create",
            "destroy",
            "update",
            "partial_update",
        ):
            return [IsSuperAdmin()]

        return [IsSuperAdminOrAssignedAdmin()]

    def get_queryset(self):
        # Prevent errors when Swagger/OpenAPI generates the schema.
        if getattr(self, "swagger_fake_view", False):
            return HotelAssignment.objects.none()

        # Super admin can see all assignments.
        if self.request.user.is_superuser:
            return HotelAssignment.objects.select_related(
                "hotel",
                "admin",
            )

        # Staff admin can only see their own assignments.
        return (
            HotelAssignment.objects
            .filter(admin=self.request.user)
            .select_related("hotel", "admin")
        )


# ============================================================
# ADMIN TASK VIEWSET
# ============================================================

class AdminTaskViewSet(viewsets.ModelViewSet):
    """
    Super admins can create/assign tasks to staff admins.

    Staff admins can only see tasks assigned to them and
    update those tasks.
    """

    serializer_class = AdminTaskSerializer

    filterset_fields = [
        "status",
        "priority",
        "assigned_to",
        "related_hotel",
    ]

    def get_permissions(self):
        # Only super admins can create or delete tasks.
        if self.action in ("create", "destroy"):
            return [IsSuperAdmin()]

        return [IsSuperAdminOrAssignedAdmin()]

    def get_queryset(self):
        # Prevent errors when Swagger/OpenAPI generates the schema.
        if getattr(self, "swagger_fake_view", False):
            return AdminTask.objects.none()

        # Super admin can see every task.
        if self.request.user.is_superuser:
            return AdminTask.objects.select_related(
                "assigned_to",
                "assigned_by",
                "related_hotel",
            )

        # Staff admin can only see tasks assigned to them.
        return (
            AdminTask.objects
            .filter(assigned_to=self.request.user)
            .select_related(
                "assigned_to",
                "assigned_by",
                "related_hotel",
            )
        )

    def perform_update(self, serializer):
        """
        Automatically set completed_at when a task becomes completed.
        """

        instance = serializer.save()

        if (
            instance.status == AdminTask.Status.COMPLETED
            and instance.completed_at is None
        ):
            instance.completed_at = timezone.now()

            instance.save(
                update_fields=["completed_at"]
            )


# ============================================================
# MY HOTELS
# ============================================================

class MyHotelsView(APIView):
    """
    GET /api/v1/admin-panel/my-hotels/

    Returns hotels managed by the logged-in staff admin.

    Super admins receive all hotels.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from tourist.serializers import HotelSerializer

        # Super admin sees all hotels.
        if request.user.is_superuser:
            hotels = Hotel.objects.all()

        else:
            # Staff admin sees only assigned hotels.
            hotel_ids = (
                HotelAssignment.objects
                .filter(admin=request.user)
                .values_list("hotel_id", flat=True)
            )

            hotels = Hotel.objects.filter(
                id__in=hotel_ids
            )

        return Response(
            HotelSerializer(
                hotels,
                many=True,
            ).data
        )


# ============================================================
# ADMIN DASHBOARD SUMMARY
# ============================================================

class AdminDashboardSummaryView(APIView):
    """
    GET /api/v1/admin-panel/dashboard-summary/

    Quick dashboard statistics for the logged-in user.

    Staff admins:
        - assigned hotels
        - their pending tasks
        - their in-progress tasks
        - their completed tasks
        - their overdue tasks

    Super admins:
        - platform-wide task/hotel information
        - total users
        - total destinations
        - active alerts
        - average budget
        - destinations by category
        - monthly visitor statistics
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # ----------------------------------------------------
        # TASKS + HOTEL COUNTS
        # ----------------------------------------------------

        if user.is_superuser:
            tasks = AdminTask.objects.all()
            hotel_count = Hotel.objects.count()

        else:
            tasks = AdminTask.objects.filter(
                assigned_to=user
            )

            hotel_count = HotelAssignment.objects.filter(
                admin=user
            ).count()

        # ----------------------------------------------------
        # BASIC DASHBOARD COUNTS
        # ----------------------------------------------------

        today = timezone.now().date()

        response_data = {
            "assigned_hotel_count": hotel_count,

            "pending_tasks": tasks.filter(
                status=AdminTask.Status.PENDING
            ).count(),

            "in_progress_tasks": tasks.filter(
                status=AdminTask.Status.IN_PROGRESS
            ).count(),

            "completed_tasks": tasks.filter(
                status=AdminTask.Status.COMPLETED
            ).count(),

            "overdue_tasks": (
                tasks
                .filter(due_date__lt=today)
                .exclude(
                    status=AdminTask.Status.COMPLETED
                )
                .count()
            ),

            "is_super_admin": user.is_superuser,
        }

        # ====================================================
        # PLATFORM-WIDE DASHBOARD STATISTICS
        # ====================================================

        User = get_user_model()

        # Total registered users.
        response_data["totalUsers"] = User.objects.count()

        # Total destinations.
        response_data["totalDestinations"] = (
            Destination.objects.count()
        )

        # Currently active alerts.
        response_data["activeAlerts"] = (
            Alert.objects
            .filter(is_active=True)
            .count()
        )

        # Average budget.
        avg_budget = (
            Budget.objects
            .aggregate(avg=Avg("amount"))["avg"]
        )

        response_data["avgBudget"] = (
            round(avg_budget, 2)
            if avg_budget is not None
            else None
        )

        # ====================================================
        # DESTINATIONS BY CATEGORY
        # ====================================================

        destination_categories = (
            Destination.objects
            .values("category__name")
            .annotate(
                count=Count("id")
            )
            .order_by("-count")
        )

        response_data["destinationsByCategory"] = [
            {
                "category": item["category__name"],
                "count": item["count"],
            }
            for item in destination_categories
        ]

        # ====================================================
        # MONTHLY VISITORS - LAST 6 MONTHS
        # ====================================================

        now = timezone.now()

        # Build the last 6 calendar months.
        year = now.year
        month = now.month

        months_back = []

        for _ in range(6):
            months_back.append(
                (year, month)
            )

            month -= 1

            if month == 0:
                month = 12
                year -= 1

        # Put months in chronological order.
        months_back.reverse()

        # Start of the oldest month.
        six_months_ago = timezone.datetime(
            months_back[0][0],
            months_back[0][1],
            1,
            tzinfo=now.tzinfo,
        )

        recent_visits = (
            VisitHistory.objects
            .filter(
                viewed_at__gte=six_months_ago
            )
        )

        # Count visits by year/month.
        counts_by_year_month = {}

        for visit in recent_visits:
            key = (
                visit.viewed_at.year,
                visit.viewed_at.month,
            )

            counts_by_year_month[key] = (
                counts_by_year_month.get(key, 0) + 1
            )

        # Always return all six months, including months
        # where there were zero visits.
        response_data["monthlyVisitors"] = [
            {
                "month": timezone.datetime(
                    year,
                    month,
                    1,
                ).strftime("%b"),

                "count": counts_by_year_month.get(
                    (year, month),
                    0,
                ),
            }

            for year, month in months_back
        ]

        return Response(response_data)


# ============================================================
# ADMIN ANALYTICS
# ============================================================

class AdminAnalyticsView(APIView):
    """
    GET /api/v1/admin-panel/analytics/?days=30

    Historical analytics for the admin panel.

    Supported period examples:

        ?days=7
        ?days=30
        ?days=90
        ?days=365
    """

    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # ----------------------------------------------------
        # PERIOD
        # ----------------------------------------------------

        try:
            days = int(
                request.query_params.get(
                    "days",
                    30,
                )
            )
        except (TypeError, ValueError):
            days = 30

        # Prevent invalid/negative periods.
        if days <= 0:
            days = 30

        period_start = (
            timezone.now()
            - timezone.timedelta(days=days)
        )

        previous_period_start = (
            period_start
            - timezone.timedelta(days=days)
        )

        User = get_user_model()

        # ====================================================
        # USER GROWTH
        # ====================================================

        new_users_this_period = (
            User.objects
            .filter(
                date_joined__gte=period_start
            )
            .count()
        )

        new_users_previous_period = (
            User.objects
            .filter(
                date_joined__gte=previous_period_start,
                date_joined__lt=period_start,
            )
            .count()
        )

        if new_users_previous_period:
            user_growth_pct = round(
                (
                    (
                        new_users_this_period
                        - new_users_previous_period
                    )
                    / new_users_previous_period
                )
                * 100,
                1,
            )

        else:
            user_growth_pct = None

        # ====================================================
        # NEW DESTINATIONS
        # ====================================================

        new_destinations_this_period = (
            Destination.objects
            .filter(
                created_at__gte=period_start
            )
            .count()
        )

        # ====================================================
        # TOP DESTINATIONS
        # ====================================================

        top_destinations = list(
            Destination.objects
            .filter(is_active=True)
            .order_by("-views_count")
            .values(
                "id",
                "name",
                "slug",
                "views_count",
                "average_rating",
            )[:10]
        )

        # ====================================================
        # CATEGORY POPULARITY
        # ====================================================

        most_viewed_categories = list(
            Destination.objects
            .filter(is_active=True)
            .values("category__name")
            .annotate(
                total_views=models.Sum(
                    "views_count"
                ),
                destination_count=models.Count(
                    "id"
                ),
            )
            .order_by("-total_views")[:10]
        )

        # ====================================================
        # ENGAGEMENT
        # ====================================================

        visits_this_period = (
            VisitHistory.objects
            .filter(
                viewed_at__gte=period_start
            )
        )

        total_visits_this_period = (
            visits_this_period.count()
        )

        unique_visitors_this_period = (
            visits_this_period
            .values("user")
            .distinct()
            .count()
        )

        # ====================================================
        # BUDGET STATISTICS
        # ====================================================

        budget_stats = (
            Budget.objects
            .filter(
                created_at__gte=period_start
            )
            .aggregate(
                count=Count("id"),
                avg_amount=Avg("amount"),
            )
        )

        # ====================================================
        # ALERTS
        # ====================================================

        alerts_this_period = (
            Alert.objects
            .filter(
                created_at__gte=period_start
            )
            .count()
        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return Response(
            {
                "period_days": days,

                "user_growth": {
                    "new_users": new_users_this_period,

                    "previous_period_new_users":
                        new_users_previous_period,

                    "growth_pct":
                        user_growth_pct,
                },

                "new_destinations":
                    new_destinations_this_period,

                "top_destinations_by_views":
                    top_destinations,

                "most_viewed_categories":
                    most_viewed_categories,

                "engagement": {
                    "total_visits":
                        total_visits_this_period,

                    "unique_visitors":
                        unique_visitors_this_period,
                },

                "budget_estimates": {
                    "count":
                        budget_stats["count"] or 0,

                    "avg_amount": (
                        round(
                            budget_stats["avg_amount"],
                            2,
                        )
                        if budget_stats["avg_amount"]
                        is not None
                        else None
                    ),
                },

                "alerts_fired":
                    alerts_this_period,
            }
        )