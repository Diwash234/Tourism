"""
Advanced Cache Manager.

Provides:
- Cache versioning (invalidate all keys with a version bump)
- Cache warming for popular endpoints
- Cache invalidation patterns
- Cache statistics and monitoring

Usage:
    from tourist.cache_manager import CacheManager
    cache = CacheManager()
    cache.warm_popular_destinations()
    cache.invalidate_pattern("dest:*")
    stats = cache.get_statistics()
"""

import logging
import time
from collections import defaultdict
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count

from .models import Destination, VisitHistory

logger = logging.getLogger(__name__)

CACHE_KEY_PREFIX = "cache_mgr"
DEFAULT_CACHE_TTL = 3600  # 1 hour


class CacheManager:
    """
    Advanced cache management with versioning, warming, and statistics.
    """

    VERSION_KEY = f"{CACHE_KEY_PREFIX}:version"
    STATS_KEY = f"{CACHE_KEY_PREFIX}:stats"

    def __init__(self):
        self._local_stats = defaultdict(lambda: {"hits": 0, "misses": 0, "sets": 0})

    # ------------------------------------------------------------------
    # Cache Versioning
    # ------------------------------------------------------------------

    @staticmethod
    def get_version():
        """Get the current cache version."""
        version = cache.get(CacheManager.VERSION_KEY)
        if version is None:
            version = 1
            cache.set(CacheManager.VERSION_KEY, version, timeout=0)  # Never expire
        return version

    @staticmethod
    def bump_version():
        """
        Bump the cache version, effectively invalidating all versioned keys.

        Returns:
            The new version number.
        """
        try:
            new_version = cache.incr(CacheManager.VERSION_KEY)
        except ValueError:
            # Key doesn't exist yet
            cache.set(CacheManager.VERSION_KEY, 2, timeout=0)
            new_version = 2
        logger.info(f"Cache version bumped to {new_version}")
        return new_version

    @classmethod
    def versioned_key(cls, key):
        """Create a versioned cache key."""
        return f"{CACHE_KEY_PREFIX}:v{cls.get_version()}:{key}"

    # ------------------------------------------------------------------
    # Cache Warming
    # ------------------------------------------------------------------

    def warm_popular_destinations(self, limit=50):
        """
        Pre-cache popular destinations for faster response times.

        Args:
            limit: Number of top destinations to warm.

        Returns:
            Number of destinations cached.
        """
        popular = (
            Destination.objects.filter(
                is_active=True,
                status=Destination.SubmissionStatus.APPROVED,
            )
            .order_by("-views_count", "-average_rating")[:limit]
        )

        count = 0
        for dest in popular:
            key = self.versioned_key(f"dest:detail:{dest.id}")
            cache.set(key, dest, timeout=DEFAULT_CACHE_TTL)
            count += 1

        # Also warm the popular list itself
        list_key = self.versioned_key("dest:popular:list")
        cache.set(list_key, list(popular.values("id", "name", "slug", "city", "average_rating")), timeout=DEFAULT_CACHE_TTL)

        logger.info(f"Warmed {count} popular destinations into cache")
        return count

    def warm_category_list(self):
        """Pre-cache the category list."""
        from .models import Category

        categories = list(Category.objects.filter(is_active=True).values("id", "name", "slug"))
        key = self.versioned_key("categories:list")
        cache.set(key, categories, timeout=DEFAULT_CACHE_TTL * 2)  # 2 hours
        logger.info(f"Warmed {len(categories)} categories into cache")
        return len(categories)

    def warm_trending_searches(self):
        """Pre-cache trending search queries."""
        from .models import SearchQuery

        week_ago = timezone.now() - timedelta(days=7)
        trending = (
            SearchQuery.objects.filter(created_at__gte=week_ago)
            .values("query")
            .annotate(count=Count("id"))
            .order_by("-count")[:20]
        )

        key = self.versioned_key("searches:trending")
        cache.set(key, list(trending), timeout=1800)  # 30 min
        logger.info(f"Warmed {len(trending)} trending searches into cache")
        return len(trending)

    def warm_all(self):
        """Run all cache warming tasks."""
        results = {
            "destinations": self.warm_popular_destinations(),
            "categories": self.warm_category_list(),
            "trending_searches": self.warm_trending_searches(),
        }
        logger.info(f"Cache warming complete: {results}")
        return results

    # ------------------------------------------------------------------
    # Cache Invalidation
    # ------------------------------------------------------------------

    def invalidate_pattern(self, pattern):
        """
        Invalidate all cache keys matching a pattern.

        Note: This works with Redis cache backend. For LocMemCache,
        it falls back to clearing the entire cache.

        Args:
            pattern: Glob-style pattern (e.g. "dest:*", "user:123:*")

        Returns:
            Number of keys invalidated (approximate for LocMemCache).
        """
        # Try Redis-style delete_pattern first
        if hasattr(cache, "delete_pattern"):
            count = cache.delete_pattern(pattern)
            logger.info(f"Invalidated {count} keys matching pattern: {pattern}")
            return count

        # Fallback: clear all cache (safe but heavy-handed)
        logger.warning(f"Cache backend doesn't support delete_pattern, clearing all cache for pattern: {pattern}")
        cache.clear()
        return -1  # Unknown count

    def invalidate_destination(self, destination_id):
        """Invalidate all cache entries related to a destination."""
        patterns = [
            self.versioned_key(f"dest:detail:{destination_id}"),
            self.versioned_key(f"dest:list:{destination_id}"),
        ]
        for key in patterns:
            cache.delete(key)

        # Also invalidate list caches
        cache.delete(self.versioned_key("dest:popular:list"))
        cache.delete(self.versioned_key("dest:map-points"))

    def invalidate_user(self, user_id):
        """Invalidate all cache entries related to a user."""
        patterns = [
            self.versioned_key(f"user:{user_id}:*"),
            self.versioned_key(f"user:{user_id}:recommendations"),
        ]
        for pattern in patterns:
            self.invalidate_pattern(pattern)

    def invalidate_all(self):
        """Clear the entire cache and bump the version."""
        cache.clear()
        self.bump_version()
        logger.info("Full cache invalidation completed")

    # ------------------------------------------------------------------
    # Cache Statistics
    # ------------------------------------------------------------------

    def get_statistics(self):
        """
        Get cache statistics and monitoring data.

        Returns:
            dict with cache hit/miss ratios, key counts, and memory usage.
        """
        stats = {
            "version": self.get_version(),
            "local_stats": dict(self._local_stats),
            "timestamp": timezone.now().isoformat(),
        }

        # Try to get backend-specific stats
        if hasattr(cache, "stats"):
            stats["backend_stats"] = cache.stats()

        # Estimate key count (backend-dependent)
        if hasattr(cache, "_cache"):
            # LocMemCache
            try:
                stats["estimated_keys"] = len(cache._cache)
            except Exception:
                pass

        return stats

    def record_hit(self, key):
        """Record a cache hit for monitoring."""
        self._local_stats[key]["hits"] += 1

    def record_miss(self, key):
        """Record a cache miss for monitoring."""
        self._local_stats[key]["misses"] += 1

    def record_set(self, key):
        """Record a cache set for monitoring."""
        self._local_stats[key]["sets"] += 1

    def get_hit_ratio(self, key=None):
        """
        Get the cache hit ratio.

        Args:
            key: Optional specific key to check. If None, returns overall ratio.

        Returns:
            Float between 0 and 1 representing hit ratio.
        """
        if key:
            stats = self._local_stats.get(key, {"hits": 0, "misses": 0})
        else:
            stats = {"hits": 0, "misses": 0}
            for s in self._local_stats.values():
                stats["hits"] += s["hits"]
                stats["misses"] += s["misses"]

        total = stats["hits"] + stats["misses"]
        if total == 0:
            return 0.0
        return round(stats["hits"] / total, 4)

    # ------------------------------------------------------------------
    # Decorator for cached views
    # ------------------------------------------------------------------

    @staticmethod
    def cached(timeout=DEFAULT_CACHE_TTL, key_func=None):
        """
        Decorator to cache function results.

        Usage:
            @CacheManager.cached(timeout=300)
            def expensive_function(arg1, arg2):
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # Default key: function name + args hash
                    key_parts = [func.__module__, func.__name__]
                    key_parts.extend(str(a) for a in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)

                versioned_key = CacheManager.versioned_key(cache_key)

                result = cache.get(versioned_key)
                if result is not None:
                    return result

                result = func(*args, **kwargs)
                cache.set(versioned_key, result, timeout=timeout)
                return result

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper
        return decorator


# Import timezone at module level for warm_trending_searches
from django.utils import timezone  # noqa: E402


# Singleton instance
_default_manager = None


def get_cache_manager():
    """Get or create the default cache manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = CacheManager()
    return _default_manager
