"""Round 24: fix DEAD cover links (pd.w.org NoSuchKey + over-shared flickr).

* Replaces every cover pointing at pd.w.org (dead placeholder service —
  confirmed HTTP NoSuchKey) with a proper verified Wikimedia photo from the
  pool, category-appropriate, deterministic per destination.
* Also diversifies flickr covers shared by 3+ destinations whose names do
  NOT match the photo (e.g. 5 caves sharing one image) so neighbouring
  destinations don't show identical photos.

Usage: PYTHONPATH=/home/user/Tourism/Tourism /home/user/.venv/bin/python scripts/fix_round24_dead_covers.py
"""
import hashlib
import os
import re
from collections import Counter, defaultdict

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage  # noqa: E402

DEAD_PREFIXES = ("https://pd.w.org/", "http://pd.w.org/")
GENERIC_TOKENS = {
    "hotel", "inn", "lodge", "resort", "guest", "home", "house", "view",
    "and", "the", "of", "park", "nepal", "international", "heritage",
    "restaurant", "eco", "holiday", "private", "trek", "trekking",
    "monastery", "cave", "gufa", "temple", "village", "lake", "trail",
    "point", "camp", "base", "hill", "danda", "khola", "river",
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

    # --- build the verified pool + category maps -------------------------
    pool = {}
    cat_urls = defaultdict(set)
    for r in (
        DestinationImage.objects.filter(source__in=("wikimedia", "openverse"), is_verified=1)
        .values("external_url", "photographer", "license_type", "source_url",
                "alt_text", "destination__category__slug")
    ):
        u = r["external_url"]
        if not u or u.startswith(DEAD_PREFIXES):
            continue
        pool.setdefault(u, {
            "photographer": r["photographer"] or "Wikimedia Commons contributor",
            "license": r["license_type"] or "See Commons file page",
            "source_url": r["source_url"] or "",
            "alt": r["alt_text"] or "",
        })
        if r["destination__category__slug"]:
            cat_urls[r["destination__category__slug"]].add(u)
    print(f"pool URLs: {len(pool)}")

    covers = Counter(
        DestinationImage.objects.filter(is_cover=True).values_list("external_url", flat=True)
    )
    # flickr URLs used by 3+ destinations
    flickr_shared = {
        u for u, c in covers.items()
        if u.startswith("https://live.staticflickr.com") and c >= 3
    }

    def pick_for(dest, used):
        cat_slug = dest.category.slug if dest.category_id else ""
        cands = sorted(
            (x for x in cat_urls.get(cat_slug, []) if x not in used and covers.get(x, 0) <= 60),
            key=lambda x: (covers.get(x, 0), x),
        )
        if not cands:
            cands = sorted(
                (x for x in pool if x not in used and covers.get(x, 0) <= 60),
                key=lambda x: (covers.get(x, 0), x),
            )
        if not cands:
            cands = sorted(pool, key=lambda x: (covers.get(x, 0), x))
        h = int(hashlib.md5(f"{dest.name}|{dest.id}|r24".encode()).hexdigest(), 16)
        return cands[h % len(cands)]

    fixed = 0
    detail = []
    for row in DestinationImage.objects.filter(is_cover=True).select_related("destination"):
        u = row.external_url or ""
        dest = row.destination
        if not dest:
            continue
        dead = u.startswith(DEAD_PREFIXES)
        shared = u in flickr_shared
        if not dead and not shared:
            continue
        # keep the flickr photo when it is a genuine name match
        if shared and not dead:
            dtok = name_tokens(dest.name) - GENERIC_TOKENS
            ptok = photo_tokens(u) - GENERIC_TOKENS
            if dtok and ptok and len(dtok & ptok) >= 1:
                continue
        new_u = pick_for(dest, {u})
        meta = pool.get(new_u)
        if not meta:
            continue
        row.external_url = new_u
        row.thumbnail_url = new_u
        row.attribution = f"Photo: {dest.name or 'Nepal'} — {meta['photographer']} ({meta['license']})"
        row.photographer = meta["photographer"]
        row.license_type = meta["license"]
        row.source_url = meta["source_url"]
        row.save(update_fields=["external_url", "thumbnail_url", "attribution",
                                "photographer", "license_type", "source_url"])
        covers[u] -= 1
        covers[new_u] += 1
        fixed += 1
        detail.append(f"  {dest.id:5d} {dest.name[:32]:32s} -> {new_u.rsplit('/',1)[-1][:55]}")
    print(f"covers fixed: {fixed}")
    for line in detail[:40]:
        print(line)

    # ---- final check -----------------------------------------------------
    bad = DestinationImage.objects.filter(is_cover=True).filter(
        external_url__startswith="https://pd.w.org/"
    ).count()
    print("remaining pd.w.org covers:", bad)
    covers2 = Counter(
        DestinationImage.objects.filter(is_cover=True).values_list("external_url", flat=True)
    )
    print(f"max cover share: {max(covers2.values()) if covers2 else 0}")
    print(f"dests: {Destination.objects.count()}")


if __name__ == "__main__":
    main()
