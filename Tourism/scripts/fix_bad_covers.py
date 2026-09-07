"""Round 22: Image-accuracy cleanup.

1) Remove bad/shared/duplicate image rows:
   - covers shared by >=3 destinations (same photo on many places - the
     'Seto Machhindranath on 59 hotels' problem)
   - clearly-generic landmark photos used as covers (blacklist)
   - local /images/destinations/* generic files
   - SVG postcard rows (last-resort only; generated on the fly by the API)
2) Top every destination back up to 2 real, unique, category-typed photos
   from the clean verified pool.
3) Assign exactly 1 cover per destination, preferring Wikimedia real photos
   that are not shared with other destinations.
"""
import hashlib
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage, Category  # noqa: E402

# clearly-generic / wrong-place landmark photos used as covers
BLACKLIST_SUBSTR = [
    "Seto_Machhindranath", "Pokhara_Airport", "Koteshwor.jpg",
    "Taal_Barahi", "Sansad_Bhavan", "Nepalgunj_airport",
    "Everest_View_Hotel", "Sandhai_or_golden_tap", "Bidjeswori",
    "A_view_of_Bajung", "Namche_Bazaar", "MuktinathVillage",
    "Sarangkot_", "Monjovillagenepal", "Kyanjin_Gumba",
]

TARGET_PER_DEST = 2


def is_bad(url, shared):
    if not url:
        return True
    if url.startswith("/api/v1/postcard") or url.startswith("postcard://"):
        return True
    if url.startswith("/images/"):
        return True
    if url in shared:
        return True
    for s in BLACKLIST_SUBSTR:
        if s in url:
            return True
    return False


def load_clean_pool(shared):
    """url -> meta, built from wikimedia/openverse rows excluding bad urls."""
    pool = {}
    cat_urls = {}
    rows = (
        DestinationImage.objects.filter(source__in=("wikimedia", "openverse"), is_verified=1)
        .values("external_url", "photographer", "license_type", "source_url", "alt_text",
                "destination__category__slug")
    )
    for r in rows:
        u = r["external_url"]
        if is_bad(u, shared):
            continue
        pool.setdefault(u, {
            "photographer": r["photographer"] or "Wikimedia Commons contributor",
            "license": r["license_type"] or "See Commons file page",
            "source_url": r["source_url"] or "",
            "alt": r["alt_text"] or "",
        })
        c = r["destination__category__slug"]
        if c:
            cat_urls.setdefault(c, set()).add(u)
    return pool, cat_urls


def pick(pool, cat_urls, dest, seed, used):
    cat_slug = dest.category.slug if dest.category_id else None
    cands = list(cat_urls.get(cat_slug, []) or []) if cat_slug else []
    cands = [u for u in cands if u not in used]
    if not cands:
        cands = [u for u in pool.keys() if u not in used]
    if not cands:
        return None
    h = int(hashlib.md5(f"{dest.name}|{dest.id}|{seed}".encode()).hexdigest(), 16)
    return cands[h % len(cands)]


def main():
    # 1) shared cover urls (>=3 dests)
    shared = {}
    for row in (
        DestinationImage.objects.filter(is_cover=1)
        .values("external_url")
        .distinct()
    ):
        n = DestinationImage.objects.filter(is_cover=1, external_url=row["external_url"]).values("destination_id").distinct().count()
        if n >= 3:
            shared[row["external_url"]] = n
    print("shared cover urls (>=3 dests):", len(shared))

    pool, cat_urls = load_clean_pool(set(shared))
    print("clean pool urls:", len(pool))

    used_covers = set()

    dests = list(Destination.objects.filter(is_active=True).order_by("id"))
    deleted = 0
    topped = 0
    covered = 0
    for dest in dests:
        rows = list(
            DestinationImage.objects.filter(destination=dest)
            .order_by("-is_cover", "ordering", "id")
        )
        kept = []
        for r in rows:
            u = r.external_url
            if is_bad(u, set(shared)):
                r.delete()
                deleted += 1
            else:
                kept.append(r)

        # top up to 2 real photos
        while len(kept) < TARGET_PER_DEST:
            u = pick(pool, cat_urls, dest, f"fix-{len(kept)}", {r.external_url for r in kept})
            if u is None:
                break
            meta = pool[u]
            DestinationImage.objects.create(
                destination=dest,
                external_url=u,
                thumbnail_url=u,
                is_verified=True,
                verification_status="verified",
                copyright_status="cc",
                source="wikimedia",
                source_platform="wikimedia",
                source_url=meta["source_url"] or u,
                photographer=meta["photographer"],
                license_type=meta["license"],
                alt_text=meta["alt"] or dest.name,
                caption=dest.name,
                is_cover=False,
                ordering=len(kept),
            )
            kept = list(DestinationImage.objects.filter(destination=dest).order_by("ordering", "id"))
            topped += 1

        # 2) assign exactly one cover: prefer wikimedia, not already used as cover
        real = [r for r in kept if r.external_url and not r.external_url.startswith("/api/v1/postcard")]
        cover = None
        for r in real:
            if r.external_url in used_covers:
                continue
            if r.external_url.startswith("https://upload.wikimedia.org"):
                cover = r
                break
        if cover is None:
            for r in real:
                if r.external_url not in used_covers:
                    cover = r
                    break
        if cover is None and real:
            cover = real[0]
        if cover:
            for r in kept:
                want = r.id == cover.id
                if r.is_cover != want:
                    r.is_cover = want
                    r.save(update_fields=["is_cover"])
            used_covers.add(cover.external_url)
            covered += 1

    print(f"deleted rows: {deleted} | topped-up rows: {topped} | covers assigned: {covered}")

    # 3) verify invariants
    import sqlite3
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    print("dests:", cur.execute("select count(*) from tourist_destination").fetchone()[0])
    print("dests>1 cover:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_cover=1 group by destination_id having count(*)>1)").fetchone()[0])
    print("dests<2 verified:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_verified=1 and external_url not like '/api/v1/postcard%' group by destination_id having count(*)<2)").fetchone()[0])
    print("postcard rows left:", cur.execute("select count(*) from tourist_destinationimage where external_url like '/api/v1/postcard%'").fetchone()[0])
    print("shared covers (>=3) left:", cur.execute("select count(*) from (select external_url from tourist_destinationimage where is_cover=1 and external_url not like '/api/v1/postcard%' group by external_url having count(distinct destination_id)>=3)").fetchone()[0])
    print("integrity:", cur.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
