import json

with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dests = data.get('destinations', {})
print(f'Total destinations: {len(dests)}')
with_images = sum(1 for d in dests.values() if d.get('images'))
print(f'With images: {with_images}')

# Check a few
for k, v in list(dests.items())[:5]:
    name = v.get('name', 'Unknown')
    images = v.get('images', [])
    print(f'  {name}: {len(images)} images')
    if images:
        for img in images[:1]:
            print(f'  URL: {img.get("url", "NO URL")[:80]}...')