"""Blank phone values that are spreadsheet missing-value markers.

The police and hospital CSV imports wrote pandas' NaN as the literal text
"nan" (788 police stations, 33 hospitals), which the district page then
displayed as "Police Station Kathmandu · nan". A marker is not a number:
store "" so every page shows "Phone unavailable" instead.

Only exact markers are touched; real numbers are left unchanged. The reverse
is a no-op (the markers carried no information).
"""
from django.db import migrations
from django.db.models import Q

MARKERS = ("nan", "nan.0", "none", "null", "n/a", "na", "-", "--")


def clear_markers(apps, schema_editor):
    marker_q = Q()
    for marker in MARKERS:
        marker_q |= Q(phone__iexact=marker)
    for model_name in ("Hospital", "PoliceStation"):
        model = apps.get_model("tourist", model_name)
        model.objects.filter(marker_q).update(phone="")
        # values padded with whitespace ("  nan ")
        for pk, phone in model.objects.exclude(phone="").values_list("pk", "phone"):
            if (phone or "").strip().lower() in MARKERS:
                model.objects.filter(pk=pk).update(phone="")


class Migration(migrations.Migration):
    dependencies = [("tourist", "0084_load_forex_seed_and_elevations")]

    operations = [migrations.RunPython(clear_markers, migrations.RunPython.noop)]
