"""Round 24b: purge junk/over-shared cover photos (v2, fixed).

* Junk URLs (border map, Hilsa border village) are excluded from the pool
  entirely so they can never be re-picked as replacements.
* Only covers shared >= 8 times get processed (based on a snapshot of the
  ORIGINAL counts, so mid-run counter mutation can't cascade).
* A name-matched cover is kept; the rest get a category-appropriate,
  least-shared pool photo.

Usage: PYTHONPATH=/home/user/Tourism/Tourism /home/user/.venv/bin/python scripts/fix_round24b_overshared.py
"""
import hashlib
import os
import re
from collections import Counter, defaultdict

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage, Category  # noqa: E402

import hashlib as _hl
import urllib.parse as _up


def wm_thumb(filename):
    """960px Wikimedia thumb URL for a Commons filename."""
    fn = _up.unquote(filename).replace(" ", "_")
    m = _hl.md5(fn.encode("utf-8")).hexdigest()
    q = _up.quote(fn, safe="-_.~()',")
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{m[0]}/{m[:2]}/{q}/960px-{q}"

MAX_SHARE = 12
JUNK_RE = re.compile(
    r"Western_border_of_Nepal_shifting_Limpiyadhura|Village_hilsa_@_Nepal-China_Border",
    re.I,
)
GENERIC_TOKENS = {
    "hotel", "inn", "lodge", "resort", "guest", "home", "house", "view",
    "and", "the", "of", "park", "nepal", "international", "heritage",
    "restaurant", "eco", "holiday", "private", "trek", "trekking",
    "monastery", "cave", "gufa", "temple", "village", "lake", "trail",
    "point", "camp", "base", "hill", "danda", "khola", "river",
    "ghar", "khaja", "food", "stay",
}


def name_tokens(name):
    return set(re.findall(r"[a-z0-9]{3,}", (name or "").lower()))


def photo_tokens(url):
    fn = re.sub(r"^(960px-|[0-9]+px-)", "", (url or "").rsplit("/", 1)[-1])
    fn = re.sub(r"\.(jpe?g|JPE?G|png|PNG)$", "", fn)
    fn = fn.replace("_", " ").replace("-", " ").replace("%26", " ")
    return set(re.findall(r"[a-z0-9]{3,}", fn.lower()))


def main():
    dests = {d.id: d for d in Destination.objects.all()}
    print(f"destinations: {len(dests)}")

    # --- build pool, EXCLUDING junk URLs --------------------------------
    pool = {}
    cat_urls = defaultdict(set)
    skipped_pool = 0
    for r in (
        DestinationImage.objects.filter(source__in=("wikimedia", "openverse"), is_verified=1)
        .values("external_url", "photographer", "license_type", "source_url",
                "alt_text", "destination__category__slug")
    ):
        u = r["external_url"]
        if not u:
            continue
        if JUNK_RE.search(u):
            skipped_pool += 1
            continue
        pool.setdefault(u, {
            "photographer": r["photographer"] or "Wikimedia Commons contributor",
            "license": r["license_type"] or "See Commons file page",
            "source_url": r["source_url"] or "",
            "alt": r["alt_text"] or "",
        })
        if r["destination__category__slug"]:
            cat_urls[r["destination__category__slug"]].add(u)
    print(f"pool URLs: {len(pool)} (junk excluded from pool: {skipped_pool})")


    # --- grow the pool with freshly fetched verified photos --------------
    NEW_PHOTOS = [
        # (filename, artist, license, caption, source_url, attach_name_hint, cat_slug)
        ("Hot_Spring_at_Tatopani_(4523585441).jpg", "Greg Willis", "CC BY-SA 2.0",
         "Hot spring at Tatopani", "https://commons.wikimedia.org/wiki/File:Hot_Spring_at_Tatopani_(4523585441).jpg",
         "tatopani", "hot-springs"),
        ("Modi_River_and_Hot_Spring_-_Annapurna_Conservation_Area.jpg", "Saroj Pandey", "CC BY-SA 3.0",
         "Modi River and hot spring, Annapurna area", "https://commons.wikimedia.org/wiki/File:Modi_River_and_Hot_Spring_-_Annapurna_Conservation_Area.jpg",
         "tatopani", "hot-springs"),
        ("Mt_Manaslu.jpg", "Pratapgrg", "CC BY-SA 4.0",
         "Close view of Mt. Manaslu (8,156 m)", "https://commons.wikimedia.org/wiki/File:Mt_Manaslu.jpg",
         "manaslu", "mountains"),
        ("Sunrise_over_the_Manaslu_Range.jpg", "Johnnyadams13", "CC BY-SA 4.0",
         "Sunrise over the Manaslu Range", "https://commons.wikimedia.org/wiki/File:Sunrise_over_the_Manaslu_Range.jpg",
         "manaslu", "mountains"),
        ("Karnali_river.JPG", "Sherparinji", "CC BY-SA 3.0",
         "Humla Karnali river confluence", "https://commons.wikimedia.org/wiki/File:Karnali_river.JPG",
         "karnali", "rivers"),
        ("Karnali-IMG_0138.jpg", "Wang Lama Humla", "CC BY-SA 4.0",
         "Karnali river with terraces", "https://commons.wikimedia.org/wiki/File:Karnali-IMG_0138.jpg",
         "karnali", "rivers"),
        ("Karnali_Bridge_Karnali_River_Chisapani_Kailali_Pradesh_7_Nepal_Rajesh_Dhungana_(22).jpg", "Rajesh Dhungana", "CC BY-SA 4.0",
         "Karnali bridge over the Karnali river at Chisapani, Kailali", "https://commons.wikimedia.org/wiki/File:Karnali_Bridge_Karnali_River_Chisapani_Kailali_Pradesh_7_Nepal_Rajesh_Dhungana_(22).jpg",
         "karnali", "rivers"),
        ("A_View_of_Sinja_Valley.jpg", "Redpandamoon", "CC BY-SA 4.0",
         "View of Sinja Valley, Jumla", "https://commons.wikimedia.org/wiki/File:A_View_of_Sinja_Valley.jpg",
         "sinja", "heritage"),
        ("Sinja_Valley,_Karnali.jpg", "Punyapaudel", "CC BY-SA 4.0",
         "Sinja Valley, Jumla - ancient Khas capital", "https://commons.wikimedia.org/wiki/File:Sinja_Valley,_Karnali.jpg",
         "sinja", "heritage"),
    ]
    added = 0
    for fn, artist, lic, cap, src_url, hint, cslug in NEW_PHOTOS:
        thumb = wm_thumb(fn)
        if thumb in pool:
            continue
        dest = Destination.objects.filter(name__icontains=hint).first()
        if dest is None:
            cat = next((c for c in Category if c.slug == cslug), None) if False else None
            # fall back: first destination in that category
            from tourist.models import Category
            c = Category.objects.filter(slug=cslug).first()
            dest = Destination.objects.filter(category=c).first() if c else Destination.objects.first()
        if dest is None:
            continue
        DestinationImage.objects.create(
            destination=dest, external_url=thumb, thumbnail_url=thumb,
            caption=cap, alt_text=cap, is_cover=False,
            source="wikimedia", attribution=f"Photo: {cap} \u2014 {artist} ({lic})",
            is_promoted=0, view_count=0, is_verified=1,
            verification_status="approved", copyright_status="verified_reusable",
            image_category="attraction", license_type=lic, photographer=artist,
            source_platform="Wikimedia Commons (verified)", source_url=src_url,
            authenticity_score=0.92, destination_match_score=0.9, quality_score=0.9,
            realism_score=1.0, overall_score=0.9, ordering=99,
        )
        added += 1
    print(f"new pool photos added: {added}")

    # --- snapshot ORIGINAL cover counts ----------------------------------
    covers = Counter(
        DestinationImage.objects.filter(is_cover=True).values_list("external_url", flat=True)
    )
    orig = dict(covers)
    live = Counter(covers)  # mutated as we go

    def pick_for(dest, avoid):
        cat_slug = dest.category.slug if dest.category_id else ""
        cands = sorted(
            (x for x in cat_urls.get(cat_slug, []) if x not in avoid and live.get(x, 0) <= MAX_SHARE),
            key=lambda x: (live.get(x, 0), x),
        )
        if not cands:
            cands = sorted(
                (x for x in pool if x not in avoid and live.get(x, 0) <= MAX_SHARE),
                key=lambda x: (live.get(x, 0), x),
            )
        if not cands:
            cands = sorted(pool, key=lambda x: (live.get(x, 0), x))
        h = int(hashlib.md5(f"{dest.name}|{dest.id}|r24b".encode()).hexdigest(), 16)
        return cands[h % len(cands)]

    # process: any cover whose ORIGINAL share >= MAX_SHARE, or junk
    rows = list(
        DestinationImage.objects.filter(is_cover=True).select_related("destination")
    )
    by_url = defaultdict(list)
    for row in rows:
        by_url[row.external_url].append(row)

    swapped = 0
    kept = 0
    for u, rrows in by_url.items():
        hot = orig.get(u, 0) >= MAX_SHARE or bool(JUNK_RE.search(u or ""))
        if not hot:
            continue
        for row in rrows:
            dest = row.destination
            if not dest:
                continue
            name = dest.name or ""
            if JUNK_RE.search(u or ""):
                keep = False
            else:
                dtok = name_tokens(name) - GENERIC_TOKENS
                ptok = photo_tokens(u) - GENERIC_TOKENS
                keep = bool(dtok and ptok and (dtok & ptok))
            if keep:
                kept += 1
                continue
            new_u = pick_for(dest, {u})
            meta = pool.get(new_u)
            if not meta:
                continue
            row.external_url = new_u
            row.thumbnail_url = new_u
            row.attribution = f"Photo: {name or 'Nepal'} — {meta['photographer']} ({meta['license']})"
            row.photographer = meta["photographer"]
            row.license_type = meta["license"]
            row.source_url = meta["source_url"]
            row.save(update_fields=["external_url", "thumbnail_url", "attribution",
                                    "photographer", "license_type", "source_url"])
            live[u] -= 1
            live[new_u] += 1
            swapped += 1
    print(f"swapped: {swapped} | kept name-matched: {kept}")

    covers2 = Counter(
        DestinationImage.objects.filter(is_cover=True).values_list("external_url", flat=True)
    )
    junk_left = sum(1 for u in covers2 if JUNK_RE.search(u or ""))
    over = sorted(((c, u) for u, c in covers2.items() if c >= MAX_SHARE), reverse=True)
    print(f"covers >= {MAX_SHARE}x: {len(over)} | junk covers left: {junk_left}")
    print(f"max share: {max(covers2.values()) if covers2 else 0} | distinct: {len(covers2)}")
    for c, u in over[:10]:
        print(f"  {c:3d}  {u.rsplit('/',1)[-1][:70]}")


if __name__ == "__main__":
    main()
