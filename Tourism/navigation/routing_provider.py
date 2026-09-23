"""Provider abstraction for road routing.

The navigation subsystem never talks to a routing vendor directly. Every
implementation (OSRM today; Google/Mapbox/Valhalla later) returns the same
canonical route shape so the React client and navigation_service stay
vendor-agnostic:

{
  "source": "osrm" | "bundled_graph_estimate" | "straight_line_estimate",
  "mode": "driving",
  "distance_m": 2800.0,
  "duration_s": 480.0,
  "geometry": [[lat, lng], ...],          # ordered route points
  "bounds": [[south, west], [north, east]],
  "steps": [{"instruction": str, "distance_m": float,
             "duration_s": float, "maneuver": str}, ...],
  "note": str | None,                     # honest capability caveats
}
"""
from __future__ import annotations


class RoutingProvider:
    """Interface. Subclasses must set `name` and `supported_modes`."""

    name = "base"
    supported_modes: tuple[str, ...] = ()

    def supports(self, mode: str) -> bool:
        return mode in self.supported_modes

    def route(self, start: tuple[float, float], destination: tuple[float, float],
              mode: str) -> dict | None:
        """Return the canonical route dict, or None when this provider
        cannot serve the request (caller falls through to the next one)."""
        raise NotImplementedError

    def alternatives(self, start: tuple[float, float], destination: tuple[float, float],
                     mode: str) -> list[dict]:
        """Alternative routes in the same canonical shape (may be empty)."""
        return []

    def match_location(self, location: tuple[float, float], geometry: list[list[float]],
                       mode: str) -> dict:
        """Map-match a GPS fix onto route geometry. Default implementation
        is provider-independent (pure geometry) so vendors only override
        when they offer server-side matching."""
        from .map_matching import match_point_to_route
        return match_point_to_route(location, geometry)
