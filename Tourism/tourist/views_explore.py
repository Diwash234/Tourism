"""Traveller discovery endpoints: search, filters, decisions, sentiment, sharing.

All endpoints are read-only and public (except share management, which is
owner-only). They answer from real records and the sourced fact table in
``traveller_facts``. Unknown values are reported as unknown, and every
derived value carries its basis.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from urllib.parse import quote
from uuid import uuid4

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import traveller_facts as tf
from . import travel_requirements as treq
from .models import (Destination, District, Hotel, ManagedPage, OSMEssentialService, Restaurant,
                     TravelPlan)
from .opening_hours import status as hours_status
from .sentiment import destination_sentiment
from .serializers import DestinationListSerializer

MAX_QUERY_LENGTH = 120

# App features people search for by name ("budget", "permit", "sos"...).
APP_PAGES = [
    {"title": "Budget estimator", "path": "/budget-estimator",
     "keywords": "budget cost price money estimate expense currency exchange rate fx"},
    {"title": "Itinerary planner", "path": "/itinerary",
     "keywords": "itinerary plan planner trip route days schedule generate"},
    {"title": "Before you travel (visa, permits, TIMS, insurance)", "path": "/before-you-travel",
     "keywords": "visa permit permits tims insurance requirements fee fees park entry restricted altitude ams"},
    {"title": "Emergency contacts", "path": "/emergency",
     "keywords": "emergency sos police ambulance hospital help hotline fire tourist police rescue"},
    {"title": "Find places by what you want to do", "path": "/discover",
     "keywords": "discover filter activity difficulty season altitude accessibility trek culture wildlife"},
    {"title": "Help me decide", "path": "/decide",
     "keywords": "decide compare versus vs which better choose decision"},
    {"title": "Recommendations for you", "path": "/recommendation",
     "keywords": "recommend recommendation suggest suggestions ideas where to go"},
    {"title": "Hotel search", "path": "/hotels/search", "keywords": "hotel hotels stay lodge room accommodation"},
    {"title": "Navigation & routes", "path": "/navigation",
     "keywords": "navigation route directions map road drive distance"},
    {"title": "Nearby places & services", "path": "/nearby-places",
     "keywords": "nearby atm bank pharmacy hospital police open now services"},
    {"title": "Explore the map", "path": "/explore-map", "keywords": "map explore"},
    {"title": "Districts of Nepal", "path": "/districts", "keywords": "district districts province"},
    {"title": "Travel risk alerts", "path": "/risk-alerts",
     "keywords": "risk alert alerts weather landslide flood warning safety"},
]
SERVICE_WORDS = {"atm": "atm", "atms": "atm", "bank": "bank", "banks": "bank", "pharmacy": "pharmacy",
                 "pharmacies": "pharmacy", "chemist": "pharmacy", "hospital": "hospital",
                 "hospitals": "hospital", "clinic": "hospital", "police": "police"}


SERVICE_PLURALS = {"atm": "ATMs", "bank": "banks", "pharmacy": "pharmacies", "hospital": "hospitals",
                   "police": "police stations"}


def _fold(text) -> str:
    """Lowercase, strip accents and punctuation, collapse spaces."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^\w\s]", " ", text).strip()


def _clean_query(raw) -> str:
    return re.sub(r"\s+", " ", str(raw or "")).strip()[:MAX_QUERY_LENGTH]


def _cards(request, ids):
    """Serialize destinations in the given order using the public list serializer."""
    objs = {d.id: d for d in Destination.publicly_visible().filter(id__in=ids).select_related("category")}
    ordered = [objs[i] for i in ids if i in objs]
    return {d["id"]: d for d in DestinationListSerializer(ordered, many=True, context={"request": request}).data}


def _score_name(row, q, tokens) -> int:
    name = _fold(row["name"])
    if not name:
        return 0
    if name == q:
        return 100
    if name.startswith(q):
        return 85
    if re.search(rf"\b{re.escape(q)}", name):
        return 70
    short = len(q) < 4  # "atm" must not match "Patmara"
    if not short and q in name:
        return 50
    aliases = _fold(row["aliases"])
    if aliases and (re.search(rf"\b{re.escape(q)}", aliases) if short else q in aliases):
        return 45
    def has(token, text):
        return bool(re.search(rf"\b{re.escape(token)}", text)) if len(token) < 4 else token in text

    if tokens and all(has(t, name) or has(t, aliases) for t in tokens):
        return 40
    if _fold(row["district"]) == q:
        return 30
    return 0


_VOCAB = {"signature": None, "words": [], "display": {}}


def _vocabulary():
    rows = tf.fact_rows()
    sig = tf._TABLE["signature"]
    if _VOCAB["signature"] != sig or not _VOCAB["words"]:
        display = {}
        for r in rows:
            for text in [r["name"]] + [a for a in re.split(r"[;,]", r["aliases"]) if a.strip()]:
                key = _fold(text)
                if 2 < len(key) <= 60:
                    display.setdefault(key, text.strip())
            if r["district"]:
                display.setdefault(_fold(r["district"]), r["district"])
        data = treq.load_dataset()
        for group in ("protected_areas", "restricted_areas", "heritage_sites"):
            for item in data[group]:
                display.setdefault(_fold(item["name"]), item["name"])
        word_set = {w for key in display for w in key.split() if len(w) > 3}
        _VOCAB.update(signature=sig, words=list(display), display=display,
                      word_set=word_set, word_list=sorted(word_set))
    return _VOCAB


def did_you_mean(q: str, limit: int = 3) -> list[str]:
    """Close spellings from real place, district and park names.

    Whole names are tried first ("pokhra" -> "Pokhara"); then each word is
    corrected against words used in real names ("namchee" -> "namche"),
    because many names are long ("Namche Bazaar Sherpa Cultural Capital").
    """
    vocab = _vocabulary()
    folded = _fold(q)
    if not folded:
        return []
    matches = difflib.get_close_matches(folded, vocab["words"], n=limit, cutoff=0.78)
    out = [vocab["display"].get(m, m) for m in matches if m != folded]
    if out:
        return out
    fixed = []
    for token in folded.split():
        if len(token) < 4 or token in vocab["word_set"]:
            fixed.append(token)
            continue
        close = difflib.get_close_matches(token, vocab["word_list"], n=1, cutoff=0.8)
        fixed.append(close[0] if close else token)
    joined = " ".join(fixed)
    return [joined] if joined != folded else []


def _search_destinations(q, limit):
    folded = _fold(q)
    tokens = [t for t in folded.split() if len(t) > 1]
    scored = []
    for row in tf.fact_rows():
        s = _score_name(row, folded, tokens)
        if s:
            scored.append((s, row["is_featured"], row["has_cover"], row["views_count"], row))
    scored.sort(key=lambda x: (-x[0], not x[1], not x[2], -x[3], x[4]["name"]))
    return [x[4] for x in scored[:limit]], len(scored)


class UniversalSearchView(APIView):
    """GET /api/v1/search/?q=...: one search box for the whole site.

    Returns grouped results (destinations, districts, hotels, restaurants,
    services, travel rules, site pages) plus a did-you-mean suggestion. When
    nothing matches but a close spelling exists, it also returns results for
    that spelling and says so (``showing_results_for``).
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = _clean_query(request.query_params.get("q"))
        if len(q) < 2:
            return Response({"query": q, "total": 0, "groups": [], "did_you_mean": [],
                             "message": "Type at least 2 characters."})
        groups, total = self._groups(request, q)
        suggestions = did_you_mean(q) if total < 3 else []
        showing_for = None
        if total == 0 and suggestions:
            showing_for = suggestions[0]
            groups, total = self._groups(request, showing_for)
        return Response({
            "query": q, "total": total, "groups": groups,
            "did_you_mean": suggestions, "showing_results_for": showing_for,
            "notes": ["Hotels, restaurants and services marked 'Unverified' come from a named public "
                      "source and have not been checked by our team yet."],
        })

    def _groups(self, request, q):
        folded = _fold(q)
        groups = []
        rows, dest_total = _search_destinations(q, 8)
        if rows:
            cards = _cards(request, [r["id"] for r in rows])
            groups.append({"type": "destinations", "label": "Destinations", "total": dest_total,
                           "more_path": f"/discover?q={quote(q)}",
                           "items": [{"id": r["id"], "title": r["name"], "path": f"/destinations/{r['slug']}",
                                      "subtitle": ", ".join(x for x in [r["category_name"], r["district"]] if x),
                                      "card": cards.get(r["id"])} for r in rows]})

        districts = District.objects.filter(name__icontains=q).order_by("name")[:5]
        if districts:
            groups.append({"type": "districts", "label": "Districts", "total": len(districts),
                           "items": [{"id": d.id, "title": f"{d.name} district", "path": f"/districts/{d.name}",
                                      "subtitle": d.region_type or ""} for d in districts]})

        if len(folded) < 4:
            name_q = Q(name__istartswith=q) | Q(name__icontains=f" {q}")
            hotel_q = name_q | Q(destination__name__istartswith=q)
        else:
            name_q = Q(name__icontains=q)
            hotel_q = name_q | Q(destination__name__icontains=q) | Q(address__icontains=q)
        hotels = (Hotel.objects.filter(is_active=True, archived_at__isnull=True)
                  .filter(hotel_q)
                  .select_related("destination").order_by("-is_verified", "name")[:6])
        if hotels:
            groups.append({"type": "hotels", "label": "Hotels", "total": len(hotels),
                           "more_path": f"/hotels/search?q={quote(q)}",
                           "items": [{"id": h.id, "title": h.name, "path": f"/hotels/search?q={quote(h.name)}",
                                      "subtitle": h.destination.name if h.destination_id else h.address,
                                      "verified": h.is_verified, "source": h.source or ""} for h in hotels]})

        restaurants = (Restaurant.objects.filter(status="published")
                       .filter(name_q if len(folded) < 4 else (name_q | Q(destination__name__icontains=q)))
                       .select_related("destination").order_by("-is_verified", "name")[:5])
        if restaurants:
            groups.append({"type": "restaurants", "label": "Restaurants", "total": len(restaurants),
                           "items": [{"id": r.id, "title": r.name,
                                      "path": f"/destinations/{r.destination.slug}" if r.destination_id else "",
                                      "subtitle": r.destination.name if r.destination_id else r.address,
                                      "verified": r.is_verified, "source": r.source_name or ""} for r in restaurants]})

        service_cat = next((SERVICE_WORDS[t] for t in folded.split() if t in SERVICE_WORDS), None)
        rest = " ".join(t for t in folded.split() if t not in SERVICE_WORDS)
        services = OSMEssentialService.objects.filter(is_archived=False)
        if service_cat:
            services = services.filter(category=service_cat)
            services = services.filter(Q(name__icontains=rest) | Q(address__icontains=rest)) if rest else services.none()
        else:
            services = services.filter(Q(name__icontains=q) | Q(address__icontains=q))
        services = services.order_by("-is_verified", "name")[:5]
        service_items = [{"id": s.id, "title": s.name, "path": f"/nearby-places?category={s.category}",
                          "subtitle": f"{s.get_category_display()} · {s.address}".strip(" ·"),
                          "verified": s.is_verified, "source": s.source_name or "OpenStreetMap",
                          "hours": hours_status(s.opening_hours)} for s in services]
        if service_cat:
            service_items.insert(0, {"id": f"nearby-{service_cat}", "title": f"Find {SERVICE_PLURALS[service_cat]} near you",
                                     "path": f"/nearby-places?category={service_cat}",
                                     "subtitle": "Uses your location · shows which are open now"})
        if service_items:
            groups.append({"type": "services", "label": "Services", "total": len(service_items), "items": service_items})

        data = treq.load_dataset()
        rules = []
        for group, kind in (("protected_areas", "Park / conservation area"),
                            ("restricted_areas", "Restricted area (permit required)"),
                            ("heritage_sites", "Heritage site")):
            for item in data[group]:
                if folded in _fold(item["name"]) or any(folded == _fold(k) for k in (item.get("match") or {}).get("name_keywords") or []):
                    rules.append({"id": f"{group}:{item['name']}", "title": item["name"], "subtitle": kind,
                                  "path": "/before-you-travel"})
        if rules:
            groups.append({"type": "travel_rules", "label": "Permits & entry fees", "total": len(rules), "items": rules[:6]})

        pages = []
        for page in APP_PAGES:
            hay = _fold(page["title"] + " " + page["keywords"])
            if folded in hay or any(t in hay.split() for t in folded.split() if len(t) > 2):
                pages.append({"id": page["path"], "title": page["title"], "path": page["path"], "subtitle": "Tool"})
        for page in ManagedPage.objects.filter(is_enabled=True, status="published", search_visible=True,
                                               title__icontains=q)[:4]:
            pages.append({"id": f"page-{page.id}", "title": page.title, "path": page.route or f"/page/{page.key}",
                          "subtitle": "Page"})
        if pages:
            groups.append({"type": "pages", "label": "Tools & pages", "total": len(pages), "items": pages[:6]})
        total = sum(g["total"] for g in groups)
        return groups, total


# --------------------------------------------------------------------------
# Traveller filters
# --------------------------------------------------------------------------
def _csv(params, key) -> set[str]:
    return {v.strip().lower() for v in (params.get(key) or "").split(",") if v.strip()}


def _int(params, key, lo=None, hi=None):
    try:
        value = int(float(params.get(key)))
    except (TypeError, ValueError):
        return None
    if lo is not None and value < lo:
        return None
    if hi is not None and value > hi:
        return None
    return value


SEASON_MIN = {"best": 3, "good": 2, "fair": 1}
ACCESSIBILITY = {
    "low_altitude": "Below the 2,500 m altitude-sickness threshold (measured elevation)",
    "hospital_10km": "A hospital on record within 10 km (straight line)",
    "hospital_25km": "A hospital on record within 25 km (straight line)",
}


def apply_filters(params, *, month=None, origin=None):
    """Filter the fact table. Returns (rows, why_by_id, applied, warnings)."""
    rows = tf.fact_rows()
    applied, why, warnings = {}, {}, []
    q = _fold(_clean_query(params.get("q")))
    activities = _csv(params, "activity") & set(tf.ACTIVITIES)
    difficulties = _csv(params, "difficulty") & {"easy", "moderate", "strenuous"}
    costs = _csv(params, "cost") & set(tf.COST_LABELS)
    access = _csv(params, "accessibility") & set(ACCESSIBILITY)
    reaches = _csv(params, "reach") & {b[0] for b in tf.REACH_BANDS}
    min_elev = _int(params, "min_elevation", 0, 9000)
    max_elev = _int(params, "max_elevation", 0, 9000)
    max_km = _int(params, "max_distance_km", 1, 2000)
    season_min = SEASON_MIN.get((params.get("season_fit") or "").lower())
    province = _fold(params.get("province"))
    district = _fold(params.get("district"))
    tokens = [t for t in q.split() if len(t) > 1]
    if (reaches or max_km) and origin is None:
        warnings.append("Distance filters need a starting point (a district or your location), so they were not applied.")
        reaches, max_km = set(), None
    if params.get("month") not in (None, "") and month is None:
        warnings.append("Month must be 1-12; season filtering was not applied.")

    for key, value in (("q", q), ("activity", sorted(activities)), ("difficulty", sorted(difficulties)),
                       ("cost", sorted(costs)), ("accessibility", sorted(access)), ("reach", sorted(reaches)),
                       ("min_elevation", min_elev), ("max_elevation", max_elev), ("max_distance_km", max_km),
                       ("season_fit", params.get("season_fit") if season_min else None),
                       ("province", province), ("district", district)):
        if value:
            applied[key] = value

    out = []
    for row in rows:
        reasons = []
        if q and not _score_name(row, q, tokens) and q not in _fold(row["category_name"]):
            continue
        if activities:
            if row["activity"] not in activities:
                continue
            reasons.append(f"Activity: {tf.ACTIVITIES[row['activity']]['label']} ({row['category_name']})")
        if difficulties:
            if row["difficulty"]["level"] not in difficulties:
                continue
            reasons.append(f"Effort: {row['difficulty']['label']}. {row['difficulty']['basis']}")
        elev = row["elevation_m"]
        if min_elev is not None or max_elev is not None:
            if elev is None or (min_elev is not None and elev < min_elev) or (max_elev is not None and elev > max_elev):
                continue
            reasons.append(f"Elevation {elev:,} m")
        if costs:
            if row["cost"]["class"] not in costs:
                continue
            reasons.append(f"Fees: {row['cost']['label']}" + (f" ({row['cost']['area']})" if row["cost"]["area"] else ""))
        if access:
            hosp = row["nearest_hospital"]
            if "low_altitude" in access and (elev is None or elev >= treq.ALTITUDE_THRESHOLD_M):
                continue
            if "hospital_10km" in access and not (hosp and hosp["km"] <= 10):
                continue
            if "hospital_25km" in access and not (hosp and hosp["km"] <= 25):
                continue
            if "low_altitude" in access:
                reasons.append(f"Below {treq.ALTITUDE_THRESHOLD_M:,} m ({elev:,} m)")
            if hosp and ("hospital_10km" in access or "hospital_25km" in access):
                reasons.append(f"Nearest hospital on record: {hosp['name']}, {hosp['km']} km")
        if province and province not in _fold(row["province"]):
            continue
        if district and _fold(row["district"]) != district:
            continue
        distance = tf.row_distance(row, origin)
        if (reaches or max_km) and distance is None:
            continue
        if reaches:
            band = tf.reach_for(distance)["band"]
            if band not in reaches:
                continue
        if max_km and distance > max_km:
            continue
        if distance is not None and (reaches or max_km):
            reasons.append(f"{distance:,.0f} km from {origin['label']} (straight line)")
        season = None
        if month:
            season = tf.season_fit(month=month, activity=row["activity"], elevation_m=elev,
                                   district=row["district"], province=row["province"])
            if season_min is not None and season["score"] < season_min:
                continue
            if season_min is not None:
                reasons.append(f"{season['label']} in {season['month_name']}: {season['reason']}")
        out.append((row, season, distance))
        why[row["id"]] = reasons
    return out, why, applied, warnings


def _sort(items, sort):
    if sort == "distance":
        return sorted(items, key=lambda x: (x[2] is None, x[2] or 0, x[0]["name"]))
    if sort == "elevation_asc":
        return sorted(items, key=lambda x: (x[0]["elevation_m"] is None, x[0]["elevation_m"] or 0))
    if sort == "elevation_desc":
        return sorted(items, key=lambda x: (x[0]["elevation_m"] is None, -(x[0]["elevation_m"] or 0)))
    if sort == "name":
        return sorted(items, key=lambda x: x[0]["name"].lower())
    # "recommended": season fit first (when a month is chosen), then places
    # with real photos and editorial features, then popularity.
    return sorted(items, key=lambda x: (-(x[1]["score"] if x[1] else 0), not x[0]["has_cover"],
                                        not x[0]["is_featured"], -x[0]["views_count"], x[0]["name"]))


def _facets(items):
    facets = {"activity": {}, "difficulty": {}, "cost": {}, "reach": {}}
    for row, _season, distance in items:
        facets["activity"][row["activity"]] = facets["activity"].get(row["activity"], 0) + 1
        level = row["difficulty"]["level"]
        facets["difficulty"][level] = facets["difficulty"].get(level, 0) + 1
        facets["cost"][row["cost"]["class"]] = facets["cost"].get(row["cost"]["class"], 0) + 1
        if distance is not None:
            band = tf.reach_for(distance)["band"]
            facets["reach"][band] = facets["reach"].get(band, 0) + 1
    return facets


class DiscoverView(APIView):
    """GET /api/v1/discover/: traveller filters over every public destination.

    Filters: activity, difficulty, min/max_elevation, cost, accessibility,
    month + season_fit, origin (district slug) or origin_lat/origin_lng,
    reach, max_distance_km, province, district, q. Sort: recommended, distance,
    elevation_asc, elevation_desc, name. Filters on a value a place lacks
    (for example elevation) exclude that place, and ``coverage`` says how
    many places have each value.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = request.query_params
        month = tf.parse_month(params.get("month"))
        origin = tf.resolve_origin(params)
        items, why, applied, warnings = apply_filters(params, month=month, origin=origin)
        sort = (params.get("sort") or "recommended").lower()
        items = _sort(items, sort)
        page_size = _int(params, "page_size", 1, 48) or 24
        page = _int(params, "page", 1, 10_000) or 1
        start = (page - 1) * page_size
        page_items = items[start:start + page_size]
        cards = _cards(request, [row["id"] for row, _s, _d in page_items])
        results = []
        for row, _season, _distance in page_items:
            if row["id"] not in cards:
                continue
            results.append({"destination": cards[row["id"]],
                            "facts": tf.facts_for_row(row, month=month, origin=origin),
                            "why": why.get(row["id"], [])})
        all_rows = tf.fact_rows()
        return Response({
            "count": len(items), "page": page, "page_size": page_size,
            "has_next": start + page_size < len(items),
            "month": month, "month_name": tf.MONTH_NAMES[month] if month else None,
            "origin": origin, "sort": sort, "applied": applied, "warnings": warnings,
            "results": results, "facets": _facets(items),
            "coverage": coverage(all_rows),
        })


def coverage(rows) -> dict:
    total = len(rows) or 1
    elev = sum(1 for r in rows if r["elevation_m"] is not None)
    coords = sum(1 for r in rows if r["latitude"] is not None)
    fee = sum(1 for r in rows if r["cost"]["class"] != "none_on_record")
    return {
        "total": len(rows),
        "elevation_known": elev, "coordinates_known": coords, "official_fee_matched": fee,
        "note": (f"Measured elevation is on record for {elev:,} of {len(rows):,} places. Filters on altitude, "
                 "effort or low-altitude access only return those places. Distance filters need coordinates "
                 f"({coords:,} places). Official fees come from DOI/NTB rules matched by name and district."),
        "elevation_share": round(elev / total, 3),
    }


class DiscoverOptionsView(APIView):
    """GET /api/v1/discover/options/: filter vocab, origins and data coverage."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        rows = tf.fact_rows()
        return Response({
            "activities": [{"key": k, "label": v["label"]} for k, v in tf.ACTIVITIES.items()],
            "difficulties": [{"key": k, "label": tf.DIFFICULTY_LABELS[k]} for k in ("easy", "moderate", "strenuous")],
            "difficulty_note": ("Effort levels are derived by this site from measured elevation (and whether the "
                                "place is a trek); they are not official route gradings."),
            "costs": [{"key": k, "label": v} for k, v in tf.COST_LABELS.items()],
            "accessibility": [{"key": k, "label": v} for k, v in ACCESSIBILITY.items()],
            "accessibility_note": ("No wheelchair or step-free data exists for destinations yet, so accessibility "
                                   "filters use measurable facts: altitude and distance to the nearest hospital."),
            "reach": [{"key": k, "label": label, "max_km": limit} for k, limit, label in tf.REACH_BANDS],
            "season_fit": [{"key": k, "label": tf.SEASON_LEVEL_LABELS[k]} for k in ("best", "good", "fair")],
            "months": [{"value": i, "label": tf.MONTH_NAMES[i]} for i in range(1, 13)],
            "origins": tf.list_origins(),
            "season_source": tf.season_source(),
            "season_disclaimer": tf.season_dataset()["disclaimer"],
            "coverage": coverage(rows),
        })


class SeasonGuideView(APIView):
    """GET /api/v1/season-guide/?month=10: NTB's guidance for a month."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data = tf.season_dataset()
        month = tf.parse_month(request.query_params.get("month")) or timezone.localdate().month
        season = data["months"][str(month)]
        payload = {"month": month, "month_name": tf.MONTH_NAMES[month], "season": season,
                   "facts": data["facts"], "reference_stations": data["reference_stations"],
                   "reference_note": data["reference_note"], "disclaimer": data["disclaimer"],
                   "sources": list(data["sources"].values())}
        key = (request.query_params.get("destination") or "").strip()
        if key:
            # Month-by-month fit for one destination (?destination=<id|slug>).
            qs = Destination.publicly_visible()
            dest = get_object_or_404(qs, pk=int(key)) if key.isdigit() else get_object_or_404(qs, slug=key)
            row = next((r for r in tf.fact_rows() if r["id"] == dest.pk), None)
            if row is None:
                return Response({"detail": "Destination not found."}, status=status.HTTP_404_NOT_FOUND)
            payload["destination"] = {
                "id": dest.pk, "name": dest.name, "slug": dest.slug,
                "activity": row["activity"], "elevation_m": row["elevation_m"],
                "elevation_source": row["elevation_source"] or None, "district": row["district"],
            }
            payload["months"] = [
                tf.season_fit(month=m, activity=row["activity"], elevation_m=row["elevation_m"],
                              district=row["district"], province=row["province"])
                for m in range(1, 13)
            ]
            payload["temperatures"] = tf.estimated_temperatures(row["elevation_m"])
        return Response(payload)


# --------------------------------------------------------------------------
# Decision pages
# --------------------------------------------------------------------------
def _fixed_fee_npr(req) -> int | None:
    fees = [f for f in req["fees"] if f.get("currency") == "NPR" and f.get("amount_per_person")]
    return sum(int(f["amount_per_person"]) for f in fees) if fees else 0


class DecisionView(APIView):
    """GET /api/v1/decide/?ids=1,2[,3,4]&month=10&origin=kaski&nationality=foreign&days=5

    Side-by-side facts and per-criterion verdicts. A criterion is only judged
    when every compared place has a value; otherwise the verdict says why it
    cannot be judged. Nothing is estimated to fill a gap.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        params = request.query_params
        raw = [v.strip() for v in (params.get("ids") or params.get("slugs") or "").split(",") if v.strip()]
        raw = list(dict.fromkeys(raw))
        if not 2 <= len(raw) <= 4:
            return Response({"detail": "Choose 2 to 4 destinations to compare."}, status=status.HTTP_400_BAD_REQUEST)
        ids = [int(v) for v in raw if v.isdigit()]
        slugs = [v for v in raw if not v.isdigit()]
        qs = Destination.publicly_visible().filter(Q(id__in=ids) | Q(slug__in=slugs)).select_related("category")
        by_key = {}
        for d in qs:
            by_key[str(d.id)] = d
            by_key[d.slug] = d
        dests = [by_key[v] for v in raw if v in by_key]
        dests = list({d.id: d for d in dests}.values())
        if len(dests) < 2:
            return Response({"detail": "At least two of those destinations were not found."},
                            status=status.HTTP_404_NOT_FOUND)
        month = tf.parse_month(params.get("month"))
        origin = tf.resolve_origin(params)
        nationality = treq.normalize_nationality(params.get("nationality") or "foreign")
        days = _int(params, "days", 1, 90)
        rows_by_id = {r["id"]: r for r in tf.fact_rows()}
        cards = _cards(request, [d.id for d in dests])
        places = []
        for d in dests:
            row = rows_by_id.get(d.id)
            if row is None:
                continue
            req = treq.destination_requirements(d, nationality=nationality, days=days, month=month)
            sentiment = destination_sentiment(d)
            places.append({
                "id": d.id, "name": d.name, "slug": d.slug, "card": cards.get(d.id),
                "facts": tf.facts_for_row(row, month=month, origin=origin),
                "requirements": {
                    "fixed_fees_npr_per_person": _fixed_fee_npr(req),
                    "fees": req["fees"], "restricted": [r["name"] for r in req["restricted_areas"]],
                    "protected": [p["name"] for p in req["protected_areas"]],
                    "tims_required": bool(req["tims"]), "insurance_priority": req["insurance"]["priority"],
                    "matching_note": req["matching_note"],
                },
                "hotels": {
                    "verified": Hotel.objects.filter(destination=d, is_active=True, archived_at__isnull=True, is_verified=True).count(),
                    "unverified": Hotel.objects.filter(destination=d, is_active=True, archived_at__isnull=True, is_verified=False).count(),
                },
                "sentiment": {k: sentiment.get(k) for k in ("status", "review_count", "overall", "message", "ratings")},
            })
        return Response({"month": month, "month_name": tf.MONTH_NAMES[month] if month else None,
                         "origin": origin, "nationality": nationality, "days": days,
                         "places": places, "verdicts": self._verdicts(places, month, origin)})

    @staticmethod
    def _verdicts(places, month, origin):
        def judge(key, title, getter, better, fmt, missing_reason):
            values = [(p, getter(p)) for p in places]
            if any(v is None for _p, v in values):
                lacking = [p["name"] for p, v in values if v is None]
                return {"key": key, "title": title, "winner": None, "judged": False,
                        "explanation": f"Can't judge: {missing_reason} for {', '.join(lacking)}."}
            best_value = better(v for _p, v in values)
            winners = [p for p, v in values if v == best_value]
            detail = "; ".join(f"{p['name']}: {fmt(v)}" for p, v in values)
            if len(winners) == len(places):
                return {"key": key, "title": title, "winner": None, "judged": True, "tie": True,
                        "explanation": f"No difference. {detail}."}
            return {"key": key, "title": title, "judged": True, "tie": len(winners) > 1,
                    "winner": [w["id"] for w in winners], "winner_names": [w["name"] for w in winners],
                    "explanation": detail + "."}

        verdicts = []
        if month:
            verdicts.append(judge(
                "season", f"Better in {tf.MONTH_NAMES[month]}",
                lambda p: p["facts"]["season"]["score"], max,
                lambda v: tf.SEASON_LEVEL_LABELS[{s: k for k, s in tf.SEASON_LEVELS.items()}[v]],
                "no season data"))
        if origin:
            verdicts.append(judge("distance", f"Closer to {origin['label']}",
                                  lambda p: p["facts"]["distance_from_origin_km"], min,
                                  lambda v: f"{v:,.0f} km straight line", "no coordinates"))
        verdicts.append(judge("altitude", "Lower altitude (less altitude-sickness risk)",
                              lambda p: p["facts"]["elevation"]["meters"], min,
                              lambda v: f"{v:,} m", "no measured elevation"))
        verdicts.append(judge("fees", "Lower fixed official fees per person",
                              lambda p: p["requirements"]["fixed_fees_npr_per_person"]
                              if not p["requirements"]["restricted"] else None,
                              min, lambda v: f"NPR {v:,}",
                              "a restricted-area permit (priced per day in USD) applies"))
        verdicts.append(judge("hospital", "Nearer hospital on record",
                              lambda p: (p["facts"]["nearest_hospital"] or {}).get("km"), min,
                              lambda v: f"{v} km", "no hospital on record nearby"))
        verdicts.append(judge("reviews", "More traveller reviews",
                              lambda p: p["sentiment"]["review_count"], max,
                              lambda v: f"{v} review{'s' if v != 1 else ''}", "no review data"))
        return verdicts


# --------------------------------------------------------------------------
# Sentiment
# --------------------------------------------------------------------------
class DestinationSentimentView(APIView):
    """GET /api/v1/destinations/<id-or-slug>/sentiment/."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, key):
        qs = Destination.publicly_visible()
        dest = get_object_or_404(qs, pk=int(key)) if str(key).isdigit() else get_object_or_404(qs, slug=key)
        return Response(destination_sentiment(dest))


# --------------------------------------------------------------------------
# Travel-plan sharing
# --------------------------------------------------------------------------
PRIVATE_PLAN_KEYS = {"notes", "user", "user_email", "email", "phone", "contact", "budget_notes", "cost_notes"}


def _public_plan_data(data):
    """Drop private keys from the saved itinerary JSON, recursively."""
    if isinstance(data, dict):
        return {k: _public_plan_data(v) for k, v in data.items() if k not in PRIVATE_PLAN_KEYS}
    if isinstance(data, list):
        return [_public_plan_data(v) for v in data]
    return data


def share_url(request, token) -> str:
    return f"/plans/shared/{token}"


class TravelPlanShareView(APIView):
    """POST creates (or returns) the plan's share link; DELETE revokes it. Owner only."""

    permission_classes = [permissions.IsAuthenticated]

    def _plan(self, request, pk):
        # Only the owner may publish or revoke; staff access to plans does not
        # extend to making someone else's plan public.
        return get_object_or_404(TravelPlan.objects.exclude(status="archived"), pk=pk, user=request.user)

    def post(self, request, pk):
        plan = self._plan(request, pk)
        if request.data.get("rotate") or plan.share_token is None:
            plan.share_token = uuid4()
            plan.shared_at = timezone.now()
            plan.save(update_fields=["share_token", "shared_at", "updated_at"])
        return Response({"shared": True, "token": str(plan.share_token), "path": share_url(request, plan.share_token),
                         "shared_at": plan.shared_at})

    def delete(self, request, pk):
        plan = self._plan(request, pk)
        plan.share_token = None
        plan.shared_at = None
        plan.save(update_fields=["share_token", "shared_at", "updated_at"])
        return Response({"shared": False})


class SharedTravelPlanView(APIView):
    """GET /api/v1/shared-plans/<uuid>/: read-only public copy of a shared plan."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        plan = get_object_or_404(
            TravelPlan.objects.exclude(status="archived").prefetch_related("stops__destination"),
            share_token=token,
        )
        stops = [{"day": s.day_number, "order": s.display_order, "destination": s.destination.name,
                  "slug": s.destination.slug} for s in plan.stops.all().order_by("day_number", "display_order")
                 if s.destination.is_active and s.destination.status == Destination.SubmissionStatus.APPROVED]
        return Response({
            "title": plan.title, "start_date": plan.start_date, "end_date": plan.end_date,
            "travelers": plan.travelers, "interests": plan.interests,
            "itinerary": _public_plan_data(plan.itinerary_data), "stops": stops,
            "shared_at": plan.shared_at, "updated_at": plan.updated_at,
            "privacy": "Shared read-only by the plan's owner. Their name, email and private notes are not included.",
        })
