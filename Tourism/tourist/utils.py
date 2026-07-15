t"""
Utility helpers used across the tourists app:
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
def translate_text(text, target_language, source_language="auto"):
    """
    Translate `text` into `target_language`.

    Uses the Google Cloud Translation API if GOOGLE_TRANSLATE_API_KEY is
    configured, otherwise falls back to the free deep-translator (Google
    Translate) backend so the feature keeps working in dev/demo environments.
    """
    if not text:
        return text

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