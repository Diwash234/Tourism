"""Municipality → district/province mapping utilities.

Two ingestion paths, both auditable and never fabricated:

1. ``import_csv(text)`` — admin-supplied CSV (name,district[,province]).
   Rows are validated against the canonical 77-district table; province is
   derived from the district when omitted. Imported rows are verified.

2. ``build_coordinate_mappings(sample_limit=5)`` — derives candidate
   mappings for municipality-level ``district`` strings by reverse-geocoding
   the coordinates of the destinations that carry them (majority vote over a
   small sample). Candidates are stored ``verified=False`` for admin review
   and never overwrite an admin-provided mapping.
"""

import csv
import io
from collections import Counter

from .administrative_boundaries import NEPAL_DISTRICTS_DATA
from .location import reverse_geocode
from .models import Destination, MunicipalityMapping

CANON_DISTRICTS = {k.lower(): k for k in NEPAL_DISTRICTS_DATA}  # lowercase -> canonical name


def import_csv(text):
    """Parse and upsert admin CSV rows. Returns {created, updated, rejected}."""
    created = updated = 0
    rejected = []
    reader = csv.DictReader(io.StringIO(text or ""))
    for i, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        district = (row.get("district") or "").strip()
        province = (row.get("province") or "").strip()
        if not name or not district:
            rejected.append({"row": i, "reason": "name and district are required"})
            continue
        canon_name = CANON_DISTRICTS.get(district.lower())
        if not canon_name:
            rejected.append({"row": i, "reason": f"unknown district '{district}'"})
            continue
        resolved_province = province or NEPAL_DISTRICTS_DATA[canon_name]["province"]
        obj, was_created = MunicipalityMapping.objects.update_or_create(
            name=name,
            defaults={
                "district": canon_name,
                "province": resolved_province,
                "source": "csv_import",
                "verified": True,
            },
        )
        created += was_created
        updated += not was_created
    return {"created": created, "updated": updated, "rejected": rejected}


def build_coordinate_mappings(sample_limit=5):
    """Derive unverified candidate mappings from destination coordinates.

    For every distinct municipality-level ``district`` string, reverse-geocode
    a small sample of destination coordinates and take the majority province
    /district result. Existing verified mappings are never touched.
    """
    from django.db.models import Count

    rows = (
        Destination.objects.exclude(district="")
        .exclude(district__isnull=True)
        .values("district")
        .annotate(n=Count("id"))
    )
    created = skipped_verified = 0
    for r in rows:
        name = r["district"]
        if name.lower() in CANON_DISTRICTS:
            continue  # already a canonical district name
        existing = MunicipalityMapping.objects.filter(name=name).first()
        if existing and existing.verified:
            skipped_verified += 1
            continue
        samples = list(
            Destination.objects.filter(district=name)
            .exclude(latitude__isnull=True)
            .exclude(longitude__isnull=True)
            .values_list("latitude", "longitude")[:sample_limit]
        )
        if not samples:
            continue
        votes = Counter()
        for lat, lng in samples:
            info = reverse_geocode(lat, lng)
            if info and info.get("district"):
                votes[(info["district"], info["province"])] += 1
        if not votes:
            continue
        (district, province), _ = votes.most_common(1)[0]
        canon_name = CANON_DISTRICTS.get(district.lower())
        if not canon_name:
            continue
        obj, was_created = MunicipalityMapping.objects.update_or_create(
            name=name,
            defaults={
                "district": canon_name,
                "province": province,
                "source": "coordinate_derived",
                "verified": False,
                "matched_destination_count": r["n"],
            },
        )
        created += was_created
    return {"candidates": MunicipalityMapping.objects.filter(verified=False).count(),
            "created": created, "skipped_verified": skipped_verified}


def backfill_provinces(dry_run=True):
    """Fill NULL/empty destination.province using VERIFIED mappings only.

    Unverified (coordinate-derived) candidates never write to destinations —
    an admin must verify a mapping first. Returns counts.
    """
    verified = {m.name: m for m in MunicipalityMapping.objects.filter(verified=True)}
    targets = Destination.objects.filter(province__isnull=True) | Destination.objects.filter(province="")
    filled = 0
    pending = 0
    for d in targets.iterator():
        m = verified.get(d.district or "")
        if m:
            if not dry_run:
                d.province = m.province
                d.save(update_fields=["province"])
            filled += 1
        else:
            pending += 1
    return {"filled": filled, "pending_verification": pending, "dry_run": dry_run}
