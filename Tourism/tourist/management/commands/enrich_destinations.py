"""Fill missing destination data from coordinates, catalogues and service CSVs.

    python manage.py enrich_destinations                     # live database
    python manage.py enrich_destinations --fixture data.json # Django fixture
    python manage.py enrich_destinations --fixture dataset/data.json \\
        --category-from data.json                            # Render catalogue

Only empty values are written - curated data is never overwritten - so the
command is safe to run repeatedly (the Docker entrypoint runs it on every
boot so a freshly seeded PostgreSQL always has distances, nearest
city/airport, normalized city names, addresses, cited elevations, service
proximity, descriptions and an honest NULL entry fee instead of 0.0).
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tourist.data_enrichment import (
    enrich_destination_fields,
    load_elevation_lookup,
    load_service_points,
)


class Command(BaseCommand):
    help = "Fill empty destination fields with values derived from real data (never overwrites)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            help="Enrich a JSON file (Django fixture or dataset catalogue) in place instead of the database.",
        )
        parser.add_argument(
            "--category-from",
            help="Fixture used to resolve category names/pks by slug (e.g. data.json).",
        )
        parser.add_argument(
            "--dataset-dir",
            default="dataset",
            help="Directory holding destination_elevations.json and the service CSVs.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing.",
        )

    # -- helpers ---------------------------------------------------------
    def _dataset_dir(self, options) -> Path:
        base = Path(__file__).resolve().parents[3]
        return (base / options["dataset_dir"]).resolve()

    @staticmethod
    def _category_maps(*sources) -> tuple[dict, dict]:
        """slug -> (category pk, category name) from any given fixture.

        Each source is a path or an already-parsed payload; the caller passes
        payloads for large files so the 59 MB fixture is never read twice.
        """
        by_slug: dict[str, tuple] = {}
        names: dict[int, str] = {}
        for source in sources:
            if not source:
                continue
            if isinstance(source, (list, dict)):
                payload = source
                # The verified snapshot is {"records": [...]}; unwrap it so
                # category resolution works against the canonical table.
                if isinstance(payload, dict):
                    payload = payload.get("records")
            else:
                path = Path(source)
                if not path.is_file():
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                continue
            for rec in payload:
                if rec.get("model") == "tourist.category":
                    names[int(rec["pk"])] = rec["fields"].get("name") or ""
            for rec in payload:
                if rec.get("model") != "tourist.destination":
                    continue
                cat = rec["fields"].get("category")
                if cat is None:
                    continue
                slug = rec["fields"].get("slug")
                if slug and cat in names:
                    by_slug.setdefault(slug, (cat, names[cat]))
        return by_slug, names

    # -- database mode ---------------------------------------------------
    def _enrich_database(self, options) -> int:
        from decimal import Decimal

        from tourist.models import Destination

        dataset_dir = self._dataset_dir(options)
        elevations = load_elevation_lookup(dataset_dir)
        category_by_slug, _ = self._category_maps(
            Path(options["category_from"]) if options["category_from"] else None
        )
        total_changes = 0
        rows_changed = 0
        queryset = Destination.objects.select_related("category").iterator(chunk_size=500)
        for dest in queryset:
            fields = {
                "slug": dest.slug,
                "name": dest.name,
                "city": dest.city or "",
                "district": dest.district or "",
                "province": dest.province or "",
                "type": dest.type or "",
                "latitude": dest.latitude,
                "longitude": dest.longitude,
                "city_english": dest.city_english,
                "city_nepali": dest.city_nepali,
                "country": dest.country,
                "address": dest.address,
                "distance_from_kathmandu_km": dest.distance_from_kathmandu_km,
                "distance_from_nearest_city_km": dest.distance_from_nearest_city_km,
                "nearest_major_city": dest.nearest_major_city,
                "distance_from_nearest_airport_km": dest.distance_from_nearest_airport_km,
                "nearest_airport_name": dest.nearest_airport_name,
                "best_time_to_visit": dest.best_time_to_visit,
                "description": dest.description,
                "short_description": dest.short_description,
                "altitude": dest.altitude,
                "elevation_m": dest.elevation_m,
                "elevation_source": dest.elevation_source,
                "elevation_retrieved_at": dest.elevation_retrieved_at,
                "entry_fee": dest.entry_fee,
            }
            category_name = dest.category.name if dest.category else ""
            changes = enrich_destination_fields(
                fields,
                category_name=category_name,
                elevations=elevations,
            )
            if not changes:
                continue
            rows_changed += 1
            total_changes += len(changes)
            if options["dry_run"]:
                continue
            update_fields = []
            for key, value in changes.items():
                if key in {"distance_from_kathmandu_km", "distance_from_nearest_city_km",
                           "distance_from_nearest_airport_km", "entry_fee"} and value is not None:
                    value = Decimal(str(value))
                setattr(dest, key, value)
                update_fields.append(key)
            dest.save(update_fields=update_fields)
        verb = "would update" if options["dry_run"] else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"Destinations {verb}: {rows_changed} ({total_changes} field values filled)"
        ))
        return rows_changed

    # -- JSON file mode --------------------------------------------------
    def _enrich_file(self, options) -> int:
        path = Path(options["fixture"]).resolve()
        if not path.is_file():
            raise CommandError(f"Fixture not found: {path}")
        dataset_dir = self._dataset_dir(options)
        elevations = load_elevation_lookup(dataset_dir)
        services = load_service_points(dataset_dir)

        raw = path.read_text(encoding="utf-8")
        trailing = "\n" if raw.endswith("\n") else ""
        payload = json.loads(raw)
        del raw  # release the source text before building the maps

        category_payload = None
        if options["category_from"]:
            category_path = Path(options["category_from"]).resolve()
            if category_path != path and category_path.is_file():
                category_payload = json.loads(category_path.read_text(encoding="utf-8"))
        category_by_slug, category_names = self._category_maps(category_payload, payload)

        rows_changed = 0
        total_changes = 0

        if isinstance(payload, dict) and isinstance(payload.get("destinations"), dict):
            # Render catalogue: {"destinations": {"<id>": {...flat...}}}
            for dest in payload["destinations"].values():
                cat_pk, cat_name = category_by_slug.get(dest.get("slug"), (None, ""))
                assigned = cat_pk is not None and dest.get("category") is None
                if assigned:
                    dest["category"] = cat_pk
                changes = enrich_destination_fields(
                    dest,
                    category_name=cat_name,
                    elevations=elevations,
                    services=services,
                )
                if assigned:
                    changes["category"] = cat_pk
                if changes:
                    dest.update(changes)
                    rows_changed += 1
                    total_changes += len(changes)
        elif isinstance(payload, list):
            # Django fixture: [{"model": ..., "pk": ..., "fields": {...}}]
            for rec in payload:
                if rec.get("model") != "tourist.destination":
                    continue
                fields = rec["fields"]
                cat_pk, cat_name = category_by_slug.get(fields.get("slug"), (None, ""))
                assigned = cat_pk is not None and fields.get("category") is None
                if assigned:
                    fields["category"] = cat_pk
                    cat_name = category_names.get(cat_pk, cat_name)
                fields_with_pk = {"pk": rec.get("pk"), **fields}
                changes = enrich_destination_fields(
                    fields_with_pk,
                    category_name=cat_name,
                    elevations=elevations,
                    services=services,
                )
                changes.pop("pk", None)
                if assigned:
                    changes["category"] = cat_pk
                if changes:
                    fields.update(changes)
                    rows_changed += 1
                    total_changes += len(changes)
        else:
            raise CommandError(
                f"{path.name} is neither a Django fixture nor a dataset catalogue"
            )

        verb = "would update" if options["dry_run"] else "updated"
        if not options["dry_run"]:
            path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + trailing,
                encoding="utf-8",
            )
        self.stdout.write(self.style.SUCCESS(
            f"{path.name}: {verb} {rows_changed} destinations ({total_changes} field values filled)"
        ))
        return rows_changed

    def handle(self, *args, **options):
        if options["fixture"]:
            self._enrich_file(options)
        else:
            self._enrich_database(options)
