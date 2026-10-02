import json

with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

destinations = d.get('destinations', {})
print(f'Destinations in data.json: {len(destinations)}')

# Check first few
for k, v in list(destinations.items())[:3]:
    name = v.get('name', 'Unknown')
    images = v.get('images', [])
    print(f'  ID: {k}, Name: {name}, Images: {len(images)}')
    if images:
        for img in images[:1]:
            url = img.get('url', 'NO URL')
            print(f'  URL: {url[:80]}...')