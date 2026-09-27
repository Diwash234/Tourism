"""Clean stringified nulls and float-mangled phone numbers.

Two defects shipped to the public catalog, both invisible in code review
because they look like ordinary strings:

1. **Stringified nulls.** 788 of 801 police stations and 33 of 362 hospitals
   carried the literal text ``"nan"`` in ``phone`` -- a missing value that was
   stringified on the way out of the source CSV. The public API therefore
   returned the word "nan" as the phone number for the police station a
   traveller was looking for.

2. **Float-mangled numbers.** 61 phone values kept a trailing ``.0`` from a
   float parse, and the national ones had also lost their trunk zero, so
   "14440000.0" was really "014440000" and "977014256656.0" was really
   "+977014256656". These are genuine numbers corrupted in transit, so they
   are repaired rather than discarded.

Both rules live in tourist/phone_quality.py so they can be unit tested and
reused by the read path. This migration applies them to storage so the
database, the published snapshot and every consumer are fixed at the source
instead of each one filtering for itself.

Templated filler ("037-520123" and friends) is also blanked here rather than
only at serialization time, so the released artifact no longer carries it
either. Irreversible by design: the original text is not recoverable, and the
repair rules are deterministic, so re-running is a no-op.
"""
from django.db import migrations

# Snapshotted here rather than imported, because app code may change after a
# migration has shipped. Kept byte-identical to tourist/phone_quality.py.
import re

_TEMPLATE_TAIL = re.compile(r"[4-6]\d0123$")
_FLOAT_ARTIFACT = re.compile(r"^(?P<body>[\d\s()+\-.]+?)\.0$")

NULL_SENTINELS = frozenset(
    {"nan", "none", "null", "nil", "nat", "na", "n/a", "n.a.", "-", "--", "?", "undefined"}
)

MODELS_WITH_PHONE = (
    ("PoliceStation", "tourist_policestation"),
    ("Hospital", "tourist_hospital"),
    ("Hotel", "tourist_hotel"),
)


def _is_null_sentinel(value):
    text = str(value if value is not None else "").strip()
    return bool(text) and text.lower() in NULL_SENTINELS


def _is_placeholder(value):
    text = str(value or "").strip()
    match = _FLOAT_ARTIFACT.match(text)
    if match:
        text = match.group("body")
    digits = re.sub(r"\D", "", text)
    return len(digits) >= 8 and bool(_TEMPLATE_TAIL.search(digits))


def _normalize(value):
    """Repair a float-mangled number; return None when nothing applies."""
    text = str(value or "").strip()
    if not text or _is_null_sentinel(text):
        return None
    match = _FLOAT_ARTIFACT.match(text)
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group("body"))
    if len(digits) == 12 and digits.startswith("977"):
        return "+" + digits
    if len(digits) == 8:
        return "0" + digits
    return match.group("body")


def clean(apps, schema_editor):
    for model_name, _table in MODELS_WITH_PHONE:
        model = apps.get_model("tourist", model_name)
        if not hasattr(model, "phone"):
            continue
        blanked = 0
        repaired = 0
        for pk, phone in model.objects.exclude(phone=None).values_list("pk", "phone"):
            if _is_null_sentinel(phone) or _is_placeholder(phone):
                model.objects.filter(pk=pk).update(phone="")
                blanked += 1
                continue
            fixed = _normalize(phone)
            if fixed and fixed != phone:
                model.objects.filter(pk=pk).update(phone=fixed)
                repaired += 1
        if blanked or repaired:
            schema_editor.execute(
                "-- tourist.%s.phone: blanked %d unusable, repaired %d float-mangled"
                % (model_name, blanked, repaired)
            )


def noop(apps, schema_editor):
    """The original values are unrecoverable; nothing to reverse."""


class Migration(migrations.Migration):
    dependencies = [("tourist", "0085_clear_placeholder_hospital_phones")]
    operations = [migrations.RunPython(clean, noop)]
