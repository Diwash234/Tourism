"""Safe connectors for approved, machine-readable Nepal authority feeds."""
from urllib.parse import urlparse

import requests
from django.conf import settings

from .risk_ingestion import ingest_records


def provider_config(provider):
    provider = provider.lower()
    if provider == "dhm":
        return settings.DHM_FEED_URL, settings.DHM_API_KEY
    if provider == "bipad":
        return settings.BIPAD_FEED_URL, settings.BIPAD_API_KEY
    raise ValueError(f"Unsupported official provider: {provider}")


def fetch_official_feed(provider, *, dry_run=False):
    url, api_key = provider_config(provider)
    if not url:
        return {"provider": provider, "configured": False, "ingested": False, "reason": "feed URL is not configured"}
    parsed = urlparse(url)
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("Official feed URL must use HTTPS.")
    headers = {"Accept": "application/json", "User-Agent": "NepalTourismRiskSync/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = requests.get(url, headers=headers, timeout=settings.EXTERNAL_SYNC_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    records = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("Official feed must return a list or an object containing a records list.")
    if dry_run:
        return {"provider": provider, "configured": True, "ingested": False, "record_count": len(records), "dry_run": True}
    summary = ingest_records(records, provider, verified=True)
    return {"provider": provider, "configured": True, "ingested": True, "record_count": len(records), "summary": summary}
