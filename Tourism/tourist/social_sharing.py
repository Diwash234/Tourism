"""
Social Sharing Module.

Generates Open Graph and Twitter Card meta tags for destinations and shared
trips. These tags control how links appear when shared on social media
platforms (Facebook, Twitter/X, LinkedIn, WhatsApp, etc.).

Usage:
    from tourist.social_sharing import generate_og_tags, generate_twitter_card
    og_tags = generate_og_tags(destination)
    twitter_tags = generate_twitter_card(destination)
"""

from django.conf import settings

from .utils import public_media_url


def _get_base_url():
    """Get the base URL of the site."""
    return getattr(settings, "FRONTEND_URL", "") or getattr(settings, "BACKEND_URL", "")


def _get_image_url(destination):
    """Get the best available image URL for a destination."""
    # Priority: og_image_url > cover_image > first gallery image
    if destination.og_image_url:
        return destination.og_image_url

    if destination.cover_image:
        return public_media_url(destination.cover_image.url)

    # Try to get the first approved gallery image
    cover_image = destination.gallery.filter(
        is_cover=True,
        verification_status="approved",
    ).first()
    if cover_image:
        if cover_image.image:
            return public_media_url(cover_image.image.url)
        if cover_image.external_url:
            return cover_image.external_url
        if cover_image.image_path and getattr(settings, "IMAGE_BASE_URL", ""):
            return f"{settings.IMAGE_BASE_URL}/images/{cover_image.image_path}"

    # Fallback to a default image
    base_url = _get_base_url()
    if base_url:
        return f"{base_url}/static/images/default-destination.jpg"
    return ""


def _truncate(text, max_length):
    """Truncate text to a maximum length, adding ellipsis if needed."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_length:
        return text
    return text[:max_length - 3].rsplit(" ", 1)[0] + "..."


def generate_og_tags(destination):
    """
    Generate Open Graph meta tags for a destination.

    Args:
        destination: A Destination model instance.

    Returns:
        dict of meta tag name → content pairs.
    """
    base_url = _get_base_url()
    image_url = _get_image_url(destination)

    title = destination.seo_title or destination.name
    description = destination.meta_description or destination.short_description or destination.description or ""

    tags = {
        "og:title": _truncate(title, 60),
        "og:description": _truncate(description, 200),
        "og:type": "website",
        "og:site_name": "Nepal Tourism Portal",
    }

    if base_url:
        tags["og:url"] = f"{base_url}/destinations/{destination.slug}/"

    if image_url:
        tags["og:image"] = image_url
        tags["og:image:alt"] = f"Photo of {destination.name}"
        tags["og:image:width"] = "1200"
        tags["og:image:height"] = "630"

    # Location-specific tags
    if destination.city:
        tags["og:locality"] = destination.city
    if destination.country:
        tags["og:country-name"] = destination.country

    # Rating information
    if destination.average_rating and destination.average_rating > 0:
        tags["og:rating"] = str(destination.average_rating)
        tags["og:rating_scale"] = "5"
        tags["og:rating_count"] = str(destination.ratings_count)

    return tags


def generate_twitter_card(destination):
    """
    Generate Twitter Card meta tags for a destination.

    Args:
        destination: A Destination model instance.

    Returns:
        dict of meta tag name → content pairs.
    """
    base_url = _get_base_url()
    image_url = _get_image_url(destination)

    title = destination.seo_title or destination.name
    description = destination.meta_description or destination.short_description or destination.description or ""

    tags = {
        "twitter:card": "summary_large_image",
        "twitter:title": _truncate(title, 70),
        "twitter:description": _truncate(description, 200),
    }

    if image_url:
        tags["twitter:image"] = image_url
        tags["twitter:image:alt"] = f"Photo of {destination.name}"

    if base_url:
        tags["twitter:url"] = f"{base_url}/destinations/{destination.slug}/"

    # Twitter site handle (if configured)
    twitter_handle = getattr(settings, "TWITTER_SITE_HANDLE", "")
    if twitter_handle:
        tags["twitter:site"] = twitter_handle

    return tags


def generate_trip_share_tags(trip, user):
    """
    Generate Open Graph and Twitter Card meta tags for a shared trip.

    Args:
        trip: A SharedTrip model instance.
        user: The User who owns the trip.

    Returns:
        dict with 'og' and 'twitter' keys containing meta tag dicts.
    """
    base_url = _get_base_url()
    share_url = f"{base_url}/shared-trips/{trip.share_token}/" if base_url else ""

    title = f"{user.full_name}'s Trip - {trip.label or 'Live Location'}"
    description = f"Follow {user.full_name}'s journey on Nepal Tourism Portal. See their live location and trip details."

    og_tags = {
        "og:title": _truncate(title, 60),
        "og:description": _truncate(description, 200),
        "og:type": "website",
        "og:site_name": "Nepal Tourism Portal",
    }

    if share_url:
        og_tags["og:url"] = share_url

    # Use user's profile picture if available
    if user.profile_picture:
        og_tags["og:image"] = public_media_url(user.profile_picture.url)
        og_tags["og:image:alt"] = f"Profile photo of {user.full_name}"

    twitter_tags = {
        "twitter:card": "summary",
        "twitter:title": _truncate(title, 70),
        "twitter:description": _truncate(description, 200),
    }

    if share_url:
        twitter_tags["twitter:url"] = share_url

    if user.profile_picture:
        twitter_tags["twitter:image"] = public_media_url(user.profile_picture.url)

    return {
        "og": og_tags,
        "twitter": twitter_tags,
    }


def generate_all_tags(destination):
    """
    Generate all social sharing meta tags for a destination.

    Returns:
        dict with 'og' and 'twitter' keys containing meta tag dicts.
    """
    return {
        "og": generate_og_tags(destination),
        "twitter": generate_twitter_card(destination),
    }


def render_meta_tags(tags_dict):
    """
    Convert a meta tag dict to HTML string.

    Args:
        tags_dict: dict of property/name → content.

    Returns:
        HTML string with <meta> tags.
    """
    html_parts = []
    for key, value in tags_dict.items():
        if value:
            # Determine if it's a property-based or name-based tag
            if key.startswith("og:") or key.startswith("twitter:"):
                html_parts.append(f'<meta property="{key}" content="{value}">')
            else:
                html_parts.append(f'<meta name="{key}" content="{value}">')
    return "\n".join(html_parts)
