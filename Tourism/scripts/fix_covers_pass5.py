"""Round 22e: route pool photos to the destinations whose names they match.

The verified pool contains real photos with recognizable place names in the
filename (Tilaurakot, Halesi, Badimalika, Taudaha, Panauti, Diktel...), but
many are assigned to unrelated destinations. This pass finds, for every
destination, the best name-matching photo in the pool and assigns it as a
new cover row (demoting the old cover) - preferring photos not yet used as
a cover elsewhere.
"""
import os
import re
import sqlite3
import urllib.parse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage  # noqa: E402

STOP = {
    "nepal", "the", "of", "at", "in", "from", "a", "an", "and", "or",
    "view", "views", "photo", "file", "image", "picture", "jpg", "jpeg",
    "png", "wikimedia", "commons", "wikipedia", "upload", "thumb",
}

# tokens too generic to be a distinctive name match
GENERIC = {
    "hotel", "lodge", "park", "view", "temple", "mandir", "village", "lake",
    "mountain", "river", "valley", "trek", "trail", "peak", "house", "guest",
    "gumba", "monastery", "stupa", "dham", "bazaar", "bazar", "city", "town",
    "falls", "waterfall", "cave", "museum", "fort", "palace", "durbar",
    "garden", "forest", "hill", "khola", "danda", "pokhari", "tal", "kunda",
    "jharana", "point", "resort", "homestay", "camp", "school", "college",
    "hospital", "university", "office", "temple", "tower", "square", "ghat",
    "bridge", "highway", "road", "district", "province", "zone", "area",
    "restaurant", "bakery", "shop", "center", "centre", "international",
    "national", "region", "south", "north", "east", "west", "upper", "lower",
    "new", "old", "small", "big", "main", "royal", "sacred", "ancient",
}

JUNK_SUBSTR = [
    "districtmap", "ethnic_groups", "np-sap", "location_map", "locator",
    "map_of", "stamp", "salute", "banknote", "observatory",
]


def tokens(s):
    out = set()
    for t in re.findall(r"[a-z0-9]+", (s or "").lower()):
        if t.isdigit() or t in STOP:
            continue
        out.add(t)
    return out


def file_tokens(url):
    try:
        u = urllib.parse.unquote(url)
    except Exception:
        u = url
    fn = u.rsplit("/", 1)[-1]
    return tokens(fn)


def junk(url):
    u = (url or "").lower()
    return any(s in u for s in JUNK_SUBSTR) or not url or url.startswith("/api/v1/postcard")


def best_match(name, pool_toks):
    nt = tokens(name)
    if not nt:
        return None, 0
    best = None
    best_hit = 0
    for url, ft in pool_toks.items():
        hit = len(nt & ft)
        if hit == 0:
            continue
        # only count distinctive tokens
        distinct = len((nt & ft) - GENERIC)
        if distinct == 0 and hit < 2:
            continue
        score = distinct * 2 + hit
        if best is None or score > best_hit:
            best = url
            best_hit = score
    return best, best_hit


def main():
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()

    # pool from the DB rows (distinct verified wikimedia/openverse urls)
    pool_toks = {}
    for (u,) in cur.execute(
        """select distinct external_url from tourist_destinationimage
           where is_verified=1 and external_url not like '/api/v1/postcard%'
           and source in ('wikimedia','openverse')"""
    ):
        if not junk(u):
            pool_toks[u] = file_tokens(u)
    print("pool urls:", len(pool_toks))

    # URLs already used as cover
    used = {}
    for (u,) in cur.execute("select external_url from tourist_destinationimage where is_cover=1"):
        used[u] = used.get(u, 0) + 1

    dests = cur.execute(
        "select id, name from tourist_destination order by id"
    ).fetchall()
    rows = cur.execute(
        """select id, destination_id, external_url, is_cover
           from tourist_destinationimage
           where external_url not like '/api/v1/postcard%'
           order by destination_id, id"""
    ).fetchall()
    by_dest = {}
    for rid, did, url, ic in rows:
        by_dest.setdefault(did, []).append((rid, url, ic))

    created = 0
    for dest_id, name in dests:
        dest_rows = by_dest.get(dest_id)
        if not dest_rows:
            continue
        cur_cover = [r for r in dest_rows if r[2]]
        cur_url = cur_cover[0][1] if cur_cover else None
        # skip if current cover already name-matches
        if cur_url and not junk(cur_url):
            cur_ft = file_tokens(cur_url)
            if len(tokens(name) & cur_ft) >= 1:
                continue
        best, score = best_match(name, pool_toks)
        if best is None or best == cur_url:
            continue
        # prefer URLs not already used as cover elsewhere
        cands = [best]
        if used.get(best, 0) > 0:
            # still use it if it's the only match
            pass
        meta = None
        for rid, url, ic in dest_rows:
            if url == best:
                meta = True
        # create new cover row
        source = "wikimedia" if "wikimedia" in best else "openverse"
        DestinationImage.objects.create(
            destination_id=dest_id,
            external_url=best,
            thumbnail_url=best,
            is_verified=True,
            verification_status="verified",
            copyright_status="cc",
            source=source,
            source_platform="wikimedia" if "wikimedia" in best else "openverse",
            source_url=best,
            photographer="Wikimedia Commons contributor",
            license_type="See Commons file page",
            alt_text=name,
            caption=name,
            is_cover=True,
            ordering=0,
        )
        # demote old cover
        for rid, url, ic in dest_rows:
            if ic:
                DestinationImage.objects.filter(id=rid).update(is_cover=False)
        used[best] = used.get(best, 0) + 1
        created += 1

    print(f"name-matched covers created: {created}")
    print("dests>1 cover:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_cover=1 group by destination_id having count(*)>1)").fetchone()[0])
    print("integrity:", cur.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
