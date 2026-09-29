"""Traveller sentiment from real, moderated reviews.

Method
------
* Text: VADER (Hutto & Gilbert, 2014), a validated lexicon and rule-based
  sentiment model for short English text. Standard thresholds: compound
  >= 0.05 is positive, <= -0.05 is negative, otherwise neutral.
* Aspects: each sentence is scored separately and grouped by the traveller
  topics it mentions (views, food, roads...), so the summary says *what*
  people liked or disliked.
* Stars: 1-5 ratings are reported separately and never mixed into text
  scores.

Honesty rules
-------------
* Only approved, unflagged reviews count; pending, flagged and archived
  reviews never do.
* Under ``MIN_REVIEWS`` analysed reviews there is no percentage breakdown,
  just the count, because three opinions are not a trend.
* VADER is English-only. Reviews that are mostly non-Latin script (for
  example Nepali) are counted as "not analysed" instead of being guessed.
"""
from __future__ import annotations

import re
from functools import lru_cache

from django.core.cache import cache
from django.db.models import Avg, Count, Max

MIN_REVIEWS = 3
POSITIVE_AT = 0.05
NEGATIVE_AT = -0.05
CACHE_SECONDS = 600

METHOD = {
    "name": "VADER sentiment (vaderSentiment 3.3.2)",
    "citation": ("Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for "
                 "Sentiment Analysis of Social Media Text. ICWSM-14."),
    "url": "https://github.com/cjhutto/vaderSentiment",
    "thresholds": {"positive": f">= {POSITIVE_AT}", "negative": f"<= {NEGATIVE_AT}"},
    "scope": "Approved, unflagged traveller reviews on this site. English text only.",
    "minimum_reviews": MIN_REVIEWS,
}

ASPECTS = {
    "views": ("Views & scenery", ["view", "views", "scenery", "scenic", "sunrise", "sunset", "panorama",
                                  "mountain", "mountains", "landscape", "himalaya", "peaks", "lake"]),
    "food": ("Food", ["food", "meal", "meals", "dal bhat", "momo", "restaurant", "breakfast", "dinner",
                      "lunch", "tea", "coffee"]),
    "stay": ("Accommodation", ["hotel", "lodge", "teahouse", "tea house", "homestay", "room", "rooms",
                               "bed", "guesthouse", "guest house", "stay"]),
    "people": ("Guides & people", ["guide", "guides", "porter", "porters", "people", "locals", "staff",
                                   "host", "hosts", "friendly", "hospitality"]),
    "transport": ("Roads & transport", ["road", "roads", "bus", "jeep", "flight", "drive", "transport",
                                        "taxi", "traffic", "trail", "trails", "path"]),
    "safety": ("Safety", ["safe", "safety", "unsafe", "dangerous", "landslide", "police", "theft",
                          "scam", "risk", "altitude sickness"]),
    "cleanliness": ("Cleanliness", ["clean", "dirty", "trash", "rubbish", "garbage", "litter",
                                    "toilet", "toilets", "hygiene", "dust", "dusty"]),
    "crowds": ("Crowds", ["crowd", "crowded", "busy", "quiet", "peaceful", "tourists", "queue"]),
    "value": ("Value for money", ["price", "prices", "expensive", "cheap", "value", "cost", "overpriced",
                                  "affordable", "fee", "fees"]),
    "weather": ("Weather", ["weather", "rain", "cold", "hot", "snow", "fog", "cloudy", "clear sky"]),
}
_ASPECT_PATTERNS = {
    key: re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.I)
    for key, (_label, words) in ASPECTS.items()
}
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?।])\s+|\n+")


@lru_cache(maxsize=1)
def _analyzer():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    return SentimentIntensityAnalyzer()


def is_analysable(text: str) -> bool:
    """VADER only understands English. Require mostly Latin letters."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 3:
        return False
    latin = sum(1 for c in letters if c.isascii())
    return latin / len(letters) >= 0.7


def label_for(compound: float) -> str:
    if compound >= POSITIVE_AT:
        return "positive"
    if compound <= NEGATIVE_AT:
        return "negative"
    return "neutral"


def score_text(text: str) -> dict | None:
    text = (text or "").strip()
    if not text or not is_analysable(text):
        return None
    compound = _analyzer().polarity_scores(text)["compound"]
    return {"compound": round(compound, 4), "label": label_for(compound)}


def aspect_mentions(text: str) -> list[tuple[str, float]]:
    """(aspect, sentence compound) for each sentence that mentions an aspect."""
    out = []
    for sentence in _SENTENCE_SPLIT.split(text or ""):
        sentence = sentence.strip()
        if not sentence or not is_analysable(sentence):
            continue
        hits = [k for k, rx in _ASPECT_PATTERNS.items() if rx.search(sentence)]
        if not hits:
            continue
        compound = _analyzer().polarity_scores(sentence)["compound"]
        out.extend((k, compound) for k in hits)
    return out


def _excerpt(text: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


def summarize(texts: list[dict], ratings: dict | None = None) -> dict:
    """Summarise ``[{"text", "created_at"}]`` plus an optional star aggregate."""
    scored, skipped = [], 0
    aspect_scores: dict[str, list[float]] = {}
    for item in texts:
        s = score_text(item["text"])
        if s is None:
            skipped += 1
            continue
        scored.append({**item, **s})
        for key, compound in aspect_mentions(item["text"]):
            aspect_scores.setdefault(key, []).append(compound)

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for s in scored:
        counts[s["label"]] += 1
    n = len(scored)
    enough = n >= MIN_REVIEWS
    result = {
        "status": "ok" if enough else ("insufficient" if n or skipped else "no_reviews"),
        "review_count": n + skipped,
        "analysed_count": n,
        "not_analysed_count": skipped,
        "not_analysed_reason": "Not English: the sentiment model only reads English." if skipped else "",
        "ratings": ratings or {"count": 0, "average": None},
        "method": METHOD,
    }
    if not enough:
        result["message"] = (
            "No traveller reviews yet." if not (n or skipped)
            else f"Only {n} analysable review{'s' if n != 1 else ''}. A summary needs at least {MIN_REVIEWS}."
        )
        return result

    avg = sum(s["compound"] for s in scored) / n
    result.update({
        "overall": {"compound": round(avg, 3), "label": label_for(avg)},
        "distribution": {k: {"count": v, "share": round(v / n, 3)} for k, v in counts.items()},
        "aspects": sorted(
            [
                {"key": k, "label": ASPECTS[k][0], "mentions": len(v),
                 "compound": round(sum(v) / len(v), 3), "label_sentiment": label_for(sum(v) / len(v))}
                for k, v in aspect_scores.items()
            ],
            key=lambda a: (-a["mentions"], a["key"]),
        ),
        "highlights": {
            "positive": _excerpt(max(scored, key=lambda s: s["compound"])["text"]) if counts["positive"] else "",
            "negative": _excerpt(min(scored, key=lambda s: s["compound"])["text"]) if counts["negative"] else "",
        },
    })
    return result


def destination_sentiment(destination) -> dict:
    """Sentiment for one destination, cached until its reviews change."""
    from .models import Rating, Review

    reviews = Review.objects.filter(destination=destination, moderation_status="approved", is_flagged=False)
    stamp = reviews.aggregate(n=Count("id"), m=Max("updated_at"))
    stars = Rating.objects.filter(destination=destination).aggregate(n=Count("id"), avg=Avg("value"), m=Max("updated_at"))
    key = f"sentiment:dest:{destination.pk}:{stamp['n']}:{stamp['m']}:{stars['n']}:{stars['m']}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    texts = [{"text": r.comment, "created_at": r.created_at.isoformat()}
             for r in reviews.only("comment", "created_at")]
    ratings = {"count": stars["n"], "average": round(float(stars["avg"]), 2) if stars["avg"] is not None else None}
    result = summarize(texts, ratings)
    result["destination"] = {"id": destination.pk, "name": destination.name, "slug": destination.slug}
    cache.set(key, result, CACHE_SECONDS)
    return result
