"""
ml_service/services/hotel_service.py

Hotel service for the Nepal tourism application.

Features:
- Loads hotels from ml_service/nepal_hotels_cleaned.csv
- Supports nearest-hotel search using latitude/longitude
- Supports text search by:
    - hotel name
    - destination/city
    - address
- Uses Haversine distance in real kilometers
- Returns hotel rating, price, currency, booking URL, etc.
- Supports both NPR (Nepali Rupees) and USD
- Optional image lookup through Django image resolver
- Uses a fallback image if image lookup fails
- Safely handles missing CSV values
- Keeps the CSV cached in memory
"""

import math
import os

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

# hotel_service.py:
#
# ml_service/
#     services/
#         hotel_service.py
#     nepal_hotels_cleaned.csv
#
# Therefore:
# os.path.dirname(__file__) -> ml_service/services
# dirname(dirname(__file__)) -> ml_service

HOTEL_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "nepal_hotels_cleaned.csv",
)


# ---------------------------------------------------------------------------
# IMAGE SETTINGS
# ---------------------------------------------------------------------------

# Optional Unsplash key if you use Unsplash directly elsewhere.
# The actual image request is sent through Django's image resolver.
UNSPLASH_ACCESS_KEY = os.environ.get(
    "UNSPLASH_ACCESS_KEY",
    "",
)


# Generic hotel image used when no image can be found.
PLACEHOLDER_IMAGE = (
    "https://images.unsplash.com/"
    "photo-1566073771259-6a8506099945"
)


# Django API base URL.
#
# Default:
# http://localhost:8000/api/v1
#
# You can change it with:
#
# Windows PowerShell:
# $env:DJANGO_API_URL="http://localhost:8000/api/v1"
#
DJANGO_API_URL = os.environ.get(
    "DJANGO_API_URL",
    "http://localhost:8000/api/v1",
)


# ---------------------------------------------------------------------------
# CURRENCY SETTINGS
# ---------------------------------------------------------------------------

# Default currency used when the CSV does not provide one.
DEFAULT_CURRENCY = "NPR"

# Approximate fallback exchange rate.
#
# IMPORTANT:
# This is only a fallback conversion rate.
# If your CSV already contains NPR/USD prices, those values are returned
# without converting them.
#
# 1 USD ~= 140 NPR
#
# Change this value if you want to use another rate.
USD_TO_NPR = float(
    os.environ.get("USD_TO_NPR", "140")
)


# ---------------------------------------------------------------------------
# REQUIRED CSV COLUMNS
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "hotel_name",
    "latitude",
    "longitude",
    "rating",
    "price_per_night",
]


# ---------------------------------------------------------------------------
# HOTEL DATA CACHE
# ---------------------------------------------------------------------------

_hotels_df = None


# ---------------------------------------------------------------------------
# LOAD HOTEL DATA
# ---------------------------------------------------------------------------

def _load_hotels():
    """
    Load the hotel CSV once and cache it in memory.

    Expected CSV columns:

        hotel_name
        latitude
        longitude
        phone
        rating
        price_per_night
        booking_url
        destination
        address
        currency
        booking_status
        price_category
    """

    global _hotels_df

    if _hotels_df is not None:
        return _hotels_df

    if not os.path.exists(HOTEL_FILE):
        raise FileNotFoundError(
            f"Hotel data file not found: {HOTEL_FILE}"
        )

    df = pd.read_csv(HOTEL_FILE)

    # Normalize column names.
    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    # Check required columns.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Hotel CSV is missing required columns: "
            + ", ".join(missing_columns)
        )

    # Add optional columns if they don't exist.
    optional_defaults = {
        "phone": "",
        "booking_url": "",
        "destination": "",
        "address": "",
        "currency": DEFAULT_CURRENCY,
        "booking_status": "",
        "price_category": "",
    }

    for column, default_value in optional_defaults.items():
        if column not in df.columns:
            df[column] = default_value

    # Convert latitude/longitude to numeric.
    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )

    # Convert rating to numeric.
    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce",
    ).fillna(0)

    # Convert price to numeric.
    df["price_per_night"] = pd.to_numeric(
        df["price_per_night"],
        errors="coerce",
    ).fillna(0)

    # Remove rows without coordinates.
    df = df.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    # Clean text columns.
    text_columns = [
        "hotel_name",
        "destination",
        "address",
        "phone",
        "booking_url",
        "currency",
        "booking_status",
        "price_category",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # Normalize currency.
    df["currency"] = (
        df["currency"]
        .replace("", DEFAULT_CURRENCY)
        .str.upper()
    )

    _hotels_df = df.reset_index(drop=True)

    return _hotels_df


# ---------------------------------------------------------------------------
# CURRENCY HELPERS
# ---------------------------------------------------------------------------

def _normalize_currency(currency):
    """
    Normalize common currency names/symbols.

    Examples:

        Rs
        Rs.
        NPR
        ₨
        रू

    become:

        NPR

    USD / $ becomes USD.
    """

    if currency is None:
        return DEFAULT_CURRENCY

    currency = str(currency).strip().upper()

    if currency in {
        "RS",
        "RS.",
        "RUPEE",
        "RUPEES",
        "NPR",
        "₨",
        "रू",
    }:
        return "NPR"

    if currency in {
        "$",
        "USD",
        "US DOLLAR",
        "DOLLAR",
        "DOLLARS",
    }:
        return "USD"

    return currency or DEFAULT_CURRENCY


def _convert_currency(amount, from_currency, to_currency):
    """
    Convert between NPR and USD.

    Returns the original amount for unsupported currencies.

    This is intended for displaying hotel prices, not financial accounting.
    """

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return 0.0

    from_currency = _normalize_currency(from_currency)
    to_currency = _normalize_currency(to_currency)

    if from_currency == to_currency:
        return round(amount, 2)

    # NPR -> USD
    if from_currency == "NPR" and to_currency == "USD":
        if USD_TO_NPR <= 0:
            return round(amount, 2)

        return round(amount / USD_TO_NPR, 2)

    # USD -> NPR
    if from_currency == "USD" and to_currency == "NPR":
        return round(amount * USD_TO_NPR, 2)

    # Unsupported conversion.
    return round(amount, 2)


# ---------------------------------------------------------------------------
# DISTANCE
# ---------------------------------------------------------------------------

def _haversine_km(
    lat1,
    lon1,
    lat2,
    lon2,
):
    """
    Calculate real-world great-circle distance between two coordinates.

    Returns:
        distance in kilometers
    """

    R = 6371.0

    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(math.radians(lat1))
        *
        math.cos(math.radians(lat2))
        *
        math.sin(dlon / 2) ** 2
    )

    # Protect against tiny floating point errors.
    a = max(0.0, min(1.0, a))

    return 2 * R * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a),
    )


# ---------------------------------------------------------------------------
# IMAGE SERVICE
# ---------------------------------------------------------------------------

def _fetch_image_url(query):
    """
    Ask Django's image resolver for a relevant hotel image.

    Expected endpoint:

        GET /api/v1/images/resolve/?query=...

    If Django is unavailable, return the generic placeholder.
    """

    query = str(query or "").strip()

    if not query:
        return PLACEHOLDER_IMAGE

    try:
        url = (
            f"{DJANGO_API_URL.rstrip('/')}"
            "/images/resolve/"
        )

        response = requests.get(
            url,
            params={
                "query": query,
            },
            timeout=6,
        )

        if response.status_code == 200:
            data = response.json()

            image_url = data.get("url")

            if image_url:
                return image_url

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ):
        pass

    return PLACEHOLDER_IMAGE


# ---------------------------------------------------------------------------
# SAFE VALUE HELPER
# ---------------------------------------------------------------------------

def _safe_value(
    row,
    column,
    default=None,
):
    """
    Safely read a pandas row value.
    """

    try:
        value = row.get(column, default)

        if pd.isna(value):
            return default

        return value

    except Exception:
        return default


# ---------------------------------------------------------------------------
# HOTEL ROW -> API DICTIONARY
# ---------------------------------------------------------------------------

def _row_to_dict(
    row,
    distance_km=None,
    with_image=True,
    display_currency=None,
):
    """
    Convert one CSV row into a clean JSON-friendly dictionary.

    Supports both:

        NPR

    and:

        USD

    If display_currency is supplied, an additional converted price is
    returned.
    """

    hotel_name = str(
        _safe_value(
            row,
            "hotel_name",
            "",
        )
        or ""
    ).strip()

    destination = str(
        _safe_value(
            row,
            "destination",
            "",
        )
        or ""
    ).strip()

    address = str(
        _safe_value(
            row,
            "address",
            "",
        )
        or ""
    ).strip()

    phone = str(
        _safe_value(
            row,
            "phone",
            "",
        )
        or ""
    ).strip()

    booking_url = str(
        _safe_value(
            row,
            "booking_url",
            "",
        )
        or ""
    ).strip()

    booking_status = str(
        _safe_value(
            row,
            "booking_status",
            "",
        )
        or ""
    ).strip()

    price_category = str(
        _safe_value(
            row,
            "price_category",
            "",
        )
        or ""
    ).strip()

    currency = _normalize_currency(
        _safe_value(
            row,
            "currency",
            DEFAULT_CURRENCY,
        )
    )

    try:
        latitude = float(
            _safe_value(
                row,
                "latitude",
                0,
            )
        )
    except (TypeError, ValueError):
        latitude = 0.0

    try:
        longitude = float(
            _safe_value(
                row,
                "longitude",
                0,
            )
        )
    except (TypeError, ValueError):
        longitude = 0.0

    try:
        rating = float(
            _safe_value(
                row,
                "rating",
                0,
            )
        )
    except (TypeError, ValueError):
        rating = 0.0

    try:
        price_per_night = float(
            _safe_value(
                row,
                "price_per_night",
                0,
            )
        )
    except (TypeError, ValueError):
        price_per_night = 0.0

    result = {
        "hotel_name": hotel_name,
        "destination": destination,
        "address": address,

        "latitude": latitude,
        "longitude": longitude,

        "phone": phone,

        "rating": round(
            rating,
            2,
        ),

        "price_per_night": round(
            price_per_night,
            2,
        ),

        "currency": currency,

        "booking_status": booking_status,

        "booking_url": booking_url,

        "price_category": price_category,
    }

    # ---------------------------------------------------------------
    # Distance
    # ---------------------------------------------------------------

    if distance_km is not None:
        result["distance_km"] = round(
            float(distance_km),
            2,
        )

    # ---------------------------------------------------------------
    # Currency conversion
    # ---------------------------------------------------------------

    if display_currency:
        display_currency = _normalize_currency(
            display_currency
        )

        converted_price = _convert_currency(
            price_per_night,
            currency,
            display_currency,
        )

        result["display_price"] = converted_price

        result["display_currency"] = display_currency

        result["price_label"] = (
            f"{converted_price:.2f} "
            f"{display_currency}"
        )

    else:
        result["display_price"] = round(
            price_per_night,
            2,
        )

        result["display_currency"] = currency

        result["price_label"] = (
            f"{price_per_night:.2f} "
            f"{currency}"
        )

    # ---------------------------------------------------------------
    # Image
    # ---------------------------------------------------------------

    if with_image:
        result["image_url"] = _fetch_image_url(
            f"{hotel_name} {destination} Nepal hotel"
        )

    return result


# ---------------------------------------------------------------------------
# NEAREST HOTELS
# ---------------------------------------------------------------------------

def nearest_hotels(
    lat,
    lon,
    limit=10,
    with_images=True,
    display_currency=None,
):
    """
    Find hotels nearest to a latitude/longitude.

    Example:

        nearest_hotels(
            27.7172,
            85.3240,
            limit=10,
            display_currency="NPR",
        )

    Returns:
        [
            {
                "hotel_name": "...",
                "distance_km": 1.25,
                ...
            }
        ]
    """

    df = _load_hotels()

    try:
        lat = float(lat)
        lon = float(lon)
    except (
        TypeError,
        ValueError,
    ):
        return []

    try:
        limit = int(limit)
    except (
        TypeError,
        ValueError,
    ):
        limit = 10

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    df = df.copy()

    # Calculate distance.
    df["_distance_km"] = df.apply(
        lambda row: _haversine_km(
            lat,
            lon,
            row["latitude"],
            row["longitude"],
        ),
        axis=1,
    )

    # Closest hotels first.
    df = (
        df
        .sort_values("_distance_km")
        .head(limit)
    )

    return [
        _row_to_dict(
            row,
            row["_distance_km"],
            with_images,
            display_currency,
        )
        for _, row in df.iterrows()
    ]


# ---------------------------------------------------------------------------
# SEARCH HOTELS
# ---------------------------------------------------------------------------

def search_hotels(
    query,
    limit=10,
    with_images=True,
    display_currency=None,
):
    """
    Search hotels by:

        - hotel name
        - destination
        - address

    Examples:

        search_hotels("Pokhara")

        search_hotels("Lakeside")

        search_hotels("Kathmandu")

        search_hotels("Hotel Yak")

    Results are sorted by rating, highest first.
    """

    df = _load_hotels()

    query = str(
        query or ""
    ).strip().lower()

    if not query:
        return []

    try:
        limit = int(limit)
    except (
        TypeError,
        ValueError,
    ):
        limit = 10

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    # Escape regex characters so a user search doesn't accidentally
    # become a regular expression.
    import re

    query_pattern = re.escape(query)

    hotel_name_match = (
        df["hotel_name"]
        .str.lower()
        .str.contains(
            query_pattern,
            na=False,
            regex=True,
        )
    )

    destination_match = (
        df["destination"]
        .str.lower()
        .str.contains(
            query_pattern,
            na=False,
            regex=True,
        )
    )

    address_match = (
        df["address"]
        .str.lower()
        .str.contains(
            query_pattern,
            na=False,
            regex=True,
        )
    )

    mask = (
        hotel_name_match
        | destination_match
        | address_match
    )

    matches = df[mask].copy()

    # Highest-rated hotels first.
    matches = (
        matches
        .sort_values(
            "rating",
            ascending=False,
        )
        .head(limit)
    )

    return [
        _row_to_dict(
            row,
            None,
            with_images,
            display_currency,
        )
        for _, row in matches.iterrows()
    ]


# ---------------------------------------------------------------------------
# SEARCH BY CITY / DESTINATION
# ---------------------------------------------------------------------------

def hotels_by_city(
    city,
    limit=10,
    with_images=True,
    display_currency=None,
):
    """
    Convenience function for city/destination searches.

    Example:

        hotels_by_city("Pokhara")

        hotels_by_city("Kathmandu")

        hotels_by_city(
            "Pokhara",
            display_currency="USD",
        )
    """

    return search_hotels(
        city,
        limit=limit,
        with_images=with_images,
        display_currency=display_currency,
    )


# ---------------------------------------------------------------------------
# HOTEL PRICE CONVERSION
# ---------------------------------------------------------------------------

def hotel_price(
    hotel,
    display_currency="NPR",
):
    """
    Convert a hotel row/dictionary price into the requested currency.

    This is useful if another service already has a hotel dictionary.

    Example:

        hotel_price(
            {
                "price_per_night": 50,
                "currency": "USD",
            },
            "NPR",
        )

    Returns:

        {
            "price": 7000,
            "currency": "NPR"
        }
    """

    if not hotel:
        return {
            "price": 0.0,
            "currency": _normalize_currency(
                display_currency
            ),
        }

    amount = hotel.get(
        "price_per_night",
        hotel.get(
            "display_price",
            0,
        ),
    )

    currency = hotel.get(
        "currency",
        DEFAULT_CURRENCY,
    )

    display_currency = _normalize_currency(
        display_currency
    )

    converted = _convert_currency(
        amount,
        currency,
        display_currency,
    )

    return {
        "price": converted,
        "currency": display_currency,
    }


# ---------------------------------------------------------------------------
# GET ALL HOTEL DESTINATIONS
# ---------------------------------------------------------------------------

def hotel_destinations():
    """
    Return unique hotel destinations/cities.

    Example result:

        [
            "Kathmandu",
            "Pokhara",
            "Chitwan",
            ...
        ]
    """

    df = _load_hotels()

    destinations = (
        df["destination"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    destinations = [
        destination
        for destination in destinations.unique()
        if destination
    ]

    return sorted(
        destinations,
        key=str.lower,
    )


# ---------------------------------------------------------------------------
# BEST-RATED HOTELS
# ---------------------------------------------------------------------------

def top_rated_hotels(
    limit=10,
    with_images=True,
    display_currency=None,
):
    """
    Return the highest-rated hotels from the dataset.
    """

    df = _load_hotels()

    try:
        limit = int(limit)
    except (
        TypeError,
        ValueError,
    ):
        limit = 10

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    matches = (
        df
        .sort_values(
            "rating",
            ascending=False,
        )
        .head(limit)
    )

    return [
        _row_to_dict(
            row,
            None,
            with_images,
            display_currency,
        )
        for _, row in matches.iterrows()
    ]


# ---------------------------------------------------------------------------
# BUDGET-FRIENDLY HOTELS
# ---------------------------------------------------------------------------

def budget_hotels(
    limit=10,
    with_images=True,
    display_currency=None,
):
    """
    Return cheaper hotels from the dataset.

    Hotels are sorted by price per night.
    """

    df = _load_hotels()

    try:
        limit = int(limit)
    except (
        TypeError,
        ValueError,
    ):
        limit = 10

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    matches = (
        df
        .sort_values(
            "price_per_night",
            ascending=True,
        )
        .head(limit)
    )

    return [
        _row_to_dict(
            row,
            None,
            with_images,
            display_currency,
        )
        for _, row in matches.iterrows()
    ]


# ---------------------------------------------------------------------------
# CLEAR CACHE
# ---------------------------------------------------------------------------

def clear_hotel_cache():
    """
    Clear cached hotel CSV data.

    Useful during development if the CSV changes while Django is running.
    """

    global _hotels_df

    _hotels_df = None