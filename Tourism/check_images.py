import json

with open('Tourism/dataset/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

destinations = data.get('destinations', {})
total = len(destinations)
with_images = sum(1 for d in destinations.values() if d.get('images') and len(d.get('images', [])) > 0)
print(f'Total destinations: {total}')
print(f'Destinations with images: {with_images}')
print(f'Destinations without images: {total - with_images}')

# Check a few images
for dest_id, dest_data in list(destinations.items())[:3]:
    images = dest_data.get('images', [])
    if images:
        for img in images[:1]:
            print(f'  Dest {dest_id}: {img.get("url", "NO URL")[:80]}...')