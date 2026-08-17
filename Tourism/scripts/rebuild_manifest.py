"""Rebuild tourist/verified_wikimedia_photos.json from the live DB.

Every approved 'wikimedia' or 'openverse' cover row in
tourist_destinationimage becomes a manifest entry, so the manifest always
mirrors the database (no network needed).

Usage:
    /home/user/.venv/bin/python scripts/rebuild_manifest.py
"""
import hashlib
import json
import os
import re
import sqlite3
import urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(REPO, "db.sqlite3")
MANIFEST_PATH = os.path.join(REPO, "tourist", "verified_wikimedia_photos.json")

GENERIC_ARTIST = "Wikimedia Commons contributor"
GENERIC_LICENSE = "See Commons file page"

THUMB_RE = re.compile(r"^https://upload\.wikimedia\.org/wikipedia/commons/thumb/([0-9a-f])/([0-9a-f]{2})/(.+)/(960px-.*)$")


def original_from_thumb(thumb: str) -> str:
    m = THUMB_RE.match(thumb)
    if m:
        return f"https://upload.wikimedia.org/wikipedia/commons/{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return thumb


def file_from_source_url(source_url: str) -> str:
    return urllib.parse.unquote(source_url.rsplit("/", 1)[-1].removeprefix("File:"))


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """SELECT destination_id, thumbnail_url, external_url, caption, alt_text,
                  source_url, photographer, license_type, source, is_cover, ordering
           FROM tourist_destinationimage
           WHERE source IN ('wikimedia', 'openverse') AND is_verified=1
           ORDER BY destination_id, is_cover DESC, ordering, id"""
    )
    rows = cur.fetchall()
    conn.close()

    manifest = {}
    for did, thumb, url, caption, alt_text, source_url, photographer, license_type, source, is_cover, ordering in rows:
        thumb = thumb or url
        original = original_from_thumb(thumb)
        fn = file_from_source_url(source_url or original)
        entry = manifest.setdefault(str(did), {
            "url": thumb, "thumb": thumb, "original": original, "file": fn,
            "label": caption or alt_text, "caption": caption or alt_text,
            "source": source,
            "source_url": source_url or f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(fn.replace(' ', '_'))}",
            "photographer": photographer or GENERIC_ARTIST,
            "license": license_type or GENERIC_LICENSE,
            "tier": "exact",
        })
        if is_cover:
            entry["url"] = thumb
            entry["thumb"] = thumb
            entry["original"] = original
            entry["file"] = fn
            entry["label"] = caption or alt_text
            entry["caption"] = caption or alt_text
        else:
            entry.setdefault("url2", thumb)
            entry.setdefault("thumb2", thumb)
            entry.setdefault("original2", original)
            entry.setdefault("file2", fn)
            entry.setdefault("label2", caption or alt_text)
            entry.setdefault("source_url2", source_url or entry.get("source_url", ""))

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    with2 = sum(1 for e in manifest.values() if e.get("url2"))
    print(f"manifest written: {MANIFEST_PATH} ({len(manifest)} entries, {with2} with a 2nd photo)")


if __name__ == "__main__":
    main()
