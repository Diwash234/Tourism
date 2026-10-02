#!/usr/bin/env python
"""
Fix images by verifying each destination has CORRECT images.
Uses the verified_tourism_data.json as ground truth for correct images.
"""
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Set, Dict as DictType
from dataclasses import dataclass
from urllib.parse import urlencode, quote_plus

@dataclass
class ImageResult:
    url: str
    thumbnail_url: str
    source: str
    attribution: str
    source_url: str
    width: int = 0
    height: int = 0
    confidence: float = 0.0

class ImageFixer:
    WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
    OPENVERSE_API_URL = "https://api.openverse.org/v1/images/"

    def __init__(self, data_path: str, verified_path: str):
        self.data_path = Path(data_path)
        self.verified_path = Path(verified_path)
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        with open(self.verified_path, 'r', encoding='utf-8') as f:
            self.verified = json.load(f)
            
        self.destinations = self.data.get('destinations', {})
        self.verified_records = self.verified.get('records', [])
        
        # Build verified image lookup
        self.verified_images = {}  # dest_id -> list of verified images
        self.verified_destinations = {}  # dest_id -> verified destination data
        self._build_verified_lookup()
        
        # Session
        self.session = None
        self.used_urls: Set[str] = set()
        self.session = None

    def _build_verified_lookup(self):
        """Build lookup from verified data."""
        for record in self.verified_records:
            if record.get('model') == 'tourist.destination':
                dest_id = record['pk']
                self.verified_destinations[dest_id] = record['fields']
            elif record.get('model') == 'tourist.destinationimage':
                dest_id = record['fields']['destination']
                if dest_id not in self.verified_images:
                    self.verified_images[dest_id] = []
                self.verified_images[dest_id].append(record['fields'])

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _validate_image(self, url: str, dest_id: str) -> float:
        """Validate if an image URL is good to use."""
        if not url or url in self.used_urls:
            return 0.0
        if not url.startswith(('http://', 'https://')):
            return 0.0
        self.used_urls.add(url)
        return 0.9  # High confidence for verified sources

    async def fetch_wikimedia(self, query: str, count: int = 3) -> List[dict]:
        """Fetch from Wikimedia Commons."""
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
            
            async with self.session.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(search_params)}") as resp:
                if not resp.ok:
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
                    async with self.session.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(info_params)}") as resp:
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
                except Exception:
                    continue
                    
            return results[:3]
        except Exception:
            return []

    async def enrich_destination(self, dest_id: str, dest_data: dict) -> List[dict]:
        """Fetch real images for a destination using verified data as ground truth."""
        # First, check if we have verified images for this destination
        if dest_id in self.verified_images:
            verified_imgs = self.verified_images[dest_id]
            if verified_imgs:
                # Use verified images
                results = []
                for img in verified_imgs[:3]:
                    if img.get('external_url'):
                        self.used_urls.add(img['external_url'])
                        results.append({
                            'url': img['external_url'],
                            'thumbnail_url': img['external_url'],
                            'source': 'verified_snapshot',
                            'attribution': img.get('caption', ''),
                            'source_url': '',
                            'confidence': 1.0
                        })
                return results[:3]
        
        # Fallback: search Wikimedia for this destination
        name = self.destinations.get(dest_id, {}).get('name', '')
        district = self.destinations.get(dest_id, {}).get('district', '')
        queries = [f"{name} {district} Nepal", f"{name} Nepal"]
        
        all_results = []
        for query in queries[:2]:
            results = await self.fetch_wikimedia(query, 2)
            for img in results:
                if img.get('url') and img['url'] not in self.used_urls:
                    self.used_urls.add(img['url'])
                    results.append(img)
        
        return results[:3]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def enrich_destination(self, dest_id: str, dest_data: dict) -> List[dict]:
        """Fetch real images for a single destination."""
        return await self._get_images_for_destination(dest_id)

    async def _get_images_for_destination(self, dest_id: str) -> List[dict]:
        # First check verified images
        if dest_id in self.verified_images:
            verified_imgs = self.verified_images[dest_id]
            if verified_imgs:
                results = []
                for img in verified_imgs[:3]:
                    if img.get('external_url'):
                        self.used_urls.add(img['external_url'])
                        results.append({
                            'url': img['external_url'],
                            'thumbnail_url': img['external_url'],
                            'source': 'verified_snapshot',
                            'attribution': img.get('caption', ''),
                            'source_url': '',
                            'confidence': 1.0
                        })
                return results[:3]
        
        # Fallback to Wikimedia search
        name = self.destinations.get(dest_id, {}).get('name', '')
        district = self.destinations.get(dest_id, {}).get('district', '')
        queries = [f"{name} {district} Nepal", f"{name} Nepal"]
        
        all_results = []
        for query in queries[:2]:
            results = await self.fetch_wikimedia(query, 2)
            for img in results:
                if img.get('url') and img['url'] not in self.used_urls:
                    self.used_urls.add(img['url'])
                    results.append(img)
        
        return results[:3]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def save_progress(self, output_path: str = None):
        """Save enriched data back to data.json"""
        # Use absolute path to avoid Windows path issues
        path = r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {path}")

async def main():
    # Use absolute path
    data_path = Path(r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json")
    verified_path = Path(r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\verified_tourism_data.json")
    
    async with ImageFixer(str(data_path), str(verified_path)) as fixer:
        print(f"Loaded {len(fixer.destinations)} destinations")
        
        # Check current state
        with_images = sum(1 for d in fixer.destinations.values() if d.get('images'))
        print(f"Destinations with images: {with_images}/{len(fixer.destinations)}")
        
        # Check verified data
        print(f"Verified destinations: {len(fixer.verified_destinations)}")
        print(f"Verified images for {len(fixer.verified_images)} destinations")
        
        # Process destinations in batches
        batch_size = 50
        dest_items = list(fixer.destinations.items())
        
        for i in range(0, len(dest_items), 50):
            batch = dest_items[i:i + 50]
            print(f"\nProcessing batch {i//50 + 1}/{(len(dest_items)-1)//50 + 1} ({len(batch)} destinations)")
            
            tasks = [fixer.enrich_destination(dest_id, dest_data) for dest_id, dest_data in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            updated = 0
            for (dest_id, dest_data), result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"  Error for {dest_id}: {result}")
                    continue
                if result:
                    dest_data['images'] = result
                    updated += 1
                    name = dest_data.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                    print(f"  + {name}: {len(result)} images")
                else:
                    name = dest_data.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                    print(f"  - {name}: no images found")
            
            # Save progress
            fixer.save_progress()
            print(f"  Progress saved. Used URLs: {len(fixer.used_urls)}")
            
            await asyncio.sleep(1)
        
        print("\nImage fixing complete!")
        fixer.save_progress()

if __name__ == "__main__":
    asyncio.run(main())