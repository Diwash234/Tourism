"""Load the bundled, cited datasets:

* dataset/nrb_forex_seed.json -- verbatim Nepal Rastra Bank rates (2026-09-26)
  so currency conversion works before the first `refresh_forex` run.
* dataset/destination_elevations.json -- Copernicus DEM (via Open-Meteo)
  elevations, applied only where the destination id AND coordinates still
  match the values that were looked up.

Both are no-ops when the files are missing. Reverse is a no-op.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from django.db import migrations

DATASET = Path(__file__).resolve().parents[2] / "dataset"


def _load_forex(apps):
    path = DATASET / "nrb_forex_seed.json"
    if not path.exists():
        return
    Snap = apps.get_model("tourist", "ForexRateSnapshot")
    data = json.loads(path.read_text(encoding="utf-8"))
    fetched = datetime.fromisoformat(f"{data.get('retrieved_at', '2026-09-26')}T00:00:00+00:00")
    for entry in data.get("payload") or []:
        rates = {}
        for row in entry.get("rates") or []:
            cur = row.get("currency") or {}
            iso = str(cur.get("iso3") or "").upper()
            if len(iso) == 3:
                rates[iso] = {"name": cur.get("name") or iso, "unit": int(cur.get("unit") or 1),
                              "buy": str(Decimal(str(row["buy"]))), "sell": str(Decimal(str(row["sell"])))}
        if rates:
            Snap.objects.update_or_create(
                rate_date=date.fromisoformat(entry["date"][:10]),
                defaults={"published_on": entry.get("published_on") or "", "rates": rates,
                          "source_name": data.get("source_name") or "Nepal Rastra Bank",
                          "source_url": data.get("source_url") or "https://www.nrb.org.np/api/forex/v1/rates",
                          "fetched_at": fetched})


def _load_elevations(apps):
    path = DATASET / "destination_elevations.json"
    if not path.exists():
        return
    Destination = apps.get_model("tourist", "Destination")
    records = json.loads(path.read_text(encoding="utf-8")).get("records") or []
    by_id = {r["id"]: r for r in records}
    for dest in Destination.objects.filter(id__in=list(by_id), elevation_m__isnull=True).only("id", "latitude", "longitude"):
        rec = by_id[dest.id]
        if dest.latitude is None or dest.longitude is None:
            continue
        if abs(float(dest.latitude) - rec["lat"]) > 1e-5 or abs(float(dest.longitude) - rec["lon"]) > 1e-5:
            continue  # destination moved since lookup -> value no longer valid
        Destination.objects.filter(pk=dest.pk).update(
            elevation_m=int(rec["elevation_m"]),
            elevation_source=rec.get("source") or "Copernicus DEM GLO-90 via Open-Meteo",
            elevation_retrieved_at=date.fromisoformat(rec.get("retrieved_at") or "2026-09-26"),
        )


def forwards(apps, schema_editor):
    _load_forex(apps)
    _load_elevations(apps)


class Migration(migrations.Migration):
    dependencies = [("tourist", "0082_elevation_and_forex")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
