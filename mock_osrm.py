"""Spec-compliant mock OSRM server for sandbox E2E verification.

Implements GET /route/v1/{profile}/{coords} exactly like the public
OSRM (router.project-osrm.org) HTTP API: GeoJSON geometry, per-leg
steps with maneuver objects, and `alternatives=true` support.

Used ONLY to verify the app's full routing pipeline end-to-end inside
the sandbox (which has no external network egress). Response shape and
field names match the real OSRM API; the road data is synthetic.
"""
import json
import math
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROFILE = re.compile(r"^/route/v1/([a-z]+)/([\d.\-]+),([\d.\-]+);([\d.\-]+),([\d.\-]+)(?:\?(.*))?$")

HIGHWAY_NAMES = [
    "Prithvi Highway", "Main Road", "Ring Road", "Bhrikuti Marg",
    "Lakeside Road", "Tribhuvan Highway", "Prithvi Marg", "Local Road",
]


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def build_geometry(lng1, lat1, lng2, lat2, segments=48, seed=1, wobble=0.004):
    """Straight-line interpolation with deterministic perpendicular wobble."""
    pts = []
    for i in range(segments + 1):
        t = i / segments
        lng = lng1 + (lng2 - lng1) * t
        lat = lat1 + (lat2 - lat1) * t
        if 0 < i < segments:
            # perpendicular offset (deterministic pseudo-random)
            k = math.sin(seed * 7.3 + i * 1.7) * wobble * (1 - abs(t - 0.5) * 1.2)
            # perpendicular unit vector (approx, small angles)
            dl = lng2 - lng1
            dlat = lat2 - lat1
            norm = math.hypot(dlat, dl) or 1.0
            lng += -dlat / norm * k
            lat += dl / norm * k
        pts.append([round(lng, 6), round(lat, 6)])
    return pts


def build_route(lng1, lat1, lng2, lat2, factor, avg_kmh, seed, alt_index=0):
    straight_m = haversine_m(lat1, lng1, lat2, lng2)
    distance = straight_m * factor
    duration = distance / (avg_kmh / 3.6)
    geom = build_geometry(lng1, lat1, lng2, lat2, segments=20 + alt_index * 8,
                          seed=seed + alt_index * 13, wobble=0.004 + alt_index * 0.002)
    steps = []
    n_steps = 8 + alt_index * 3
    step_dist = distance / n_steps
    for i in range(n_steps):
        t0 = i / n_steps
        loc = [geom[int(t0 * (len(geom) - 1))][0], geom[int(t0 * (len(geom) - 1))][1]]
        if i == 0:
            maneuver = {"type": "depart", "modifier": "left", "location": loc}
            name = ""
        elif i == n_steps - 1:
            maneuver = {"type": "arrive", "modifier": "right", "location": loc}
            name = ""
        else:
            jitter = math.sin(seed * 3.1 + i * 2.3)
            kind = "new name" if i % 3 == 0 else "turn"
            mod = "right" if jitter > 0 else "left"
            maneuver = {"type": kind, "modifier": mod, "location": loc}
            name = HIGHWAY_NAMES[(seed + i + alt_index) % len(HIGHWAY_NAMES)]
        steps.append({
            "distance": round(step_dist, 1),
            "duration": round(step_dist / (avg_kmh / 3.6), 1),
            "name": name,
            "ref": "",
            "maneuver": maneuver,
            "mode": "road",
        })
    return {
        "distance": round(distance, 1),
        "duration": round(duration, 1),
        "geometry": {"type": "LineString", "coordinates": geom},
        "legs": [{
            "distance": round(distance, 1),
            "duration": round(duration, 1),
            "steps": steps,
            "summary": "Prithvi Highway",
        }],
        "weight": round(duration, 1),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        m = PROFILE.match(self.path)
        if not m:
            self.send_json({"code": "NoRoute"}, 404)
            return
        profile, lng1, lat1, lng2, lat2, query = m.groups()
        params = dict(re.findall(r"([^=&]+)=([^&]*)", query or ""))
        seed = int(abs(hash((lng1, lat1, lng2, lat2))) % 997)
        routes = [build_route(float(lng1), float(lat1), float(lng2), float(lat2),
                              factor=1.10, avg_kmh=27.5, seed=seed)]
        if params.get("alternatives") == "true":
            routes.append(build_route(float(lng1), float(lat1), float(lng2), float(lat2),
                                      factor=1.14, avg_kmh=26.0, seed=seed, alt_index=1))
            routes.append(build_route(float(lng1), float(lat1), float(lng2), float(lat2),
                                      factor=1.19, avg_kmh=25.0, seed=seed, alt_index=2))
        payload = {
            "code": "Ok",
            "waypoints": [
                {"name": "", "location": [round(float(lng1), 6), round(float(lat1), 6)]},
                {"name": "", "location": [round(float(lng2), 6), round(float(lat2), 6)]},
            ],
            "routes": routes,
        }
        self.send_json(payload, 200)

    def send_json(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 9877), Handler).serve_forever()
