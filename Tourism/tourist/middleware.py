import ipaddress

from django.utils.functional import SimpleLazyObject

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
            # Lazy: the visitor's IP is sent to the GeoIP provider only when a
            # view actually reads request.geo_location (a nearby search with
            # no GPS coordinates), never on every request. Non-blocking: a
            # cold-cache miss returns None and warms the cache in the
            # background. Private/loopback addresses are never looked up.
            request.geo_location = SimpleLazyObject(lambda: _lookup_public(ip))
        return self.get_response(request)


def _lookup_public(ip):
    try:
        addr = ipaddress.ip_address(str(ip or "").strip())
    except ValueError:
        return None
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
        return None
    return geoip_lookup(str(addr), blocking=False)
