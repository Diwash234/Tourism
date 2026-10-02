import json

with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json', 'r', encoding='utf-8') as f:
    v = json.load(f)

images = {}
img_count = 0
for r in v['records']:
    if r.get('model') == 'tourist.destinationimage':
        dest_id = str(r['fields']['destination'])
        if dest_id not in images:
            images[dest_id] = []
        images[dest_id].append(r['fields'])
        img_count += 1

print(f'Total images: {img_count}')
print(f'Destinations with images: {len(images)}')
for k, v in list(images.items())[:3]:
    print(f'  Dest {k}: {len(v)} images')
    for img in v[:1]:
        print(f'  URL: {img.get("external_url", "NO URL")[:80]}...')