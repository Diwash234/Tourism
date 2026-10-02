"""Recommendation engine for personalized destination suggestions.

Provides:
- Collaborative filtering (user-item interactions)
- Content-based filtering (destination features)
- Hybrid recommendations
- Trending destinations
- Personalized feed
"""
import logging
from collections import defaultdict
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.cache import cache

from .models import (
    Destination, DestinationImage, Review, Rating, Favorite,
    VisitHistory, UserPreferenceProfile, RecommendationEvent,
    DestinationFeatureProfile,
)

logger = logging.getLogger(__name__)


def get_recommendations(user_id, limit=10):
    """Get personalized recommendations for a user.

    Uses a hybrid approach combining collaborative filtering and
    content-based filtering.

    Args:
        user_id: User ID
        limit: Maximum number of recommendations

    Returns:
        List of recommended destinations
    """
    cache_key = f"recommendations:user:{user_id}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # Get user's preference profile
        profile = UserPreferenceProfile.objects.filter(user_id=user_id).first()

        # Get user's visit history
        visited = set(VisitHistory.objects.filter(user_id=user_id).values_list('destination_id', flat=True))

        # Get user's favorites
        favorited = set(Favorite.objects.filter(user_id=user_id).values_list('destination_id', flat=True))

        # Combine visited and favorited as "interacted"
        interacted = visited | favorited

        # Content-based scores
        content_scores = _content_based_scores(profile, interacted)

        # Collaborative scores
        collab_scores = _collaborative_scores(user_id, interacted)

        # Combine scores (hybrid)
        combined = {}
        for dest_id in set(content_scores.keys()) | set(collab_scores.keys()):
            combined[dest_id] = (
                content_scores.get(dest_id, 0) * 0.6 +
                collab_scores.get(dest_id, 0) * 0.4
            )

        # Sort and filter
        sorted_destinations = sorted(combined.items(), key=lambda x: -x[1])

        # Get destination objects
        dest_ids = [d[0] for d in sorted_destinations[:limit]]
        destinations = Destination.publicly_visible().filter(id__in=dest_ids)

        # Preserve order
        dest_map = {d.id: d for d in destinations}
        result = [dest_map[did] for did in dest_ids if did in dest_map]

        # Cache for 1 hour
        cache.set(cache_key, result, 3600)

        return result

    except Exception as exc:
        logger.error(f"Error generating recommendations for user {user_id}: {exc}")
        return get_trending_destinations(limit)


def get_similar_destinations(destination_id, limit=5):
    """Get destinations similar to a given destination.

    Uses category, district, and feature profile similarity.

    Args:
        destination_id: Destination ID
        limit: Maximum number of similar destinations

    Returns:
        List of similar destinations
    """
    cache_key = f"similar:destination:{destination_id}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        source = Destination.objects.get(id=destination_id)

        # Get feature profiles for scoring
        source_profile = DestinationFeatureProfile.objects.filter(destination=source).first()

        # Find candidates in same category/district
        candidates = Destination.publicly_visible().exclude(id=destination_id).filter(
            Q(category=source.category) | Q(district=source.district)
        )[:50]

        scored = []
        for candidate in candidates:
            score = 0.0

            # Same category
            if candidate.category == source.category:
                score += 0.3

            # Same district
            if candidate.district == source.district:
                score += 0.2

            # Feature similarity
            candidate_profile = DestinationFeatureProfile.objects.filter(destination=candidate).first()
            if source_profile and candidate_profile:
                score += _feature_similarity(source_profile, candidate_profile) * 0.5

            scored.append((candidate, score))

        # Sort by score
        scored.sort(key=lambda x: -x[1])
        result = [s[0] for s in scored[:limit]]

        # Cache for 30 minutes
        cache.set(cache_key, result, 1800)

        return result

    except Destination.DoesNotExist:
        return []
    except Exception as exc:
        logger.error(f"Error finding similar destinations: {exc}")
        return []


def get_trending_destinations(limit=10):
    """Get trending destinations based on recent activity.

    Considers views, reviews, and favorites in the last 7 days.

    Args:
        limit: Maximum number of destinations

    Returns:
        List of trending destinations
    """
    cache_key = f"trending:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        week_ago = timezone.now() - timedelta(days=7)

        # Get destinations with recent activity
        trending = Destination.publicly_visible().annotate(
            recent_views=Count('visit_history', filter=Q(visit_history__viewed_at__gte=week_ago)),
            recent_reviews=Count('reviews', filter=Q(reviews__created_at__gte=week_ago)),
            recent_favorites=Count('favorited_by', filter=Q(favorited_by__created_at__gte=week_ago)),
            avg_rating=Avg('ratings__value'),
        ).order_by(
            '-recent_views', '-recent_reviews', '-recent_favorites', '-avg_rating'
        )[:limit]

        result = list(trending)

        # Cache for 15 minutes
        cache.set(cache_key, result, 900)

        return result

    except Exception as exc:
        logger.error(f"Error getting trending destinations: {exc}")
        return []


def get_personalized_feed(user_id, limit=20):
    """Get a personalized feed for the user's homepage.

    Mixes recommendations, trending, and new destinations.

    Args:
        user_id: User ID
        limit: Maximum number of items

    Returns:
        List of destinations for the feed
    """
    try:
        # Get personalized recommendations (60%)
        recommendations = get_recommendations(user_id, limit=int(limit * 0.6))

        # Get trending (30%)
        trending = get_trending_destinations(limit=int(limit * 0.3))

        # Get new destinations (10%)
        new_destinations = Destination.publicly_visible().order_by('-created_at')[:int(limit * 0.1)]

        # Combine and deduplicate
        seen = set()
        feed = []

        for dest in recommendations + trending + list(new_destinations):
            if dest.id not in seen:
                seen.add(dest.id)
                feed.append(dest)
                if len(feed) >= limit:
                    break

        return feed

    except Exception as exc:
        logger.error(f"Error generating personalized feed: {exc}")
        return get_trending_destinations(limit)


def track_recommendation_event(user_id, destination_id, event_type, score=None, context=None):
    """Track a recommendation event for analytics.

    Args:
        user_id: User ID
        destination_id: Destination ID
        event_type: Type of event (impression, select, view, save, rating)
        score: Recommendation score (optional)
        context: Additional context (dict)
    """
    try:
        RecommendationEvent.objects.create(
            user_id=user_id,
            destination_id=destination_id,
            event_type=event_type,
            score=score,
            context=context or {},
        )
    except Exception as exc:
        logger.error(f"Error tracking recommendation event: {exc}")


def _content_based_scores(profile, interacted):
    """Calculate content-based scores for destinations.

    Args:
        profile: UserPreferenceProfile instance
        interacted: Set of destination IDs the user has interacted with

    Returns:
        Dict mapping destination_id -> score
    """
    scores = defaultdict(float)

    if not profile:
        return scores

    # Get all candidate destinations
    candidates = Destination.publicly_visible().exclude(id__in=interacted)

    for dest in candidates:
        dest_profile = DestinationFeatureProfile.objects.filter(destination=dest).first()
        if not dest_profile:
            continue

        # Calculate weighted score based on user preferences
        score = 0.0
        score += dest_profile.culture_score * profile.culture_weight
        score += dest_profile.adventure_score * profile.adventure_weight
        score += dest_profile.nature_score * profile.nature_weight
        score += dest_profile.spiritual_score * profile.spiritual_weight
        score += dest_profile.wildlife_score * profile.wildlife_weight
        score += dest_profile.photography_score * profile.photography_weight
        score += dest_profile.family_score * profile.family_weight

        # Normalize by total weight
        total_weight = (
            profile.culture_weight + profile.adventure_weight +
            profile.nature_weight + profile.spiritual_weight +
            profile.wildlife_weight + profile.photography_weight +
            profile.family_weight
        )
        if total_weight > 0:
            score /= total_weight

        scores[dest.id] = score

    return scores


def _collaborative_scores(user_id, interacted):
    """Calculate collaborative filtering scores.

    Finds users with similar tastes and recommends what they liked.

    Args:
        user_id: User ID
        interacted: Set of destination IDs the user has interacted with

    Returns:
        Dict mapping destination_id -> score
    """
    scores = defaultdict(float)

    try:
        # Find similar users (users who favorited the same destinations)
        similar_users = Favorite.objects.filter(
            destination_id__in=interacted
        ).exclude(user_id=user_id).values_list('user_id', flat=True).distinct()[:20]

        if not similar_users:
            return scores

        # Get destinations that similar users favorited
        similar_favorites = Favorite.objects.filter(
            user_id__in=similar_users
        ).exclude(destination_id__in=interacted).values('destination_id').annotate(
            count=Count('id')
        ).order_by('-count')[:50]

        for fav in similar_favorites:
            scores[fav['destination_id']] = fav['count'] / len(similar_users)

    except Exception as exc:
        logger.error(f"Error in collaborative filtering: {exc}")

    return scores


def _feature_similarity(profile_a, profile_b):
    """Calculate similarity between two feature profiles.

    Args:
        profile_a: DestinationFeatureProfile instance
        profile_b: DestinationFeatureProfile instance

    Returns:
        Similarity score (0-1)
    """
    attributes = [
        'nature_score', 'adventure_score', 'culture_score',
        'spiritual_score', 'wildlife_score', 'photography_score',
        'family_score', 'accessibility_score',
    ]

    # Calculate Euclidean distance
    distance = sum(
        (getattr(profile_a, attr, 0) - getattr(profile_b, attr, 0)) ** 2
        for attr in attributes
    ) ** 0.5

    # Convert to similarity (max distance is ~14.14 for 8 attributes with range 0-5)
    max_distance = (8 * 25) ** 0.5  # ~14.14
    similarity = 1 - (distance / max_distance)

    return max(0, similarity)
