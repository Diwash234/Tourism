"""Rebuild tourist/verified_wikimedia_photos.json from the live DB.

Every approved 'wikimedia' cover row in tourist_destinationimage becomes a
manifest entry, so the manifest always mirrors the database (no network needed).

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

THUMB_RE = re.compile(r"^https://upload\.wikimedia\.org/wikipedia/commons/thumb/([0-9a-f])/([0-9a-f]{2})/(.+)/(1000px-.*)$")


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
        """SELECT destination_id, thumbnail_url, external_url, caption,
                  source_url, photographer, license_type
           FROM tourist_destinationimage
           WHERE source='wikimedia' AND is_cover=1
           ORDER BY destination_id"""
    )
    rows = cur.fetchall()
    conn.close()

    manifest = {}
    for did, thumb, url, caption, source_url, photographer, license_type in rows:
        thumb = thumb or url
        original = original_from_thumb(thumb)
        fn = file_from_source_url(source_url or original)
        manifest[str(did)] = {
            "url": thumb,
            "thumb": thumb,
            "original": original,
            "file": fn,
            "label": caption,
            "caption": caption,
            "source": "wikimedia",
            "source_url": source_url or f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(fn.replace(' ', '_'))}",
            "photographer": photographer or GENERIC_ARTIST,
            "license": license_type or GENERIC_LICENSE,
            "tier": "exact",
        }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(f"manifest written: {MANIFEST_PATH} ({len(manifest)} entries)")


if __name__ == "__main__":
    main()
