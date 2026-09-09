from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Avg, Count

from rest_framework import viewsets, permissions, generics
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
from audit.logging_services import log_action
from tourist.models import Notification


def _notify(user, title, message, metadata=None):
    if user is None:
        return
    Notification.objects.create(user=user, title=title, message=message, metadata=metadata or {})
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

    def perform_create(self, serializer):
        task = serializer.save()
        _notify(task.assigned_to, "New task assigned",
                f"\"{task.title}\" was assigned to you"
                + (f" (due {task.due_date})" if task.due_date else "") + ".",
                {"task_id": task.id})
        log_action(action="task.assign", category="content", message=f"Task '{task.title}' assigned to {task.assigned_to.email}",
                   object_type="AdminTask", object_id=task.id, user=task.assigned_by)

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

# ============================================================
# DESTINATION MEDIA MANAGEMENT
# ADDED: supports the admin "Destination Media Manager" page —
# triaging which destinations need real photos, without paging through
# all ~5,900 rows by hand. Confirmed live against the real database:
# most "no images" destinations are actually miscategorized hotels/
# guesthouses (category_id in ACCOMMODATION_CATEGORY_IDS below), so
# this excludes those by default — an admin fixing "missing images"
# almost certainly means genuine attractions, not business listings.
# ============================================================

# Category IDs that are accommodation/business, not tourist
# destinations (matches tourist_category table: hotel, guest_house,
# hostel, motel, resort, home_stay, homestay, chalet, apartment,
# wilderness_hut, caravan_site, travel_agency). Kept as a constant here
# rather than a DB flag since recategorizing ~3,600 rows is a bigger,
# separate data-cleanup decision — this view just doesn't surface them
# as "destinations needing photos".
ACCOMMODATION_CATEGORY_IDS = [1, 2, 8, 10, 11, 14, 18, 20, 21, 26, 29, 31, 32, 33]


class DestinationsMissingImagesView(generics.ListAPIView):
    """
    GET /api/v1/admin-panel/destinations-missing-images/
    Staff-only. Paginated list of genuine destinations (excludes
    accommodation-category rows) that have neither a cover_image nor
    any gallery image — the admin's actual to-do list for photos.
    """
    permission_classes = [IsSuperAdminOrAssignedAdmin]
    serializer_class = None  # set dynamically below to avoid a circular import at module load

    def get_serializer_class(self):
        from tourist.serializers import DestinationListSerializer
        return DestinationListSerializer

    def get_queryset(self):
        return (
            Destination.objects.filter(is_active=True)
            .exclude(category_id__in=ACCOMMODATION_CATEGORY_IDS)
            .filter(models.Q(cover_image="") | models.Q(cover_image__isnull=True))
            .annotate(gallery_count=Count("gallery"))
            .filter(gallery_count=0)
            .order_by("name")
        )

# ============================================================
# TASK ACTIONS — assignment-driven workflow (Staff Ops spec)
# ============================================================

class AdminTaskActionView(APIView):
    """Explicit task workflow actions with backend authorization.

    Staff (assigned_to only — IDOR guarded): start, complete (note
    required), block (reason required), submit_review, escalate.
    Admins/superusers: approve / reject a submitted task.

    Every action writes an audit entry and notifies the counterpart, so the
    admin↔staff loop is fully traceable.
    """

    permission_classes = [permissions.IsAuthenticated]

    STAFF_ACTIONS = {"start", "complete", "block", "submit_review", "escalate"}
    ADMIN_ACTIONS = {"approve", "reject"}

    def _is_admin(self, user):
        return user.is_superuser or getattr(user, "role", None) in {"admin", "super_admin", "tourism_admin"}

    def post(self, request, pk):
        action = (request.data.get("action") or "").strip().lower()
        note = (request.data.get("note") or "").strip()

        task = AdminTask.objects.select_related("assigned_to", "assigned_by").filter(pk=pk).first()
        if task is None:
            return Response({"detail": "Task not found."}, status=404)

        is_admin = self._is_admin(request.user)
        is_assignee = task.assigned_to_id == request.user.id
        if action in self.STAFF_ACTIONS:
            if not is_assignee:
                return Response({"detail": "Only the assigned staff member may perform this action."}, status=403)
        elif action in self.ADMIN_ACTIONS:
            if not is_admin:
                return Response({"detail": "Only an administrator may approve or reject submitted work."}, status=403)
        else:
            return Response({"detail": "Unknown action."}, status=400)

        S = AdminTask.Status
        error = None
        if action == "start":
            if task.status not in {S.PENDING, S.BLOCKED}:
                error = "Only pending or blocked tasks can be started."
            else:
                task.status = S.IN_PROGRESS
                task.started_at = task.started_at or timezone.now()
        elif action == "complete":
            if not note:
                error = "A completion note is required."
            elif task.status in {S.COMPLETED, S.CANCELLED}:
                error = "This task is already closed."
            else:
                task.status = S.COMPLETED
                task.completion_note = note
                task.completed_at = timezone.now()
        elif action == "block":
            if not note:
                error = "A reason is required to block a task."
            elif task.status in {S.COMPLETED, S.CANCELLED}:
                error = "Closed tasks cannot be blocked."
            else:
                task.status = S.BLOCKED
                task.blocked_reason = note
        elif action == "submit_review":
            if task.status not in {S.IN_PROGRESS, S.PENDING}:
                error = "Only active tasks can be submitted for review."
            else:
                task.status = S.IN_REVIEW
                if note:
                    task.completion_note = note
        elif action == "escalate":
            if not note:
                error = "A reason is required to escalate."
            elif task.status in {S.COMPLETED, S.CANCELLED}:
                error = "Closed tasks cannot be escalated."
            else:
                task.is_escalated = True
                task.escalation_reason = note
                if task.status == S.PENDING:
                    task.status = S.IN_PROGRESS
                    task.started_at = task.started_at or timezone.now()
        elif action == "approve":
            if task.status != S.IN_REVIEW:
                error = "Only tasks submitted for review can be approved."
            else:
                task.status = S.COMPLETED
                task.completed_at = task.completed_at or timezone.now()
                task.reviewed_by = request.user
                task.reviewed_at = timezone.now()
                task.review_note = note
        elif action == "reject":
            if task.status != S.IN_REVIEW:
                error = "Only tasks submitted for review can be rejected."
            elif not note:
                error = "A rejection reason is required."
            else:
                task.status = S.IN_PROGRESS
                task.reviewed_by = request.user
                task.reviewed_at = timezone.now()
                task.review_note = note

        if error:
            return Response({"detail": error}, status=400)

        task.save()

        # Notify the counterpart so the loop closes both ways.
        if action in {"complete", "submit_review", "escalate"} and task.assigned_by_id:
            _notify(task.assigned_by, f"Task {action.replace('_', ' ')}: {task.title}",
                    note or f"{request.user.email} updated task #{task.id}.", {"task_id": task.id})
        elif action in {"approve", "reject"}:
            _notify(task.assigned_to, f"Your submission was {'approved' if action == 'approve' else 'rejected'}: {task.title}",
                    note or f"Reviewed by {request.user.email}.", {"task_id": task.id})

        log_action(request=request, action=f"task.{action}", category="content",
                   message=f"Task '{task.title}' → {action} by {request.user.email}" + (f" ({note[:120]})" if note else ""),
                   object_type="AdminTask", object_id=task.id)

        from .serializers import AdminTaskSerializer
        return Response(AdminTaskSerializer(task, context={"request": request}).data)


# ============================================================
# MY PERFORMANCE — operational productivity, staff-scoped
# ============================================================

class MyPerformanceView(APIView):
    """Aggregates the caller's own task record. Operational view only."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        qs = AdminTask.objects.filter(assigned_to=user)
        today = timezone.now().date()
        completed = qs.filter(status=AdminTask.Status.COMPLETED)
        on_time = 0
        overdue_completed = 0
        for t in completed:
            if t.due_date and t.completed_at and t.completed_at.date() > t.due_date:
                overdue_completed += 1
            else:
                on_time += 1
        total_completed = completed.count()
        durations = [
            (t.completed_at - t.started_at).total_seconds() / 3600.0
            for t in completed if t.started_at and t.completed_at
        ]
        return Response({
            "tasks_total": qs.count(),
            "tasks_completed": total_completed,
            "on_time_completed": on_time,
            "late_completed": overdue_completed,
            "on_time_rate": round(on_time / total_completed * 100, 1) if total_completed else None,
            "in_progress": qs.filter(status=AdminTask.Status.IN_PROGRESS).count(),
            "pending": qs.filter(status=AdminTask.Status.PENDING).count(),
            "blocked": qs.filter(status=AdminTask.Status.BLOCKED).count(),
            "in_review": qs.filter(status=AdminTask.Status.IN_REVIEW).count(),
            "overdue_open": qs.filter(due_date__lt=today).exclude(status__in=["completed", "cancelled"]).count(),
            "escalations": qs.filter(is_escalated=True).count(),
            "avg_completion_hours": round(sum(durations) / len(durations), 1) if durations else None,
        })
