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


# ============================================================
# CUSTOMER SUPPORT CENTER — staff-scoped ticket operations
# (Staff Ops spec §7-10; reuses the existing UserFeedback /
# FeedbackMessage thread architecture and 'feedback' capability)
# ============================================================

def _is_support_admin(user):
    return user.is_superuser or getattr(user, "role", None) in {"admin", "super_admin", "tourism_admin"}


def _ticket_payload(fb, request):
    return {
        "id": fb.id,
        "subject": fb.subject,
        "message": fb.message,
        "category": fb.category,
        "status": fb.status,
        "priority": fb.priority,
        "customer_name": fb.name or (fb.user.full_name if fb.user else "") or "Guest",
        "customer_email": fb.email or (fb.user.email if fb.user else ""),
        "assigned_to": fb.assigned_to_id,
        "assigned_to_email": fb.assigned_to.email if fb.assigned_to else None,
        "is_escalated": fb.is_escalated,
        "escalation_reason": fb.escalation_reason,
        "created_at": fb.created_at,
        "closed_at": fb.closed_at,
        "messages": [{
            "id": m.id,
            "sender": m.sender.email if m.sender else "customer",
            "sender_is_staff": bool(m.sender and (m.sender.is_staff or m.sender.is_superuser)),
            "body": m.body, "is_internal": m.is_internal, "created_at": m.created_at,
        } for m in fb.messages.all()],
    }


class SupportTicketListView(APIView):
    """Ticket queue scoped to the caller.

    Admins see every ticket. Staff see tickets assigned to them plus the
    unassigned pool they may claim — never another staff member's tickets.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from tourist.views_admin import _require_capability as require_cap
        require_cap(request, "feedback", "view")
        from tourist.models import UserFeedback
        qs = UserFeedback.objects.select_related("user", "assigned_to").prefetch_related("messages", "messages__sender")
        if not _is_support_admin(request.user):
            qs = qs.filter(models.Q(assigned_to=request.user) | models.Q(assigned_to__isnull=True))
        status = request.query_params.get("status")
        if status == "escalated":
            qs = qs.filter(is_escalated=True)
        elif status == "urgent":
            qs = qs.filter(priority="urgent").exclude(status__in=["resolved", "closed", "archived"])
        elif status == "open":
            qs = qs.exclude(status__in=["resolved", "closed", "archived"])
        elif status:
            qs = qs.filter(status=status)
        qs = qs.order_by("-priority", "-updated_at")[:200]

        base = UserFeedback.objects.all() if _is_support_admin(request.user) else UserFeedback.objects.filter(
            models.Q(assigned_to=request.user) | models.Q(assigned_to__isnull=True))
        counts = {
            "open": base.exclude(status__in=["resolved", "closed", "archived"]).count(),
            "waiting_user": base.filter(status="waiting_user").count(),
            "escalated": base.filter(is_escalated=True).exclude(status__in=["resolved", "closed"]).count(),
            "resolved": base.filter(status__in=["resolved", "closed"]).count(),
            "urgent": base.filter(priority="urgent").exclude(status__in=["resolved", "closed", "archived"]).count(),
            "unassigned": base.filter(assigned_to__isnull=True).exclude(status__in=["resolved", "closed", "archived"]).count(),
        }
        return Response({"counts": counts, "results": [_ticket_payload(fb, request) for fb in qs]})


class SupportTicketActionView(APIView):
    """Ticket workflow actions: claim, escalate, waiting_user, resolve, reopen.

    Staff may claim unassigned tickets and act on their own tickets only
    (IDOR-guarded). Escalation notifies the admin team. Audited.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from tourist.views_admin import _require_capability as require_cap
        require_cap(request, "feedback", "change")
        from tourist.models import UserFeedback, FeedbackMessage
        fb = UserFeedback.objects.select_related("assigned_to").filter(pk=pk).first()
        if fb is None:
            return Response({"detail": "Ticket not found."}, status=404)

        action = (request.data.get("action") or "").strip().lower()
        note = (request.data.get("note") or "").strip()
        is_admin = _is_support_admin(request.user)
        is_assignee = fb.assigned_to_id == request.user.id
        error = None

        if action == "claim":
            if fb.assigned_to_id is not None:
                error = "This ticket is already assigned."
            else:
                fb.assigned_to = request.user
                if fb.status == UserFeedback.Status.NEW:
                    fb.status = UserFeedback.Status.IN_PROGRESS
        elif action == "escalate":
            if not is_admin and not is_assignee:
                error = "Only the assigned staff member may escalate this ticket."
            elif not note:
                error = "An escalation reason is required."
            else:
                fb.is_escalated = True
                fb.escalation_reason = note
                if fb.assigned_to_id is None:
                    fb.assigned_to = request.user
                FeedbackMessage.objects.create(feedback=fb, sender=request.user,
                                               body=f"[Escalated] {note}", is_internal=True)
                # Notify every admin/superuser so a supervisor picks it up.
                from django.contrib.auth import get_user_model
                for admin_user in get_user_model().objects.filter(
                    models.Q(is_superuser=True) | models.Q(role__in=["admin", "super_admin", "tourism_admin"])
                )[:10]:
                    _notify(admin_user, f"Escalated ticket: {fb.subject}"[:200], note[:300], {"ticket_id": fb.id})
        elif action == "waiting_user":
            if not is_admin and not is_assignee:
                error = "Only the assigned staff member may change this ticket."
            else:
                fb.status = UserFeedback.Status.WAITING_USER
        elif action == "resolve":
            if not is_admin and not is_assignee:
                error = "Only the assigned staff member may resolve this ticket."
            else:
                if note:
                    FeedbackMessage.objects.create(feedback=fb, sender=request.user, body=note, is_internal=False)
                    fb.admin_reply = note
                fb.status = UserFeedback.Status.RESOLVED
                fb.is_escalated = False
                fb.closed_at = timezone.now()
                if fb.user_id:
                    _notify(fb.user, f"Resolved: {fb.subject}"[:200], note or "Marked resolved by the support team.",
                            {"ticket_id": fb.id})
        elif action == "reopen":
            if not is_admin and not is_assignee:
                error = "Only the assigned staff member may reopen this ticket."
            else:
                fb.status = UserFeedback.Status.IN_PROGRESS
                fb.closed_at = None
        else:
            return Response({"detail": "Unknown action."}, status=400)

        if error:
            return Response({"detail": error}, status=400)

        fb.save()
        log_action(request=request, action=f"support.{action}", category="content",
                   message=f"Support ticket #{fb.id} '{fb.subject}' → {action} by {request.user.email}",
                   object_type="UserFeedback", object_id=fb.id)
        return Response(_ticket_payload(fb, request))


# ============================================================
# HOTELS & BOOKINGS — scope-restricted operations
# (Staff Ops spec §11-12; staff see only their assigned hotels
# and the bookings attached to them. 'hotels' capability.)
# ============================================================

def _scoped_hotel_ids(user):
    """Hotel ids this staff member manages; None means 'all' (admin)."""
    if user.is_superuser or getattr(user, "role", None) in {"admin", "super_admin", "tourism_admin"}:
        return None
    return list(
        HotelAssignment.objects.filter(admin=user).values_list("hotel_id", flat=True)
    )


def _booking_payload(b):
    return {
        "id": b.id,
        "reference": getattr(b, "booking_reference", None) or f"#{b.id}",
        "hotel_id": b.hotel_id,
        "hotel_name": b.hotel.name,
        "hotel_address": b.hotel.address,
        "customer_name": b.user.full_name,
        "customer_email": b.user.email,
        "check_in": b.check_in,
        "check_out": b.check_out,
        "guests": b.guests,
        "status": b.status,
        "total_price": str(b.total_price) if b.total_price is not None else None,
        "currency": b.currency,
        "special_requests": b.special_requests,
        "created_at": b.created_at,
    }


class MyBookingsView(APIView):
    """GET /api/v1/admin-panel/my-bookings/ — bookings inside the caller's hotel scope."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from booking.models import Booking
        from tourist.views_admin import _require_capability as require_cap

        require_cap(request, "hotels", "view")
        hotel_ids = _scoped_hotel_ids(request.user)
        qs = Booking.objects.select_related("hotel", "user")
        if hotel_ids is not None:
            qs = qs.filter(hotel_id__in=hotel_ids)
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        counts = {
            choice: Booking.objects.filter(hotel_id__in=hotel_ids).filter(status=choice).count() if hotel_ids is not None
            else Booking.objects.filter(status=choice).count()
            for choice, _label in Booking.Status.choices
        }
        counts["all"] = sum(counts.values())
        return Response({"counts": counts, "results": [_booking_payload(b) for b in qs[:100]]})


class BookingActionView(APIView):
    """POST /api/v1/admin-panel/my-bookings/<pk>/action/ — confirm/cancel/complete within scope."""

    permission_classes = [permissions.IsAuthenticated]

    ALLOWED = {"confirm", "cancel", "complete"}
    NEXT = {"confirm": "confirmed", "cancel": "cancelled", "complete": "completed"}

    def post(self, request, pk):
        from booking.models import Booking
        from tourist.views_admin import _require_capability as require_cap

        require_cap(request, "hotels", "change")
        action = (request.data.get("action") or "").strip()
        if action not in self.ALLOWED:
            return Response({"detail": f"Unknown action '{action}'. Allowed: {', '.join(sorted(self.ALLOWED))}."}, status=400)
        try:
            booking = Booking.objects.select_related("hotel", "user").get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=404)

        hotel_ids = _scoped_hotel_ids(request.user)
        if hotel_ids is not None and booking.hotel_id not in hotel_ids:
            return Response({"detail": "This booking belongs to a hotel outside your assignment."}, status=403)

        previous = booking.status
        booking.status = self.NEXT[action]
        booking.save(update_fields=["status", "updated_at"])

        note = (request.data.get("note") or "").strip()
        if action == "cancel":
            _notify(booking.user, "Booking cancelled",
                    f"Your booking at {booking.hotel.name} ({booking.check_in} → {booking.check_out}) was cancelled."
                    + (f" Reason: {note}" if note else ""),
                    metadata={"booking_id": booking.id})
        elif action == "confirm":
            _notify(booking.user, "Booking confirmed",
                    f"Your booking at {booking.hotel.name} ({booking.check_in} → {booking.check_out}) is confirmed.",
                    metadata={"booking_id": booking.id})

        log_action(request=request, action=f"booking.{action}", category="hotels",
                   message=f"Booking #{booking.id} at {booking.hotel.name}: {previous} → {booking.status}"
                           + (f" ({note})" if note else ""),
                   object_type="Booking", object_id=str(booking.id))
        return Response(_booking_payload(booking))


# ============================================================
# DESTINATION DATA ENTRY + MEDIA MANAGER
# (Staff Ops spec §13-15; DRAFT → SUBMITTED → REVIEW → APPROVED
# on the existing Destination model, image queue on the existing
# DestinationImage pipeline. No new permission systems.)
# ============================================================

def _is_reviewer(user):
    return user.is_superuser or getattr(user, "role", None) in {"admin", "super_admin", "tourism_admin"}


def _entry_payload(d):
    return {
        "id": d.id,
        "name": d.name,
        "slug": d.slug,
        "district": d.district,
        "city": d.city_english,
        "status": d.status,
        "review_note": d.review_note,
        "short_description": d.short_description,
        "submitted_by": d.submitted_by.email if d.submitted_by else None,
        "created_at": d.created_at,
        "updated_at": d.updated_at,
    }


class DataEntryListView(APIView):
    """GET/POST /api/v1/admin-panel/data-entry/ — staff drafts + submissions."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from tourist.views_admin import _require_capability as require_cap

        require_cap(request, "destinations", "view")
        qs = Destination.objects.all()
        if not _is_reviewer(request.user):
            qs = qs.filter(submitted_by=request.user)
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        else:
            qs = qs.filter(status__in=["draft", "submitted", "pending", "rejected"])
        counts = {
            choice: (qs if status else Destination.objects.filter(submitted_by=request.user) if not _is_reviewer(request.user) else Destination.objects.all()).filter(status=choice).count()
            for choice, _label in Destination.SubmissionStatus.choices
        }
        return Response({"counts": counts, "results": [_entry_payload(d) for d in qs.order_by("-updated_at")[:100]]})

    def post(self, request):
        from tourist.views_admin import _require_capability as require_cap

        require_cap(request, "destinations", "add")
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "A destination name is required."}, status=400)
        dest = Destination.objects.create(
            name=name[:200],
            district=(request.data.get("district") or "").strip()[:100],
            city_english=(request.data.get("city") or "").strip()[:100],
            short_description=(request.data.get("short_description") or "").strip()[:500],
            description=(request.data.get("description") or "").strip(),
            status=Destination.SubmissionStatus.DRAFT,
            submitted_by=request.user,
        )
        lat, lng = request.data.get("latitude"), request.data.get("longitude")
        if lat not in (None, "") and lng not in (None, ""):
            try:
                dest.latitude, dest.longitude = float(lat), float(lng)
                dest.save(update_fields=["latitude", "longitude"])
            except (TypeError, ValueError):
                pass
        log_action(request=request, action="dataentry.create", category="destinations",
                   message=f"Draft destination '{dest.name}' created", object_type="Destination", object_id=str(dest.id))
        return Response(_entry_payload(dest), status=201)


class DataEntryActionView(APIView):
    """POST /api/v1/admin-panel/data-entry/<pk>/action/ — submit/approve/reject/reopen."""

    permission_classes = [permissions.IsAuthenticated]
    ALLOWED = {"submit", "approve", "reject", "reopen"}

    def post(self, request, pk):
        from tourist.views_admin import _require_capability as require_cap
        from tourist.models import DestinationAuditLog

        require_cap(request, "destinations", "change")
        action = (request.data.get("action") or "").strip()
        if action not in self.ALLOWED:
            return Response({"detail": f"Unknown action '{action}'. Allowed: {', '.join(sorted(self.ALLOWED))}."}, status=400)
        try:
            dest = Destination.objects.get(pk=pk)
        except Destination.DoesNotExist:
            return Response({"detail": "Destination not found."}, status=404)

        note = (request.data.get("note") or "").strip()
        previous = dest.status
        actor = request.user

        if action in {"approve", "reject"}:
            require_cap(request, "destinations", "approve")
            if previous in {"approved", "archived"}:
                return Response({"detail": f"Cannot {action} a destination that is already {previous}."}, status=400)
            if action == "reject" and not note:
                return Response({"detail": "A rejection note is required so the author knows what to fix."}, status=400)
            dest.status = Destination.SubmissionStatus.APPROVED if action == "approve" else Destination.SubmissionStatus.REJECTED
            dest.review_note = note[:255] or None
        elif action == "submit":
            if not _is_reviewer(actor) and dest.submitted_by_id and dest.submitted_by_id != actor.id:
                return Response({"detail": "You can only submit entries you authored."}, status=403)
            if previous not in {"draft", "rejected"}:
                return Response({"detail": f"Only draft or rejected entries can be submitted (currently '{previous}')."}, status=400)
            dest.status = Destination.SubmissionStatus.SUBMITTED
            if not dest.submitted_by_id:
                dest.submitted_by = actor
            # let reviewers know there is something in the queue
            from tourist.models import User as _User
            for reviewer in _User.objects.filter(is_superuser=True)[:10]:
                _notify(reviewer, "Destination awaiting review",
                        f"'{dest.name}' was submitted by {actor.email} and needs review.",
                        metadata={"destination_id": dest.id})
        elif action == "reopen":
            require_cap(request, "destinations", "approve")
            dest.status = Destination.SubmissionStatus.SUBMITTED
            dest.review_note = None

        dest.save(update_fields=["status", "review_note", "submitted_by", "updated_at"])

        audit_map = {"submit": DestinationAuditLog.Action.SUBMITTED, "approve": DestinationAuditLog.Action.APPROVED,
                     "reject": DestinationAuditLog.Action.REJECTED, "reopen": DestinationAuditLog.Action.SUBMITTED}
        DestinationAuditLog.objects.create(destination=dest, action=audit_map[action], actor=actor,
                                           note=note or f"{action} from '{previous}'",
                                           previous_status=previous, new_status=dest.status)
        if action in {"approve", "reject"} and dest.submitted_by:
            _notify(dest.submitted_by, f"Destination {action}d: {dest.name}",
                    note or ("Your submission was approved and is now published." if action == "approve" else "See the review note."),
                    metadata={"destination_id": dest.id})
        log_action(request=request, action=f"dataentry.{action}", category="destinations",
                   message=f"Destination '{dest.name}': {previous} → {dest.status}" + (f" ({note})" if note else ""),
                   object_type="Destination", object_id=str(dest.id))
        return Response(_entry_payload(dest))


def _image_payload(img):
    return {
        "id": img.id,
        "destination_id": img.destination_id,
        "destination_name": img.destination.name,
        "caption": img.caption,
        "alt_text": img.alt_text,
        "external_url": img.external_url,
        "image_url": img.image.url if img.image else (img.external_url or ""),
        "status": img.verification_status,
        "created_at": img.created_at,
    }


class MediaQueueView(APIView):
    """GET/POST /api/v1/admin-panel/media/ — destination image review queue."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from tourist.views_admin import _require_capability as require_cap
        from tourist.models import DestinationImage

        require_cap(request, "images", "view")
        qs = DestinationImage.objects.select_related("destination")
        status = (request.query_params.get("status") or "").strip()
        if status:
            qs = qs.filter(verification_status=status)
        counts = {choice: DestinationImage.objects.filter(verification_status=choice).count()
                  for choice, _label in DestinationImage.ImageStatus.choices}
        counts["all"] = sum(counts.values())
        return Response({"counts": counts, "results": [_image_payload(i) for i in qs.order_by("-created_at")[:100]]})

    def post(self, request):
        from tourist.views_admin import _require_capability as require_cap
        from tourist.models import DestinationImage

        require_cap(request, "images", "add")
        destination_id = request.data.get("destination")
        url = (request.data.get("external_url") or "").strip()
        try:
            dest = Destination.objects.get(pk=destination_id)
        except (Destination.DoesNotExist, TypeError, ValueError):
            return Response({"detail": "A valid destination id is required."}, status=400)
        file = request.FILES.get("image")
        if not file and not url:
            return Response({"detail": "Provide an image file or an external_url."}, status=400)
        img = DestinationImage.objects.create(
            destination=dest,
            external_url=url[:600],
            caption=(request.data.get("caption") or "").strip()[:255],
            alt_text=(request.data.get("alt_text") or "").strip()[:255],
            verification_status=DestinationImage.ImageStatus.PENDING if not _is_reviewer(request.user) else DestinationImage.ImageStatus.APPROVED,
            **({"image": file} if file else {}),
        )
        log_action(request=request, action="image.add", category="images",
                   message=f"Image added to '{dest.name}' (status {img.verification_status})",
                   object_type="DestinationImage", object_id=str(img.id))
        return Response(_image_payload(img), status=201)


class MediaActionView(APIView):
    """POST /api/v1/admin-panel/media/<pk>/action/ — approve/reject an image."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        from tourist.views_admin import _require_capability as require_cap
        from tourist.models import DestinationImage

        require_cap(request, "images", "approve")
        action = (request.data.get("action") or "").strip()
        if action not in {"approve", "reject"}:
            return Response({"detail": "Allowed actions: approve, reject."}, status=400)
        try:
            img = DestinationImage.objects.select_related("destination").get(pk=pk)
        except DestinationImage.DoesNotExist:
            return Response({"detail": "Image not found."}, status=404)
        previous = img.verification_status
        img.verification_status = DestinationImage.ImageStatus.APPROVED if action == "approve" else DestinationImage.ImageStatus.REJECTED
        img.save(update_fields=["verification_status", "updated_at"])
        log_action(request=request, action=f"image.{action}", category="images",
                   message=f"Image #{img.id} on '{img.destination.name}': {previous} → {img.verification_status}",
                   object_type="DestinationImage", object_id=str(img.id))
        return Response(_image_payload(img))


# ============================================================
# SAFETY OPERATIONS (Staff Ops spec §16)
# Unified staff queue over the existing Alert / CurrentHazard /
# DataReport models. 'safety' capability; every action audited.
# ============================================================

def _alert_payload(a):
    return {"kind": "alert", "id": a.id, "title": a.title, "severity": a.severity,
            "type": a.alert_type, "location": a.city or a.district or "Nepal",
            "is_active": a.is_active, "is_verified": a.is_verified,
            "source": a.source, "created_at": a.created_at}


def _hazard_payload(h):
    return {"kind": "hazard", "id": h.id, "title": h.title, "severity": h.severity,
            "type": h.hazard_type, "location": h.affected_area or h.destination.name,
            "is_active": h.is_active, "is_verified": h.verified,
            "source": h.source_name, "created_at": h.observed_at or h.created_at}


def _report_payload(r):
    return {"kind": "report", "id": r.id, "title": r.description[:120] or f"{r.get_report_type_display()} report",
            "severity": r.severity, "type": r.report_type,
            "location": r.destination.name if r.destination else "General",
            "status": r.status, "reporter": r.user.email if r.user else "anonymous",
            "created_at": r.created_at}


class SafetyOpsView(APIView):
    """GET /api/v1/admin-panel/safety/ — alerts, hazards and user reports in one queue."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from tourist.views_admin import _require_capability as require_cap
        from tourist.models import Alert, CurrentHazard, DataReport

        require_cap(request, "safety", "view")
        alerts = Alert.objects.order_by("-created_at")[:10]
        hazards = CurrentHazard.objects.filter(is_active=True).select_related("destination").order_by("-observed_at")[:10]
        reports = DataReport.objects.filter(status__in=["new", "under_review", "needs_verification"]).select_related("user", "destination").order_by("-created_at")[:10]
        return Response({
            "counts": {
                "active_alerts": Alert.objects.filter(is_active=True).count(),
                "unverified_alerts": Alert.objects.filter(is_active=True, is_verified=False).count(),
                "active_hazards": CurrentHazard.objects.filter(is_active=True).count(),
                "open_reports": DataReport.objects.filter(status__in=["new", "under_review", "needs_verification"]).count(),
            },
            "alerts": [_alert_payload(a) for a in alerts],
            "hazards": [_hazard_payload(h) for h in hazards],
            "reports": [_report_payload(r) for r in reports],
        })


class SafetyActionView(APIView):
    """POST /api/v1/admin-panel/safety/<kind>/<pk>/action/ — verify/deactivate/resolve/review/fix/reject."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, kind, pk):
        from tourist.views_admin import _require_capability as require_cap
        from tourist.models import Alert, CurrentHazard, DataReport

        require_cap(request, "safety", "change")
        action = (request.data.get("action") or "").strip()
        note = (request.data.get("note") or "").strip()

        if kind == "alert":
            if action not in {"verify", "deactivate"}:
                return Response({"detail": "Alert actions: verify, deactivate."}, status=400)
            try:
                obj = Alert.objects.get(pk=pk)
            except Alert.DoesNotExist:
                return Response({"detail": "Alert not found."}, status=404)
            if action == "verify":
                obj.is_verified = True
                obj.save(update_fields=["is_verified"])
            else:
                obj.is_active = False
                obj.save(update_fields=["is_active"])
            detail = f"Alert '{obj.title}' {'verified' if action == 'verify' else 'deactivated'}"
        elif kind == "hazard":
            if action not in {"verify", "resolve"}:
                return Response({"detail": "Hazard actions: verify, resolve."}, status=400)
            try:
                obj = CurrentHazard.objects.get(pk=pk)
            except CurrentHazard.DoesNotExist:
                return Response({"detail": "Hazard not found."}, status=404)
            if action == "verify":
                obj.verified = True
                obj.save(update_fields=["verified"])
            else:
                obj.is_active = False
                obj.save(update_fields=["is_active"])
            detail = f"Hazard '{obj.title}' {'verified' if action == 'verify' else 'resolved'}"
        elif kind == "report":
            if action not in {"review", "fix", "reject"}:
                return Response({"detail": "Report actions: review, fix, reject."}, status=400)
            try:
                obj = DataReport.objects.get(pk=pk)
            except DataReport.DoesNotExist:
                return Response({"detail": "Report not found."}, status=404)
            if action == "review":
                obj.status = DataReport.Status.UNDER_REVIEW
                obj.save(update_fields=["status"])
            elif action == "fix":
                obj.status = DataReport.Status.FIXED
                obj.resolved_by = request.user
                obj.resolved_at = timezone.now()
                obj.save(update_fields=["status", "resolved_by", "resolved_at"])
            else:
                if not note:
                    return Response({"detail": "A note is required to reject a user report."}, status=400)
                obj.status = DataReport.Status.REJECTED
                obj.internal_notes = (obj.internal_notes + "\n" if obj.internal_notes else "") + f"Rejected by {request.user.email}: {note}"
                obj.save(update_fields=["status", "internal_notes"])
            detail = f"Data report #{obj.id} → {obj.status}"
        else:
            return Response({"detail": f"Unknown kind '{kind}'. Allowed: alert, hazard, report."}, status=400)

        log_action(request=request, action=f"safety.{kind}.{action}", category="safety",
                   message=detail + (f" ({note})" if note else ""),
                   object_type={"alert": "Alert", "hazard": "CurrentHazard", "report": "DataReport"}[kind],
                   object_id=str(pk))
        return Response({"ok": True, "detail": detail})
