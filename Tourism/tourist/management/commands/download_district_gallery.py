import csv
import re
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from rest_framework.test import APIRequestFactory

from tourist.views import DistrictGalleryView


class Command(BaseCommand):
    help = "Download up to five source-attributed district gallery images into frontend public folders"

    def add_arguments(self, parser):
        parser.add_argument("--output", default="../frontend/Tourism/public/images/destinations/districts")
        parser.add_argument("--timeout", type=int, default=20)
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        response = DistrictGalleryView.as_view()(APIRequestFactory().get("/api/v1/gallery/districts/"))
        data = response.data
        root = Path(options["output"]).resolve()
        root.mkdir(parents=True, exist_ok=True)
        manifest_rows, downloaded, skipped = [], 0, 0
        session = requests.Session()
        session.headers["User-Agent"] = "NepalTourismDistrictGallery/1.0 (source-preserving download)"
        for group in data["districts"]:
            slug = re.sub(r"[^a-z0-9]+", "-", group["district"].lower()).strip("-")
            folder = root / slug; folder.mkdir(parents=True, exist_ok=True)
            for index, media in enumerate(group["images"][:5], 1):
                target = folder / f"img{index}.jpg"
                row = {
                    "district": group["district"], "file": str(target.relative_to(root)),
                    "destination": media["destination_name"], "source_url": media.get("source_url") or media["url"],
                    "image_url": media["url"], "photographer": media.get("photographer") or "",
                    "license": media.get("license") or "", "status": "",
                }
                if target.exists() and not options["overwrite"]:
                    row["status"] = "existing"; skipped += 1; manifest_rows.append(row); continue
                try:
                    result = session.get(media["url"], timeout=options["timeout"], stream=True)
                    result.raise_for_status()
                    content_type = result.headers.get("Content-Type", "")
                    if not content_type.startswith("image/"):
                        raise ValueError(f"non-image content type: {content_type}")
                    content = result.content
                    if not 2_000 <= len(content) <= 8_000_000:
                        raise ValueError(f"unexpected image size: {len(content)}")
                    target.write_bytes(content)
                    row["status"] = "downloaded"; downloaded += 1
                except Exception as exc:  # per-image failure stays visible in manifest
                    row["status"] = f"failed: {str(exc)[:100]}"; skipped += 1
                manifest_rows.append(row)
        manifest = root / "manifest.csv"
        with manifest.open("w", newline="", encoding="utf-8") as handle:
            fields = ["district", "file", "destination", "source_url", "image_url", "photographer", "license", "status"]
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(manifest_rows)
        self.stdout.write(self.style.SUCCESS(f"Downloaded {downloaded}; skipped/failed {skipped}; manifest: {manifest}"))
