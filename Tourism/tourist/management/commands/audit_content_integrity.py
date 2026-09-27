"""Dataset-wide, non-destructive integrity audit for Nepal Yatra.

This command NEVER deletes media. It creates explicit match states and only
changes records when --repair is supplied. A repair is deliberately
conservative: it can quarantine obviously repeated/broken media and classify
strong filename/path matches, but it never invents an image for a place.

Run:
    python manage.py audit_content_integrity
    python manage.py audit_content_integrity --json report.json
    python manage.py audit_content_integrity --repair --json report.json
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Count

from tourist.models import Destination, DestinationImage, Hotel, HotelImage


def norm(value):
    value = (value or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def tokens(*values):
    out = set()
    for value in values:
        out.update(x for x in norm(value).split() if len(x) >= 3)
    return out


def media_text(photo):
    return " ".join(
        str(getattr(photo, field, "") or "")
        for field in ("image_path", "external_url", "source_url", "alt_text", "caption")
    ).lower()


def hotel_media_text(photo):
    return " ".join(
        str(getattr(photo, field, "") or "")
        for field in ("external_url", "source_url", "alt_text", "caption")
    ).lower()


class Command(BaseCommand):
    help = "Audit and conservatively repair destination/hotel media, coordinates and provenance."

    def add_arguments(self, parser):
        parser.add_argument("--repair", action="store_true", help="Apply only conservative classifications/quarantine; never delete media.")
        parser.add_argument("--json", dest="json_path", default="", help="Write the complete report to JSON.")
        parser.add_argument("--limit", type=int, default=0, help="Limit destination rows for a trial run.")

    def handle(self, *args, **options):
        repair = options["repair"]
        destinations = Destination.objects.all().order_by("id")
        if options["limit"]:
            destinations = destinations[: options["limit"]]

        report = {
            "mode": "repair" if repair else "audit",
            "non_destructive": True,
            "destinations": {},
            "hotels": {},
            "media": {},
            "coordinates": {},
            "warnings": [],
        }

        dest_ids = [d.id for d in destinations]
        images = list(DestinationImage.objects.filter(destination_id__in=dest_ids))
        hotels = list(Hotel.objects.filter(destination_id__in=dest_ids))
        hotel_ids = [h.id for h in hotels]
        hotel_images = list(HotelImage.objects.filter(hotel_id__in=hotel_ids))

        status_counts = Counter()
        source_counts = Counter()
        suspicious_repeated = []
        changed = 0

        for photo in images:
            destination = next((d for d in destinations if d.id == photo.destination_id), None)
            if not destination:
                continue
            status, note = self.classify_destination(photo, destination)
            status_counts[status] += 1
            source_counts[photo.source or "unknown"] += 1
            if repair and status != photo.match_status:
                photo.match_status = status
                photo.verification_note = note
                update = ["match_status", "verification_note"]
                # Never publish a media row that our conservative audit says
                # is unverified merely because an old import marked it approved.
                if status in {"unverified", "unavailable"}:
                    photo.verification_status = DestinationImage.ImageStatus.PENDING
                    photo.is_verified = False
                    update += ["verification_status", "is_verified"]
                elif status == "verified_entity" and photo.source_url:
                    photo.verified_source_url = photo.source_url
                    update.append("verified_source_url")
                photo.save(update_fields=update + ["updated_at"])
                changed += 1

        url_groups = defaultdict(list)
        for photo in images:
            key = (photo.external_url or "").strip()
            if key:
                url_groups[key].append(photo.destination_id)
        for url, ids in url_groups.items():
            unique = len(set(ids))
            if unique >= 5:
                suspicious_repeated.append({"url": url[:500], "destination_count": unique})
                if repair:
                    qs = DestinationImage.objects.filter(external_url=url, destination_id__in=ids)
                    qs.update(match_status="unverified", verification_status=DestinationImage.ImageStatus.PENDING, is_verified=False)

        hotel_status = Counter()
        hotel_changed = 0
        for hotel in hotels:
            gallery = [x for x in hotel_images if x.hotel_id == hotel.id]
            if not gallery:
                # Preserve legacy cover/external media by copying it into the
                # new history table; the legacy field remains untouched.
                if hotel.cover_image or hotel.external_image_url:
                    hi = HotelImage.objects.create(
                        hotel=hotel,
                        image=hotel.cover_image if hotel.cover_image else None,
                        external_url=hotel.external_image_url or "",
                        source_url=hotel.source_url or "",
                        alt_text=hotel.name,
                        caption=hotel.name,
                        match_status="unverified",
                        verification_note="Migrated from legacy Hotel image field; requires entity verification.",
                        is_cover=True,
                    )
                    gallery = [hi]
                    hotel_changed += 1
            for photo in gallery:
                status, note = self.classify_hotel(photo, hotel)
                hotel_status[status] += 1
                if repair and status != photo.match_status:
                    photo.match_status = status
                    photo.verification_note = note
                    photo.save(update_fields=["match_status", "verification_note", "updated_at"])
                    hotel_changed += 1

        valid_coords = invalid_coords = missing_coords = 0
        for d in destinations:
            try:
                lat, lon = float(d.latitude), float(d.longitude)
                valid = 26.0 <= lat <= 31.5 and 80.0 <= lon <= 89.5
            except (TypeError, ValueError):
                valid = False
            if d.latitude is None or d.longitude is None:
                missing_coords += 1
            elif valid:
                valid_coords += 1
            else:
                invalid_coords += 1

        report["destinations"] = {
            "total": len(destinations),
            "with_images": len({p.destination_id for p in images}),
            "without_images": len(destinations) - len({p.destination_id for p in images}),
        }
        report["hotels"] = {
            "total": len(hotels),
            "with_gallery": len({p.hotel_id for p in hotel_images}),
            "legacy_media_migrated_or_updated": hotel_changed,
        }
        report["media"] = {
            "destination_images": len(images),
            "hotel_images": len(hotel_images),
            "destination_match_status": dict(status_counts),
            "hotel_match_status": dict(hotel_status),
            "sources": dict(source_counts),
            "repeated_external_urls_across_5_or_more_destinations": len(suspicious_repeated),
            "records_changed": changed,
        }
        report["coordinates"] = {
            "valid_in_nepal_bounds": valid_coords,
            "invalid": invalid_coords,
            "missing": missing_coords,
        }
        report["warnings"].append(
            "Image visual identity cannot be proven from metadata alone. Rows marked unverified require human/media-source verification; the command never invents a destination or hotel relationship."
        )
        report["warnings"].append(
            "Road distance is not computed here. Run the existing audit_routes command against the same database; straight-line distance must never be labelled as driving distance."
        )

        if options["json_path"]:
            path = Path(options["json_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False))

    @staticmethod
    def classify_destination(photo, destination):
        text = media_text(photo)
        strong = tokens(destination.name, destination.slug, destination.city, destination.city_english, destination.district)
        if not (photo.external_url or photo.image_path or photo.image):
            return "unavailable", "No image binary or external/image-server URL."
        if not (photo.source_url or photo.image_path or photo.image):
            return "unverified", "No provenance/source reference."
        matched = sum(1 for t in strong if t and t in text)
        if matched >= 1 and (photo.image_path or photo.source_url or photo.external_url):
            return "verified_entity", "Conservative metadata match to destination name/location."
        return "area_context", "Media exists but metadata does not prove destination-specific identity."

    @staticmethod
    def classify_hotel(photo, hotel):
        text = hotel_media_text(photo)
        strong = tokens(hotel.name)
        if not (photo.external_url or photo.image):
            return "unavailable", "No image binary or external URL."
        if any(t in text for t in strong if len(t) >= 4):
            return "verified_entity", "Conservative metadata match to hotel name."
        return "unverified", "Hotel-specific identity is not proven by available metadata."
