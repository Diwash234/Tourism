"""Apply round-2 verified Wikimedia photos (viewpoints, stupas, festivals,
tea/coffee, adventures, heritage, temples) as approved covers.

Usage:
    /home/user/.venv/bin/python manage.py shell < scripts/apply_round2_photos.py
"""
import os
import hashlib
import urllib.parse

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
django.setup()

from tourist.models import Destination, DestinationImage  # noqa: E402

TSV = os.path.join(os.path.dirname(__file__), "round2_verified_photos.tsv")
BASE = "https://upload.wikimedia.org/wikipedia/commons/thumb/{a}/{ab}/{q}/1000px-{q}"


def thumb_url(filename: str) -> str:
    fn_ = filename.replace(" ", "_")
    m = hashlib.md5(fn_.encode("utf-8")).hexdigest()
    q = urllib.parse.quote(fn_, safe="-_.~")
    return BASE.format(a=m[0], ab=m[0:2], q=q)


CATEGORY_IMAGE_KIND = {
    44: "temple", 45: "monastery", 56: "festival", 62: "farm", 3: "viewpoint",
    53: "viewpoint", 58: "adventure", 60: "adventure", 59: "adventure",
    64: "adventure", 46: "heritage", 70: "heritage", 34: "temple",
    30: "temple", 74: "pilgrimage", 43: "trekking", 38: "religious",
}


def main():
    entries = []
    with open(TSV, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            did_s, fn = line.split("\t", 1)
            entries.append((int(did_s), fn))

    created = 0
    demoted = 0
    skipped = []
    for did, filename in entries:
        dest = Destination.objects.filter(pk=did).first()
        if dest is None:
            skipped.append((did, filename, "no destination"))
            continue
        # demote any postcard cover
        old_covers = DestinationImage.objects.filter(
            destination=dest, is_cover=True,
            external_url__startswith="/api/v1/postcard/")
        for oc in old_covers:
            oc.is_cover = False
            oc.save(update_fields=["is_cover", "updated_at"])
            demoted += 1
        # remove any pre-existing wikimedia cover (should not exist)
        DestinationImage.objects.filter(
            destination=dest, is_cover=True, source="wikimedia").delete()
        title = filename
        url = thumb_url(filename)
        kind = CATEGORY_IMAGE_KIND.get(dest.category_id, "attraction")
        DestinationImage.objects.create(
            destination=dest,
            external_url=url,
            thumbnail_url=url,
            caption=dest.name,
            alt_text=dest.name,
            is_cover=True,
            source="wikimedia",
            attribution=f"Photo: Wikimedia Commons \u2014 {title}",
            is_promoted=0,
            view_count=0,
            is_verified=1,
            verification_status="approved",
            copyright_status="verified_reusable",
            image_category=kind,
            license_type="See Commons file page",
            photographer="Wikimedia Commons contributor",
            source_platform="Wikimedia Commons",
            source_url=f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(title.replace(' ', '_'))}",
            authenticity_score=1.0,
            destination_match_score=1.0,
            quality_score=0.98,
            realism_score=1.0,
            overall_score=0.98,
            ordering=0,
        )
        created += 1

    print(f"Created covers: {created}")
    print(f"Demoted old covers: {demoted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
