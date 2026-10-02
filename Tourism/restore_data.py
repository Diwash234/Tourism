import json

try:
    with open('Tourism/dataset/data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('data.json is valid JSON')
    print(f'Destinations: {len(data.get("destinations", {}))}')
except json.JSONDecodeError as e:
    print(f'JSON Error: {e}')
    print('Attempting to restore from verified_tourism_data.json...')
    with open('Tourism/dataset/verified_tourism_data.json', 'r', encoding='utf-8') as f:
        verified = json.load(f)
    print(f'Verified records: {len(verified["records"])}')
    # Extract destinations from verified
    dests = {}
    for r in verified['records']:
        if r.get('model') == 'tourist.destination':
            dests[str(r['pk'])] = r['fields']
    print(f'Destinations in verified: {len(dests)}')
    # Save as data.json
    with open('Tourism/dataset/data.json', 'w', encoding='utf-8') as f:
        json.dump({'destinations': dests}, f, indent=2, ensure_ascii=False)
    print('Restored data.json from verified snapshot')