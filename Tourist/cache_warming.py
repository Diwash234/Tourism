"""Cache warming system.

Provides:
- Pre-load popular destinations into cache
- Pre-load search results for common queries
- Pre-load CMS content
- Cache warming orchestration
"""
import logging

from django.core.cache import cache
from django.db.models import Count

from .models import Destination, ManagedPage, ContentSection
from .cache_manager import CacheKeys, make_key

logger = logging.getLogger(__name__)


def warm_destination_cache(limit=100):
    """Pre-load popular destinations into cache.

    Args:
        limit: Number of destinations to warm

    Returns:
        Number of destinations cached
    """
    try:
        # Get popular destinations
        popular = Destination.publicly_visible().annotate(
            view_count=Count('visit_history')
        ).order_by('-view_count')[:limit]

        count = 0
        for dest in popular:
            cache_key = CacheKeys.destination_detail(dest.slug)
            cache.set(cache_key, dest, 3600)
            count += 1

        logger.info(f"Warmed destination cache: {count} destinations")
        return count

    except Exception as exc:
        logger.error(f"Error warming destination cache: {exc}")
        return 0


def warm_search_cache(queries=None):
    """Pre-load search results for common queries.

    Args:
        queries: List of search queries to warm

    Returns:
        Number of search results cached
    """
    if queries is None:
        # Default popular queries
        queries = [
            'pokhara', 'kathmandu', 'everest', 'annapurna',
            'chitwan', 'lumbini', 'bhaktapur', 'nagarkot',
        ]

    try:
        from .search_index import search

        count = 0
        for query in queries:
            results = search(query, limit=20)
            cache_key = CacheKeys.search_results(query)
            cache.set(cache_key, results, 1800)
            count += 1

        logger.info(f"Warmed search cache: {count} queries")
        return count

    except Exception as exc:
        logger.error(f"Error warming search cache: {exc}")
        return 0


def warm_cms_cache():
    """Pre-load CMS content into cache.

    Returns:
        Number of CMS items cached
    """
    try:
        # Cache published pages
        pages = ManagedPage.objects.filter(status='published', is_enabled=True)
        for page in pages:
            cache_key = make_key("cms", "page", page.key)
            cache.set(cache_key, page, 3600)

        # Cache published sections
        sections = ContentSection.objects.filter(status='published', is_visible=True)
        for section in sections:
            cache_key = make_key("cms", "section", section.page.key, section.key)
            cache.set(cache_key, section, 3600)

        count = pages.count() + sections.count()
        logger.info(f"Warmed CMS cache: {count} items")
        return count

    except Exception as exc:
        logger.error(f"Error warming CMS cache: {exc}")
        return 0


def warm_nearby_cache(centers=None, radius_km=50):
    """Pre-load nearby destinations for common centers.

    Args:
        centers: List of (lat, lon) tuples
        radius_km: Search radius in km

    Returns:
        Number of nearby results cached
    """
    if centers is None:
        # Default centers (major cities)
        centers = [
            (27.7172, 85.3240),  # Kathmandu
            (28.2096, 83.9560),  # Pokhara
            (27.6727, 85.3240),  # Lalitpur
            (27.6710, 85.4298),  # Bhaktapur
        ]

    try:
        from .models import Destination

        count = 0
        for lat, lon in centers:
            # Get destinations within radius
            nearby = Destination.publicly_visible().filter(
                latitude__range=(lat - 0.5, lat + 0.5),
                longitude__range=(lon - 0.5, lon + 0.5),
            )[:50]

            cache_key = CacheKeys.nearby_destinations(lat, lon, radius_km)
            cache.set(cache_key, list(nearby), 1800)
            count += 1

        logger.info(f"Warmed nearby cache: {count} centers")
        return count

    except Exception as exc:
        logger.error(f"Error warming nearby cache: {exc}")
        return 0


def warm_all():
    """Run all cache warming tasks.

    Returns:
        Dict with warming statistics
    """
    logger.info("Starting cache warming...")

    stats = {
        'destinations': warm_destination_cache(),
        'search': warm_search_cache(),
        'cms': warm_cms_cache(),
        'nearby': warm_nearby_cache(),
    }

    total = sum(stats.values())
    logger.info(f"Cache warming complete: {total} items cached")

    return stats


def get_warming_stats():
    """Get cache warming statistics.

    Returns:
        Dict with statistics
    """
    return {
        'last_warm_time': cache.get('cache_warm_last_run'),
        'total_items': cache.get('cache_warm_total_items', 0),
    }
