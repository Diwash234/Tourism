"""GPS fix validation and validated distance measurement.

Why this exists
---------------
A coordinate pair is not automatically a location. The range check
(-90..90 / -180..180) that the serializers already perform accepts several
values that are certainly wrong: the "null island" (0, 0) in the Gulf of
Guinea, a stale fix from three hours ago, or a fix whose reported accuracy is
two kilometres. Each of those produces a *confidently wrong* distance or
map pin, which is worse than no answer.

This module therefore separates three things that were previously conflated:

* whether a pair is a **usable position** (parseable, in range, not null
  island, not absurdly inaccurate, not stale);
* how much to **trust** it (``precise`` / ``approximate`` / ``unusable``);
* and what to do when it is not usable: refuse and say why, instead of
  returning a number nobody can trust.

It also provides the single canonical Haversine implementation. The project had
five divergent copies (``utils``, ``location_utils``, ``views_navigation``,
``discovery_pipeline``, ``duplicates``), so a fix applied to one of them would
silently not apply to the others.

Nothing here invents a position. An unusable fix yields ``km=None`` plus a
machine-readable reason; it never falls back to a guess, to zero, or to a
geocoded city centroid.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

# Coarse validity bounds. Deliberately generous: this is a sanity gate, not
# geocoding, and a traveller legitimately standing outside Nepal.
LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0

# Nepal bounds, used only to raise a *warning* flag. It never rejects a fix:
# tourists are abroad, and rejecting them would break the product to satisfy a
# tidiness check.
NEPAL_LAT_MIN, NEPAL_LAT_MAX = 26.0, 31.0
NEPAL_LON_MIN, NEPAL_LON_MAX = 80.0, 89.0

# A fix reporting worse accuracy than this cannot position a map pin.
UNUSABLE_ACCURACY_M = 5_000.0
# Beyond this, distances are only order-of-magnitude useful.
APPROXIMATE_ACCURACY_M = 200.0
# A fix older than this is not the traveller's current position.
STALE_AFTER = timedelta(minutes=30)
# Plausible timestamp sanity window (device clock is not trusted blindly).
FIX_FUTURE_TOLERANCE = timedelta(minutes=5)
FIX_PAST_FLOOR = datetime(2000, 1, 1, tzinfo=timezone.utc)

EARTH_RADIUS_KM = 6371.0088

# Quality tiers.
QUALITY_PRECISE = "precise"
QUALITY_APPROXIMATE = "approximate"
QUALITY_UNUSABLE = "unusable"
QUALITY_UNKNOWN = "unknown"


def _as_float(value) -> Optional[float]:
    """Parse a coordinate, treating junk as absent rather than as zero."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "" or text.lower() in {"null", "none", "undefined", "nan", "n/a"}:
            return None
        value = text
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _as_aware(value) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


@dataclass
class GeoFix:
    """A coordinate pair plus the verdict on whether it can be trusted."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = ""
    accuracy_m: Optional[float] = None
    recorded_at: Optional[datetime] = None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quality: str = QUALITY_UNKNOWN

    @property
    def has_position(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    @property
    def usable(self) -> bool:
        """True only when this fix may drive a map pin or a distance."""
        return self.has_position and self.quality in {QUALITY_PRECISE, QUALITY_APPROXIMATE}

    @property
    def precise(self) -> bool:
        return self.usable and self.quality == QUALITY_PRECISE

    @property
    def outside_nepal(self) -> bool:
        if not self.has_position:
            return False
        return not (
            NEPAL_LAT_MIN <= self.latitude <= NEPAL_LAT_MAX
            and NEPAL_LON_MIN <= self.longitude <= NEPAL_LON_MAX
        )

    def as_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source": self.source,
            "accuracy_m": self.accuracy_m,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "quality": self.quality,
            "usable": self.usable,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "outside_nepal": self.outside_nepal,
        }


def validate_fix(
    latitude,
    longitude,
    *,
    source: str = "",
    accuracy_m=None,
    recorded_at=None,
    now: Optional[datetime] = None,
) -> GeoFix:
    """Validate one coordinate pair and classify how far it can be trusted.

    Returns a :class:`GeoFix`. It never raises for bad input, because a device
    with a broken GPS should degrade to "no position", not to a 500.
    """
    now = now or datetime.now(tz=timezone.utc)
    lat = _as_float(latitude)
    lng = _as_float(longitude)
    fix = GeoFix(
        latitude=lat,
        longitude=lng,
        source=(source or "").strip()[:50],
        accuracy_m=_as_float(accuracy_m),
        recorded_at=_as_aware(recorded_at),
    )

    # 1. Is there a position at all?
    if lat is None and lng is None:
        fix.reasons.append("no_position")
        fix.quality = QUALITY_UNUSABLE
        return fix
    if lat is None or lng is None:
        fix.reasons.append("incomplete_pair")
        fix.quality = QUALITY_UNUSABLE
        return fix

    # 2. Is it a real place on Earth?
    if not (LAT_MIN <= lat <= LAT_MAX) or not (LON_MIN <= lng <= LON_MAX):
        fix.reasons.append("out_of_range")
        fix.quality = QUALITY_UNUSABLE
        return fix

    # 3. Null island: the single most common broken value. It is inside range,
    #    so only an explicit check catches it.
    if lat == 0.0 and lng == 0.0:
        fix.reasons.append("null_island")
        fix.quality = QUALITY_UNUSABLE
        return fix

    # 4. Accuracy, when the device reports it.
    if fix.accuracy_m is not None:
        if fix.accuracy_m < 0:
            fix.warnings.append("negative_accuracy")
            fix.accuracy_m = None
        elif fix.accuracy_m > UNUSABLE_ACCURACY_M:
            fix.reasons.append("accuracy_too_low")
            fix.quality = QUALITY_UNUSABLE
            return fix
        elif fix.accuracy_m > APPROXIMATE_ACCURACY_M:
            fix.warnings.append("approximate_accuracy")
            fix.quality = QUALITY_APPROXIMATE
        else:
            fix.quality = QUALITY_PRECISE

    # 5. Fix age. A stale fix is not the traveller's current position.
    if fix.recorded_at is not None:
        if fix.recorded_at < FIX_PAST_FLOOR:
            fix.reasons.append("implausible_timestamp")
            fix.quality = QUALITY_UNUSABLE
            return fix
        if fix.recorded_at > now + FIX_FUTURE_TOLERANCE:
            fix.warnings.append("timestamp_in_future")
        elif now - fix.recorded_at > STALE_AFTER:
            fix.reasons.append("stale_fix")
            fix.quality = QUALITY_UNUSABLE
            return fix

    if fix.quality == QUALITY_UNKNOWN:
        # No accuracy and no timestamp reported: valid position, but we cannot
        # claim precision we were not told about.
        fix.quality = QUALITY_APPROXIMATE
        fix.warnings.append("no_accuracy_or_timestamp_reported")

    if fix.outside_nepal:
        # Informational only. Tourists are abroad; this must never block them.
        fix.warnings.append("outside_nepal")

    return fix


def is_usable(latitude, longitude, **kwargs) -> bool:
    return validate_fix(latitude, longitude, **kwargs).usable


# --- Distance ------------------------------------------------------------


@dataclass
class DistanceResult:
    """A distance, or an explicit refusal to produce one."""

    km: Optional[float] = None
    quality: str = QUALITY_UNKNOWN
    reasons: list[str] = field(default_factory=list)
    origin: Optional[GeoFix] = None
    destination: Optional[GeoFix] = None

    @property
    def available(self) -> bool:
        return self.km is not None

    def __float__(self) -> float:
        if self.km is None:
            raise ValueError(f"distance unavailable: {', '.join(self.reasons)}")
        return self.km

    def as_dict(self) -> dict:
        return {
            "km": self.km,
            "available": self.available,
            "quality": self.quality,
            "reasons": list(self.reasons),
        }


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """The one canonical Haversine in this project, in kilometres."""
    radius_lat1, radius_lat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(radius_lat1) * math.cos(radius_lat2) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 3)


def distance_between(
    origin_lat,
    origin_lon,
    destination_lat,
    destination_lon,
    *,
    origin: Optional[GeoFix] = None,
    destination: Optional[GeoFix] = None,
    **fix_kwargs,
) -> DistanceResult:
    """Measure a distance, refusing to invent one from unusable coordinates.

    ``origin`` / ``destination`` may be pre-validated :class:`GeoFix` objects
    (for example from a GPS fix that carries accuracy metadata); otherwise the
    raw pairs are validated here.
    """
    origin_fix = origin or validate_fix(origin_lat, origin_lon, **fix_kwargs)
    destination_fix = destination or validate_fix(
        destination_lat, destination_lon, **{k: v for k, v in fix_kwargs.items() if k in {"accuracy_m", "recorded_at", "now"}}
    )
    reasons: list[str] = []
    if not origin_fix.usable:
        reasons.extend(f"origin:{reason}" for reason in (origin_fix.reasons or ["unusable"]))
    if not destination_fix.usable:
        reasons.extend(
            f"destination:{reason}" for reason in (destination_fix.reasons or ["unusable"])
        )
    if reasons:
        return DistanceResult(
            km=None, quality=QUALITY_UNUSABLE, reasons=reasons,
            origin=origin_fix, destination=destination_fix,
        )

    km = haversine_km(
        origin_fix.latitude, origin_fix.longitude,
        destination_fix.latitude, destination_fix.longitude,
    )
    quality = (
        QUALITY_PRECISE
        if origin_fix.precise and destination_fix.precise
        else QUALITY_APPROXIMATE
    )
    return DistanceResult(
        km=km, quality=quality, reasons=[],
        origin=origin_fix, destination=destination_fix,
    )


def bearing_between(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
    """Initial bearing in degrees, or ``None`` when either point is unusable."""
    origin = validate_fix(lat1, lon1)
    target = validate_fix(lat2, lon2)
    if not (origin.usable and target.usable):
        return None
    radius_lat1, radius_lat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(radius_lat2)
    x = math.cos(radius_lat1) * math.sin(radius_lat2) - math.sin(radius_lat2) * math.cos(
        radius_lat1
    ) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def describe_fix(latitude, longitude, **kwargs) -> dict:
    """Serialisable verdict, suitable for an API response or an audit row."""
    return validate_fix(latitude, longitude, **kwargs).as_dict()
