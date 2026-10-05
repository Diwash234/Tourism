"""Deciding whether a photograph actually depicts a named place.

Kept free of Django imports so the matching rule can be unit tested on its own,
and so the fetch command and any future importer agree on one definition of
"this photo is of that place".

The rule is deliberately strict. An image attached to the wrong destination is
worse than no image at all, because a traveller trusts it. So a candidate is
only accepted when the photograph's own title or tags name the place: every
distinctive word in the destination name must appear, and words that carry no
identifying information ("nepal", "sunset", "temple") are ignored on both
sides so they cannot create a false match.

Known trade-off
---------------
Words are compared on a singular stem, because catalogue names and photo
captions disagree on number constantly: the destination is "Davis Falls" and
the photograph is titled "Davis Fall". The cost is that a plural region name can
match a single-feature photograph -- "Pokhara Lakes" is accepted for a photo of
"Phewa Lake". That direction of error is chosen deliberately: a destination left
without a photo is a visible gap, while a wrong photo is a false statement, and
the gap is the cheaper failure. Narrowing this would need per-destination review
rather than a rule.
"""
import re

#: Words that identify nothing, in a place name or a photo title.
GENERIC = {
    "nepal", "nepali", "the", "of", "and", "in", "at", "on", "for", "to", "from",
    "view", "photo", "photos", "image", "images", "picture", "shot", "a", "an",
    "new", "old", "city", "town", "village", "district", "province", "municipality",
    "rural", "ward", "north", "south", "east", "west", "central", "sunset",
    "sunrise", "night", "day", "morning", "evening", "aerial", "panorama",
    "panoramic", "viewpoint", "main", "street", "road", "gate", "entrance",
    "front", "side", "top", "upper", "lower", "part", "near", "during",
    "over", "under", "across", "along", "around", "through", "between",
    "wikipedia", "commons", "wikimedia", "upload", "org", "thumb", "jpg", "jpeg",
    "png", "webp", "svg", "px", "copyright", "creative",
}

#: Words shorter than this are too weak to identify a place on their own.
MIN_WORD = 4


def tokens(text):
    """Significant, lower-cased words for matching."""
    text = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
    return {w for w in text.split() if len(w) >= MIN_WORD and w not in GENERIC}


def _singular(word):
    """A crude but safe singular form, for spelling drift in photo titles.

    Catalogue names and photo captions disagree on number all the time: the
    destination is "Davis Falls" and the photograph is titled "Davis Fall".
    Stripping one plural ending recovers those without loosening anything else.
    """
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("es") and word[-3] in "sxzh":
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _stem_set(words):
    return {_singular(w) for w in words}


def match_score(destination_name, haystack):
    """How confidently a photo's text identifies ``destination_name``.

    Returns 1.0 when every distinctive word of the place appears in the
    photograph's own text, and 0.0 otherwise. Partial matches score 0.0 on
    purpose: "Davis Falls" must not be satisfied by "Davis Lake", and "Patan
    Museum" must not be satisfied by a photo of "Patan Durbar Square".

    Words are compared on a singular stem so number drift between a catalogue
    name and a photo caption does not reject a genuine match.
    """
    name_tokens = tokens(destination_name)
    if not name_tokens:
        return 0.0
    hay = tokens(haystack)
    if not hay:
        return 0.0
    if _stem_set(name_tokens).issubset(_stem_set(hay)):
        return 1.0
    return 0.0
