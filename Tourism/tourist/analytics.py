"""
Advanced Analytics Module.

Tracks user engagement metrics, conversion funnels, popular destinations,
search query analytics, and real-time active users.

All functions are designed to be called from management commands, Celery tasks,
or API endpoints. Results are cached where appropriate.
"""

import logging
from collections import Counter
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, F, Max, Min, Q, Sum
from django.utils import timezone

from .models import (
    Booking,
    Destination,
    Favorite,
    Rating,
    Review,
    SearchQuery,
    User,
    VisitHistory,
)

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "analytics"
CACHE_TTL = 300  # 5 minutes


def _cache_key(name):
    return f"{CACHE_KEY_PREFIX}:v1:{name}"


# ---------------------------------------------------------------------------
# User Engagement Metrics
# ---------------------------------------------------------------------------

def get_user_engagement_metrics(days=30):
    """
    Calculate user engagement metrics for the last N days.

    Returns:
        dict with:
        - total_sessions: number of unique user sessions
        - avg_time_on_site: average session duration in minutes
        - avg_pages_per_session: average pages viewed per session
        - bounce_rate: percentage of single-page sessions
        - returning_users: count of users with 2+ sessions
    """
    cache_key = _cache_key(f"engagement:{days}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    since = timezone.now() - timedelta(days=days)

    # Sessions = unique user-day combinations with activity
    sessions = (
        VisitHistory.objects.filter(viewed_at__gte=since)
        .values("user_id")
        .annotate(
            page_views=Count("id"),
            first_view=Min("viewed_at"),
            last_view=Max("viewed_at"),
        )
    )

    total_sessions = len(sessions)
    if total_sessions == 0:
        return {
            "total_sessions": 0,
            "avg_time_on_site_minutes": 0,
            "avg_pages_per_session": 0,
            "bounce_rate": 0,
            "returning_users": 0,
        }

    durations = []
    page_counts = []
    single_page_sessions = 0

    for session in sessions:
        duration = (session["last_view"] - session["first_view"]).total_seconds() / 60
        durations.append(duration)
        page_counts.append(session["page_views"])
        if session["page_views"] <= 1:
            single_page_sessions += 1

    # Returning users: users with activity on 2+ distinct days
    returning = (
        VisitHistory.objects.filter(viewed_at__gte=since)
        .values("user_id")
        .annotate(distinct_days=Count("viewed_at__date", distinct=True))
        .filter(distinct_days__gte=2)
        .count()
    )

    result = {
        "total_sessions": total_sessions,
        "avg_time_on_site_minutes": round(sum(durations) / len(durations), 2),
        "avg_pages_per_session": round(sum(page_counts) / len(page_counts), 2),
        "bounce_rate": round(single_page_sessions / total_sessions * 100, 2),
        "returning_users": returning,
        "period_days": days,
    }

    cache.set(cache_key, result, CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Conversion Funnel
# ---------------------------------------------------------------------------

def get_conversion_funnel(days=30):
    """
    Track the conversion funnel: view → search → book.

    Returns:
        dict with:
        - views: total destination views
        - searches: total searches performed
        - bookings: total bookings made
        - view_to_search_rate: % of viewers who also searched
        - search_to_book_rate: % of searchers who also booked
        - overall_conversion: % of viewers who booked
    """
    cache_key = _cache_key(f"funnel:{days}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    since = timezone.now() - timedelta(days=days)

    views = VisitHistory.objects.filter(viewed_at__gte=since).count()
    searches = SearchQuery.objects.filter(created_at__gte=since).count()
    bookings = Booking.objects.filter(created_at__gte=since).count()

    # Users who both viewed and searched
    viewers = set(
        VisitHistory.objects.filter(viewed_at__gte=since)
        .values_list("user_id", flat=True)
        .distinct()
    )
    searchers = set(
        SearchQuery.objects.filter(created_at__gte=since)
        .values_list("user_id", flat=True)
        .distinct()
    )
    bookers = set(
        Booking.objects.filter(created_at__gte=since)
        .values_list("user_id", flat=True)
        .distinct()
    )

    view_to_search = len(viewers & searchers)
    search_to_book = len(searchers & bookers)
    view_to_book = len(viewers & bookers)

    result = {
        "views": views,
        "searches": searches,
        "bookings": bookings,
        "view_to_search_rate": round(view_to_search / max(len(viewers), 1) * 100, 2),
        "search_to_book_rate": round(search_to_book / max(len(searchers), 1) * 100, 2),
        "overall_conversion": round(view_to_book / max(len(viewers), 1) * 100, 2),
        "period_days": days,
    }

    cache.set(cache_key, result, CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Popular Destinations & Categories
# ---------------------------------------------------------------------------

def get_popular_destinations(limit=20, days=30):
    """
    Get the most popular destinations by views, ratings, and bookings.
    """
    cache_key = _cache_key(f"popular_destinations:{limit}:{days}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    since = timezone.now() - timedelta(days=days)

    destinations = (
        Destination.objects.filter(is_active=True)
        .annotate(
            recent_views=Count("visit_history", filter=Q(visit_history__viewed_at__gte=since)),
            recent_bookings=Count("bookings", filter=Q(bookings__created_at__gte=since)),
            total_favorites=Count("favorites"),
        )
        .order_by("-recent_views", "-average_rating")
        .values(
            "id", "name", "slug", "city", "country",
            "average_rating", "views_count", "recent_views",
            "recent_bookings", "total_favorites",
        )[:limit]
    )

    result = list(destinations)
    cache.set(cache_key, result, CACHE_TTL)
    return result


def get_popular_categories(limit=10, days=30):
    """
    Get the most popular categories by destination views and bookings.
    """
    cache_key = _cache_key(f"popular_categories:{limit}:{days}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    since = timezone.now() - timedelta(days=days)

    categories = (
        Destination.objects.filter(is_active=True)
        .values("category__name", "category__slug")
        .annotate(
            total_views=Sum("views_count"),
            destination_count=Count("id"),
            avg_rating=Avg("average_rating"),
        )
        .exclude(category__name=None)
        .order_by("-total_views")[:limit]
    )

    result = [
        {
            "name": c["category__name"],
            "slug": c["category__slug"],
            "total_views": c["total_views"] or 0,
            "destination_count": c["destination_count"],
            "avg_rating": round(float(c["avg_rating"] or 0), 2),
        }
        for c in categories
    ]
    cache.set(cache_key, result, CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Search Query Analytics
# ---------------------------------------------------------------------------

def get_search_analytics(limit=50, days=30):
    """
    Analyze search queries to find trending searches and zero-result queries.
    """
    cache_key = _cache_key(f"search_analytics:{limit}:{days}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    since = timezone.now() - timedelta(days=days)

    # Most common search queries
    top_searches = (
        SearchQuery.objects.filter(created_at__gte=since)
        .values("query")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )

    # Search volume over time (daily)
    daily_volume = (
        SearchQuery.objects.filter(created_at__gte=since)
        .extra({"date": "date(created_at)"})
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    result = {
        "top_searches": [
            {"query": s["query"], "count": s["count"]}
            for s in top_searches
        ],
        "daily_volume": [
            {"date": str(d["date"]), "count": d["count"]}
            for d in daily_volume
        ],
        "total_searches": SearchQuery.objects.filter(created_at__gte=since).count(),
        "unique_searchers": (
            SearchQuery.objects.filter(created_at__gte=since)
            .values("user_id")
            .distinct()
            .count()
        ),
        "period_days": days,
    }

    cache.set(cache_key, result, CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Real-Time Active Users
# ---------------------------------------------------------------------------

def get_active_users(minutes=15):
    """
    Get the number of currently active users (active in the last N minutes).

    Uses the cache to track active user IDs with TTL-based expiration.
    """
    cache_key = _cache_key("active_users")
    active_user_ids = cache.get(cache_key) or set()

    # Clean up expired entries (users whose last activity was too long ago)
    cutoff = timezone.now() - timedelta(minutes=minutes)
    # We store (user_id, last_seen) tuples
    cleaned = {uid for uid, last_seen in active_user_ids if last_seen > cutoff}

    return len(cleaned)


def mark_user_active(user_id):
    """
    Mark a user as currently active. Called by middleware on each request.
    """
    cache_key = _cache_key("active_users")
    active_user_ids = cache.get(cache_key) or set()

    # Remove old entry for this user if exists
    active_user_ids = {item for item in active_user_ids if item[0] != user_id}
    active_user_ids.add((user_id, timezone.now()))

    # Keep only last 10000 entries to prevent unbounded growth
    if len(active_user_ids) > 10000:
        active_user_ids = set(sorted(active_user_ids, key=lambda x: x[1], reverse=True)[:5000])

    cache.set(cache_key, active_user_ids, 1800) # 30 min TTL


def get_realtime_stats():
    """
    Get a snapshot of real-time platform statistics.
    """
    return {
        "active_users_15min": get_active_users(minutes=15),
        "active_users_5min": get_active_users(minutes=5),
        "active_users_1min": get_active_users(minutes=1),
        "total_users": User.objects.filter(is_active=True).count(),
        "total_destinations": Destination.objects.filter(is_active=True).count(),
        "total_bookings": Booking.objects.count(),
        "total_reviews": Review.objects.count(),
        "timestamp": timezone.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# User Retention
# ---------------------------------------------------------------------------

def get_retention_metrics(days=30):
    """
    Calculate user retention metrics.

    Returns:
        dict with:
        - new_users: users who joined in the period
        - retained_users: new users who returned after their first day
        - retention_rate: percentage of new users who returned
    """
    cache_key = _cache_key(f"retention:{days}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    since = timezone.now() - timedelta(days=days)

    new_users = User.objects.filter(date_joined__gte=since)
    new_user_ids = set(new_users.values_list("id", flat=True))

    if not new_user_ids:
        return {"new_users": 0, "retained_users": 0, "retention_rate": 0}

    # Retained = new users who had activity after their join date
    retained = (
        VisitHistory.objects.filter(
            user_id__in=new_user_ids,
            viewed_at__gte=since,
        )
        .values("user_id")
        .distinct()
        .count()
    )

    result = {
        "new_users": len(new_user_ids),
        "retained_users": retained,
        "retention_rate": round(retained / len(new_user_ids) * 100, 2),
        "period_days": days,
    }

    cache.set(cache_key, result, CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# Invalidate all analytics caches
# ---------------------------------------------------------------------------

def invalidate_all_caches():
    """Invalidate all analytics cache entries."""
    # Since we use a prefix pattern, we can delete by pattern if using
    # a cache backend that supports it (Redis). For LocMemCache, we track
    # keys manually or just let them expire.
    cache.delete(_cache_key("engagement:30"))
    cache.delete(_cache_key("funnel:30"))
    cache.delete(_cache_key("popular_destinations:20:30"))
    cache.delete(_cache_key("popular_categories:10:30"))
    cache.delete(_cache_key("search_analytics:50:30"))
    cache.delete(_cache_key("retention:30"))
    cache.delete(_cache_key("active_users"))
