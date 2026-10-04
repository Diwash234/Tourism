"""City and district names used to normalize itinerary search locations."""
from __future__ import annotations

import csv
import functools
import logging
import re
from pathlib import Path
from typing import Any, Optional


_DATA_PATH = Path(__file__).resolve().parents[1] / "dataset" / "nepal_cities_200.csv"
logger = logging.getLogger(__name__)


def _tokenize(value: str) -> str:
    return re.sub(r"\W+", "_", (value or "").lower()).strip("_")


@functools.lru_cache(maxsize=1)
def _city_index() -> dict[str, dict[str, Any]]:
    if not _DATA_PATH.exists():
        logger.warning("Itinerary city catalogue is missing: %s", _DATA_PATH)
        return {}
    index: dict[str, dict[str, Any]] = {}
    with _DATA_PATH.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            city = (row.get("city") or "").strip()
            district = (row.get("district") or "").strip()
            if not city:
                continue
            profile = {
                "city": city,
                "district": district,
                "province": (row.get("province") or "").strip(),
            }
            index[_tokenize(city)] = profile
            district_key = _tokenize(district)
            if district_key and district_key not in index:
                index[district_key] = profile
    return index


def get_city_profile(name: str) -> Optional[dict[str, Any]]:
    """Return the canonical city/district for a known location."""
    needle = _tokenize(name)
    if not needle:
        return None
    return _city_index().get(needle)
