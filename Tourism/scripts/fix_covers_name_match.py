"""Round 22b: Name-match cover pass.

For every destination, score each of its own verified image rows by how many
tokens of the destination name (and district) appear in the photo filename.
Assign the best-matching photo as the cover, so 'Boudha Stupa' gets
Boudha_Stupa.jpg instead of a random pool photo. This replaces pool-repeated
covers with name-matched ones wherever the data allows.
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


def tokens(s):
    out = set()
    for t in re.findall(r"[a-z0-9]+", (s or "").lower()):
        if t.isdigit():
            continue
        if t in STOP:
            continue
        out.add(t)
    return out


def score(url, name, district):
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


def main():
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    dests = cur.execute(
        "select id, name, district from tourist_destination order by id"
    ).fetchall()
    rows = cur.execute(
        """select id, destination_id, external_url, is_cover, source
           from tourist_destinationimage
           where external_url not like '/api/v1/postcard%'
           order by destination_id, id"""
    ).fetchall()
    by_dest = {}
    for rid, did, url, is_cover, src in rows:
        by_dest.setdefault(did, []).append((rid, url, is_cover, src))

    changed = 0
    for dest_id, name, district in dests:
        dest_rows = by_dest.get(dest_id)
        if not dest_rows:
            continue
        scored = [(score(u, name, district), rid, u, src) for rid, u, ic, src in dest_rows]
        scored.sort(key=lambda x: (-x[0], 0 if x[3] == "wikimedia" else 1, x[1]))
        best_score, best_rid, best_url, _ = scored[0]
        if best_score <= 0:
            continue  # nothing name-matches; leave current cover
        # promote the best row to cover
        for rid, u, ic, src in dest_rows:
            want = rid == best_rid
            if ic != want:
                DestinationImage.objects.filter(id=rid).update(is_cover=want)
                changed += 1

    print(f"cover flags changed: {changed}")

    # report
    print("dests>1 cover:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_cover=1 group by destination_id having count(*)>1)").fetchone()[0])
    print("dests<2 verified:", cur.execute("select count(*) from (select destination_id from tourist_destinationimage where is_verified=1 and external_url not like '/api/v1/postcard%' group by destination_id having count(*)<2)").fetchone()[0])
    print("integrity:", cur.execute("PRAGMA integrity_check").fetchone()[0])


if __name__ == "__main__":
    main()
