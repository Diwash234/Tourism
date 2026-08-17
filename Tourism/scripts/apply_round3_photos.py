"""Apply round-3 verified photos from Openverse (Flickr / WordPress.org /
Wikimedia via Openverse) as approved covers — multi-platform real images.

Usage:
    PYTHONPATH=. /home/user/.venv/bin/python scripts/apply_round3_photos.py
"""
import hashlib
import os
import urllib.parse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage  # noqa: E402

TSV = os.path.join(os.path.dirname(__file__), "round3_verified_photos.tsv")
BASE = "https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{q}/1000px-{q}"

CATEGORY_IMAGE_KIND = {
    52: "cave", 49: "waterfall", 66: "hot_spring", 44: "temple", 45: "monastery",
    54: "village", 4: "museum", 37: "wildlife", 43: "trekking", 62: "farm",
    3: "viewpoint", 53: "viewpoint", 50: "forest", 65: "snow", 69: "food",
    58: "adventure", 60: "adventure", 68: "handicraft", 70: "scenic",
    71: "eco_tourism", 56: "festival",
}


def wikimedia_thumb(filename: str) -> str:
    fn_ = filename.replace(" ", "_")
    m = hashlib.md5(fn_.encode("utf-8")).hexdigest()
    q = urllib.parse.quote(fn_, safe="-_.~")
    return BASE.format(a=m[0], ab=m[0:2], q=q)


def main():
    entries = []
    with open(TSV, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            entries.append(parts)

    created = 0
    demoted = 0
    skipped = []
    for parts in entries:
        did_s, value, kind, title, creator, lic, provider, source_url = parts
        did = int(did_s)
        dest = Destination.objects.filter(pk=did).first()
        if dest is None:
            skipped.append((did, "no destination"))
            continue
        if kind == "wm":
            url = wikimedia_thumb(value)
            thumb = url
        else:
            url = value
            thumb = url
        # demote old postcard cover
        for oc in DestinationImage.objects.filter(
            destination=dest, is_cover=True,
            external_url__startswith="/api/v1/postcard/"):
            oc.is_cover = False
            oc.save(update_fields=["is_cover", "updated_at"])
            demoted += 1
        DestinationImage.objects.filter(
            destination=dest, is_cover=True, source__in=("wikimedia", "openverse")).delete()
        platform = {
            "flickr": "Flickr (via Openverse)",
            "wordpress": "WordPress.org Photos (via Openverse)",
            "wikimedia": "Wikimedia Commons (via Openverse)",
        }.get(provider, provider)
        kind_label = CATEGORY_IMAGE_KIND.get(dest.category_id, "attraction")
        DestinationImage.objects.create(
            destination=dest,
            external_url=url,
            thumbnail_url=thumb,
            caption=dest.name,
            alt_text=title,
            is_cover=True,
            source="openverse",
            attribution=f"Photo: {title} — {creator} ({lic})",
            is_promoted=0,
            view_count=0,
            is_verified=1,
            verification_status="approved",
            copyright_status="verified_reusable",
            image_category=kind_label,
            license_type=lic,
            photographer=creator,
            source_platform=platform,
            source_url=source_url,
            authenticity_score=1.0,
            destination_match_score=1.0,
            quality_score=0.95,
            realism_score=1.0,
            overall_score=0.95,
            ordering=0,
        )
        created += 1

    print(f"Created covers: {created}")
    print(f"Demoted old covers: {demoted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
