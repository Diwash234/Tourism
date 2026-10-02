import json

with open('Tourism/dataset/data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

destinations = data.get('destinations', {})
count = 0
for dest_id, dest_data in list(destinations.items())[:5]:
    images = dest_data.get('images', [])
    if images:
        print(f'Dest {dest_id} ({dest_data.get("name")}): {len(images)} images')
        for img in images[:2]:
            print(f'  Image: {img.get("url", "NO URL")[:80]}...')
    else:
        print(f'Dest {dest_id} ({dest_data.get("name")}): NO IMAGES')