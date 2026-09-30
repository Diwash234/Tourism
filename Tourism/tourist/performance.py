"""
Performance optimization utilities.
"""
import logging
import time
from functools import wraps
from typing import Callable

from django.db import connection, reset_queries

logger = logging.getLogger(__name__)


def query_counter(func: Callable) -> Callable:
    """Decorator that logs the number of database queries."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        query_count = len(connection.queries)
        logger.info(
            "%s executed %d queries in %.3fs",
            func.__name__,
            query_count,
            elapsed,
        )
        return result
    return wrapper


def cache_page(timeout: int = 300):
    """Decorator to cache a view's response."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            from django.http import HttpResponse

            cache_key = f"page:{request.path}:{request.META.get('QUERY_STRING', '')}"
            cached = cache.get(cache_key)
            if cached is not None:
                return HttpResponse(cached)

            response = func(request, *args, **kwargs)
            cache.set(cache_key, response.content, timeout=timeout)
            return response
        return wrapper
    return decorator


def select_related_fields(*fields: str):
    """Decorator to add select_related to a queryset."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            queryset = func(*args, **kwargs)
            if fields:
                queryset = queryset.select_related(*fields)
            return queryset
        return wrapper
    return decorator


def prefetch_related_fields(*fields: str):
    """Decorator to add prefetch_related to a queryset."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            queryset = func(*args, **kwargs)
            if fields:
                queryset = queryset.prefetch_related(*fields)
            return queryset
        return wrapper
    return decorator
