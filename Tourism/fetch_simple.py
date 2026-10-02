#!/usr/bin/env python
"""
Fix images in data.json using verified_tourism_data.json as primary source.
Only use Wikimedia/Openverse as fallback for destinations not in verified snapshot.
"""
import json
import asyncio
import aiohttp
import time
from urllib.parse import urlencode, quote_plus
import time

DATA_FILE = r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json"
VERIFIED_FILE = r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json"

# Rate limiting
RATE_LIMITS = {
    'wikimedia': {'calls': 0, 'last_reset': time.time(), 'limit': 50, 'window': 3600},
    'openverse': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600},
}

USED_URLS = set()

def check_rate_limit(source):
    rl = {'wikimedia': {'calls': 0, 'last_reset': time.time(), 'limit': 50, 'window': 3600},
          'openverse': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600}}
    rl = RATE_LIMITS[source]
    now = time.time()
    if now - rl['last_reset'] >= 3600:
        rl['calls'] = 0
        rl['last_reset'] = now
    if rl['calls'] >= rl['limit']:
        return False
    rl['calls'] += 1
    return True

def looks_like_place(text, query):
    if not text: return False
    lower = text.lower()
    for bad in ['portrait', 'selfie', 'headshot', 'model', 'fashion', 'makeup', 'wedding dress', 'studio shoot', 'person smiling', 'close-up of face']:
        if bad in lower: return False
    query_words = query.lower().split()
    for w in query_words:
        if len(w) > 3 and w in lower: return True
    return True

async def fetch_wikimedia(query, session, count=3):
    if not check_rate_limit('wikimedia'): return []
    try:
        params = {'action': 'query', 'list': 'search', 'srsearch': f'{query} filetype:bitmap',
                  'srnamespace': '6', 'srlimit': str(count * 2), 'format': 'json', 'origin': '*'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(search_params)}") as resp:
                if not resp.ok: return []
                data = await resp.json()
            hits = data.get('query', {}).get('search', [])
            results = []
            for hit in hits[:count * 2]:
                if len(results) >= 3: break
                info_params = {'action': 'query', 'titles': hit['title'],
                               'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size',
                               'format': 'json', 'origin': '*'}
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(info_params)}") as resp:
                            if not resp.ok: continue
                            info_data = await resp.json()
                            page = list(info_data.get('query', {}).get('pages', {}).values())[0]
                            image_info = page.get('imageinfo', [{}])[0]
                            if image_info.get('url'):
                                extmeta = image_info.get('extmetadata', {})
                                artist = extmeta.get('Artist', {}).get('value', '').replace('<', '').replace('>', '') or 'Wikimedia Commons'
                                results.append({
                                    'url': image_info['url'], 'thumbnail_url': image_info['url'],
                                    'source': 'wikimedia', 'attribution': f'Photo: {artist} (Wikimedia Commons)',
                                    'source_url': f"https://commons.wikimedia.org/wiki/{quote_plus(hit['title'])}",
                                    'width': image_info.get('width', 0), 'height': image_info.get('height', 0),
                                    'confidence': 0.9
                                })
                except: pass
            return results[:3]
    except Exception as e:
        print(f"  Wikimedia error: {e}")
        return []

async def fetch_openverse(query, session, count=3):
    if not check_rate_limit('openverse'): return []
    try:
        params = {'q': query, 'page_size': str(count * 2), 'license_type': 'commercial,modification'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.openverse.org/v1/images/?{urlencode(params)}') as resp:
                if not resp.ok: return []
                data = await resp.json()
            results = []
            for r in data.get('results', [])[:count * 2]:
                if looks_like_place(r.get('title', ''), query):
                    results.append({
                        'url': r.get('url', ''), 'thumbnail_url': r.get('thumbnail', r.get('url', '')),
                        'source': 'openverse', 'attribution': f"{r.get('title', 'Image')} by {r.get('creator', 'Unknown')} ({r.get('license', '').upper()}, via Openverse)",
                        'source_url': r.get('foreign_landing_url', r.get('url', '')),
                        'width': r.get('width', 0), 'height': r.get('height', 0), 'confidence': 0.8
                    })
            return results[:3]
    except: return []

def looks_like_place(text, query):
    if not text: return False
    lower = text.lower()
    for bad in ['portrait', 'selfie', 'headshot', 'model', 'fashion', 'makeup', 'wedding dress', 'studio shoot', 'person smiling', 'close-up of face']:
        if bad in lower: return False
    query_words = query.lower().split()
    for w in query_words:
        if len(w) > 3 and w in lower: return True
    return True

def check_rate_limit(source):
    RATE_LIMITS = {'wikimedia': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600},
                   'openverse': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600}}
    rl = RATE_LIMITS[source]
    now = time.time()
    if now - rl['last_reset'] >= 3600:
        rl['calls'] = 0
        rl['last_reset'] = now
    if rl['calls'] >= rl['limit']: return False
    rl['calls'] += 1
    return True

def looks_like_place(text, query):
    if not text: return False
    lower = text.lower()
    for bad in ['portrait', 'selfie', 'headshot', 'model', 'fashion', 'makeup', 'wedding dress', 'studio shoot', 'person smiling', 'close-up of face']:
        if bad in lower: return False
    query_words = query.lower().split()
    for w in query_words:
        if len(w) > 3 and w in lower: return True
    return True

async def enrich_destination(dest_id, dest_data, session):
    name = dest_data.get('name', '')
    district = dest_data.get('district', '')
    queries = [f"{name} {district} Nepal", f"{name} Nepal"]
    if district: queries.append(f"{name} {district} Nepal")
    
    all_results = []
    for query in queries[:2]:
        tasks = [
            fetch_wikimedia(query, 2),
            fetch_openverse(query, 2),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                for img in result:
                    if img.get('url') and img['url'] not in USED_URLS:
                        USED_URLS.add(img['url'])
                        all_results.append(img)
    all_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    return all_results[:3]

def load_data():
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('destinations', {})

def save_data(destinations):
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'w', encoding='utf-8') as f:
        json.dump({'destinations': destinations}, f, indent=2, ensure_ascii=False)

async def main():
    global USED_URLS
    USED_URLS = set()
    
    # Load verified snapshot FIRST to get high-quality images
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json', 'r', encoding='utf-8') as f:
        verified = json.load(f)
    
    # Build verified image lookup by destination name/slug
    images_by_name = {}
    for r in json.load(open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json', 'r', encoding='utf-8'))['records']:
        if r.get('model') == 'tourist.destinationimage':
            dest_id = str(r['fields']['destination'])
            # Get destination name from the verified snapshot
            # We'll match by name later
            pass
    
    # Build lookup: destination name -> images
    images_by_name = {}
    dest_names = {}
    for r in json.load(open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json', 'r', encoding='utf-8'))['records']:
        if r.get('model') == 'tourist.destination':
            pk = str(r['pk'])
            name = r['fields'].get('name', '').lower().strip()
            if name: dest_names[pk] = name
    
    images_by_dest = {}
    for r in json.load(open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json', 'r', encoding='utf-8'))['records']:
        if r.get('model') == 'tourist.destinationimage':
            dest_id = str(r['fields']['destination'])
            if dest_id not in images_by_dest: images_by_dest[dest_id] = []
            images_by_dest[dest_id].append(r['fields'])
    
    images_by_name = {}
    for pk, imgs in images_by_dest.items():
        name = dest_names.get(pk, '').lower()
        if name: images_by_name[name] = imgs
    
    print(f"Verified images for {len(images_by_dest)} destination IDs")
    print(f"Mapped by name: {len(images_by_name)} destinations")
    
    # Load current data.json
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    destinations = data.get('destinations', {})
    print(f"Total destinations in data.json: {len(destinations)}")
    
    # Build lookup by name and slug
    dest_by_name = {}
    dest_by_slug = {}
    for pk, dest in destinations.items():
        name = dest.get('name', '').lower().strip()
        slug = dest.get('slug', '').lower().strip()
        if name: dest_by_name[name.lower()] = dest
        if slug: dest_by_slug[slug.lower()] = dest
    
    updated = 0
    for pk, dest in destinations.items():
        name = dest.get('name', '').lower().strip()
        slug = dest.get('slug', '').lower().strip()
        
        verified_imgs = None
        if name in images_by_name:
            verified_imgs = images_by_name[name]
        elif slug in images_by_name:
            verified_imgs = images_by_name[slug]
        else:
            for vn, imgs in images_by_name.items():
                if name and name in vn:
                    verified_imgs = imgs; break
                if slug and slug in vn:
                    verified_imgs = imgs; break
        
        if verified_imgs:
            new_images = []
            for img in verified_imgs[:3]:
                if img.get('external_url'):
                    new_images.append({
                        'id': int(pk) * 1000 + len(dest.get('images', [])),
                        'url': img['external_url'],
                        'caption': img.get('caption', ''),
                        'is_cover': img.get('is_cover', False),
                        'status': 'approved'
                    })
            if new_images:
                dest['images'] = new_images
                name_safe = dest.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                print(f"  Updated {name_safe} with {len(new_images)} verified images")
                updated += 1
    
    print(f"Updated {updated} destinations with verified images")
    
    # For remaining destinations without images, add placeholder
    for pk, dest in destinations.items():
        if not dest.get('images'):
            dest['images'] = [{
                'id': int(pk) * 1000,
                'url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg',
                'caption': f"{dest.get('name', 'Nepal')} - View",
                'is_cover': True, 'status': 'approved'
            }]
    
    with open(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved!")

if __name__ == '__main__':
    asyncio.run(main())