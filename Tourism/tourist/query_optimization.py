"""
Database query optimization utilities.
"""
import logging
from functools import wraps
from time import time

from django.db import connection, reset_queries

logger = logging.getLogger(__name__)


def query_debugger(func):
    """
    Decorator to log database queries executed by a function.
    Usage:
        @query_debugger
        def my_view(request):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start = time()
        result = func(*args, **kwargs)
        end = time()
        queries = len(connection.queries)
        total_time = sum(float(q['time']) for q in connection.queries)
        logger.info(f"Function: {func.__name__}")
        logger.info(f"Number of Queries: {queries}")
        logger.info(f"Total time: {total_time:.3f}s")
        logger.info(f"Execution time: {end - start:.3f}s")
        return result
    return wrapper


def optimize_queryset(queryset, select_related=None, prefetch_related=None, only=None, defer=None):
    """
    Apply common queryset optimizations.
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    if only:
        queryset = queryset.only(*only)
    if defer:
        queryset = queryset.defer(*defer)
    return queryset


class QueryOptimizer:
    """
    Helper class to optimize common query patterns.
    """

    @staticmethod
    def optimize_destination_list(queryset):
        """Optimize destination list queries."""
        return optimize_queryset(
            queryset,
            select_related=['category', 'created_by'],
            prefetch_related=['gallery'],
            only=['id', 'name', 'slug', 'description', 'district', 'province',
                  'latitude', 'longitude', 'is_published', 'is_featured',
                  'average_rating', 'review_count', 'cover_image']
        )

    @staticmethod
    def optimize_destination_detail(queryset):
        """Optimize destination detail queries."""
        return optimize_queryset(
            queryset,
            select_related=['category', 'created_by'],
            prefetch_related=['gallery', 'videos', 'reviews', 'translations']
        )

    @staticmethod
    def optimize_review_list(queryset):
        """Optimize review list queries."""
        return optimize_queryset(
            queryset,
            select_related=['user', 'destination'],
            only=['id', 'rating', 'comment', 'created_at', 'is_approved']
        )

    @staticmethod
    def optimize_user_profile(queryset):
        """Optimize user profile queries."""
        return optimize_queryset(
            queryset,
            prefetch_related=['travel_plans', 'favorites', 'reviews', 'documents']
        )
