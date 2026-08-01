"""
Utility helpers used across the tourist app:
  - Haversine distance calculation (used for "nearby" queries)
  - GeoIP lookup (fallback when the browser does not supply GPS coordinates)
  - Translation service wrapper (Google Translate API, with an automatic
    fallback to the free deep-translator library when no API key is set)
  - Email / SMS / Push notification senders
"""
import logging
from datetime import timedelta
from math import radians, cos, sin, asin, sqrt
from django.db.models import Q
from django.utils import timezone

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
    """
    if not ip_address or ip_address in ("127.0.0.1", "localhost"):
        return None
    try:
        url = settings.GEOIP_PROVIDER_URL.format(ip=ip_address)
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get("status") == "fail":
            return None
        return {
            "country": data.get("country", ""),
            "city": data.get("city", ""),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
        }
    except (requests.RequestException, ValueError) as exc:
        logger.warning("GeoIP lookup failed for %s: %s", ip_address, exc)
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



def _translate_via_gemini(text, target_language, source_language):
    """
    Returns translated text via Google's Gemini API, or None if not
    configured/unreachable. Same shape as _translate_via_openai --
    slots into the same tiered chain.
    """
    if not settings.GEMINI_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
            params={"key": settings.GEMINI_API_KEY},
            json={
                "contents": [{
                    "parts": [{
                        "text": (
                            f"Translate the following text into the language with ISO code "
                            f"'{target_language}'{source_note}. Reply with ONLY the translated "
                            f"text, no explanations, no quotes.\n\n{text}"
                        )
                    }]
                }],
                "generationConfig": {"temperature": 0.2},
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("Gemini translation failed, falling back: %s", exc)
        return None


def _translate_via_groq(text, target_language, source_language):
    """
    Returns translated text via Groq's chat completion API (OpenAI-compatible
    format), or None if not configured/unreachable.
    """
    if not settings.GROQ_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": settings.GROQ_MODEL,
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
        logger.warning("Groq translation failed, falling back: %s", exc)
        return None


def translate_text(text, target_language, source_language="auto", provider="auto"):
    """
    Translate `text` into `target_language`.

    provider: "auto" (default -- tiered fallback below), or an explicit
        choice: "gemini", "groq", "openai" (all three = "AI-enhanced
        contextual translation" per the original spec), or "standard"
        (skips straight to Google/deep-translator, no AI model involved).

    Automatic tiers, tried in order when provider="auto":
      1. Gemini (if GEMINI_API_KEY is configured)
      2. Groq (if GROQ_API_KEY is configured)
      3. OpenAI (if OPENAI_API_KEY is configured) — generally the highest
         quality for nuanced tourism copy (descriptions, alerts).
      4. The ML teammate's local-language model (`{ML_SERVICE_URL}/translate-custom`),
         for languages Google Translate handles poorly (e.g. underrepresented
         local languages) — see ml-service/model/translation_engine.py.
         Tried before Google/deep-translator for languages listed in
         LOCAL_TRANSLATION_LANGUAGE_CODES (set in settings).
      5. Google Cloud Translation API, if GOOGLE_TRANSLATE_API_KEY is configured.
      6. The free deep-translator (Google Translate) library — always available,
         no credentials needed, so translation never fully breaks.
    """
    if not text:
        return text

    if provider == "standard":
        pass  # skip straight past all AI tiers below
    elif provider in ("gemini", "groq", "openai"):
        result = {
            "gemini": _translate_via_gemini,
            "groq": _translate_via_groq,
            "openai": _translate_via_openai,
        }[provider](text, target_language, source_language)
        if result is not None:
            return result
        # Explicit provider failed/unconfigured -- fall through to the
        # rest of the chain rather than returning nothing.
    else:
        gemini_result = _translate_via_gemini(text, target_language, source_language)
        if gemini_result is not None:
            return gemini_result

        groq_result = _translate_via_groq(text, target_language, source_language)
        if groq_result is not None:
            return groq_result

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
    Generates a 6-digit OTP, stores it as an SMSVerificationToken, and
    sends it via send_sms_notification() above. Mirrors
    _issue_email_verification()'s pattern in views_auth.py.
    """
    import random
    from .models import SMSVerificationToken

    code = f"{random.randint(0, 999999):06d}"
    token = SMSVerificationToken.objects.create(
        user=user, code=code, expires_at=timezone.now() + timedelta(minutes=10)
    )
    send_sms_notification(
        user.phone_number,
        f"Your Tourism Portal verification code is {code}. It expires in 10 minutes.",
    )
    return token


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
def get_ml_recommendations(user=None, latitude=None, longitude=None, top_n=5):
    """
    Calls the teammate's ML microservice (FastAPI, running separately —
    see /ml-service) for personalized/nearby recommendations.

    Contract (see ml-service/app.py):
      POST {ML_SERVICE_URL}/recommend
      body: {"user_id": <int|null>, "latitude": <float|null>,
             "longitude": <float|null>, "top_n": <int>}
      response: {"recommendations": [{"destination_id": 3, "score": 0.92}, ...]}

    Returns a list of {"destination_id", "score"} dicts, or [] if the ML
    service is unreachable — callers should fall back to a simple heuristic
    (e.g. top-rated destinations) in that case, never hard-fail the request.
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/recommendation",
            json={
                "interest": f"nearby destinations around latitude {latitude} longitude {longitude}",
            },
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
    Calls {ML_SERVICE_URL}/predict-budget for an estimated trip cost.
    latitude/longitude: the destination's real coordinates (from the
        resolved Destination object, when available).
    user_latitude/user_longitude: the traveler's current GPS position --
        when both this and the destination coordinates are present,
        ml_service computes a real distance-based transport cost instead
        of a flat per-city baseline.
    Returns None if the ML service is unreachable.
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/budget/predict-budget",
            json={
                "city": city, "country": country, "days": days,
                "travelers": travelers, "budget_level": budget_level,
                "latitude": latitude, "longitude": longitude,
                "user_latitude": user_latitude, "user_longitude": user_longitude,
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
    Calls {ML_SERVICE_URL}/routes/best-route for a routed path.
    route_type: "fastest" | "safest" | "trekking" | "cheapest"
    Returns None if the ML service is unreachable.
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


                artist = (
                    image
                    .get("extmetadata", {})
                    .get("Artist", {})
                    .get("value", "Wikimedia contributor")
                )

                page = next(iter(pages.values()), {})

                image = (
                    page.get("imageinfo") or [{}]
                )[0]

                url = image.get("url")

                if not url:
                    continue

                # Skip SVG drawings and obvious non-photo files
                url_lower = url.lower()

                if url_lower.endswith(".svg"):
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
        queries.append(f"{destination.city} Nepal")

    if getattr(destination, "district", None):
        queries.append(f"{destination.district} Nepal")

    if getattr(destination, "province", None):
        queries.append(f"{destination.province} Nepal")

    return list(dict.fromkeys(queries))



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
            if "Unsplash" in external.get(
                "attribution",
                ""
            )
            else DestinationImage.Source.WIKIMEDIA
        )


        photo = DestinationImage.objects.create(
            destination=destination,
            external_url=external["url"],
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

from .models import EmergencyContact

def get_disaster_helplines(country=None):
    qs = EmergencyContact.objects.all()

    if country:
        qs = qs.filter(
            Q(country__iexact=country) | Q(country__isnull=True)
        )

    return qs