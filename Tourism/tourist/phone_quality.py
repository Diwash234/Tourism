"""Detect templated placeholder phone numbers in imported datasets.

The project's original hospital CSV filled unknown numbers with a template:
district area code + "[4-6]x0123" (e.g. 037-520123, 089-420123, 025-560123),
sometimes float-mangled ("87520123.0"). They are not real numbers and must
never be shown as callable -- display "Phone unavailable" instead.
"""
import re

_TEMPLATE_TAIL = re.compile(r"[4-6]\d0123$")


def is_placeholder_phone(value) -> bool:
    text = str(value or "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = re.sub(r"\D", "", text)
    return len(digits) >= 8 and bool(_TEMPLATE_TAIL.search(digits))
