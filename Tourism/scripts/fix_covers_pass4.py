"""Round 22d: final cover repair.

Only-improve pass:
- junk photos (maps, stamps, salutes, logos, flags, observatories,
  airports, hotels, railway stations on unrelated destinations) are never
  allowed as covers
- cover is switched only when a strictly-better name/category/district
  match exists among the destination's own rows
- among equally-scored rows the least-used URL wins (less repetition)
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

JUNK_TOKENS = {
    "map", "districtmap", "stamp", "salute", "flag", "logo", "seal",
    "banknote", "coin", "locator", "observatory", "insignia", "coat",
    "chart", "diagram", "graph",
}

CAT_KEYWORDS = {
    "temples": ["temple", "mandir", "shiva", "bhagawati", "bhagwati", "devi", "kali",
                "ganesh", "bhairav", "maha", "durga", "narayan", "vishnu", "laxmi",
                "barahi", "dattatraya", "machhindranath", "linga", "shivalaya"],
    "buddhist-sites": ["stupa", "gompa", "gumba", "monastery", "buddha", "vihar",
                       "chaitya", "bodh", "boudha", "swayambhu", "lumbini"],
    "lakes": ["lake", "tal", "pokhari", "daha", "kunda", "sarovar", "pond"],
    "waterfalls": ["waterfall", "jharana", "falls", "chhango"],
    "caves": ["cave", "gufa"],
    "mountains": ["peak", "himal", "mountain", "massif", "chuli", "lek"],
    "valleys": ["valley", "khola", "gorge", "danda"],
    "rivers": ["river", "khola", "nadi", "ghat", "confluence"],
    "viewpoints": ["viewpoint", "danda", "tower", "sunrise", "sunset", "panorama"],
    "parks-gardens": ["park", "garden", "botanical"],
    "heritage": ["durbar", "palace", "fort", "gadhi", "kot", "darbar", "museum", "monument", "temple"],
    "villages": ["village", "gaun", "bazaar", "bazar", "town", "settlement"],
    "trekking": ["trek", "trail", "pass", "base camp", "kharka", "camp"],
    "wildlife": ["safari", "tiger", "rhino", "elephant", "bird", "deer", "wild"],
    "museums": ["museum"],
    "hot-springs": ["hot spring", "tatopani", "spring"],
    "pilgrimage": ["dham", "tirtha", "kunda", "ashram"],
    "shopping": ["bazaar", "market", "handicraft"],
    "forests": ["forest", "jungle"],
    "agriculture": ["farm", "tea garden", "orchard", "field"],
    "tea-coffee": ["tea", "coffee"],
    "scenic-routes": ["highway", "bridge", "gorge"],
    "spiritual-wellness": ["ashram", "meditation", "retreat"],
    "adventure": ["bungee", "rafting", "paragliding", "zipline", "skydive"],
    "cities": ["city", "bazaar", "bazar"],
    "natural-wonders": ["glacier", "icefall", "cliff", "rock"],
    "national-park": ["national park", "reserve", "conservation"],
    "hills": ["hill", "danda", "pahad"],
}

ACCOMMODATION = {"hotel", "guest_house", "hostel", "motel", "resort", "apartment", "alpine_hut", "home_stay", "homestay", "camp_site", "camp_pitch", "chalet", "wilderness_hut", "caravan_site", "lodge"}


def tokens(s):
    out = set()
    for t in re.findall(r"[a-z0-9]+", (s or "").lower()):
        if t.isdigit() or t in STOP:
            continue
        out.add(t)
    return out


def is_junk(url, cat_slug, name):
    if not url or url.startswith("/api/v1/postcard"):
        return True
    try:
        u = urllib.parse.unquote(url).lower()
    except Exception:
        u = url.lower()
    ut = tokens(u)
    if not ut:
        return True
    if JUNK_TOKENS & ut:
        return True
    # airports / stations / hotels only allowed on matching destinations
    if "airport" in ut and "airport" not in tokens(name):
        return True
    if "railway" in ut and "railway" not in tokens(name) and "station" not in tokens(name):
        return True
    if ("hotel" in ut or "guesthouse" in ut or "guest_house" in ut or "lodge" in ut) and cat_slug not in ACCOMMODATION:
        return True
    if "museum" in ut and cat_slug not in ("museums", "heritage"):
        return True
    return False


def score(url, name, district, cat_slug):
    try:
        u = urllib.parse.unquote(url).lower()
    except Exception:
        u = url.lower()
    ut = tokens(u)
    if not ut:
        return -1
    nt = tokens(name)
    dt = tokens(district or "")
    s = 2 * len(nt & ut) + len(dt & ut)
    kws = CAT_KEYWORDS.get(cat_slug, [])
    if kws:
        s += sum(1 for k in kws if k in u)
    return s


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

    cover_use = {}
    for rid, did, url, is_cover, src in rows:
        if is_cover:
            cover_use[url] = cover_use.get(url, 0) + 1

    changed = 0
    fixed_junk = 0
    for dest_id, name, district, cat_id in dests:
        dest_rows = by_dest.get(dest_id)
        if not dest_rows:
            continue
        cat_slug = cat_slugs.get(cat_id, "")
        scored = []
        for rid, url, ic, src in dest_rows:
            j = is_junk(url, cat_slug, name)
            s = -1 if j else score(url, name, district, cat_slug)
            scored.append((s, -cover_use.get(url, 0), 0 if src == "wikimedia" else 1, rid, url, j))
        scored.sort(key=lambda x: (-x[0], -x[1], x[2], x[3]))

        cur_cover = [r for r in dest_rows if r[2]]
        cur_url = cur_cover[0][1] if cur_cover else None
        cur_junk = False
        if cur_url:
            cur_junk = is_junk(cur_url, cat_slug, name)

        best = scored[0]
        best_score, _, _, best_rid, best_url, best_junk = best
        cur_score = -1
        if cur_url:
            cur_score = -1 if cur_junk else score(cur_url, name, district, cat_slug)

        if best_junk and not cur_junk:
            continue  # nothing usable; keep current
        if cur_junk and best_junk:
            continue  # all junk; leave as is
        if not cur_junk and best_score <= cur_score:
            continue  # only improve, never degrade
        # switch
        for rid, url, ic, src in dest_rows:
            want = rid == best_rid
            if ic != want:
                DestinationImage.objects.filter(id=rid).update(is_cover=want)
                changed += 1
                if cur_junk:
                    fixed_junk += 1

    print(f"cover flags changed: {changed} | junk covers fixed: {fixed_junk}")
    print("dests>1 cover:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_cover=1 group by destination_id having count(*)>1)").fetchone()[0])
    print("integrity:", cur.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
