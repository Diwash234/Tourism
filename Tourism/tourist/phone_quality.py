"""Phone-number quality for imported service datasets.

Three distinct defects arrive from the original CSVs, and none of them may be
shown to a user as if it were a real, callable number.

1. **Templated filler.** Unknown numbers were filled with a template of the
   district area code plus "[4-6]x0123" (e.g. 037-520123, 089-420123,
   025-560123). These are not real numbers at all.

2. **Stringified nulls.** A missing value that passed through pandas and a
   ``str()`` conversion is stored as the literal text ``"nan"`` (or ``"None"``,
   ``"null"``, ``"N/A"``). 788 police stations and 33 hospitals shipped with
   ``phone == "nan"``, so the public API was returning the word "nan" as a
   phone number to anyone looking for nearby police.

3. **Float-mangled numbers.** Values read as floats keep a trailing ``.0``
   and, where the source was a national number, lose the leading trunk zero.
   ``14440000.0`` is really ``014440000`` and ``977014256656.0`` is really
   ``+977014256656``. Unlike the templated filler these are genuine numbers
   that were corrupted in transit, so they are repaired rather than dropped --
   see :func:`normalize_phone_artifact`.

Kept free of Django imports so migrations can use it without importing app
state that may later change.
"""
import re

_TEMPLATE_TAIL = re.compile(r"[4-6]\d0123$")
_FLOAT_ARTIFACT = re.compile(r"^(?P<body>[\d\s()+\-.]+?)\.0$")

#: Text that a missing value turns into once it has been stringified. None of
#: these is ever a real phone number.
#:
#: The machine-shaped ones (``nan``, ``None``, ``n/a``) come from a missing cell
#: passing through pandas and ``str()``. The prose ones come from the OSM-derived
#: service CSVs, which mark absence in English: 2,752 of the 3,293 rows in
#: ``emergency_services.csv`` carry the literal text ``Not Available`` in the
#: phone column, and the same marker fills that file's email, website, opening
#: hours, brand and address fields. Those values look populated -- a naive
#: "is this cell non-empty" count reports 3,293 phones where 541 are real -- so
#: an import that trusted emptiness would publish "Not Available" as a callable
#: number.
NULL_SENTINELS = frozenset(
    {
        "nan",
        "none",
        "null",
        "nil",
        "nat",
        "na",
        "n/a",
        "n.a.",
        "-",
        "--",
        "?",
        "undefined",
        "not available",
        "not applicable",
        "not found",
        "not listed",
        "not known",
        "no data",
        "no information",
        "unknown",
        "information not available",
    }
)

# Nepal's country code, and the national trunk prefix that a landline area code
# carries in dialling form (01 for Koshi/Bhaktapur, 061 for Pokhara, ...).
_COUNTRY_CODE = "977"
_TRUNK = "0"


def _strip_float_artifact(text: str):
    """Return (body_without_.0, was_float) for a float-mangled string."""
    match = _FLOAT_ARTIFACT.match(text)
    if not match:
        return text, False
    return match.group("body"), True


def is_null_sentinel(value) -> bool:
    """True when the value is a stringified missing number, e.g. ``"nan"``."""
    text = str(value if value is not None else "").strip()
    if not text:
        return False
    return text.lower() in NULL_SENTINELS


def is_placeholder_phone(value) -> bool:
    """True for the templated filler that was never a real number."""
    text = str(value or "").strip()
    text, _ = _strip_float_artifact(text)
    digits = re.sub(r"\D", "", text)
    return len(digits) >= 8 and bool(_TEMPLATE_TAIL.search(digits))


def is_unusable_phone(value) -> bool:
    """True when the value must never be presented as callable.

    Covers a stringified null and the templated filler. Deliberately does
    *not* cover the float-mangled case, which holds a real number and is
    repaired instead of suppressed.
    """
    return is_null_sentinel(value) or is_placeholder_phone(value)


def usable_phone(value) -> str:
    """Return a phone value that is safe to publish.

    The single entry point for building a response field: an unusable value
    becomes an empty string, a float-mangled real number is repaired, and
    anything else is passed through untouched.

    Views that assemble rows from model attributes rather than going through a
    serializer must use this, or a value written after migration 0086 ran --
    an import, an admin edit -- could put "nan" straight into a response.
    """
    if is_unusable_phone(value):
        return ""
    return normalize_phone_artifact(value)


def normalize_phone_artifact(value) -> str:
    """Repair a float-mangled phone number, or return the input unchanged.

    The only corrections made are ones the numbering plan justifies:

    * a trailing ``.0`` from a float parse is removed;
    * a 12-digit value starting with the country code becomes an
      international number (``977014256656`` -> ``+977014256656``);
    * an 8-digit value is a national landline that lost its trunk zero, so the
      zero is restored (``14440000`` -> ``014440000``).

    Nothing is invented: a value that does not match one of those shapes is
    returned byte-for-byte, and a templated or stringified-null value is
    returned unchanged so the caller can decide to blank it.
    """
    text = str(value or "").strip()
    if not text or is_null_sentinel(text):
        return text

    body, was_float = _strip_float_artifact(text)
    if not was_float:
        return text

    digits = re.sub(r"\D", "", body)
    if len(digits) == 12 and digits.startswith(_COUNTRY_CODE):
        return "+" + digits
    if len(digits) == 8:
        return _TRUNK + digits
    return body
