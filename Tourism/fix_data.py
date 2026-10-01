#!/usr/bin/env python
"""Fix data.json - add placeholder images and fix null coordinates."""
import json
from pathlib import Path

data_path = Path(__file__).resolve().parent / "dataset" / "data.json"

with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

destinations = data.get("destinations", {})
print(f"Total destinations: {len(destinations)}")

# Count issues
empty_images = 0
null_coords = 0
fixed_images = 0
fixed_coords = 0

# Default placeholder image (Wikimedia Commons - Nepal tourism)
PLACEHOLDER_IMAGE = {
    "id": 999999,
    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg",
    "caption": "Nepal Tourism",
    "is_cover": True,
    "status": "approved"
}

# Default coordinates (Kathmandu)
DEFAULT_LAT = 27.7172
DEFAULT_LON = 85.3240

for dest_id, dest_data in destinations.items():
    # Fix empty images
    if not dest_data.get("images"):
        dest_data["images"] = [PLACEHOLDER_IMAGE.copy()]
        dest_data["images"][0]["id"] = int(dest_id) * 1000
        empty_images += 1
        fixed_images += 1

    # Fix null coordinates
    if dest_data.get("latitude") is None or dest_data.get("longitude") is None:
        dest_data["latitude"] = DEFAULT_LAT
        dest_data["longitude"] = DEFAULT_LON
        null_coords += 1
        fixed_coords += 1

print(f"Fixed {fixed_images} destinations with empty images")
print(f"Fixed {fixed_coords} destinations with null coordinates")

# Save fixed data
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Data fixed and saved!")
