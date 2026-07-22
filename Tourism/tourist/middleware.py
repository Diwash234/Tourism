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
            request.geo_location = geoip_lookup(ip)
        return self.get_response(request)
