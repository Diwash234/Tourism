"""Open-now status from OpenStreetMap ``opening_hours`` values.

Supports the subset of the OSM syntax actually present in the data:

* ``24/7``
* rules separated by ``;``, each ``[days] times``. Days are ``Mo``..``Su``,
  as ranges (``Mo-Fr``, wrapping ``Fr-Mo``) and lists (``Mo,We``). Times
  are ``HH:MM-HH:MM`` ranges, comma-separated. ``off`` and ``closed`` also
  work.
* later rules override earlier ones for the same day (OSM semantics);
* ranges ending after midnight (``18:00-02:00``) run into the next day.

Anything else (public holidays ``PH``, month or week selectors, ``sunrise``,
comments) makes the value *unknown* instead of guessed: a wrong "Open now"
is worse than none. Evaluated in Nepal time (Asia/Kathmandu).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

NEPAL_TZ = ZoneInfo("Asia/Kathmandu")
DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_TIME_RANGE = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")
_DAY_TOKEN = re.compile(r"^(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?$")
MAX_OVERNIGHT_MINUTES = 16 * 60
SOURCE_NOTE = "Hours from OpenStreetMap. They may be out of date, and public holidays may differ."


class Unsupported(ValueError):
    pass


def _parse_days(token: str) -> set[int]:
    days = set()
    for part in token.split(","):
        m = _DAY_TOKEN.match(part.strip())
        if not m:
            raise Unsupported(part)
        start = DAYS.index(m.group(1))
        end = DAYS.index(m.group(2)) if m.group(2) else start
        i = start
        while True:
            days.add(i)
            if i == end:
                break
            i = (i + 1) % 7
    return days


def _parse_times(token: str) -> list[tuple[int, int]]:
    spans = []
    for part in token.split(","):
        m = _TIME_RANGE.match(part.strip())
        if not m:
            raise Unsupported(part)
        h1, m1, h2, m2 = (int(x) for x in m.groups())
        if h1 > 24 or h2 > 24 or m1 > 59 or m2 > 59:
            raise Unsupported(part)
        start, end = h1 * 60 + m1, h2 * 60 + m2
        if end <= start:
            end += 24 * 60  # runs past midnight
            if end - start > MAX_OVERNIGHT_MINUTES:
                # e.g. "10:00-5:00" is valid syntax but almost always a
                # missing PM; refusing it avoids a false "Open now".
                raise Unsupported(part)
        spans.append((start, end))
    return spans


_AMPM = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([AaPp])\.?[Mm]\.?")
_DAY_CASE = re.compile(r"\b(mo|tu|we|th|fr|sa|su)\b", re.I)


def _to_24h(match) -> str:
    hour, minute, half = int(match.group(1)), int(match.group(2) or 0), match.group(3).lower()
    if not 1 <= hour <= 12:
        raise Unsupported(match.group(0))
    hour = hour % 12 + (12 if half == "p" else 0)
    return f"{hour:02d}:{minute:02d}"


def normalize(value: str) -> str:
    """Unambiguous clean-ups only: spacing, day case, AM/PM, "24 hours"."""
    text = re.sub(r"\s+", " ", (value or "").strip())
    if re.fullmatch(r"(?i)24\s*(hours|hrs|h)|open 24 hours", text):
        return "24/7"
    text = _AMPM.sub(_to_24h, text)
    text = _DAY_CASE.sub(lambda m: m.group(1).capitalize(), text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = re.sub(r"\s*,\s*", ",", text)
    return text


def parse(value: str) -> dict[int, list[tuple[int, int]]] | str:
    """Weekday -> [(start_min, end_min)], or ``"24/7"``. Raises Unsupported."""
    text = normalize(value)
    if not text:
        raise Unsupported("empty")
    if text == "24/7":
        return "24/7"
    week: dict[int, list[tuple[int, int]]] = {}
    for rule in [r.strip() for r in text.split(";") if r.strip()]:
        parts = rule.split(None, 1)
        if _DAY_TOKEN.match(parts[0].split(",")[0]):
            days = _parse_days(parts[0])
            rest = parts[1].strip() if len(parts) > 1 else ""
        else:
            days = set(range(7))
            rest = rule
        if rest.lower() in ("off", "closed"):
            spans = []
        elif rest == "24/7" or rest == "00:00-24:00":
            spans = [(0, 24 * 60)]
        else:
            spans = _parse_times(rest)
        for d in days:
            week[d] = list(spans)  # later rules override earlier ones
    if not week:
        raise Unsupported(text)
    return week


def _fmt(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def status(value: str, now: datetime | None = None) -> dict:
    """``{"state": "open"|"closed"|"unknown", "label", "raw", ...}``."""
    raw = (value or "").strip()
    if not raw:
        return {"state": "unknown", "label": "Hours not on record", "raw": "", "note": ""}
    try:
        week = parse(raw)
    except Unsupported:
        return {"state": "unknown", "label": "Hours unclear", "raw": raw,
                "note": "These hours use a format this site cannot check automatically."}
    now = (now or datetime.now(NEPAL_TZ)).astimezone(NEPAL_TZ)
    if week == "24/7":
        return {"state": "open", "label": "Open 24 hours", "raw": raw, "note": SOURCE_NOTE}
    today = now.weekday()
    minute = now.hour * 60 + now.minute
    yesterday = (today - 1) % 7
    # Spans from yesterday that run past midnight count as today too.
    for start, end in week.get(yesterday, []):
        if end > 24 * 60 and minute < end - 24 * 60:
            return {"state": "open", "label": f"Open now · closes {_fmt(end)}", "raw": raw,
                    "closes_at": _fmt(end), "note": SOURCE_NOTE}
    for start, end in week.get(today, []):
        if start <= minute < end:
            return {"state": "open", "label": f"Open now · closes {_fmt(end)}", "raw": raw,
                    "closes_at": _fmt(end), "note": SOURCE_NOTE}
    # Next opening within the coming week.
    for offset in range(0, 8):
        day = (today + offset) % 7
        for start, _end in sorted(week.get(day, [])):
            if offset == 0 and start <= minute:
                continue
            when = "today" if offset == 0 else ("tomorrow" if offset == 1 else DAYS[day])
            return {"state": "closed", "label": f"Closed · opens {when} {_fmt(start)}", "raw": raw,
                    "opens_at": _fmt(start), "opens_day": when, "note": SOURCE_NOTE}
    return {"state": "closed", "label": "Closed", "raw": raw, "note": SOURCE_NOTE}


def is_open(value: str, now: datetime | None = None) -> bool | None:
    s = status(value, now)
    return None if s["state"] == "unknown" else s["state"] == "open"


def now_in_nepal() -> datetime:
    return datetime.now(NEPAL_TZ)


__all__ = ["status", "is_open", "parse", "now_in_nepal", "NEPAL_TZ", "timedelta"]


def annotate(rows, now: datetime | None = None, *, key: str = "opening_hours") -> list[dict]:
    """Copy each row dict and add ``hours`` (open/closed/unknown) from its OSM value."""
    now = now or now_in_nepal()
    out = []
    for row in rows or []:
        item = dict(row)
        item["hours"] = status(item.get(key) or "", now)
        out.append(item)
    return out


def truthy(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
