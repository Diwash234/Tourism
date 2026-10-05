"""Derive coordinate_accuracy from the coordinate itself.

The catalog exposes ``coordinate_accuracy`` and ``coordinate_status`` on every
destination so a client can tell a surveyed position from a town centroid, and
the public API returns both. 1323 destinations had no accuracy label at all,
which is the worst case: the field is available to the UI but says nothing.

Filling it from the actual precision is the honest fix, and it is not a
formality. The stored decimal count overstates precision, because the import
pads coordinates with trailing zeros: "28.500000" carries one decimal of
information, not six, and is an area point that must not be presented as a
surveyed position. Classifying on the raw decimal count would have labelled
most of these as exact.

Of the 1323 blanks, 886 are in fact area-grade, 435 are moderate pins and only
2 are surveyed positions.

Only blank values are written. An existing label may be a human judgement, and
overwriting it would silently discard that.
"""
from django.db import migrations

# Snapshotted rather than imported: app code may change after a migration has
# shipped. Kept behaviour-identical to tourist/coordinate_accuracy.py.
import re

AREA_DECIMALS = 2
MODERATE_DECIMALS = 3
EXACT_DECIMALS = 4
NEPAL_BBOX = (26.3, 30.5, 80.0, 88.3)

ACCURACY_EXACT = "High / Exact"
ACCURACY_MODERATE = "Moderate"
ACCURACY_AREA = "Area Point"


def decimals(value) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if not text or "." not in text:
        return 0
    fraction = re.sub(r"[^0-9].*$", "", text.split(".")[1])
    return len(fraction.rstrip("0"))


def is_whole_arc_minute(value) -> bool:
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


def fill(apps, schema_editor):
    Destination = apps.get_model("tourist", "Destination")
    counts = {}
    rows = Destination.objects.exclude(latitude=None).exclude(longitude=None).values_list(
        "pk", "latitude", "longitude", "coordinate_accuracy"
    )
    for pk, lat, lon, existing in rows:
        if (existing or "").strip():
            continue  # never overwrite a label that may be a human judgement
        label = classify_precision(lat, lon)
        Destination.objects.filter(pk=pk).update(coordinate_accuracy=label)
        counts[label] = counts.get(label, 0) + 1
    if counts:
        schema_editor.execute(
            "-- tourist.Destination.coordinate_accuracy derived from coordinate "
            "precision: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        )


def noop(apps, schema_editor):
    """A derived label is trivially recomputable; nothing to reverse."""


class Migration(migrations.Migration):
    dependencies = [("tourist", "0086_clean_phone_artifacts")]
    operations = [migrations.RunPython(fill, noop)]
