#!/usr/bin/env python
"""
Fetch REAL images for all destinations from Wikimedia and Openverse.
"""
import json
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from urllib.parse import urlencode, quote_plus
import time

DATA_PATH = r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json"

# Wikimedia Commons API
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"

# Rate limiting
RATE_LIMITS = {
    'wikimedia': {'calls': 0, 'last_reset': 0, 'limit': 100, 'window': 3600},
    'openverse': {'calls': 0, 'last_reset': 0, 'limit': 100, 'window': 3600},
}

RATE_LIMITS = {}

def check_rate_limit(source: str) -> bool:
    global RATE_LIMITS
    if source not in RATE_LIMITS:
        RATE_LIMITS[source] = {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600}
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
    if not text:
        return False
    lower = text.lower()
    for bad in ['portrait', 'selfie', 'headshot', 'model', 'fashion', 'makeup', 'wedding dress', 'studio shoot', 'person smiling', 'close-up of face']:
        if bad in lower:
            return False
    query_words = query.lower().split()
    for w in query_words:
        if len(w) > 3 and w in lower:
            return True
    return True

async def fetch_wikimedia(query: str, session, count=3):
    """Fetch images from Wikimedia Commons."""
    if not check_rate_limit('wikimedia'):
        return []
    
    try:
        search_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': f'{query} filetype:bitmap',
            'srnamespace': '6',
            'srlimit': str(count * 2),
            'format': 'json',
            'origin': '*',
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(search_params)}") as resp:
                if not resp.ok:
                    print(f"  Wikimedia search failed: {resp.status}")
                    return []
                data = await resp.json()
            
            hits = data.get('query', {}).get('search', [])
            results = []
            
            for hit in hits[:count * 2]:
                if len(results) >= 3:
                    break
                info_params = {
                    'action': 'query',
                    'titles': hit['title'],
                    'prop': 'imageinfo',
                    'iiprop': 'url|extmetadata|size',
                    'format': 'json',
                    'origin': '*',
                }
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(info_params)}") as resp:
                            if not resp.ok:
                                continue
                            info_data = await resp.json()
                        
                        page = list(info_data.get('query', {}).get('pages', {}).values())[0]
                        image_info = page.get('imageinfo', [{}])[0]
                        
                        if image_info.get('url'):
                            extmeta = image_info.get('extmetadata', {})
                            artist = extmeta.get('Artist', {}).get('value', '').replace('<', '').replace('>', '') or 'Wikimedia Commons'
                            results.append({
                                'url': image_info['url'],
                                'thumbnail_url': image_info['url'],
                                'source': 'wikimedia',
                                'attribution': f'Photo: {artist} (Wikimedia Commons)',
                                'source_url': f"https://commons.wikimedia.org/wiki/{quote_plus(hit['title'])}",
                                'width': image_info.get('width', 0),
                                'height': image_info.get('height', 0),
                                'confidence': 0.9
                            })
                except Exception as e:
                    print(f"  Error fetching image info: {e}")
                    continue
                    
            return results[:3]
    except Exception as e:
        print(f"  Wikimedia error: {e}")
        return []

async def fetch_openverse(query: str, session, count=3):
    if not check_rate_limit('openverse'):
        return []
    
    try:
        params = {'q': query, 'page_size': str(count * 2), 'license_type': 'commercial,modification'}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.openverse.org/v1/images/?{urlencode(params)}') as resp:
                if not resp.ok:
                    return []
                data = await resp.json()
            
            results = []
            for r in data.get('results', [])[:count * 2]:
                if looks_like_place(r.get('title', ''), query):
                    results.append({
                        'url': r.get('url', ''),
                        'thumbnail_url': r.get('thumbnail', r.get('url', '')),
                        'source': 'openverse',
                        'attribution': f"{r.get('title', 'Image')} by {r.get('creator', 'Unknown')} ({r.get('license', '').upper()}, via Openverse)",
                        'source_url': r.get('foreign_landing_url', r.get('url', '')),
                        'width': r.get('width', 0),
                        'height': r.get('height', 0),
                        'confidence': 0.8
                    })
            return results[:3]
    except Exception as e:
        print(f"  Openverse error: {e}")
        return []

def looks_like_place(text, query):
    if not text:
        return False
    lower = text.lower()
    for bad in ['portrait', 'selfie', 'headshot', 'model', 'fashion', 'makeup', 'wedding dress', 'studio shoot', 'person smiling', 'close-up of face']:
        if bad in lower:
            return False
    query_words = query.lower().split()
    for w in query_words:
        if len(w) > 3 and w in lower:
            return True
    return True

def check_rate_limit(source: str) -> bool:
    if source not in RATE_LIMITS:
        return True
    rl = {'wikimedia': {'calls': 0, 'last_reset': 0, 'limit': 100, 'window': 3600},
          'openverse': {'calls': 0, 'last_reset': 0, 'limit': 100, 'window': 3600}}
    rl = rl[source]
    now = time.time()
    if now - rl['last_reset'] >= 3600:
        rl['calls'] = 0
        rl['last_reset'] = now
    if rl['calls'] >= rl['limit']:
        return False
    rl['calls'] += 1
    return True

async def enrich_destination(dest_id, dest_data):
    name = dest_data.get('name', '')
    district = dest_data.get('district', '')
    
    queries = [f"{name} {district} Nepal", f"{name} Nepal"]
    if district:
        queries.append(f"{name} {district} Nepal")
    
    all_results = []
    for query in queries[:2]:
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_wikimedia(query, None, 2),
                fetch_openverse(query, None, 2),
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
    destinations = load_data()
    print(f"Loaded {len(destinations)} destinations")
    
    with_images = sum(1 for d in destinations.values() if d.get('images'))
    print(f"Destinations with images: {with_images}/{len(destinations)}")
    
    batch_size = 50
    dest_items = list(destinations.items())
    
    for i in range(0, len(dest_items), 50):
        batch = dest_items[i:i + 50]
        print(f"\nProcessing batch {i//50 + 1}/{(len(dest_items)-1)//50 + 1} ({len(batch)} destinations)")
        
        tasks = [enrich_destination(dest_id, dest_data) for dest_id, dest_data in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (dest_id, dest_data), result in zip(batch, results):
            if isinstance(result, Exception):
                print(f"  Error for {dest_id}: {result}")
                continue
            if result:
                dest_data['images'] = result
                name = dest_data.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                print(f"  + {name}: {len(result)} new images")
            else:
                name = dest_data.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                print(f"  - {name}: no new images")
        
        save_data(destinations)
        print(f"  Progress saved.")
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())