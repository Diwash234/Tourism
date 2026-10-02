"""
Standardized API response utilities.
"""
from typing import Any, Optional

from rest_framework.response import Response
from rest_framework import status


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK,
    meta: Optional[dict] = None,
) -> Response:
    """Return a standardized success response."""
    response_data = {
        "success": True,
        "message": message,
        "data": data,
    }
    if meta:
        response_data["meta"] = meta
    return Response(response_data, status=status_code)


def error_response(
    message: str = "An error occurred",
    code: str = "error",
    details: Optional[dict] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Return a standardized error response."""
    return Response(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        },
        status=status_code,
    )


def paginated_response(
    data: Any,
    count: int,
    total_pages: int,
    current_page: int,
    next_url: Optional[str] = None,
    previous_url: Optional[str] = None,
) -> Response:
    """Return a standardized paginated response."""
    return Response(
        {
            "success": True,
            "data": data,
            "pagination": {
                "count": count,
                "total_pages": total_pages,
                "current_page": current_page,
                "next": next_url,
                "previous": previous_url,
            },
        }
    )
