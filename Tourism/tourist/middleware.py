from .utils import get_client_ip, geoip_lookup


class GeoIPMiddleware:
    """
    Attaches `request.geo_location` (country/city/lat/lon or None) based on
    the client's IP address. This is used as a fallback whenever the
    frontend does not supply browser GPS coordinates. Lookups are cheap and
    best-effort; failures never break the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.geo_location = None
        if request.path.startswith("/api/"):
            ip = get_client_ip(request)
            # Non-blocking: a cold-cache miss must never delay the request
            # waiting on an external provider. The lookup warms the cache
            # in a background thread; the next request gets the value.
            request.geo_location = geoip_lookup(ip, blocking=False)
        return self.get_response(request)
