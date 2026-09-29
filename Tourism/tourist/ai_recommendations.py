"""
AI-Powered Recommendation Engine.

Analyzes user behavior (views, searches, bookings) to generate personalized
destination recommendations using collaborative filtering with a popularity-
based fallback. Results are cached per user for 1 hour.

Usage:
    from tourist.ai_recommendations import get_recommendations
    recommendations = get_recommendations(user, limit=10)
"""

import logging
import random
from collections import Counter, defaultdict
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from .models import Booking, Destination, Favorite, Rating, Review, SearchQuery, VisitHistory

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 hour
CACHE_KEY_PREFIX = "ai_recs"


def _cache_key(user_id):
    return f"{CACHE_KEY_PREFIX}:v1:user_{user_id}"


def get_recommendations(user, limit=10, include_reason=False):
    """
    Get personalized destination recommendations for a user.

    Strategy:
    1. Collaborative filtering: find users with similar tastes and recommend
       what they liked but the current user hasn't seen.
    2. Content-based: recommend destinations similar to ones the user has
       viewed, rated highly, or bookmarked.
    3. Popularity fallback: if insufficient data, return popular destinations.

    Args:
        user: The User instance to generate recommendations for.
        limit: Maximum number of recommendations to return.
        include_reason: If True, include a 'reason' field explaining each rec.

    Returns:
        List of dicts with destination data and optional 'reason' and 'score'.
    """
    cache_key = _cache_key(user.id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached[:limit]

    recommendations = []

    # Gather user's interaction history
    viewed_ids = set(VisitHistory.objects.filter(user=user).values_list("destination_id", flat=True))
    favorited_ids = set(Favorite.objects.filter(user=user).values_list("destination_id", flat=True))
    booked_ids = set(Booking.objects.filter(user=user).values_list("hotel__destination_id", flat=True))
    rated_ids = set(Rating.objects.filter(user=user).values_list("destination_id", flat=True))
    reviewed_ids = set(Review.objects.filter(user=user).values_list("destination_id", flat=True))

    # All destinations the user has already interacted with
    seen_ids = viewed_ids | favorited_ids | booked_ids | rated_ids | reviewed_ids

    # --- Collaborative Filtering ---
    collab_recs = _collaborative_filtering(user, seen_ids, limit=limit * 2)
    recommendations.extend(collab_recs)

    # --- Content-Based Filtering ---
    content_recs = _content_based_filtering(user, seen_ids, viewed_ids, rated_ids, limit=limit * 2)
    recommendations.extend(content_recs)

    # --- Popularity Fallback ---
    if len(recommendations) < limit:
        popular_recs = _popularity_based(seen_ids, limit=limit * 2)
        recommendations.extend(popular_recs)

    # Deduplicate and rank
    seen_dest_ids = set()
    ranked = []
    for rec in recommendations:
        dest_id = rec["destination_id"]
        if dest_id not in seen_dest_ids:
            seen_dest_ids.add(dest_id)
            ranked.append(rec)

    # Sort by score descending
    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Enrich with destination data
    dest_ids = [r["destination_id"] for r in ranked[:limit]]
    destinations = {d.id: d for d in Destination.objects.filter(id__in=dest_ids, is_active=True)}

    result = []
    for rec in ranked[:limit]:
        dest = destinations.get(rec["destination_id"])
        if dest:
            item = {
                "destination_id": dest.id,
                "name": dest.name,
                "slug": dest.slug,
                "city": dest.city,
                "country": dest.country,
                "category": dest.category.name if dest.category else None,
                "average_rating": float(dest.average_rating) if dest.average_rating else 0,
                "cover_image": dest.cover_image.url if dest.cover_image else None,
                "score": round(rec.get("score", 0), 3),
            }
            if include_reason:
                item["reason"] = rec.get("reason", "Popular among similar travelers")
            result.append(item)

    # Cache the results
    cache.set(cache_key, result, CACHE_TTL)
    return result


def _collaborative_filtering(user, seen_ids, limit=20):
    """
    Find users with similar taste and recommend what they liked.

    Looks at users who viewed/rated the same destinations as the current user,
    then recommends highly-rated destinations from those similar users that
    the current user hasn't seen yet.
    """
    if not seen_ids:
        return []

    # Find similar users (those who interacted with the same destinations)
    similar_user_ids = set(
        VisitHistory.objects.filter(destination_id__in=seen_ids)
        .exclude(user=user)
        .values_list("user_id", flat=True)
    )
    similar_user_ids.update(
        Rating.objects.filter(destination_id__in=seen_ids)
        .exclude(user=user)
        .values_list("user_id", flat=True)
    )
    similar_user_ids.update(
        Favorite.objects.filter(destination_id__in=seen_ids)
        .exclude(user=user)
        .values_list("user_id", flat=True)
    )

    if not similar_user_ids:
        return []

    # Get destinations that similar users liked (high ratings, favorites)
    candidate_scores = defaultdict(float)

    # High ratings from similar users
    high_ratings = Rating.objects.filter(
        user_id__in=similar_user_ids,
        value__gte=4,
    ).exclude(destination_id__in=seen_ids)

    for rating in high_ratings:
        candidate_scores[rating.destination_id] += rating.value * 2

    # Favorites from similar user
    favorites = Favorite.objects.filter(
        user_id__in=similar_user_ids,
    ).exclude(destination_id__in=seen_ids)

    for fav in favorites:
        candidate_scores[fav.destination_id] += 5

    # Bookings from similar users
    bookings = Booking.objects.filter(
        user_id__in=similar_user_ids,
    ).exclude(hotel__destination_id__in=seen_ids)

    for booking in bookings:
        candidate_scores[booking.hotel.destination_id] += 8

    # Build recommendations
    recommendations = []
    for dest_id, score in sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)[:limit]:
        recommendations.append({
            "destination_id": dest_id,
            "score": score,
            "reason": "Travelers with similar taste enjoyed this",
        })

    return recommendations


def _content_based_filtering(user, seen_ids, viewed_ids, rated_ids, limit=20):
    """
    Recommend destinations similar to ones the user has shown interest in.

    Uses category, city, and tags to find similar destinations.
    """
    if not seen_ids:
        return []

    # Get categories and cities the user is interested in
    user_destinations = Destination.objects.filter(id__in=seen_ids)

    categories = set()
    cities = set()
    for dest in user_destinations:
        if dest.category_id:
            categories.add(dest.category_id)
        if dest.city:
            cities.add(dest.city)

    if not categories and not cities:
        return []

    # Find similar destinations
    similar_qs = Destination.objects.filter(
        is_active=True,
        status=Destination.SubmissionStatus.APPROVED,
    ).exclude(id__in=seen_ids)

    category_filter = Q()
    if categories:
        category_filter |= Q(category_id__in=categories)
    if cities:
        category_filter |= Q(city__in=cities)

    similar_destinations = similar_qs.filter(category_filter).annotate(
        popularity_score=Count("views_count"),
    ).order_by("-average_rating", "-views_count")[:limit]

    recommendations = []
    for dest in similar_destinations:
        score = float(dest.average_rating) * 10 + min(dest.views_count / 100, 5)
        reason = "Similar to places you've shown interest in"
        if dest.category_id in categories:
            reason = f"More {dest.category.name} destinations you might like"
        recommendations.append({
            "destination_id": dest.id,
            "score": score,
            "reason": reason,
        })

    return recommendations


def _popularity_based(seen_ids, limit=20):
    """
    Fallback: recommend popular destinations the user hasn't seen.
    """
    popular = Destination.objects.filter(
        is_active=True,
        status=Destination.SubmissionStatus.APPROVED,
    ).exclude(id__in=seen_ids).order_by("-views_count", "-average_rating")[:limit]

    recommendations = []
    for dest in popular:
        score = min(dest.views_count / 1000, 10) + float(dest.average_rating)
        recommendations.append({
            "destination_id": dest.id,
            "score": score,
            "reason": "Popular among travelers",
        })

    return recommendations


def invalidate_cache(user_id):
    """Invalidate cached recommendations for a user."""
    cache.delete(_cache_key(user_id))


def record_search(user, query):
    """
    Record a search query for analytics and recommendation improvement.
    """
    if not query or not query.strip():
        return
    SearchQuery.objects.create(
        user=user,
        query=query.strip()[:500],
    )


def get_trending_destinations(limit=10):
    """
    Get currently trending destinations based on recent activity.
    """
    cache_key = f"{CACHE_KEY_PREFIX}:v1:trending"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached[:limit]

    # Trending = most viewed in the last 7 days
    week_ago = timezone.now() - timedelta(days=7)

    trending = Destination.objects.filter(
        is_active=True,
        status=Destination.SubmissionStatus.APPROVED,
        visit_history__viewed_at__gte=week_ago,
    ).annotate(
        recent_views=Count("visit_history"),
    ).order_by("-recent_views", "-average_rating")[:limit]

    result = [
        {
            "destination_id": d.id,
            "name": d.name,
            "slug": d.slug,
            "city": d.city,
            "recent_views": d.recent_views,
            "average_rating": float(d.average_rating) if d.average_rating else 0,
        }
        for d in trending
    ]

    cache.set(cache_key, result, 1800)  # 30 min cache
    return result
