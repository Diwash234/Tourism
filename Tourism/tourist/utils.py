"""
Utility helpers used across the tourist app:
  - Haversine distance calculation (used for "nearby" queries)
  - GeoIP lookup (fallback when the browser does not supply GPS coordinates)
  - Translation service wrapper (Google Translate API, with an automatic
    fallback to the free deep-translator library when no API key is set)
  - Email / SMS / Push notification senders
"""
import logging
from math import radians, cos, sin, asin, sqrt

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points in kilometers."""
    lat1, lon1, lat2, lon2 = map(lambda v: radians(float(v)), [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    earth_radius_km = 6371
    return earth_radius_km * c


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
            f"{settings.ML_SERVICE_URL}/translate-custom",
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
            f"{settings.ML_SERVICE_URL}/recommend",
            json={
                "user_id": user.id if user and user.is_authenticated else None,
                "latitude": float(latitude) if latitude is not None else None,
                "longitude": float(longitude) if longitude is not None else None,
                "top_n": top_n,
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
            f"{settings.ML_SERVICE_URL}/predict-safety",
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


def get_ml_budget_prediction(city=None, country=None, days=3, travelers=1, budget_level="mid"):
    """
    Calls {ML_SERVICE_URL}/predict-budget for an estimated trip cost.
    Returns None if the ML service is unreachable.
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/predict-budget",
            json={
                "city": city, "country": country, "days": days,
                "travelers": travelers, "budget_level": budget_level,
            },
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        logger.warning("ML budget prediction unreachable: %s", exc)
        return None


def get_ml_best_route(start_latitude, start_longitude, end_latitude, end_longitude):
    """
    Calls {ML_SERVICE_URL}/best-route for a routed path (OSM-based once the
    ML teammate's road graph is loaded; straight-line fallback until then).
    Returns None if the ML service is unreachable.
    """
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/best-route",
            json={
                "start_latitude": float(start_latitude), "start_longitude": float(start_longitude),
                "end_latitude": float(end_latitude), "end_longitude": float(end_longitude),
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


def fetch_wikimedia_photo(query):
    """Wikimedia Commons — free, no key required. Returns a single best-match photo."""
    try:
        search_response = requests.get(
            settings.WIKIMEDIA_API_URL,
            params={
                "action": "query", "list": "search", "srsearch": f"{query} filetype:bitmap",
                "srnamespace": 6, "format": "json",
            },
            timeout=6,
        )
        search_response.raise_for_status()
        hits = search_response.json().get("query", {}).get("search", [])
        if not hits:
            return None
        title = hits[0]["title"]

        info_response = requests.get(
            settings.WIKIMEDIA_API_URL,
            params={
                "action": "query", "titles": title, "prop": "imageinfo",
                "iiprop": "url|extmetadata", "format": "json",
            },
            timeout=6,
        )
        info_response.raise_for_status()
        pages = info_response.json().get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        image_info = (page.get("imageinfo") or [{}])[0]
        artist = image_info.get("extmetadata", {}).get("Artist", {}).get("value", "Wikimedia Commons contributor")
        return {"url": image_info.get("url"), "attribution": f"Photo: {artist} (Wikimedia Commons)", "source_link": title}
    except (requests.RequestException, KeyError, IndexError, StopIteration) as exc:
        logger.warning("Wikimedia lookup failed: %s", exc)
        return None


def find_nearby_places(latitude, longitude, query, radius_m=2000):
    """
    Combines Foursquare and Google Places (whichever have keys configured)
    into one simple result list for "restaurants/shops/hotels near this
    destination" style features. Returns [] if neither is configured —
    callers should treat an empty list as "no external data available",
    not an error.
    """
    results = []
    for place in foursquare_search_nearby(latitude, longitude, radius_m, query=query):
        results.append({
            "name": place["name"], "address": place.get("address", ""),
            "distance_m": place.get("distance_m"), "source": "foursquare",
        })
    if not results:  # only fall back to Google Places if Foursquare returned nothing (avoid duplicate/paid calls)
        for place in google_places_search(f"{query} near {latitude},{longitude}", latitude, longitude):
            results.append({
                "name": place["name"], "address": place.get("address", ""),
                "rating": place.get("rating"), "source": "google_places",
            })
    return results


def get_disaster_helplines(destination):
    """
    If there's an active weather/flood/landslide/earthquake alert covering
    this destination's city, this surfaces the nearest ward office/ward
    member and emergency contacts specifically — the "who do I actually
    call right now" list — rather than making the frontend cross-reference
    alerts and contacts itself.
    """
    from .models import Alert, EmergencyContact

    disaster_types = [Alert.AlertType.FLOOD, Alert.AlertType.LANDSLIDE, Alert.AlertType.EARTHQUAKE, Alert.AlertType.WEATHER]
    active_alert = (
        Alert.objects.filter(is_active=True, alert_type__in=disaster_types, city__iexact=destination.city or "")
        .order_by("-severity", "-created_at")
        .first()
    )
    if not active_alert:
        return {"active_alert": None, "helplines": []}

    nearest_by_type = {}
    priority_types = [
        EmergencyContact.ContactType.POLICE, EmergencyContact.ContactType.HOSPITAL,
        EmergencyContact.ContactType.WARD_OFFICE, EmergencyContact.ContactType.WARD_MEMBER,
    ]
    for contact in EmergencyContact.objects.filter(contact_type__in=priority_types):
        distance = haversine_distance(destination.latitude, destination.longitude, contact.latitude, contact.longitude)
        if distance > 50:  # 50km cap — don't surface a contact from a different region
            continue
        current = nearest_by_type.get(contact.contact_type)
        if current is None or distance < current[0]:
            nearest_by_type[contact.contact_type] = (distance, contact)

    from .serializers import EmergencyContactSerializer

    contacts = [c for _, c in sorted(nearest_by_type.values(), key=lambda pair: pair[0])]
    return {
        "active_alert": {
            "alert_type": active_alert.alert_type, "severity": active_alert.severity,
            "title": active_alert.title, "description": active_alert.description,
        },
        "helplines": EmergencyContactSerializer(contacts, many=True).data,
    }


def ensure_cover_photo(destination):
    """
    Guarantees a destination has SOME cover image available before it's
    ever serialized in a list/search/detail response. If it already has a
    `cover_image` file or any gallery photo, this is a no-op. Otherwise it
    fetches one external fallback image (Unsplash, then Wikimedia Commons)
    and PERSISTS it as a real DestinationImage row (is_cover=True) — so the
    external API is called at most ONCE per destination, ever, not on
    every search result. This is what actually makes `cover_image_url`
    show images for destinations that have no local photos yet.
    """
    from .models import DestinationImage

    if destination.cover_image or destination.gallery.exists():
        return None

    external = fetch_unsplash_photo(f"{destination.name} {destination.city}".strip()) or fetch_wikimedia_photo(
        f"{destination.name} {destination.city}".strip()
    )
    if not external or not external.get("url"):
        return None

    source = DestinationImage.Source.UNSPLASH if "Unsplash" in external["attribution"] else DestinationImage.Source.WIKIMEDIA
    return DestinationImage.objects.create(
        destination=destination,
        external_url=external["url"],
        attribution=external["attribution"],
        source=source,
        is_cover=True,
    )


def get_destination_photos(destination):
    """
    Returns the photo list the frontend should render for a destination:
    local gallery first (community uploads + admin uploads, most-viewed/
    promoted first per DestinationImage.Meta.ordering). Calls
    ensure_cover_photo() first so a brand-new destination with zero photos
    gets one cached external image instead of coming back empty.
    """
    ensure_cover_photo(destination)
    return list(destination.gallery.all())


def register_photo_view(photo):
    """
    Increments a photo's view_count and checks whether it should be
    auto-promoted. Call this whenever a photo is actually served/displayed
    to a user (e.g. shown in search results), not on every unrelated request.
    """
    from django.db.models import F
    from .models import DestinationImage

    DestinationImage.objects.filter(pk=photo.pk).update(view_count=F("view_count") + 1)
    photo.refresh_from_db(fields=["view_count"])
    maybe_promote_photo(photo)


def maybe_promote_photo(photo):
    """
    Auto-promotes a highly-viewed community upload to be the destination's
    official cover photo, once it crosses PHOTO_PROMOTION_IMPRESSION_THRESHOLD
    views and has more views than the current cover (if any). This is how
    "if it's highly searched, add it to the sources/destination" is
    implemented — no manual admin step required, though admins can still
    override via Django admin.
    """
    from .models import DestinationImage

    if photo.source == DestinationImage.Source.ADMIN or photo.view_count < settings.PHOTO_PROMOTION_IMPRESSION_THRESHOLD:
        return

    current_cover = photo.destination.gallery.filter(is_cover=True).exclude(pk=photo.pk).first()
    if current_cover and current_cover.view_count >= photo.view_count:
        return

    DestinationImage.objects.filter(destination=photo.destination).update(is_cover=False)
    photo.is_cover = True
    photo.is_promoted = True
    photo.save(update_fields=["is_cover", "is_promoted"])
    logger.info("Promoted photo %s to cover for destination %s (%s views)", photo.pk, photo.destination.name, photo.view_count)
