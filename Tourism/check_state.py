import json

with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dests = data.get('destinations', {})
print(f'Total destinations: {len(data.get("destinations", {}))}')
with_images = sum(1 for d in dests.values() if d.get('images'))
print(f'With images: {with_images}')

# Check first 3
for k, v in list(dests.items())[:3]:
    print(f'  {v.get("name")}: {len(v.get("images", []))} images')