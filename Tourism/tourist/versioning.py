"""
API versioning support — allows multiple API versions to coexist.
"""
from rest_framework.versioning import URLPathVersioning


class APIVersioning(URLPathVersioning):
    """
    API versioning via URL path: /api/v1/, /api/v2/, etc.

    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            versioning_class = APIVersioning
    """
    default_version = "v1"
    allowed_versions = ["v1", "v2"]
    version_param = "version"


def get_api_version(request):
    """Get the current API version from the request."""
    return getattr(request, "version", "v1")
