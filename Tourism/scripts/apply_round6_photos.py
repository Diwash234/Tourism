"""Apply round-6 photos: covers + gallery rows (Wikimedia/Flickr/WordPress)."""
import hashlib
import os
import urllib.parse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage  # noqa: E402

TSV = os.path.join(os.path.dirname(__file__), "round6_photos.tsv")
BASE = "https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{q}/960px-{q}"


def wikimedia_thumb(filename: str) -> str:
    fn_ = urllib.parse.unquote(filename).replace(" ", "_")
    m = hashlib.md5(fn_.encode("utf-8")).hexdigest()
    q = urllib.parse.quote(fn_, safe="-_.~")
    return BASE.format(a=m[0], ab=m[0:2], q=q)


CATEGORY_IMAGE_KIND = {
    43: "trekking", 44: "temple", 45: "monastery", 49: "waterfall", 52: "cave",
    54: "village", 56: "festival", 58: "adventure", 62: "farm", 66: "hot_spring",
    67: "city", 68: "shopping", 3: "viewpoint", 4: "museum", 37: "wildlife",
    46: "heritage", 47: "lake", 48: "river", 50: "forest", 53: "viewpoint",
    65: "snow", 69: "food", 70: "scenic", 71: "eco_tourism", 74: "pilgrimage",
    40: "mountain",
}


def main():
    entries = []
    with open(TSV, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) == 9:
                did, value, kind, title, creator, lic, provider, source_url, role = parts
            else:
                continue
            entries.append((int(did), value, kind, title, creator, lic, provider, source_url, role))

    created = 0
    demoted = 0
    skipped = []
    for did, value, kind, title, creator, lic, provider, source_url, role in entries:
        dest = Destination.objects.filter(pk=did).first()
        if dest is None:
            skipped.append((did, "no destination"))
            continue
        url = wikimedia_thumb(value) if kind == "wm" else value
        thumb = url
        if role == "cover":
            # demote old postcard cover
            for oc in DestinationImage.objects.filter(
                destination=dest, is_cover=True,
                external_url__startswith="/api/v1/postcard/"):
                oc.is_cover = False
                oc.save(update_fields=["is_cover", "updated_at"])
                demoted += 1
            DestinationImage.objects.filter(
                destination=dest, is_cover=True, source__in=("wikimedia", "openverse")).delete()
            is_cover = True
            ordering = 0
        else:
            # gallery: avoid dupes with existing rows
            if DestinationImage.objects.filter(destination=dest, external_url=url).exists():
                continue
            is_cover = False
            ordering = DestinationImage.objects.filter(destination=dest).count() + 1
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
            caption=dest.name if is_cover else title,
            alt_text=title,
            is_cover=is_cover,
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
            ordering=ordering,
        )
        created += 1

    print(f"Created rows: {created} (covers + gallery)")
    print(f"Demoted old covers: {demoted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
