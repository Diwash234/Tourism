"""
Utility helpers used across the tourist app:
  - Haversine distance calculation (used for "nearby" queries)
  - GeoIP lookup (fallback when the browser does not supply GPS coordinates)
  - Translation service wrapper (Google Translate API, with an automatic
    fallback to the free deep-translator library when no API key is set)
  - Email / SMS / Push notification senders
"""
import logging
import re
from math import radians, cos, sin, asin, sqrt
from django.db.models import Q

import requests
from django.conf import settings
from django.core.mail import send_mail
WIKIMEDIA_HEADERS = {
    "User-Agent": "TourismApp/1.0 (diwashacharyapast456@gmail.com)"
}

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Distance
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Great-circle distance between two points in kilometers.
    Returns None if any coordinate is missing.
    """

    if None in (lat1, lon1, lat2, lon2):
        return None

    try:
        lat1, lon1, lat2, lon2 = map(
            lambda v: radians(float(v)),
            [lat1, lon1, lat2, lon2]
        )

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            sin(dlat / 2) ** 2
            + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        )

        c = 2 * asin(sqrt(a))

        return 6371 * c

    except (TypeError, ValueError):
        return None



def bounding_box(lat, lon, radius_km):
    """Rough bounding box for a first-pass DB filter before precise haversine filtering."""
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.320 * cos(radians(float(lat))) or 1)
    return {
        "min_lat": float(lat) - lat_delta,
        "max_lat": float(lat) + lat_delta,
        "min_lon": float(lon) - lon_delta,
        "max_lon": float(lon) + lon_delta,
    }


# ---------------------------------------------------------------------------
# GeoIP (fallback location detection)
# ---------------------------------------------------------------------------
def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def geoip_lookup(ip_address):
    """
    Resolve an IP address to country/city/lat/lon using a free GeoIP HTTP
    provider (default: ip-api.com). Returns None on failure so callers can
    gracefully degrade.

    FIX: results are cached for 24h. The GeoIPMiddleware calls this for
    EVERY /api/ request, so without a cache a page firing many parallel
    requests triggered an external HTTP call each time (slow,
    rate-limit-prone).
    """
    if not ip_address or ip_address in ("127.0.0.1", "localhost"):
        return None

    from django.core.cache import cache

    cache_key = f"geoip:{ip_address}"
    sentinel = object()
    cached = cache.get(cache_key, sentinel)
    if cached is not sentinel:
        return cached

    try:
        url = settings.GEOIP_PROVIDER_URL.format(ip=ip_address)
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get("status") == "fail":
            cache.set(cache_key, None, 60 * 60 * 24)
            return None
        result = {
            "country": data.get("country", ""),
            "city": data.get("city", ""),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
        }
        cache.set(cache_key, result, 60 * 60 * 24)
        return result
    except (requests.RequestException, ValueError) as exc:
        logger.warning("GeoIP lookup failed for %s: %s", ip_address, exc)
        cache.set(cache_key, None, 60 * 60)
        return None


def resolve_location(request, gps_latitude=None, gps_longitude=None):
    """
    Location resolution strategy: browser GPS first, GeoIP fallback second.
    Returns a dict with latitude, longitude, country, city, source.
    """
    if gps_latitude is not None and gps_longitude is not None:
        return {
            "latitude": gps_latitude,
            "longitude": gps_longitude,
            "country": "",
            "city": "",
            "source": "gps",
        }

    ip = get_client_ip(request)
    geo = geoip_lookup(ip)
    if geo:
        geo["source"] = "geoip"
        return geo

    return {"latitude": None, "longitude": None, "country": "", "city": "", "source": ""}


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
def _translate_via_openai(text, target_language, source_language):
    """
    Returns translated text via the OpenAI API, or None if not configured/
    unreachable. Used as the first-choice translation tier when
    OPENAI_API_KEY is set — generally higher quality than Google Translate
    for nuanced tourism copy (descriptions, alerts), at a per-call cost.
    """
    if not settings.OPENAI_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Translate the user's text into the language with ISO code "
                            f"'{target_language}'{source_note}. Reply with ONLY the translated "
                            f"text, no explanations, no quotes."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("OpenAI translation failed, falling back: %s", exc)
        return None


def _translate_via_ml_service(text, target_language, source_language):
    """Returns translated text from the ML service, or None if unreachable/not yet trained."""
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/translation/translate-custom",
            json={"text": text, "target_language": target_language, "source_language": source_language},
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        translated = response.json().get("translated_text")
        # The ML service's pass-through fallback returns the text unchanged
        # when no local model is loaded yet — treat that as "not handled"
        # so we still fall through to Google/deep-translator.
        return translated if translated and translated != text else None
    except requests.RequestException as exc:
        logger.info("ML translation service unreachable, falling back: %s", exc)
        return None


def translate_text(text, target_language, source_language="auto"):
    """
    Translate `text` into `target_language`. Four tiers, tried in order:

      1. OpenAI (if OPENAI_API_KEY is configured) — generally the highest
         quality for nuanced tourism copy (descriptions, alerts).
      2. The ML teammate's local-language model (`{ML_SERVICE_URL}/translate-custom`),
         for languages Google Translate handles poorly (e.g. underrepresented
         local languages) — see ml-service/model/translation_engine.py.
         Tried before Google/deep-translator for languages listed in
         LOCAL_TRANSLATION_LANGUAGE_CODES (set in settings).
      3. Google Cloud Translation API, if GOOGLE_TRANSLATE_API_KEY is configured.
      4. The free deep-translator (Google Translate) library — always available,
         no credentials needed, so translation never fully breaks.
    """
    if not text:
        return text

    openai_result = _translate_via_openai(text, target_language, source_language)
    if openai_result is not None:
        return openai_result

    use_local_first = target_language in settings.LOCAL_TRANSLATION_LANGUAGE_CODES
    if use_local_first:
        local_result = _translate_via_ml_service(text, target_language, source_language)
        if local_result is not None:
            return local_result

    if settings.GOOGLE_TRANSLATE_API_KEY:
        try:
            response = requests.post(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": settings.GOOGLE_TRANSLATE_API_KEY},
                data={
                    "q": text,
                    "target": target_language,
                    "source": None if source_language == "auto" else source_language,
                    "format": "text",
                },
                timeout=5,
            )
            response.raise_for_status()
            return response.json()["data"]["translations"][0]["translatedText"]
        except (requests.RequestException, KeyError, IndexError) as exc:
            logger.warning("Google Translate API failed, falling back: %s", exc)

    if not use_local_first:
        # Wasn't tried yet above — try it now as a second-to-last resort.
        local_result = _translate_via_ml_service(text, target_language, source_language)
        if local_result is not None:
            return local_result

    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source=source_language, target=target_language).translate(text)
    except Exception as exc:  # noqa: BLE001 - translation is best-effort
        logger.error("Translation fallback failed: %s", exc)
        return text


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
def send_email_notification(to_email, subject, message):
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Email send failed to %s: %s", to_email, exc)
        return False


def send_sms_notification(to_number, message):
    """Sends an SMS via Twilio if credentials are configured; no-op otherwise."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER):
        logger.info("SMS not sent (Twilio not configured). Would send to %s: %s", to_number, message)
        return False
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=settings.TWILIO_FROM_NUMBER, to=str(to_number))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("SMS send failed to %s: %s", to_number, exc)
        return False


def issue_phone_verification(user):
    """
    Generate a 6-digit OTP, persist it as an SMSVerificationToken and send
    it via SMS (Twilio). The token is stored even when Twilio is not
    configured so the flow can be exercised locally (the code is logged by
    send_sms_notification in that case).

    FIX: this function was imported by views_auth.py but was missing from
    utils.py, which crashed the whole `tourist.urls` import chain
    (ImportError: cannot import name 'issue_phone_verification').
    """
    import secrets
    from datetime import timedelta

    from django.utils import timezone

    from .models import SMSVerificationToken

    code = f"{secrets.randbelow(1_000_000):06d}"
    SMSVerificationToken.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_sms_notification(
        user.phone_number,
        f"Your Tourism Portal verification code is {code}. It expires in 10 minutes.",
    )
    return code


def send_push_notification(device_tokens, title, message):
    """Sends a push notification via Firebase Cloud Messaging if configured."""
    if not settings.FCM_SERVER_KEY or not device_tokens:
        logger.info("Push not sent (FCM not configured). Would send to %s tokens: %s", len(device_tokens or []), title)
        return False
    try:
        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "registration_ids": device_tokens,
            "notification": {"title": title, "body": message},
        }
        response = requests.post(
            "https://fcm.googleapis.com/fcm/send", json=payload, headers=headers, timeout=5
        )
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.error("Push notification failed: %s", exc)
        return False


def notify_user(user, title, message, channel="in_app", related_alert=None):
    """Creates a Notification record and dispatches it over the requested channel."""
    from .models import Notification  # local import avoids circular import

    notification = Notification.objects.create(
        user=user, channel=channel, title=title, message=message, related_alert=related_alert
    )

    sent = False
    if channel == "email":
        sent = send_email_notification(user.email, title, message)
    elif channel == "sms" and user.phone_number:
        sent = send_sms_notification(user.phone_number, message)
    elif channel == "push":
        tokens = list(user.device_tokens.values_list("token", flat=True))
        sent = send_push_notification(tokens, title, message)
    else:
        sent = True  # in-app notifications are considered "sent" once stored

    notification.is_sent = sent
    notification.save(update_fields=["is_sent"])
    return notification


# ---------------------------------------------------------------------------
# ML microservice client
# ---------------------------------------------------------------------------
def _build_personalized_interest_string(user, fallback_interest=""):
    """
    THE ACTUAL BUG this fixes: get_ml_recommendations() used to send a
    fixed "nearby destinations around latitude X longitude Y" string to
    the ML service every time -- the recommendation engine is a real
    TF-IDF/cosine-similarity text matcher (see model/recommendation/
    recommendation_engine.py, that part was always fine), but numeric
    coordinates carry almost no meaning to a text vectorizer trained on
    destination names/categories/types. Every user, every request,
    produced essentially the same noisy near-identical top-N regardless
    of who was asking -- matching exactly "same recommendation every
    time" as reported.

    Also: the frontend-supplied `interest` query param was being read by
    the Django view but never forwarded here at all -- silently dropped.

    Fix: build a REAL text query from what the user has actually shown
    interest in -- their most recent viewed (VisitHistory) and favorited
    (Favorite) destinations' names/categories -- so two different users
    genuinely get two different results, and the same user's results
    change over time as they interact more. Falls back to the frontend's
    typed interest, then a generic default, only if there's truly no
    history yet (e.g. a brand new user).
    """
    if fallback_interest:
        return fallback_interest

    if not user or not getattr(user, "is_authenticated", False):
        return "popular destinations Nepal"

    from .models import VisitHistory, Favorite

    recent_visits = list(
        VisitHistory.objects.filter(user=user).select_related("destination", "destination__category")
        .order_by("-viewed_at")[:5]
    )
    favorites = list(
        Favorite.objects.filter(user=user).select_related("destination", "destination__category")
        .order_by("-created_at")[:5]
    )

    interest_terms = []
    for record in recent_visits + favorites:
        destination = record.destination
        if destination.category:
            interest_terms.append(destination.category.name)
        interest_terms.append(destination.name)

    if not interest_terms:
        return "popular destinations Nepal"

    # Most-repeated terms first (categories the user keeps coming back
    # to should weigh more than a single destination visited once).
    from collections import Counter
    ranked = [term for term, _ in Counter(interest_terms).most_common(8)]
    return " ".join(ranked)


def get_ml_recommendations(user=None, latitude=None, longitude=None, top_n=5, interest=""):
    """
    Calls the recommendation engine (FastAPI ml_service) for
    personalized recommendations. `interest` is the frontend-typed
    search text if the user provided one; if blank, a real personalized
    query is built from the user's actual visit/favorite history (see
    _build_personalized_interest_string above) instead of the old
    fixed lat/lon string that produced identical results for everyone.

    Returns a list of recommendation dicts, or [] if the ML service is
    unreachable -- callers should fall back to a simple heuristic (e.g.
    top-rated destinations) in that case, never hard-fail the request.
    """
    query_text = _build_personalized_interest_string(user, interest)

    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/recommendation",
            json={"interest": query_text, "limit": top_n},
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("recommendations", [])
    except requests.RequestException as exc:
        logger.warning("ML service unreachable, falling back: %s", exc)
        return []


def request_ml_image_analysis(destination_id, image_url):
    """
    Fires an (async, best-effort) request asking the ML service to analyze a
    newly submitted destination's cover photo. The ML service is expected to
    POST its result back to the `/api/v1/ml/results/` webhook once done,
    rather than blocking this request on the analysis itself.
    """
    try:
        requests.post(
            f"{settings.ML_SERVICE_URL}/analyze-image",
            json={
                "destination_id": destination_id,
                "image_url": image_url,
                "webhook_url": f"{settings.BACKEND_URL}/api/v1/ml/results/",
                "webhook_secret": settings.ML_WEBHOOK_SECRET,
            },
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        return True
    except requests.RequestException as exc:
        logger.info("ML image analysis request skipped (service unreachable): %s", exc)
        return False


def get_ml_safety_prediction(latitude, longitude, city=None, country=None):
    """
    Calls {ML_SERVICE_URL}/predict-safety for a risk assessment of a given
    location. Returns None if the ML service is unreachable — callers
    should degrade gracefully (e.g. hide the safety badge) rather than fail.
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/risk/predict-safety",
            json={
                "latitude": float(latitude), "longitude": float(longitude),
                "city": city, "country": country,
            },
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("ML safety prediction unreachable: %s", exc)
        return None


def get_ml_budget_prediction(city=None, country=None, days=3, travelers=1, budget_level="mid",
                             latitude=None, longitude=None, user_latitude=None, user_longitude=None):
    """
    Calls {ML_SERVICE_URL}/budget/predict-budget for an estimated trip cost.
    Returns None if the ML service is unreachable.

    FIX: signature extended to accept/forward destination coordinates and
    the traveler's own coordinates — views_ml.py was passing them and the
    ML service expects them (see ml_service/api/budget.py BudgetRequest).
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/budget/predict-budget",
            json={
                "city": city, "country": country,
                "latitude": latitude, "longitude": longitude,
                "user_latitude": user_latitude, "user_longitude": user_longitude,
                "days": days, "travelers": travelers, "budget_level": budget_level,
            },
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("ML budget prediction unreachable: %s", exc)
        return None


def get_ml_best_route(start_latitude, start_longitude, end_latitude, end_longitude, route_type="fastest"):
    """
    Calls {ML_SERVICE_URL}/routes/best-route for a routed path (OSM-based
    once the ML teammate's road graph is loaded; straight-line fallback
    until then). Returns None if the ML service is unreachable.

    FIX: added `route_type` — views_compat.py passes it and the ML service
    (BestRouteRequest) accepts it.
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/routes/best-route",
            json={
                "start_latitude": float(start_latitude), "start_longitude": float(start_longitude),
                "end_latitude": float(end_latitude), "end_longitude": float(end_longitude),
                "route_type": route_type,
            },
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("ML routing service unreachable: %s", exc)
        return None


def get_ml_supported_languages():
    """Calls {ML_SERVICE_URL}/languages — used by the sync_languages management command."""
    try:
        response = requests.get(f"{settings.ML_SERVICE_URL}/languages", timeout=settings.ML_SERVICE_TIMEOUT)
        response.raise_for_status()
        return response.json().get("languages", [])
    except requests.RequestException as exc:
        logger.warning("ML languages endpoint unreachable: %s", exc)
        return []


# ---------------------------------------------------------------------------
# External data sources: weather, places, and images
# Every function here returns None / [] on failure rather than raising, so a
# missing API key or a downed third-party service never breaks the request
# that called it — callers just get less-enriched data back.
# ---------------------------------------------------------------------------
def get_current_weather(latitude, longitude):
    """OpenWeatherMap current conditions for a point. Returns None if not configured/unreachable."""
    if not settings.OPENWEATHER_API_KEY:
        return None
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": latitude, "lon": longitude,
                "appid": settings.OPENWEATHER_API_KEY, "units": "metric",
            },
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "temperature_c": data["main"]["temp"],
            "feels_like_c": data["main"]["feels_like"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed_ms": data["wind"]["speed"],
        }
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("OpenWeather lookup failed: %s", exc)
        return None


def overpass_search_nearby(latitude, longitude, radius_m=2000, tourism_only=True):
    """
    OpenStreetMap Overpass API — free, no key required. Returns raw OSM
    tourism/amenity nodes near a point, useful for discovering places not
    yet in your own Destination table.
    """
    tag_filter = 'node["tourism"]' if tourism_only else 'node["tourism"];node["amenity"]'
    query = f"""
    [out:json][timeout:10];
    (
      {tag_filter}(around:{radius_m},{latitude},{longitude});
    );
    out body;
    """
    try:
        response = requests.post(settings.OVERPASS_API_URL, data={"data": query}, timeout=12)
        response.raise_for_status()
        elements = response.json().get("elements", [])
        return [
            {
                "osm_id": el["id"],
                "name": el.get("tags", {}).get("name", "Unnamed"),
                "type": el.get("tags", {}).get("tourism") or el.get("tags", {}).get("amenity"),
                "latitude": el.get("lat"),
                "longitude": el.get("lon"),
                "tags": el.get("tags", {}),
            }
            for el in elements
        ]
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Overpass API lookup failed: %s", exc)
        return []


def geonames_reverse_geocode(latitude, longitude):
    """GeoNames — resolves a point to nearest city/country. Requires a free registered username."""
    if not settings.GEONAMES_USERNAME:
        return None
    try:
        response = requests.get(
            "http://api.geonames.org/findNearbyPlaceNameJSON",
            params={"lat": latitude, "lng": longitude, "username": settings.GEONAMES_USERNAME},
            timeout=5,
        )
        response.raise_for_status()
        results = response.json().get("geonames", [])
        if not results:
            return None
        place = results[0]
        return {"city": place.get("name"), "country": place.get("countryName"), "admin_area": place.get("adminName1")}
    except (requests.RequestException, ValueError, IndexError) as exc:
        logger.warning("GeoNames lookup failed: %s", exc)
        return None


def google_places_search(query, latitude=None, longitude=None):
    """Google Places API (Text Search) — commercial, requires billing enabled."""
    if not settings.GOOGLE_PLACES_API_KEY:
        return []
    try:
        params = {"query": query, "key": settings.GOOGLE_PLACES_API_KEY}
        if latitude is not None and longitude is not None:
            params["location"] = f"{latitude},{longitude}"
            params["radius"] = 5000
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json", params=params, timeout=8
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {
                "place_id": r["place_id"], "name": r["name"],
                "address": r.get("formatted_address", ""), "rating": r.get("rating"),
                "latitude": r["geometry"]["location"]["lat"], "longitude": r["geometry"]["location"]["lng"],
                "photo_reference": (r.get("photos") or [{}])[0].get("photo_reference"),
            }
            for r in results
        ]
    except (requests.RequestException, KeyError) as exc:
        logger.warning("Google Places search failed: %s", exc)
        return []


def foursquare_search_nearby(latitude, longitude, radius_m=2000, query=None):
    """Foursquare Places API — requires a free-tier API key."""
    if not settings.FOURSQUARE_API_KEY:
        return []
    try:
        params = {"ll": f"{latitude},{longitude}", "radius": radius_m}
        if query:
            params["query"] = query
        response = requests.get(
            "https://api.foursquare.com/v3/places/search",
            params=params,
            headers={"Authorization": settings.FOURSQUARE_API_KEY, "Accept": "application/json"},
            timeout=8,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {
                "fsq_id": r["fsq_id"], "name": r["name"],
                "categories": [c["name"] for c in r.get("categories", [])],
                "address": r.get("location", {}).get("formatted_address", ""),
                "distance_m": r.get("distance"),
            }
            for r in results
        ]
    except (requests.RequestException, KeyError) as exc:
        logger.warning("Foursquare search failed: %s", exc)
        return []


def fetch_unsplash_photo(query):
    """
    Unsplash API — free tier available. Returns a single best-match photo
    with the attribution Unsplash's license requires you to display.
    """
    if not settings.UNSPLASH_ACCESS_KEY:
        return None
    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1},
            headers={"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"},
            timeout=6,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return None
        photo = results[0]
        return {
            "url": photo["urls"]["regular"],
            "attribution": f'Photo by {photo["user"]["name"]} on Unsplash',
            "source_link": photo["links"]["html"],
        }
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("Unsplash lookup failed: %s", exc)
        return None
def fetch_wikimedia_photos(queries, limit=5):
    """
    Search Wikimedia Commons for multiple Nepal destination photos.
    Returns multiple images so users can choose.
    """

    photos = []

    bad_keywords = [
        "map",
        "maps",
        "diagram",
        "logo",
        "flag",
        "location",
        "plan",
        "route",
        "svg",
        "icon",
        "coat of arms",
        "emblem",
    ]

    for query in queries:

        try:
            response = requests.get(
                settings.WIKIMEDIA_API_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f"{query} Nepal landscape photo",
                    "srnamespace": 6,
                    "srlimit": 5,
                    "format": "json",
                },
                headers=WIKIMEDIA_HEADERS,
                timeout=8,
            )

            response.raise_for_status()

            hits = (
                response.json()
                .get("query", {})
                .get("search", [])
            )


            for hit in hits:

                title = hit["title"]

                lower_title = title.lower()

                if any(word in lower_title for word in bad_keywords):
                    continue


                info = requests.get(
                    settings.WIKIMEDIA_API_URL,
                    params={
                        "action": "query",
                        "titles": title,
                        "prop": "imageinfo",
                        "iiprop": "url|extmetadata",
                        "format": "json",
                    },
                    headers=WIKIMEDIA_HEADERS,
                    timeout=8,
                )

                info.raise_for_status()

                pages = (
                    info.json()
                    .get("query", {})
                    .get("pages", {})
                )

                page = next(iter(pages.values()), {})

                image = (
                    page.get("imageinfo") or [{}]
                )[0]

                url = image.get("url")

                if not url:
                    continue

                # FIXED: this used to only block .svg by extension, plus
                # a title-text keyword check (bad_keywords, above) --
                # neither catches a file whose *title* looks fine but
                # is actually a PDF. Confirmed live against the real
                # database: 147 rows across dozens of destinations had
                # a PDF (mostly "Wiki Loves Earth jury report" documents
                # whose text happened to mention a place name) stored as
                # that destination's "photo". Now allow-lists real image
                # extensions instead of block-listing one bad one.
                url_lower = url.lower()

                if not re.search(r"\.(jpe?g|png|webp|gif)(?:$|\?)", url_lower):
                    continue

                if any(keyword in url_lower for keyword in ("map", "flag", "logo", "icon")):
                    continue

                artist = (
                    image
                    .get("extmetadata", {})
                    .get("Artist", {})
                    .get("value", "Wikimedia contributor")
                )

                photos.append(
                    {
                        "url": url,
                        "title": title,
                        "attribution": (
                            f"Photo: {artist} "
                            "(Wikimedia Commons)"
                        ),
                    }
                )


                if len(photos) >= limit:
                    return photos


        except Exception as exc:
            logger.warning(
                "Wikimedia search failed for %s : %s",
                query,
                exc
            )


    return photos

def _photo_search_queries(destination):
    """
    Build clean Wikimedia search queries without adding None values.

    FIXED: the fallback queries used to drop destination.name entirely,
    searching only "{district} Nepal" or "{province} Nepal" once the
    full query came up empty. Confirmed live: for "Arun Valley"
    (district="Makalu Region", no city/province), that fell back to
    searching just "Makalu Region Nepal" and matched an 1921 geological
    survey illustration of the *Everest* region -- topically nearby,
    completely wrong place. Every query now keeps destination.name, so
    a broader fallback can widen the geographic context but can never
    drop the actual place being searched for.
    """

    queries = []

    parts = [destination.name]

    if getattr(destination, "city", None):
        parts.append(destination.city)

    if getattr(destination, "district", None):
        parts.append(destination.district)

    if getattr(destination, "province", None):
        parts.append(destination.province)

    if getattr(destination, "country", None):
        parts.append(destination.country)
    else:
        parts.append("Nepal")

    queries.append(" ".join(parts))

    if getattr(destination, "city", None):
        queries.append(f"{destination.name} {destination.city} Nepal")

    if getattr(destination, "district", None):
        queries.append(f"{destination.name} {destination.district} Nepal")

    if getattr(destination, "province", None):
        queries.append(f"{destination.name} {destination.province} Nepal")

    queries.append(f"{destination.name} Nepal")

    return list(dict.fromkeys(queries))



import threading

# ADDED: this function was called from serializers.py (get_cover_image_url,
# both DestinationListSerializer and the detail serializer) and even had
# an explanatory comment above the call site describing exactly what it
# should do -- but it was never actually defined anywhere in this file.
# That's not a small bug: `from .utils import ... queue_cover_photo_fetch`
# in serializers.py raised ImportError at Django startup, which means
# tourist/urls.py (which imports views.py -> serializers.py) failed to
# load at all, taking down every single API endpoint under /api/v1/ --
# not just images, ALL destinations, hotels, everything, on every page
# that hits the API. This is the actual root cause behind "no destination
# or images shown despite having API keys in .env" -- the keys were
# never the problem, the backend wasn't serving anything at all.
#
# Implementation: fire-and-forget background thread that calls the
# existing synchronous ensure_cover_photo() off the request thread, so
# a list-page request returns immediately (this destination just won't
# have a photo on THIS response) while the fetch completes in the
# background and is picked up on the next request, exactly as the
# removed comment already promised. Deduplicates concurrent calls for
# the same destination (a list endpoint can serialize the same
# destination via multiple overlapping requests) with a simple guarded
# in-process set -- intentionally not Celery/Redis, since no task queue
# is configured anywhere in this project (checked settings.py); adding
# one is a bigger, separate infrastructure decision.
_pending_cover_photo_fetches = set()
_pending_cover_photo_fetches_lock = threading.Lock()


def queue_cover_photo_fetch(destination):
    """
    Non-blocking version of ensure_cover_photo(): schedules the fetch on
    a background thread and returns immediately. Safe to call many times
    for the same destination -- duplicate concurrent calls are skipped.
    """
    destination_id = destination.pk
    if destination_id is None:
        return

    with _pending_cover_photo_fetches_lock:
        if destination_id in _pending_cover_photo_fetches:
            return
        _pending_cover_photo_fetches.add(destination_id)

    def _run():
        from django.db import close_old_connections
        try:
            # Background threads need their own DB connection state --
            # reusing the request thread's connection here would be a
            # real (if intermittent) source of "database is locked" /
            # threading errors under load.
            close_old_connections()
            ensure_cover_photo(destination)
        except Exception:  # noqa: BLE001 -- a failed background fetch must never surface as a 500 on some unrelated later request
            logger.exception("Background cover photo fetch failed for destination id=%s", destination_id)
        finally:
            close_old_connections()
            with _pending_cover_photo_fetches_lock:
                _pending_cover_photo_fetches.discard(destination_id)

    threading.Thread(target=_run, daemon=True).start()


import csv
import os
import sys

# ADDED: mirrors the sys.path setup already used successfully in
# chatbot/views.py to import from the sibling ml_service package
# (Tourism/tourist/utils.py -> .. -> ml_service).
_ML_SERVICE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ML_SERVICE_ROOT not in sys.path:
    sys.path.append(_ML_SERVICE_ROOT)

_risk_rows_cache = None


def _load_risk_rows():
    """
    Lazily loads dataset/risk_features.csv once per process. Same dataset
    ml_service/training/train_risk_model.py trains on -- this just reads
    it directly rather than requiring a live model call, since the ask
    here is "nearest known risk data point", not a prediction.
    """
    global _risk_rows_cache
    if _risk_rows_cache is not None:
        return _risk_rows_cache

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset", "risk_features.csv")
    rows = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    lat = row.get("Latitude")
                    lon = row.get("Longitude")
                    if not lat or not lon:
                        continue
                    rows.append({**row, "Latitude": float(lat), "Longitude": float(lon)})
                except (KeyError, ValueError, TypeError):
                    continue
    except FileNotFoundError:
        logger.warning("risk_features.csv not found at %s -- get_local_risk_summary will return None", csv_path)
    _risk_rows_cache = rows
    return rows


def get_local_risk_summary(destination, max_distance_km=50):
    """
    ADDED: called from DestinationDetailSerializer.get_risk_summary(),
    but never actually implemented (see queue_cover_photo_fetch's
    docstring above for the wider story -- several functions were
    referenced and called from serializers.py without ever being
    written, which broke Django's startup entirely).

    Finds the nearest row in dataset/risk_features.csv to this
    destination's coordinates and returns it as a plain dict, or None
    if nothing is within max_distance_km (avoids attaching, say,
    Everest Base Camp's earthquake risk to a destination 300km away
    just because it was the closest row in the file).
    """
    if destination.latitude is None or destination.longitude is None:
        return None

    rows = _load_risk_rows()
    if not rows:
        return None

    best_row, best_distance = None, None
    for row in rows:
        distance = haversine_distance(
            float(destination.latitude), float(destination.longitude),
            row["Latitude"], row["Longitude"],
        )
        if distance is None:
            continue
        if best_distance is None or distance < best_distance:
            best_row, best_distance = row, distance

    if best_row is None or best_distance > max_distance_km:
        return None

    return {
        "nearest_reference_place": best_row.get("Place"),
        "district": best_row.get("District"),
        "distance_km": round(best_distance, 1),
        "landslide": best_row.get("landslide"),
        "avalanche": best_row.get("avalanche"),
        "flood": best_row.get("flood"),
        "earthquake_damage": best_row.get("earthquake_damage"),
        "emergency_risk": best_row.get("Emergency_Risk"),
        "natural_disaster_risk": best_row.get("Natural_Disaster_Risk"),
        "tourism_risk_index": best_row.get("Tourism_Risk_Index"),
        "risk_category": best_row.get("Risk_Category"),
    }


def get_nearby_emergency_services(destination, limit=5):
    """
    ADDED: called from DestinationDetailSerializer.get_nearby_emergency_services(),
    same missing-implementation story as get_local_risk_summary() above.

    Wraps the already-working ml_service.services.emergency_service.nearest_facilities()
    (the same function chatbot/views.py already imports and uses
    successfully) rather than duplicating hospital/police CSV-loading
    logic a second time here.
    """
    if destination.latitude is None or destination.longitude is None:
        return []

    try:
        from ml_service.services.emergency_service import nearest_facilities
    except ImportError:
        logger.exception("Could not import ml_service.services.emergency_service.nearest_facilities")
        return []

    try:
        results = nearest_facilities(
            float(destination.latitude), float(destination.longitude), limit=limit
        )
        # DEFENSIVE: nearest_facilities() reads hospital/police CSVs via
        # pandas, which leaves NaN in any column outside lat/lon that's
        # blank in the source CSV (only lat/lon get pandas.dropna()'d in
        # emergency_service.py). A raw NaN float can't be JSON-encoded
        # ("Out of range float values are not JSON compliant: nan"),
        # confirmed against a real record while testing this. Not
        # touching emergency_service.py itself since chatbot/views.py
        # already depends on its current behavior; just sanitizing the
        # copy returned through this new endpoint.
        import math

        def _clean(value):
            if isinstance(value, float) and math.isnan(value):
                return None
            return value

        return [{k: _clean(v) for k, v in record.items()} for record in results]
    except Exception:  # noqa: BLE001 -- a broken CSV/lookup must not 500 a destination detail page
        logger.exception("get_nearby_emergency_services failed for destination id=%s", destination.pk)
        return []


def ensure_cover_photo(destination):
    """
    Automatically finds multiple Wikimedia/Unsplash photos
    for any Nepal destination.
    """

    from .models import DestinationImage


    # already exists
    if destination.cover_image or destination.gallery.exists():
        return None


    existing = destination.gallery.filter(
        is_cover=True
    ).first()

    if existing:
        return existing



    # Generate many search queries
    queries = _photo_search_queries(destination)


    logger.info(
        "Searching Wikimedia images: %s",
        queries
    )


    external_photos = []


    # Try Unsplash first
    if queries:
        unsplash = fetch_unsplash_photo(
            queries[0]
        )

        if unsplash:
            external_photos.append(
                unsplash
            )


    # Get multiple Wikimedia images
    wikimedia = fetch_wikimedia_photos(
        queries,
        limit=5
    )


    if wikimedia:
        external_photos.extend(
            wikimedia
        )


    if not external_photos:
        logger.warning(
            "No photos found for %s",
            destination.name
        )

        return None



    created_photo = None


    # Save all images
    for index, external in enumerate(external_photos):

        if not external.get("url"):
            continue


        source = (
            DestinationImage.Source.UNSPLASH
            if "Unsplash" in external.get("attribution", "")
            else DestinationImage.Source.WIKIMEDIA
        )

        # ADDED: Wikimedia file titles are contributor-written
        # descriptions of the actual photographed subject -- a
        # reasonably reliable signal that the photo genuinely depicts
        # the named place. Unsplash search is keyword/semantic
        # similarity over generic stock photography with no location
        # verification at all -- for a well-known place ("Everest Base
        # Camp") that's usually fine, but for a hyperlocal, obscure
        # name ("Pame Picnic Site", "balbalika picnic side") Unsplash
        # has no possibility of a genuine photo of that exact spot, so
        # whatever it returns is a generic stand-in at best. Labeling
        # this honestly in the caption itself (not just relying on a
        # frontend badge) means it stays correct even if queried
        # directly or shown somewhere the frontend badge logic doesn't
        # reach.
        caption = external.get("caption", "")
        if source == DestinationImage.Source.UNSPLASH and not caption:
            caption = f"Representative photo -- {destination.name} area"

        photo = DestinationImage.objects.create(
            destination=destination,
            external_url=external["url"],
            caption=caption,
            attribution=external.get(
                "attribution",
                ""
            ),
            source=source,

            # first image becomes cover
            is_cover=(index == 0),
        )


        if index == 0:
            created_photo = photo



    logger.info(
        "Created %s images for %s",
        len(external_photos),
        destination.name
    )


    return created_photo

from .models import DestinationImage

from .models import Destination

def find_nearby_places(latitude, longitude, place_type=None, radius_km=10):
    

    nearby = []

    try:
        radius_km = float(radius_km)
    except (TypeError, ValueError):
        radius_km = 10.0

    queryset = Destination.objects.all()

    # Optional category filtering
    if place_type:
        try:
            queryset = queryset.filter(
                category__name__iexact=place_type
            )
        except Exception:
            # If category relation does not exist,
            # continue without filtering
            pass

    for destination in queryset:

        if destination.latitude is None or destination.longitude is None:
            continue

        distance = haversine_distance(
            latitude,
            longitude,
            destination.latitude,
            destination.longitude,
        )

        if distance is not None and distance <= radius_km:
            destination.distance = round(distance, 2)
            nearby.append(destination)

    return sorted(
        nearby,
        key=lambda item: item.distance
    )

def get_destination_photos(destination):
    """
    Returns destination images.
    Creates fallback image first if destination has no images.
    """

    ensure_cover_photo(destination)

    return list(destination.gallery.all())


def register_photo_view(photo):
    """
    Increase image view count and check promotion.
    """

    from django.db.models import F
    from .models import DestinationImage

    DestinationImage.objects.filter(
        pk=photo.pk
    ).update(
        view_count=F("view_count") + 1
    )

    photo.refresh_from_db(fields=["view_count"])

    maybe_promote_photo(photo)


def maybe_promote_photo(photo):
    """
    Automatically promotes popular user images.
    """

    from .models import DestinationImage

    if (
        photo.source == DestinationImage.Source.ADMIN
        or photo.view_count < settings.PHOTO_PROMOTION_IMPRESSION_THRESHOLD
    ):
        return

    current_cover = (
        photo.destination.gallery
        .filter(is_cover=True)
        .exclude(pk=photo.pk)
        .first()
    )

    if current_cover and current_cover.view_count >= photo.view_count:
        return

    DestinationImage.objects.filter(
        destination=photo.destination
    ).update(
        is_cover=False
    )

    photo.is_cover = True
    photo.is_promoted = True

    photo.save(
        update_fields=[
            "is_cover",
            "is_promoted",
        ]
    )

    logger.info(
        "Promoted photo %s as cover image for %s",
        photo.pk,
        photo.destination.name,
    )

def get_disaster_helplines(destination=None, country=None):
    """
    Return {"active_alert": {...} or None, "helplines": [...]} for the given
    destination (falls back to a bare country string). Used by the
    destination "essentials" bundle to surface emergency numbers whenever a
    disaster alert is active in the area.

    FIX: this function previously returned a raw QuerySet while both
    callers expect a dict — every request to
    /destinations/{slug}/essentials/ crashed with
    "TypeError: QuerySet indices must be integers or slices, not str".
    """
    from .models import Alert, EmergencyContact
    from .serializers import EmergencyContactSerializer

    city = getattr(destination, "city", None)
    dest_country = getattr(destination, "country", None) or country

    alert_filters = Q()
    if city:
        alert_filters = Q(city__iexact=city)
    elif dest_country:
        alert_filters = Q(country__iexact=dest_country)

    active_alert = (
        Alert.objects.filter(is_active=True)
        .filter(alert_filters)
        .order_by("-severity", "-created_at")
        .first()
    )

    contact_qs = EmergencyContact.objects.all()
    if city:
        contact_qs = contact_qs.filter(Q(city__iexact=city) | Q(city=""))
    elif dest_country:
        contact_qs = contact_qs.filter(Q(country__iexact=dest_country) | Q(country=""))

    return {
        "active_alert": (
            {
                "alert_type": active_alert.alert_type,
                "severity": active_alert.severity,
                "title": active_alert.title,
                "description": active_alert.description,
            }
            if active_alert
            else None
        ),
        "helplines": EmergencyContactSerializer(contact_qs, many=True).data,
    }