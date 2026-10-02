
"""
Helpers for frontend integration.
"""
from typing import Any, Optional

from django.http import JsonResponse


def api_response(
    data: Any = None,
    message: str = "Success",
    status: int = 200,
    meta: Optional[dict] = None,
) -> JsonResponse:
    """Return a standardized API response."""
    response = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        response["meta"] = meta
    return JsonResponse(response, status=status)


def api_error(
    message: str = "An error occurred",
    code: str = "error",
    details: Optional[dict] = None,
    status: int = 400,
) -> JsonResponse:
    """Return a standardized error response."""
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        },
        status=status,
    )


def paginate_response(
    queryset,
    page: int = 1,
    per_page: int = 10,
) -> dict:
    """Return a paginated response."""
    start = (page - 1) * per_page
    end = start + per_page
    total = queryset.count() if hasattr(queryset, "count") else len(queryset)

    return {
        "data": queryset[start:end],
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        },
    }
