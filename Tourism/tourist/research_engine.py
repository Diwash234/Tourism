"""
Destination lookup for the "research a place" action.

History: this module used to *construct* a destination for any unknown name
-- Pokhara's coordinates, Kaski district, a default "1,400m" altitude, a
4.85 rating from "32 ratings", generic history/culture text, stock Unsplash
photos of other places labelled as Wikimedia CC BY-SA, and three
"verified" citations (including an "NTB profile" at nepaltourism.gov.np,
which is not the Nepal Tourism Board's domain) -- and saved it as APPROVED
regardless of the auto_publish flag. That is fabricated data presented as
verified, so it has been removed.

The endpoint now only ever:
  * returns an existing catalogue record (exact / slug / alias / substring), or
  * returns close catalogue suggestions, or
  * reports that nothing was found and points to the reviewed submission flow.

It never creates, edits or approves records. New places must come through
Submit a Place / the admin destination form with a real source, where the
normal review workflow applies.
"""

from django.db.models import Q
from django.utils.text import slugify

from .models import Destination

SUBMIT_URL = "/destinations/submit"


def _public(qs):
    return qs.filter(status=Destination.SubmissionStatus.APPROVED, is_active=True)


def research_and_build_destination(query_name: str, auto_publish: bool = False, actor=None) -> dict:
    """Look a place up in the catalogue. Never writes to the database.

    ``auto_publish`` and ``actor`` are accepted for API compatibility only.
    """
    clean_query = (query_name or "").strip()
    if not clean_query:
        return {"error": "Destination name is required for research."}

    existing = (
        Destination.objects.filter(
            Q(name__iexact=clean_query)
            | Q(slug__iexact=slugify(clean_query))
            | Q(aliases__icontains=clean_query)
            | Q(name__icontains=clean_query)
        )
        .order_by("-status", "name")
        .first()
    )
    if existing:
        return {
            "status": "existing",
            "message": f"Destination '{existing.name}' already exists in the catalogue.",
            "destination_id": existing.id,
            "slug": existing.slug,
            "name": existing.name,
            "is_published": existing.status == Destination.SubmissionStatus.APPROVED and existing.is_active,
        }

    tokens = [t for t in clean_query.replace("-", " ").split() if len(t) >= 3]
    suggestions = []
    if tokens:
        token_q = Q()
        for token in tokens:
            token_q |= Q(name__icontains=token) | Q(aliases__icontains=token)
        suggestions = [
            {"id": d.id, "name": d.name, "slug": d.slug, "district": d.district or ""}
            for d in _public(Destination.objects.filter(token_q)).order_by("name")[:5]
        ]

    return {
        "status": "not_found",
        "created": False,
        "message": (
            f"No catalogue record matches '{clean_query}'. Nothing was created automatically — "
            "add it through Submit a Place with a source so it can be reviewed."
        ),
        "suggestions": suggestions,
        "submit_url": SUBMIT_URL,
    }
