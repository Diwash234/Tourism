#!/usr/bin/env python
"""
Real Image Enrichment System for Nepal Tourism
Fetches REAL, accurate images for each destination from FREE sources:
- Wikimedia Commons (free, no API key)
- Openverse (free, no API key)

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
from urllib.parse import urlencode, quote_plus
import math

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
    WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
    OPENVERSE_API_URL = "https://api.openverse.org/v1/images/"

    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.destinations = self.data.get('destinations', {})
        
        # Session for connection pooling
        self.session = None
        
        # Cache for API responses
        self.cache = {}
        
        # Rate limiting
        self.rate_limits = {
            'wikimedia': {'calls': 0, 'last_reset': time.time(), 'limit': 100},
            'openverse': {'calls': 0, 'last_reset': time.time(), 'limit': 100},
        }
        
        # Track used image URLs to avoid duplicates
        self.used_urls: Set[str] = set()

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

    def _validate_image(self, url: str, dest_id: str) -> float:
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
        irrelevant = ['placeholder', 'default', 'generic', 'stock', 'blank', 'default.jpg', 'default.png']
        for irr in ['placeholder', 'default', 'generic', 'stock', 'blank', 'default.jpg', 'default.png']:
            if irr in url_lower:
                return 0.0
        
        # Score based on relevance
        score = 0.5  # base score
        
        # Check if destination name appears in URL
        dest_data = self.destinations.get(dest_id, {})
        dest_name = dest_data.get('name', '').lower()
        if dest_name:
            name_words = [w for w in dest_name.split() if len(w) > 3]
            if any(word in url.lower() for word in name_words):
                score += 0.3
        
        # District match
        district = self.destinations.get(dest_id, {}).get('district', '').lower()
        if district and district in url.lower():
            score += 0.2
        
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
            
            async with self.session.get(f'{self.OPENVERSE_API_URL}?{urlencode(params)}') as resp:
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

    def _validate_image(self, url: str, dest_id: str) -> float:
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
        for irr in ['placeholder', 'default', 'generic', 'stock', 'blank', 'default.jpg', 'default.png']:
            if irr in url_lower:
                return 0.0
        
        # Score based on relevance
        score = 0.5  # base score
        
        # Check if destination name appears in URL
        dest_data = self.destinations.get(dest_id, {})
        dest_name = dest_data.get('name', '').lower()
        if dest_name:
            name_words = [w for w in dest_name.split() if len(w) > 3]
            if any(word in url.lower() for word in name_words):
                score += 0.3
        
        # District match
        district = dest_data.get('district', '').lower()
        if district and district in url.lower():
            score += 0.2
        
        return min(score, 1.0)

    async def enrich_destination(self, dest_id: str, dest_data: dict) -> List[dict]:
        """Fetch real images for a single destination."""
        name = dest_data.get('name', '')
        district = dest_data.get('district', '')
        city = dest_data.get('city_english', '') or dest_data.get('city', '')
        category = dest_data.get('type', '')
        
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
        
        for query in queries[:2]:  # Limit to 2 queries per destination
            tasks = [
                self.fetch_wikimedia(query, 2),
                self.fetch_openverse(query, 2),
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
                                self.used_urls.add(img['url'])
                                all_results.append(img)
        
        # Sort by confidence and return top 3
        all_results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return all_results[:3]

    def save_progress(self, output_path: str = None):
        """Save enriched data back to data.json"""
        path = Path(output_path) if output_path else self.data_path
        # Ensure we use absolute path
        path = Path(path).resolve()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {path}")

async def main():
    data_path = Path(__file__).resolve().parent / "dataset" / "data.json"
    
    async with ImageEnricher(str(data_path.resolve())) as enricher:
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