"""Fetch and verify the OSM extract that real road routing needs.

Why a script and not just a docker-compose service
--------------------------------------------------
OSRM is not magic: it can only route along roads that are in its data file. A
routing container with an empty extract answers every request with "no route",
and a naive setup then falls back to the bundled graph while the UI still says
"real road routing". So the extract has to be fetched, *verified*, and its
provenance recorded, and that has to happen before anything claims to be
road-verified.

Checksum policy
---------------
This script does **not** ship a checksum. A hardcoded hash is a liability: it
goes stale weekly, and a wrong one either blocks every legitimate update or,
worse, gets "fixed" by someone copying the hash of whatever they downloaded.

Instead it fetches Geofabrik's own published ``.md5`` for the same file at the
same moment, verifies the download against it, and writes both the hash and the
data timestamp into ``routing_extract_provenance.json``. The claim is then
"this file matched the publisher's hash at this time", which is verifiable, not
"trust me".

Usage
-----
    python scripts/fetch_osm_extract.py                 # fetch + verify
    python scripts/fetch_osm_extract.py --print-only    # show current provenance

Afterwards, build the routing graph (see docs/ROUTING.md) and set
``ROUTING_BASE_URL``. Then run ``manage.py audit_routing`` -- it refuses to call
routing road-verified unless the returned geometry is physically consistent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GEOFABRIK_BASE = "https://download.geofabrik.de/asia"
EXTRACT_NAME = "nepal-latest.osm.pbf"
MD5_NAME = "nepal-latest.osm.pbf.md5"
PROVENANCE_NAME = "routing_extract_provenance.json"
USER_AGENT = "NepalYatraRoutingSetup/1.0 (https://github.com/Diwash234/Tourism)"

CHUNK = 1024 * 1024


def download(url: str, destination: Path, *, timeout: int = 120) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        total = response.headers.get("Content-Length")
        print(f"  downloading {url}")
        if total:
            print(f"  expected size: {int(total) / 1_048_576:.1f} MB")
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".part")
        seen = 0
        with open(partial, "wb") as fh:
            while True:
                block = response.read(CHUNK)
                if not block:
                    break
                fh.write(block)
                seen += len(block)
                if total and sys.stdout.isatty():
                    pct = 100.0 * seen / int(total)
                    print(f"\r  {pct:5.1f}% ({seen / 1_048_576:.1f} MB)", end="")
        if total and sys.stdout.isatty():
            print()
        partial.replace(destination)


def md5_of(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - matching the publisher's own format
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def published_md5() -> str:
    url = f"{GEOFABRIK_BASE}/{MD5_NAME}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        text = response.read().decode("utf-8", "replace").strip()
    # Geofabrik publishes the bare hex digest, sometimes with a trailing
    # filename. Take the first whitespace-delimited token.
    token = text.split()[0] if text.split() else ""
    if len(token) != 32 or any(c not in "0123456789abcdefABCDEF" for c in token):
        raise SystemExit(f"could not read an md5 from {url}: {text!r}")
    return token.lower()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default="data/osm", help="Directory for the extract.")
    parser.add_argument("--print-only", action="store_true",
                        help="Show recorded provenance and exit.")
    parser.add_argument("--skip-download", action="store_true",
                        help="Verify an extract already present in --dest.")
    args = parser.parse_args(argv)

    dest_dir = Path(args.dest)
    extract = dest_dir / EXTRACT_NAME
    provenance_path = dest_dir / PROVENANCE_NAME

    if args.print_only:
        if not provenance_path.exists():
            print(f"no provenance recorded at {provenance_path}")
            print("the extract has not been fetched through this script")
            return 1
        print(json.dumps(json.loads(provenance_path.read_text(encoding="utf-8")), indent=2))
        return 0

    if not args.skip_download:
        print("Resolving the publisher's checksum first, so the download can be verified.")
        expected = published_md5()
        print(f"  published md5: {expected}")
        download(f"{GEOFABRIK_BASE}/{EXTRACT_NAME}", extract)
    else:
        if not extract.exists():
            raise SystemExit(f"no extract at {extract}")
        expected = published_md5()
        print(f"  published md5: {expected}")

    print("Verifying.")
    actual = md5_of(extract)
    size = extract.stat().st_size
    if actual != expected:
        # Refuse loudly. A corrupted or partial extract produces routing answers
        # that look plausible and are wrong.
        raise SystemExit(
            f"CHECKSUM MISMATCH\n  expected {expected}\n  actual   {actual}\n"
            f"  file     {extract} ({size} bytes)\n"
            "Delete it and re-run. Do not proceed to build a routing graph from this file."
        )
    print(f"  md5 matches: {actual}")

    last_modified = ""
    try:
        request = urllib.request.Request(
            f"{GEOFABRIK_BASE}/{EXTRACT_NAME}",
            headers={"User-Agent": USER_AGENT}, method="HEAD")
        with urllib.request.urlopen(request, timeout=60) as response:
            last_modified = response.headers.get("Last-Modified", "")
    except Exception:  # noqa: BLE001 - provenance is best-effort metadata
        last_modified = ""

    record = {
        "file": EXTRACT_NAME,
        "source_url": f"{GEOFABRIK_BASE}/{EXTRACT_NAME}",
        "checksum_url": f"{GEOFABRIK_BASE}/{MD5_NAME}",
        "checksum_algorithm": "md5",
        "checksum": actual,
        "checksum_verified_against": "publisher-published md5 for the same file",
        "size_bytes": size,
        "publisher_last_modified": last_modified,
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "licence": "ODbL 1.0 (OpenStreetMap contributors)",
        "note": "This record is proof the download matched the publisher's own checksum. "
                "It is not a guarantee that the underlying road data is complete or current.",
    }
    dest_dir.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(f"Provenance written to {provenance_path}")
    print("Now build the routing graph and start OSRM: see docs/ROUTING.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
