"""OSRM road-routing provider (project-osrm.org HTTP API).

Configured entirely through Django settings / environment variables:
    ROUTING_PROVIDER   = "osrm" (default)
    ROUTING_BASE_URL   = e.g. https://router.project-osrm.org
    ROUTING_TIMEOUT    = seconds (default 6)
    ROUTING_MAX_RETRIES= retries on transport error (default 2)

Only modes the deployed OSRM instance actually serves should be listed in
`available_profiles`; the public demo server only hosts the driving
profile, so walking/cycling report unsupported there instead of silently
returning car routes (honesty over convenience).
"""
from __future__ import annotations

import logging

import requests
from django.conf import settings

from .routing_provider import RoutingProvider

logger = logging.getLogger(__name__)

# app mode -> OSRM profile name
PROFILE_BY_MODE = {
    "driving": "driving",
    "motorcycle": "driving",   # OSRM has no motorcycle profile; car is the
                               # honest closest road profile
    "walking": "foot",
    "hiking": "foot",
    "cycling": "bike",
}

MANEUVER_WORDS = {
    "depart": "Head out",
    "arrive": "Arrive at destination",
    "turn": "Turn",
    "new name": "Continue",
    "merge": "Merge",
    "on ramp": "Take the ramp",
    "off ramp": "Take the exit",
    "fork": "Keep at the fork",
    "end of road": "At the end of the road",
    "continue": "Continue",
    "roundabout": "Take the roundabout",
    "rotary": "Take the rotary",
    "roundabout turn": "Take the roundabout",
    "notification": "Note",
    "exit roundabout": "Exit the roundabout",
    "exit rotary": "Exit the rotary",
}


def _step_instruction(step: dict) -> str:
    m = step.get("maneuver") or {}
    kind = (m.get("type") or "").lower()
    modifier = (m.get("modifier") or "").lower()
    base = MANEUVER_WORDS.get(kind, "Continue")
    name = (step.get("name") or "").strip()
    if kind == "turn" and modifier:
        base = f"Turn {modifier}"
    elif kind in ("roundabout", "rotary") and m.get("exit"):
        base = f"Take exit {m['exit']} of the roundabout"
    elif modifier and kind not in ("depart", "arrive"):
        base = f"{base} {modifier}".strip()
    if name and kind not in ("arrive",):
        return f"{base} onto {name}"
    return base


def _maneuver_key(step: dict) -> str:
    m = step.get("maneuver") or {}
    return "-".join(x for x in [m.get("type"), m.get("modifier")] if x) or "waypoint"


class OSRMProvider(RoutingProvider):
    name = "osrm"

    def __init__(self, base_url: str | None = None, timeout: float | None = None,
                 max_retries: int | None = None, available_profiles: tuple[str, ...] | None = None):
        self.base_url = (base_url or getattr(settings, "ROUTING_BASE_URL", "")
                         or getattr(settings, "ROUTING_API_URL", "") or "").rstrip("/")
        self.timeout = float(timeout if timeout is not None
                             else getattr(settings, "ROUTING_TIMEOUT", 6))
        self.max_retries = int(max_retries if max_retries is not None
                               else getattr(settings, "ROUTING_MAX_RETRIES", 2))
        # profiles the configured server actually hosts; an explicit
        # constructor argument wins over settings (used by tests/callers)
        if available_profiles is not None:
            self.available_profiles = tuple(available_profiles)
        else:
            configured = getattr(settings, "ROUTING_PROFILES", None)
            self.available_profiles = tuple(configured) if configured else ("driving",)
        self.supported_modes = tuple(
            m for m, p in PROFILE_BY_MODE.items() if p in self.available_profiles)

    def supports(self, mode: str) -> bool:
        return bool(self.base_url) and mode in self.supported_modes

    # -- canonical helpers -------------------------------------------------
    @staticmethod
    def _canonical(osrm_route: dict, mode: str, note: str | None = None) -> dict:
        geo = osrm_route.get("geometry") or {}
        coords = [[lat, lng] for lng, lat in geo.get("coordinates", [])]
        bounds = None
        if coords:
            lats = [c[0] for c in coords]
            lngs = [c[1] for c in coords]
            bounds = [[min(lats), min(lngs)], [max(lats), max(lngs)]]
        steps = []
        for leg in osrm_route.get("legs", []):
            for st in leg.get("steps", []):
                steps.append({
                    "instruction": _step_instruction(st),
                    "distance_m": round(float(st.get("distance", 0)), 1),
                    "duration_s": round(float(st.get("duration", 0)), 1),
                    "maneuver": _maneuver_key(st),
                })
        return {
            "source": "osrm",
            "mode": mode,
            "distance_m": round(float(osrm_route.get("distance", 0)), 1),
            "duration_s": round(float(osrm_route.get("duration", 0)), 1),
            "geometry": coords,
            "bounds": bounds,
            "steps": steps,
            "note": note,
        }

    def _get(self, path: str) -> dict | None:
        url = f"{self.base_url}{path}"
        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = requests.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    payload = resp.json()
                    if payload.get("code") == "Ok":
                        return payload
                    logger.info("OSRM non-Ok code %s for %s", payload.get("code"), path)
                    return None
                last_err = f"HTTP {resp.status_code}"
            except requests.RequestException as exc:
                last_err = str(exc)
        logger.warning("OSRM request failed after %d attempt(s): %s", self.max_retries + 1, last_err)
        return None

    # -- interface ----------------------------------------------------------
    def route(self, start, destination, mode):
        if not self.supports(mode):
            return None
        profile = PROFILE_BY_MODE[mode]
        path = (f"/route/v1/{profile}/"
                f"{start[1]},{start[0]};{destination[1]},{destination[0]}"
                f"?overview=full&geometries=geojson&steps=true&annotations=duration,distance")
        payload = self._get(path)
        if not payload or not payload.get("routes"):
            return None
        note = None
        if mode == "motorcycle":
            note = ("OSRM has no motorcycle profile; this route uses the car "
                    "road profile.")
        return self._canonical(payload["routes"][0], mode, note=note)

    def alternatives(self, start, destination, mode):
        if not self.supports(mode):
            return []
        profile = PROFILE_BY_MODE[mode]
        path = (f"/route/v1/{profile}/"
                f"{start[1]},{start[0]};{destination[1]},{destination[0]}"
                f"?overview=full&geometries=geojson&steps=true&alternatives=true")
        payload = self._get(path)
        if not payload:
            return []
        routes = payload.get("routes") or []
        return [self._canonical(r, mode) for r in routes[1:3]]
