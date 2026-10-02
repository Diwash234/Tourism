#!/usr/bin/env python
"""
Fetch REAL images for all destinations from Wikimedia and Openverse.
Fixed version with proper session handling.
"""
import json
import asyncio
import aiohttp
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
from urllib.parse import urlencode, quote_plus
import time

DATA_PATH = r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\data.json"

# Wikimedia Commons API
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"

# Rate limiting
RATE_LIMITS = {
    'wikimedia': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600},
    'openverse': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600},
}

USED_URLS = set()

async def fetch_wikimedia(query: str, session, count=3):
    """Fetch images from Wikimedia Commons using the provided session."""
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
        
        # Use the passed session
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