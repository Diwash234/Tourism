#!/usr/bin/env python
"""
Real Image Enrichment System for Nepal Tourism
Fetches REAL, accurate images for each destination from multiple sources:
- Wikimedia Commons (free, no API key)
- Openverse (free, no API key)
- Unsplash (requires API key)
- Pexels (requires API key)
- Pixabay (requires API key)
- Flickr (requires API key)

Validates images are relevant to the destination (by name, district, category)
"""
import json
import os
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from urllib.parse import quote_plus

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

class ImageEnricher:
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.destinations = self.data.get('destinations', {})
        
        # API keys from environment
        self.unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY', '')
        self.pexels_key = os.getenv('PEXELS_API_KEY', '')
        self.pixabay_key = os.getenv('PIXABAY_API_KEY', '')
        self.flickr_key = os.getenv('FLICKR_API_KEY', '')
        self.flickr_secret = os.getenv('FLICKR_API_SECRET', '')
        
        # Session for connection pooling
        self.session = None
        
        # Cache for API responses
        self.cache = {}
        
        # Rate limiting
        self.rate_limits = {
            'unsplash': {'calls': 0, 'last_reset': time.time(), 'limit': 50},
            'pexels': {'calls': 0, 'last_reset': time.time(), 'limit': 200},
            'pixabay': {'calls': 0, 'last_reset': time.time(), 'limit': 100},
            'flickr': {'calls': 0, 'last_reset': time.time(), 'limit': 3600},
            'wikimedia': {'calls': 0, 'last_reset': time.time(), 'limit': 100},
            'openverse': {'calls': 0, 'last_reset': time.time(), 'limit': 100},
        }
        
        # Track used image URLs to avoid duplicates
        self.used_urls: Set[str] = set()
        
        # Destination-specific search terms for better results
        self.search_hints = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _check_rate_limit(self, source: str) -> bool:
        """Check and update rate limit for a source."""
        rl = self.rate_limits[source]
        now = time.time()
        if now - rl['last_reset'] >= 3600:  # Reset hourly
            rl['calls'] = 0
            rl['last_reset'] = now
        if rl['calls'] >= rl['limit']:
            return False
        rl['calls'] += 1
        return True

    def _check_rate_limit(self, source: str) -> bool:
        """Check and update rate limit for a source."""
        rl = self.rate_limits[source]
        now = time.time()
        if now - rl['last_reset'] >= 3600:  # Reset hourly
            rl['calls'] = 0
            rl['last_reset'] = now
        if rl['calls'] >= rl['limit']:
            return False
        rl['calls'] += 1
        return True

    def _validate_image(self, url: str, destination_name: str, district: str = "", category: str = "") -> float:
        """
        Validate if an image is relevant to the destination.
        Returns confidence score 0.0 - 1.0
        """
        if not url or url in self.used_urls:
            return 0.0
        
        self.used_urls.add(url)
        
        # Basic checks
        if not url or not url.startswith(('http://', 'https://')):
            return 0.0
        
        # Check for common irrelevant patterns
        url_lower = url.lower()
        irrelevant = ['placeholder', 'default', 'generic', 'stock', 'default', 'blank', 'default.jpg', 'default.png']
        for irr in irrelevant:
            if irr in url.lower():
                return 0.0
        
        # Score based on relevance
        score = 0.5  # base score
        
        # Check if destination name appears in URL
        dest_name = self.destinations.get(dest_id, {}).get('name', '').lower()
        if dest_name and any(word in url.lower() for word in dest_name.split() if len(word) > 3):
            score += 0.3
        
        # District match
        district = self.destinations.get(dest_id, {}).get('district', '').lower()
        if district and district in url.lower():
            score += 0.2
        
        # Category relevance
        category = self.destinations.get(dest_id, {}).get('type', '').lower()
        if category and category in url.lower():
            score += 0.1
            
        return min(score, 1.0)

    async def fetch_wikimedia(self, query: str, count: int = 3) -> List[dict]:
        """Fetch images from Wikimedia Commons."""
        if not self._check_rate_limit('wikimedia'):
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
            
            async with self.session.get(f"{self.WIKIMEDIA_API_URL}?{urlencode(search_params)}") as resp:
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
                    async with self.session.get(f"{self.WIKIMEDIA_API_URL}?{urlencode(info_params)}") as resp:
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

    async def fetch_openverse(self, query: str, count: int = 3) -> List[dict]:
        """Fetch from Openverse (free, no API key)."""
        if not self._check_rate_limit('openverse'):
            return []
        
        try:
            params = {
                'q': query,
                'page_size': str(count * 2),
                'license_type': 'commercial,modification',
            }
            
            async with self.session.get(f'https://api.openverse.org/v1/images/?{urlencode(params)}') as resp:
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
        except Exception:
            return []

    async def fetch_unsplash(self, query: str, count: int = 3) -> List[dict]:
        if not self.unsplash_key or not self._check_rate_limit('unsplash'):
            return []
        
        try:
            params = {
                'query': query,
                'per_page': str(count * 2),
                'orientation': 'landscape',
            }
            headers = {'Authorization': f'Client-ID {self.unsplash_key}'}
            
            async with self.session.get(f'https://api.unsplash.com/search/photos?{urlencode(params)}', headers=headers) as resp:
                if not resp.ok:
                    return []
                data = await resp.json()
                
            results = []
            for r in data.get('results', [])[:count * 2]:
                if looks_like_place(f"{r.get('description', '')} {r.get('alt_description', '')}", query):
                    results.append({
                        'url': r['urls']['regular'],
                        'thumbnail_url': r['urls']['small'],
                        'source': 'unsplash',
                        'attribution': f"Photo by {r['user']['name']} on Unsplash",
                        'source_link': r['links']['html'],
                        'width': r['width'],
                        'height': r['height'],
                        'confidence': 0.85
                    })
            return results[:3]
        except Exception:
            return []

    async def fetch_pexels(self, query: str, count: int = 3) -> List[dict]:
        if not self.pexels_key or not self._check_rate_limit('pexels'):
            return []
        
        try:
            params = {'query': query, 'per_page': str(count * 2)}
            headers = {'Authorization': self.pexels_key}
            
            async with self.session.get(f'https://api.pexels.com/v1/search?{urlencode(params)}', headers=headers) as resp:
                if not resp.ok:
                    return []
                data = await resp.json()
                
            results = []
            for p in data.get('photos', [])[:count * 2]:
                if looks_like_place(p.get('alt', ''), query):
                    results.append({
                        'url': p['src']['large'],
                        'thumbnail_url': p['src']['medium'],
                        'source': 'pexels',
                        'attribution': f"Photo by {p['photographer']} on Pexels",
                        'source_link': p['url'],
                        'width': p['width'],
                        'height': p['height'],
                        'confidence': 0.85
                    })
            return results[:3]
        except Exception:
            return []

    async def fetch_pixabay(self, query: str, count: int = 3) -> List[dict]:
        if not self.pixabay_key or not self._check_rate_limit('pixabay'):
            return []
        
        try:
            params = {
                'key': self.pixabay_key,
                'q': query,
                'image_type': 'photo',
                'per_page': str(count * 2),
            }
            
            async with self.session.get(f'https://pixabay.com/api/?{urlencode(params)}') as resp:
                if not resp.ok:
                    return []
                data = await resp.json()
                
            results = []
            for h in data.get('hits', [])[:count * 2]:
                if looks_like_place(h.get('tags', ''), query):
                    results.append({
                        'url': h['largeImageURL'],
                        'thumbnail_url': h['webformatURL'],
                        'source': 'pixabay',
                        'attribution': f"Photo by {h['user']} on Pixabay",
                        'source_link': h['pageURL'],
                        'width': h['imageWidth'],
                        'height': h['imageHeight'],
                        'confidence': 0.8
                    })
            return results[:3]
        except Exception:
            return []

    async def fetch_flickr(self, query: str, count: int = 3) -> List[dict]:
        if not self.flickr_key or not self.flickr_secret or not self._check_rate_limit('flickr'):
            return []
        
        try:
            params = {
                'method': 'flickr.photos.search',
                'api_key': self.flickr_key,
                'text': query,
                'per_page': str(count * 2),
                'format': 'json',
                'nojsoncallback': 1,
                'license': '1,2,3,4,5,6,7,8,9,10',  # CC licenses
                'content_type': 1,  # photos only
                'media': 'photos',
                'sort': 'relevance',
            }
            
            async with self.session.get(f'https://api.flickr.com/services/rest/?{urlencode(params)}') as resp:
                if not resp.ok:
                    return []
                data = await resp.json()
                
            results = []
            for photo in data.get('photos', {}).get('photo', [])[:count * 2]:
                # Get sizes
                size_params = {
                    'method': 'flickr.photos.getSizes',
                    'api_key': self.flickr_key,
                    'photo_id': photo['id'],
                    'format': 'json',
                    'nojsoncallback': 1,
                }
                
                async with self.session.get(f'https://api.flickr.com/services/rest/?{urlencode(size_params)}') as resp:
                    if not resp.ok:
                        continue
                    size_data = await resp.json()
                    
                sizes = size_data.get('sizes', {}).get('size', [])
                large = next((s for s in sizes if s['label'] == 'Large'), sizes[-1] if sizes else None)
                thumb = next((s for s in sizes if s['label'] == 'Thumbnail'), sizes[0] if sizes else None)
                
                if large:
                    results.append({
                        'url': large['source'],
                        'thumbnail_url': thumb['source'] if thumb else large['source'],
                        'source': 'flickr',
                        'attribution': f"Photo on Flickr",
                        'source_link': f"https://www.flickr.com/photos/{photo['owner']}/{photo['id']}",
                        'width': int(large.get('width', 0)),
                        'height': int(large.get('height', 0)),
                        'confidence': 0.75
                    })
                    
            return results[:3]
        except Exception:
            return []

    async def enrich_destination(self, dest_id: str, dest_data: dict) -> List[dict]:
        """Fetch real images for a single destination."""
        name = dest_data.get('name', '')
        district = dest_data.get('district', '')
        city = dest_data.get('city_english', '') or dest_data.get('city', '')
        category = dest_data.get('type', '')
        district = dest_data.get('district', '')
        
        # Build search queries with context
        queries = [
            f"{name} {district} Nepal",
            f"{name} Nepal",
        ]
        
        if district:
            queries.append(f"{name} {district} Nepal")
        if city and city != name:
            queries.append(f"{city} {district} Nepal")
        
        all_results = []
        seen_urls = set()
        
        for query in queries[:2]:  # Limit to 2 queries per destination
            tasks = [
                self.fetch_wikimedia(query, 2),
                self.fetch_openverse(query, 2),
                self.fetch_unsplash(query, 2),
                self.fetch_pexels(query, 2),
                self.fetch_pixabay(query, 2),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    for img in result:
                        if img.get('url') and img['url'] not in self.used_urls:
                            # Validate relevance
                            confidence = self._validate_image(img['url'], dest_id)
                            if confidence > 0.5:
                                img['confidence'] = confidence
                                all_results.append(img)
                                self.used_urls.add(img['url'])
        
        # Sort by confidence and return top 3
        all_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return all_results[:3]

    def save_progress(self, output_path: str = None):
        """Save enriched data back to data.json"""
        path = Path(output_path) if output_path else self.data_path
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {path}")

async def main():
    data_path = Path(__file__).resolve().parent / "dataset" / "data.json"
    
    # Load API keys from environment
    os.environ.setdefault('UNSPLASH_ACCESS_KEY', os.getenv('UNSPLASH_ACCESS_KEY', ''))
    os.environ.setdefault('PEXELS_API_KEY', os.getenv('PEXELS_API_KEY', ''))
    os.environ.setdefault('PIXABAY_API_KEY', os.getenv('PIXABAY_API_KEY', ''))
    os.environ.setdefault('FLICKR_API_KEY', os.getenv('FLICKR_API_KEY', ''))
    os.environ.setdefault('FLICKR_API_SECRET', os.getenv('FLICKR_API_SECRET', ''))
    
    async with ImageEnricher("C:/Users/ADMIN/Desktop/Chatbot/Tourism/dataset/data.json") as enricher:
        print(f"Loaded {len(enricher.destinations)} destinations")
        
        # Check current state
        with_images = sum(1 for d in enricher.destinations.values() if d.get('images'))
        print(f"Destinations with images: {with_images}/{len(enricher.destinations)}")
        
        # Process destinations in batches
        batch_size = 50
        dest_items = list(enricher.destinations.items())
        
        for i in range(0, len(dest_items), batch_size):
            batch = dest_items[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(dest_items)-1)//batch_size + 1} ({len(batch)} destinations)")
            
            tasks = [enricher.enrich_destination(dest_id, dest_data) for dest_id, dest_data in batch]
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
            
            # Save progress every batch
            enricher.save_progress()
            print(f"  Progress saved. Used URLs: {len(enricher.used_urls)}")
            
            # Rate limit between batches
            await asyncio.sleep(2)
        
        print("\nEnrichment complete!")
        enricher.save_progress()

if __name__ == "__main__":
    asyncio.run(main())