"""
Full replacement for ml_service/services/hotel_service.py.

What was wrong with the original:
  1. HOTEL_FILE = "data/hotel/hotel.csv" -- that file doesn't exist in the
     repo at all. The real, clean data is at ml_service/nepal_hotels_cleaned.csv
     (1603 real hotels with lat/lon/price/rating/booking_url).
  2. Even if the path were right, it read columns as "Hotel Name",
     "Latitude", "Longitude", "Phone", "Rating", "Price Per Night",
     "Booking URL" -- Title Case with spaces. The real CSV's columns are
     snake_case: hotel_name, latitude, longitude, phone, rating,
     price_per_night, booking_url, destination, address, currency,
     booking_status, price_category. Every row access would KeyError.
  3. distance() used raw Euclidean degree distance, not real km.
  4. There was no way to search by city/area name at all (e.g. "Pokhara",
     "Lakeside") -- only nearest-by-coordinates.
  5. No image field exists in the CSV at all, so nothing was ever shown.

This version fixes all of that, adds `search_hotels(query)` for
name/city/address text search, and adds a lightweight image lookup
(Unsplash, same free-tier pattern as the Django-side destination photos)
so results always include an `image_url` -- with a Wikimedia fallback and
finally a generic placeholder if neither has a match, so the frontend
never has to handle "no image" as a special case.
"""
import math
import os

import pandas as pd
import requests

HOTEL_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nepal_hotels_cleaned.csv")

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")
PLACEHOLDER_IMAGE = "https://images.unsplash.com/photo-1566073771259-6a8506099945"  # generic Nepal/mountain shot

_hotels_df = None  # loaded lazily, cached in memory for the life of the process


def _load_hotels():
    global _hotels_df
    if _hotels_df is None:
        _hotels_df = pd.read_csv(HOTEL_FILE)
    return _hotels_df


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _fetch_image_url(query):
    """Best-effort image lookup. Never raises -- always returns a usable URL."""
    if UNSPLASH_ACCESS_KEY:
        try:
            resp = requests.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1},
                headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
                timeout=4,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                return results[0]["urls"]["regular"]
        except requests.RequestException:
            pass

    try:
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "list": "search",
                "srsearch": f"{query} filetype:bitmap", "srnamespace": 6, "format": "json",
            },
            headers={"User-Agent": "TourismApp/1.0 (https://github.com/Diwash234/Tourism)"},
            timeout=4,
        )
        resp.raise_for_status()
        hits = resp.json().get("query", {}).get("search", [])
        if hits:
            title = hits[0]["title"]
            info = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url", "format": "json"},
                headers={"User-Agent": "TourismApp/1.0 (https://github.com/Diwash234/Tourism)"},
                timeout=4,
            ).json()
            pages = info.get("query", {}).get("pages", {})
            page = next(iter(pages.values()), {})
            image_info = (page.get("imageinfo") or [{}])[0]
            if image_info.get("url"):
                return image_info["url"]
    except requests.RequestException:
        pass

    return PLACEHOLDER_IMAGE


def _row_to_dict(row, distance_km=None, with_image=True):
    result = {
        "hotel_name": row["hotel_name"],
        "destination": row["destination"],
        "address": row["address"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "phone": row["phone"],
        "rating": row["rating"],
        "price_per_night": row["price_per_night"],
        "currency": row.get("currency", "USD"),
        "booking_status": row.get("booking_status"),
        "booking_url": row.get("booking_url"),
        "price_category": row.get("price_category"),
    }
    if distance_km is not None:
        result["distance_km"] = round(distance_km, 2)
    if with_image:
        result["image_url"] = _fetch_image_url(f"{row['hotel_name']} {row['destination']} hotel")
    return result


def nearest_hotels(lat, lon, limit=10, with_images=True):
    df = _load_hotels()
    df = df.copy()
    df["_distance_km"] = df.apply(lambda r: _haversine_km(lat, lon, r["latitude"], r["longitude"]), axis=1)
    df = df.sort_values("_distance_km").head(limit)
    return [_row_to_dict(row, row["_distance_km"], with_images) for _, row in df.iterrows()]


def search_hotels(query, limit=10, with_images=True):
    """
    Text search across hotel name, destination/city, and address -- this
    is what lets a search for "Pokhara" or "Lakeside" return matching
    hotels, which the old code had no way to do at all.
    """
    df = _load_hotels()
    query = (query or "").strip().lower()
    if not query:
        return []

    mask = (
        df["hotel_name"].str.lower().str.contains(query, na=False)
        | df["destination"].str.lower().str.contains(query, na=False)
        | df["address"].str.lower().str.contains(query, na=False)
    )
    matches = df[mask].sort_values("rating", ascending=False).head(limit)
    return [_row_to_dict(row, None, with_images) for _, row in matches.iterrows()]