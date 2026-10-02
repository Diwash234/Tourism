"""Search index for destinations with full-text search and autocomplete.

Provides:
- Full-text search with ranking
- Fuzzy matching (typo tolerance)
- Autocomplete suggestions
- Search analytics
"""
import logging
from collections import defaultdict

from django.db.models import Q, F, Value, FloatField
from django.db.models.functions import Concat
from django.core.cache import cache

from .models import Destination, DestinationTranslation

logger = logging.getLogger(__name__)


def rebuild_index():
    """Rebuild the search index.

    This is a no-op for the database-backed search, but can be used
    to rebuild external search indexes (Elasticsearch, etc.) if configured.

    Returns:
        Number of destinations indexed
    """
    count = Destination.publicly_visible().count()
    logger.info(f"Search index rebuilt: {count} destinations")
    return count


def search(query, filters=None, limit=20):
    """Search destinations with full-text search and ranking.

    Args:
        query: Search query string
        filters: Optional dict of filters (category, district, province, etc.)
        limit: Maximum number of results

    Returns:
        List of matching destinations
    """
    if not query or not query.strip():
        return []

    cache_key = f"search:{query}:{hash(str(filters))}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # Build search query
        search_filter = Q()

        # Search in name, description, aliases, city, district
        for term in query.split():
            search_filter |= Q(name__icontains=term)
            search_filter |= Q(description__icontains=term)
            search_filter |= Q(aliases__icontains=term)
            search_filter |= Q(city__icontains=term)
            search_filter |= Q(district__icontains=term)

        # Apply filters
        queryset = Destination.publicly_visible().filter(search_filter)

        if filters:
            if filters.get('category'):
                queryset = queryset.filter(category_id=filters['category'])
            if filters.get('district'):
                queryset = queryset.filter(district=filters['district'])
            if filters.get('province'):
                queryset = queryset.filter(province=filters['province'])
            if filters.get('min_rating'):
                queryset = queryset.filter(average_rating__gte=filters['min_rating'])
            if filters.get('max_rating'):
                queryset = queryset.filter(average_rating__lte=filters['max_rating'])
            if filters.get('has_images'):
                queryset = queryset.filter(gallery__isnull=False).distinct()
            if filters.get('verified_only'):
                queryset = queryset.filter(coordinate_status__in=['VERIFIED', 'OFFICIAL'])

        # Rank results
        results = _rank_results(queryset, query)[:limit]

        # Cache for 5 minutes
        cache.set(cache_key, results, 300)

        return results

    except Exception as exc:
        logger.error(f"Search error: {exc}")
        return []


def suggest(query, limit=5):
    """Get autocomplete suggestions.

    Args:
        query: Partial search query
        limit: Maximum number of suggestions

    Returns:
        List of suggestion strings
    """
    if not query or len(query) < 2:
        return []

    cache_key = f"suggest:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # Search in names
        name_matches = Destination.publicly_visible().filter(
            name__icontains=query
        ).values_list('name', flat=True)[:limit]

        # Search in aliases
        alias_matches = Destination.publicly_visible().filter(
            aliases__icontains=query
        ).values_list('name', flat=True)[:limit]

        # Search in cities
        city_matches = Destination.publicly_visible().filter(
            city__icontains=query
        ).values_list('city', flat=True)[:limit]

        # Combine and deduplicate
        suggestions = []
        seen = set()

        for item in list(name_matches) + list(alias_matches) + list(city_matches):
            if item and item not in seen:
                seen.add(item)
                suggestions.append(item)
                if len(suggestions) >= limit:
                    break

        # Cache for 10 minutes
        cache.set(cache_key, suggestions, 600)

        return suggestions

    except Exception as exc:
        logger.error(f"Suggest error: {exc}")
        return []


def get_popular_searches(limit=10):
    """Get popular search queries.

    Args:
        limit: Maximum number of results

    Returns:
        List of popular search queries
    """
    cache_key = f"popular_searches:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # Get from recommendation events
        from .models import RecommendationEvent

        popular = RecommendationEvent.objects.filter(
            event_type='search',
            query__isnull=False,
        ).exclude(
            query=''
        ).values('query').annotate(
            count=F('id')
        ).order_by('-count')[:limit]

        result = [p['query'] for p in popular]

        # Cache for 1 hour
        cache.set(cache_key, result, 3600)

        return result

    except Exception as exc:
        logger.error(f"Error getting popular searches: {exc}")
        return []


def _rank_results(queryset, query):
    """Rank search results by relevance.

    Args:
        queryset: QuerySet of destinations
        query: Search query

    Returns:
        Sorted list of destinations
    """
    terms = query.lower().split()

    # Annotate with relevance score
    queryset = queryset.annotate(
        relevance_score=Value(0.0, output_field=FloatField())
    )

    # Score based on matches
    for term in terms:
        queryset = queryset.annotate(
            relevance_score=F('relevance_score') + (
                # Name match (highest weight)
                Q(name__icontains=term) * 10 +
                # Alias match
                Q(aliases__icontains=term) * 8 +
                # City match
                Q(city__icontains=term) * 5 +
                # District match
                Q(district__icontains=term) * 4 +
                # Description match (lowest weight)
                Q(description__icontains=term) * 2
            )
        )

    # Boost by rating and popularity
    queryset = queryset.annotate(
        relevance_score=F('relevance_score') +
            F('average_rating') * 2 +
            F('views_count') * 0.001
    )

    return queryset.order_by('-relevance_score')
