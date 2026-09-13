"""Round 22c: category-keyword + least-shared cover pass.

For destinations whose cover cannot be name-matched (hotels, generic
entries), pick the best row by:
  1. name-token match
  2. category-keyword match (temple photos for temples, lake photos for
     lakes, ...)
  3. district-token match
  4. tiebreak: the URL used as cover by the FEWEST other destinations
This distributes repeated pool photos and keeps them category-consistent.
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

CAT_KEYWORDS = {
    "temples": ["temple", "mandir", "shiva", "bhagawati", "bhagwati", "devi", "kali",
                "ganesh", "bhairav", "maha", "durga", "narayan", "vishnu", "laxmi",
                "barahi", "dattatraya", "machhindranath", "linga", "shivalaya"],
    "buddhist-sites": ["stupa", "gompa", "gumba", "monastery", "buddha", "vihar",
                       "chaitya", "bodh", "boudha", "swayambhu", "lumbini", "gompa"],
    "lakes": ["lake", "tal", "pokhari", "daha", "kunda", "sarovar", "pond", "pokhar"],
    "waterfalls": ["waterfall", "jharana", "falls", "chhango", "jharna"],
    "caves": ["cave", "gufa", "gufaa"],
    "mountains": ["peak", "himal", "mountain", "massif", "ri ", "chuli", "lek"],
    "valleys": ["valley", "khola", "gorge", "danda"],
    "rivers": ["river", "khola", "nadi", "ghat", "confluence"],
    "viewpoints": ["viewpoint", "danda", "tower", "point", "sunrise", "sunset", "panorama"],
    "parks-gardens": ["park", "garden", "ban", "botanical"],
    "heritage": ["durbar", "palace", "fort", "gadhi", "kot", "darbar", "museum", "monument"],
    "villages": ["village", "gaun", "bazaar", "bazar", "town", "settlement"],
    "trekking": ["trek", "trail", "pass", "base camp", "kharka", "camp"],
    "wildlife": ["safari", "tiger", "rhino", "elephant", "bird", "national park", "deer", "wild"],
    "museums": ["museum"],
    "hot-springs": ["hot spring", "tatopani", "spring"],
    "pilgrimage": ["dham", "tirtha", "kunda", "ashram"],
    "shopping": ["bazaar", "market", "handicraft", "handicrafts"],
    "forests": ["forest", "jungle"],
    "camping": ["camp"],
    "agriculture": ["farm", "tea garden", "orchard", "field"],
    "tea-coffee": ["tea", "coffee"],
    "scenic-routes": ["highway", "bridge", "road", "gorge"],
    "spiritual-wellness": ["ashram", "meditation", "retreat"],
    "adventure": ["bungee", "rafting", "paragliding", "zipline", "skydive"],
    "cities": ["city", "bazaar", "bazar"],
    "natural-wonders": ["glacier", "icefall", "cliff", "rock"],
    "national-park": ["national park", "reserve", "conservation"],
    "religion": ["temple", "mandir", "dham", "gumba", "stupa"],
    "hills": ["hill", "danda", "pahad"],
}


def tokens(s):
    out = set()
    for t in re.findall(r"[a-z0-9]+", (s or "").lower()):
        if t.isdigit() or t in STOP:
            continue
        out.add(t)
    return out


def score_name(url, name, district):
    if not url or url.startswith("/api/v1/postcard"):
        return -1
    try:
        u = urllib.parse.unquote(url)
    except Exception:
        u = url
    ut = tokens(u)
    if not ut:
        return -1
    nt = tokens(name)
    dt = tokens(district or "")
    return 2 * len(nt & ut) + len(dt & ut)


def score_cat(url, cat_slug):
    if not url:
        return 0
    try:
        u = urllib.parse.unquote(url).lower()
    except Exception:
        u = url.lower()
    kws = CAT_KEYWORDS.get(cat_slug, [])
    if not kws:
        return 0
    hits = sum(1 for k in kws if k in u)
    return hits


def main():
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    dests = cur.execute(
        "select id, name, district, category_id from tourist_destination order by id"
    ).fetchall()
    cat_slugs = {cid: slug for cid, slug in cur.execute("select id, slug from tourist_category")}
    rows = cur.execute(
        """select id, destination_id, external_url, is_cover, source
           from tourist_destinationimage
           where external_url not like '/api/v1/postcard%'
           order by destination_id, id"""
    ).fetchall()
    by_dest = {}
    for rid, did, url, is_cover, src in rows:
        by_dest.setdefault(did, []).append((rid, url, is_cover, src))

    # global cover usage per url (for tiebreak)
    cover_use = {}
    for rid, did, url, is_cover, src in rows:
        if is_cover:
            cover_use[url] = cover_use.get(url, 0) + 1

    changed = 0
    for dest_id, name, district, cat_id in dests:
        dest_rows = by_dest.get(dest_id)
        if not dest_rows:
            continue
        cat_slug = cat_slugs.get(cat_id, "")
        scored = []
        for rid, url, ic, src in dest_rows:
            sn = score_name(url, name, district)
            sc = score_cat(url, cat_slug)
            # combined: name match dominates, then category keyword, then district
            key = (sn * 1000 + sc * 100, -cover_use.get(url, 0),
                   0 if src == "wikimedia" else 1, rid)
            scored.append((key, rid, url, src, sn, sc))
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0]
        # only re-assign when the best row is clearly better than current cover
        cur_cover = [r for r in dest_rows if r[2]]
        cur_url = cur_cover[0][1] if cur_cover else None
        if cur_url == best[2]:
            continue
        # demote current, promote best
        for rid, url, ic, src in dest_rows:
            want = rid == best[1]
            if ic != want:
                DestinationImage.objects.filter(id=rid).update(is_cover=want)
                changed += 1

    print(f"cover flags changed: {changed}")
    print("dests>1 cover:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_cover=1 group by destination_id having count(*)>1)").fetchone()[0])
    print("integrity:", cur.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
