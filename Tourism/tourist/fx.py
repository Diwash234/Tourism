"""Official exchange rates from Nepal Rastra Bank (NRB).

Rules (release audit P0 "currency"):
  * The only rate source is NRB's public forex API. There is no hard-coded
    or environment "fallback" rate anywhere -- if no snapshot exists the
    conversion is reported as unavailable instead of silently guessed.
  * Every converted figure carries the NRB rate date and a ``stale`` flag
    (rate older than ``STALE_AFTER_DAYS``).
  * NPR <-> foreign conversion uses the NRB **buying** rate, i.e. the NPR a
    bank pays for one unit of foreign currency. This is stated in the API
    response so the UI can label it.

Network access is short-timeout and failures are cached for an hour so a
down NRB endpoint never slows page loads.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

NRB_API = "https://www.nrb.org.np/api/forex/v1/rates"
NRB_SOURCE_NAME = "Nepal Rastra Bank"
STALE_AFTER_DAYS = 3
FETCH_TIMEOUT_SECONDS = 6
FAILED_FETCH_BACKOFF_SECONDS = 3600
RATE_TYPE = "NRB buying rate"
SEED_FILE = Path(settings.BASE_DIR) / "dataset" / "nrb_forex_seed.json"


def _nepal_today() -> date:
    # Nepal is UTC+05:45 and NRB publishes rates just after local midnight.
    return (timezone.now() + timedelta(hours=5, minutes=45)).date()


def _parse_entry(entry: dict) -> tuple[date, str, dict]:
    rate_date = date.fromisoformat(str(entry["date"])[:10])
    rates = {}
    for row in entry.get("rates") or []:
        cur = row.get("currency") or {}
        iso = str(cur.get("iso3") or "").upper()
        if len(iso) != 3:
            continue
        try:
            unit = int(cur.get("unit") or 1)
            buy = Decimal(str(row.get("buy")))
            sell = Decimal(str(row.get("sell")))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if unit <= 0 or buy <= 0:
            continue
        rates[iso] = {"name": cur.get("name") or iso, "unit": unit, "buy": str(buy), "sell": str(sell)}
    return rate_date, str(entry.get("published_on") or ""), rates


def store_payload_entries(entries, source_url: str, fetched_at=None) -> list:
    """Upsert NRB payload entries into ForexRateSnapshot. Returns snapshots."""
    from .models import ForexRateSnapshot

    saved = []
    for entry in entries or []:
        try:
            rate_date, published_on, rates = _parse_entry(entry)
        except (KeyError, ValueError):
            continue
        if not rates:
            continue
        snap, _ = ForexRateSnapshot.objects.update_or_create(
            rate_date=rate_date,
            defaults={
                "published_on": published_on,
                "rates": rates,
                "source_name": NRB_SOURCE_NAME,
                "source_url": source_url,
                "fetched_at": fetched_at or timezone.now(),
            },
        )
        saved.append(snap)
    return saved


def load_seed_file(path: Path | None = None) -> list:
    path = Path(path or SEED_FILE)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    fetched = datetime.fromisoformat(f"{data.get('retrieved_at', '2026-09-26')}T00:00:00+00:00")
    return store_payload_entries(data.get("payload") or [], data.get("source_url") or NRB_API, fetched)


def fetch_from_nrb(days_back: int = 7, timeout: int = FETCH_TIMEOUT_SECONDS) -> list:
    """Fetch the last ``days_back`` days from NRB and store them. Raises on network error."""
    import requests

    today = _nepal_today()
    params = {
        "page": 1,
        "per_page": max(days_back, 1),
        "from": (today - timedelta(days=days_back)).isoformat(),
        "to": today.isoformat(),
    }
    resp = requests.get(NRB_API, params=params, timeout=timeout, headers={"Accept": "application/json"})
    resp.raise_for_status()
    payload = ((resp.json() or {}).get("data") or {}).get("payload") or []
    source_url = f"{NRB_API}?page=1&per_page={params['per_page']}&from={params['from']}&to={params['to']}"
    return store_payload_entries(payload, source_url)


def latest_snapshot(allow_fetch: bool = True):
    """Most recent stored snapshot; tries one NRB refresh per hour when out of date."""
    from .models import ForexRateSnapshot

    snap = ForexRateSnapshot.objects.order_by("-rate_date").first()
    if allow_fetch and (snap is None or snap.rate_date < _nepal_today()) and not cache.get("fx:nrb:backoff"):
        cache.set("fx:nrb:backoff", 1, FAILED_FETCH_BACKOFF_SECONDS)
        try:
            fetch_from_nrb()
            snap = ForexRateSnapshot.objects.order_by("-rate_date").first()
        except Exception as exc:  # network / parse errors must never break a page
            logger.info("NRB forex refresh failed: %s", exc)
    return snap


def npr_per_unit(snap, iso: str) -> Decimal | None:
    """NPR for ONE unit of ``iso`` at the NRB buying rate (unit-normalised)."""
    iso = (iso or "").upper()
    if iso == "NPR":
        return Decimal(1)
    row = (snap.rates or {}).get(iso) if snap else None
    if not row:
        return None
    return Decimal(row["buy"]) / Decimal(row["unit"])


def convert(amount, from_iso: str, to_iso: str, snap=None) -> float | None:
    """Convert via NPR using NRB buying rates. None when a rate is unavailable."""
    snap = snap if snap is not None else latest_snapshot()
    if amount is None or snap is None:
        return None
    src = npr_per_unit(snap, from_iso)
    dst = npr_per_unit(snap, to_iso)
    if src is None or dst is None or dst == 0:
        return None
    return float(Decimal(str(amount)) * src / dst)


def snapshot_meta(snap) -> dict:
    if snap is None:
        return {
            "available": False,
            "source": NRB_SOURCE_NAME,
            "detail": "No official exchange rate is available yet. Amounts are shown in NPR only.",
        }
    age_days = (_nepal_today() - snap.rate_date).days
    return {
        "available": True,
        "source": snap.source_name,
        "source_url": snap.source_url,
        "rate_date": snap.rate_date.isoformat(),
        "published_on": snap.published_on,
        "fetched_at": snap.fetched_at.isoformat() if snap.fetched_at else None,
        "rate_type": RATE_TYPE,
        "age_days": age_days,
        "stale": age_days > STALE_AFTER_DAYS,
    }


def rates_payload(snap=None) -> dict:
    snap = snap if snap is not None else latest_snapshot()
    meta = snapshot_meta(snap)
    if not meta["available"]:
        return meta
    currencies = {"NPR": {"name": "Nepalese Rupee", "unit": 1, "buy": "1", "sell": "1", "npr_per_unit": 1.0}}
    for iso, row in sorted((snap.rates or {}).items()):
        currencies[iso] = {**row, "npr_per_unit": float(npr_per_unit(snap, iso))}
    return {**meta, "base": "NPR", "currencies": currencies}
