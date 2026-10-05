"""Classify how precisely a coordinate actually locates a place.

The catalog carries ``coordinate_accuracy`` and ``coordinate_status`` on every
destination, and the public API exposes both, so a client can tell a surveyed
position from a town centroid. Those labels are supposed to be derived from the
coordinate itself rather than guessed: a pin recorded to six decimals is a
surveyed position, and one rounded to a single decimal is an area point that
should never be presented as an exact location.

The rules here mirror the thresholds tourist/elevation.py already uses when it
decides whether a coordinate is precise enough to look up an elevation
(``MIN_DECIMALS = 3``, plus the whole-arc-minute check), so the two cannot
drift apart. This module holds no Django imports so migrations can use it
without importing app state that may later change.
"""
import re

#: Labels already used in the catalog, kept stable so existing clients match.
ACCURACY_EXACT = "High / Exact"
ACCURACY_MODERATE = "Moderate"
ACCURACY_AREA = "Area Point"

#: Below this many decimal places a coordinate is an area reference, not a pin.
AREA_DECIMALS = 2
#: At this many decimal places (~110 m) a coordinate is a usable map pin.
MODERATE_DECIMALS = 3
#: At this many decimal places (~11 m) it is a surveyed position.
EXACT_DECIMALS = 4

#: Nepal's bounding box, as used by tourist/elevation.py.
NEPAL_BBOX = (26.3, 30.5, 80.0, 88.3)


def decimals(value) -> int:
    """Decimal places actually present, ignoring trailing zeros.

    ``28.500`` is one decimal of information, not three: the trailing zeros
    carry no precision, and counting them would overstate the position.
    """
    if value is None:
        return 0
    text = str(value).strip()
    if not text or "." not in text:
        return 0
    fraction = text.split(".")[1]
    fraction = re.sub(r"[^0-9].*$", "", fraction)
    return len(fraction.rstrip("0"))


def is_whole_arc_minute(value) -> bool:
    """True for values like 28.0833 / 85.4167 (whole arc-minutes, ~1.8 km grid).

    These carry four decimals and so look exact, but they are degree-minute
    data rounded to the nearest minute, which is far too coarse in the
    mountains. tourist/elevation.py makes the same check before trusting a
    coordinate.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if decimals(value) > 4:
        return False
    minutes = (abs(number) % 1) * 60
    return abs(minutes - round(minutes)) < 0.01


def in_nepal(lat, lon) -> bool:
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return (
        NEPAL_BBOX[0] <= lat_f <= NEPAL_BBOX[1]
        and NEPAL_BBOX[2] <= lon_f <= NEPAL_BBOX[3]
    )


def classify_precision(lat, lon) -> str:
    """Return the accuracy label implied by the coordinate itself.

    The scale is the one the model's own help text names:

    * ``High / Exact`` -- four or more decimals and not whole arc-minutes, so
      roughly 11 m or better;
    * ``Moderate`` -- three decimals, roughly 110 m;
    * ``Area Point`` -- two decimals or fewer, or whole arc-minutes, which is
      1.1 km or worse. This is a town or district centre and must not be
      presented as a precise location.

    A missing or out-of-Nepal coordinate is reported as ``Area Point`` rather
    than optimistically, so an unusable pin is never labelled as exact.
    """
    if lat in (None, "") or lon in (None, ""):
        return ACCURACY_AREA
    if not in_nepal(lat, lon):
        return ACCURACY_AREA

    places = min(decimals(lat), decimals(lon))
    if places <= AREA_DECIMALS:
        return ACCURACY_AREA
    if is_whole_arc_minute(lat) or is_whole_arc_minute(lon):
        return ACCURACY_AREA
    if places >= EXACT_DECIMALS:
        return ACCURACY_EXACT
    if places >= MODERATE_DECIMALS:
        return ACCURACY_MODERATE
    return ACCURACY_AREA


#: Ground distance covered by one degree of latitude, in km. Used to turn a
#: coordinate's decimal resolution into the distance it actually pins to.
KM_PER_DEGREE = 111.0


def resolution_km(lat, lon) -> float:
    """Rough ground resolution, in km, that this coordinate pins a place to.

    A distance computed *to* a place is only as precise as the pin that place
    is stored with. A destination recorded to two decimals is a town centre
    good to about a kilometre, so reporting "0.34 km away" as though it were
    exact overstates what the data supports. Callers use this to publish the
    uncertainty next to the distance instead of implying false precision.

    Returns ``None`` when either coordinate is missing or unusable, so callers
    can distinguish "no idea" from "precise".
    """
    if lat in (None, "") or lon in (None, ""):
        return None
    try:
        lat_f, lon_f = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not in_nepal(lat_f, lon_f):
        return None

    places = min(decimals(lat), decimals(lon))
    # The arc-minute shortcut only applies to values that *look* precise. With
    # zero or one decimal the plain rule below is already coarser, and a
    # whole number trivially satisfies the arc-minute test, which would
    # otherwise report 1.85 km for a coordinate stored to the nearest degree.
    if places >= 3 and (is_whole_arc_minute(lat) or is_whole_arc_minute(lon)):
        # Whole arc-minutes are degree-minute data however many decimals they
        # are printed with: one arc-minute is about 1.85 km.
        return 1.85
    if places <= 0:
        return round(KM_PER_DEGREE, 1)
    return round(KM_PER_DEGREE / (10 ** places), 4)
