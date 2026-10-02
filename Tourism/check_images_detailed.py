import json
import sys

with open('Tourism/dataset/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

destinations = data.get('destinations', {})

# Check for duplicate images
image_urls = {}
for dest_id, dest_data in destinations.items():
    images = dest_data.get('images', [])
    for img in images:
        url = img.get('url', '')
        if url in image_urls:
            image_urls[url].append(dest_data.get('name', 'Unknown'))
        else:
            image_urls[url] = [dest_data.get('name', 'Unknown')]

# Find URLs used by multiple destinations
duplicate_urls = {url: names for url, names in image_urls.items() if len(names) > 1}
print(f"Total unique images: {len(image_urls)}")
print(f"Duplicate images (used by multiple destinations): {len(duplicate_urls)}")

for url, names in list(duplicate_urls.items())[:10]:
    safe_names = [n.encode('ascii', 'ignore').decode('ascii') for n in names[:5]]
    print(f"  Used by {len(names)} destinations: {safe_names}")

# Check for placeholder images
placeholder_count = sum(1 for url in image_urls if 'Nepal_Mount_Everest' in url)
print(f"\nDestinations using Mount Everest placeholder: {placeholder_count}")

# Check first 10 destinations in detail
print("\nFirst 10 destinations with images:")
for dest_id, dest_data in list(destinations.items())[:10]:
    images = dest_data.get('images', [])
    name = dest_data.get('name', 'Unknown')
    safe_name = name.encode('ascii', 'ignore').decode('ascii')
    print(f"  {safe_name}: {len(images)} images")
    for img in images[:1]:
        print(f"  Image: {img.get('url', 'NO URL')[:80]}...")