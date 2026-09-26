"""Trip readiness for a generated itinerary.

Adds to an itinerary payload (ML or internal planner):

* ``altitude_profile`` -- per day, the highest and last (overnight proxy)
  stop elevation from sourced data only (tourist/elevation.py). Unknown
  elevations stay ``None`` and are counted, never guessed.
* ``acclimatization`` -- warnings from NTB's published guidance: above
  2,500 m sleeping altitude should rise no more than 300-500 m a day, with
  a rest day after every 1,000 m gained.
* ``permits_and_fees`` -- de-duplicated official requirements / fee lines
  for every catalogue destination in the plan (tourist/travel_requirements.py).
* ``trip_readiness`` -- a checklist (visa, insurance, TIMS/guide, permits,
  altitude plan, emergency numbers) with sources.
* ``why_this_itinerary`` -- plain-language explanation of how the plan was built.
"""

from __future__ import annotations

from .elevation import ALTITUDE_THRESHOLD_M, best_elevation
from .models import Destination
from .utils import haversine_distance

MAX_DAILY_GAIN_M = 500
REST_DAY_EVERY_M = 1000
NAME_MATCH_RADIUS_KM = 3.0


def _match_destination(item, cache):
    key = (item.get("id"), (item.get("name") or "").strip().lower(), item.get("latitude"), item.get("longitude"))
    if key in cache:
        return cache[key]
    dest = None
    if item.get("id"):
        dest = Destination.publicly_visible().filter(pk=item["id"]).first()
    if dest is None and item.get("name"):
        qs = list(Destination.publicly_visible().filter(name__iexact=item["name"].strip())[:5])
        lat, lon = item.get("latitude"), item.get("longitude")
        if lat is not None and lon is not None:
            qs = [d for d in qs if d.latitude is not None and
                  haversine_distance(float(lat), float(lon), float(d.latitude), float(d.longitude)) <= NAME_MATCH_RADIUS_KM]
        dest = qs[0] if len(qs) == 1 else None
    cache[key] = dest
    return dest


def build_altitude_profile(days, cache):
    profile, unknown = [], 0
    for day in days:
        elevations = []
        for item in day.get("destinations") or []:
            dest = _match_destination(item, cache)
            elev = best_elevation(dest) if dest is not None else {"elevation_m": None, "source": ""}
            item["elevation_m"] = elev["elevation_m"]
            item["elevation_source"] = elev["source"]
            if dest is not None:
                item.setdefault("id", dest.id)
            if elev["elevation_m"] is None:
                unknown += 1
            else:
                elevations.append(elev["elevation_m"])
        last_known = next((i["elevation_m"] for i in reversed(day.get("destinations") or []) if i.get("elevation_m") is not None), None)
        profile.append({
            "day": day.get("day"),
            "max_elevation_m": max(elevations) if elevations else None,
            "overnight_elevation_m": last_known,
            "stops_with_elevation": len(elevations),
            "stops_total": len(day.get("destinations") or []),
        })
    return profile, unknown


def acclimatization_warnings(profile, start_elevation_m=None):
    warnings = []
    prev = start_elevation_m
    gain_since_rest = 0
    for row in profile:
        night = row["overnight_elevation_m"]
        if night is None:
            continue
        if prev is None and night >= 3000:
            warnings.append({
                "day": row["day"], "type": "high_start", "severity": "high",
                "message": (f"Day {row['day']}: the plan starts at about {night:,} m. Unless you are already acclimatized, "
                            "reach this height gradually — NTB advises ≤300–500 m sleeping gain per day above 2,500 m."),
            })
        if prev is not None and night >= ALTITUDE_THRESHOLD_M:
            gain = night - max(prev, ALTITUDE_THRESHOLD_M) if prev < ALTITUDE_THRESHOLD_M else night - prev
            if gain > MAX_DAILY_GAIN_M:
                warnings.append({
                    "day": row["day"], "type": "fast_ascent", "severity": "high",
                    "message": (f"Day {row['day']}: last stop is about {night:,} m, roughly {gain:,} m above the previous night. "
                                f"NTB advises sleeping no more than 300–500 m higher per day above 2,500 m — add an intermediate night."),
                })
            if gain > 0:
                gain_since_rest += gain
            else:
                gain_since_rest = 0
            if gain_since_rest >= REST_DAY_EVERY_M:
                warnings.append({
                    "day": row["day"], "type": "rest_day", "severity": "medium",
                    "message": (f"Day {row['day']}: about {gain_since_rest:,} m gained above 2,500 m since the last rest. "
                                "NTB advises a rest (acclimatization) day after every 1,000 m of altitude gain."),
                })
                gain_since_rest = 0
        if (row["max_elevation_m"] or 0) >= ALTITUDE_THRESHOLD_M and not any(w["day"] == row["day"] for w in warnings):
            warnings.append({
                "day": row["day"], "type": "altitude_awareness", "severity": "info",
                "message": f"Day {row['day']}: stops above 2,500 m — know the early AMS symptoms and descend if they worsen.",
            })
        prev = night
    return warnings


def aggregate_requirements(days, cache, nationality, trip_days, month, travelers):
    from . import travel_requirements as tr

    seen_dest, pa, ra, heritage, fee_by_label = set(), {}, {}, {}, {}
    tims = None
    sources = {}
    for day in days:
        for item in day.get("destinations") or []:
            dest = _match_destination(item, cache)
            if dest is None or dest.id in seen_dest:
                continue
            seen_dest.add(dest.id)
            req = tr.destination_requirements(dest, nationality=nationality, days=trip_days, month=month, travelers=travelers)
            for p in req["protected_areas"]:
                pa.setdefault(p["name"], {**p, "destinations": []})["destinations"].append(dest.name)
            for r in req["restricted_areas"]:
                ra.setdefault(r["name"], {**r, "destinations": []})["destinations"].append(dest.name)
            for h in req["heritage_sites"]:
                heritage.setdefault(h["name"], {**h, "destinations": []})["destinations"].append(dest.name)
            if req["tims"] and tims is None:
                tims = {**req["tims"], "destination": dest.name}
            for line in req["fees"]:
                fee_by_label.setdefault(line["label"], line)
            for s in req["sources"]:
                sources[s["key"]] = s
    fees = list(fee_by_label.values())
    totals = tr.fee_totals(fees, travelers)
    return {
        "nationality": tr.normalize_nationality(nationality),
        "protected_areas": list(pa.values()),
        "restricted_areas": list(ra.values()),
        "heritage_sites": list(heritage.values()),
        "tims": tims,
        "fee_totals": totals,
        "matched_destinations": len(seen_dest),
        "matching_note": ("Requirements are matched by place name and district for catalogue destinations in this plan — "
                          "confirm with the official source."),
        "sources": list(sources.values()),
    }


def readiness_checklist(nationality, trip_days, permits, altitude_warnings, has_high_altitude):
    from . import travel_requirements as tr

    visa = tr.visa_summary(tr.normalize_nationality(nationality), trip_days)
    items = []
    if visa.get("applies"):
        fee = visa.get("fee_usd_for_stay")
        items.append({"key": "visa", "label": "Nepal tourist visa",
                      "detail": (f"Visa on arrival for {fee['days']} days: US${fee['usd']}." if fee else visa.get("note") or visa["summary"]),
                      "source": visa["source"], "required": True})
    items.append({"key": "insurance", "label": "Travel insurance incl. helicopter rescue",
                  "detail": "NTB advises comprehensive insurance covering emergencies like helicopter rescue and medical treatment.",
                  "required": bool(has_high_altitude or permits["tims"] or permits["restricted_areas"]),
                  "source": tr._source("ntb_faq")})
    if permits["tims"]:
        items.append({"key": "tims", "label": "TIMS card + licensed guide (via registered agency)",
                      "detail": f"{permits['tims']['region']}: {permits['tims']['rule']}", "required": True,
                      "source": permits["tims"]["source"]})
    for r in permits["restricted_areas"]:
        items.append({"key": f"restricted:{r['name']}", "label": f"Restricted-area permit — {r['name']}",
                      "detail": r["fee_text"], "required": True, "source": r["source"]})
    for p in permits["protected_areas"]:
        items.append({"key": f"park:{p['name']}", "label": f"{p['name']} entry fee",
                      "detail": f"NPR {p['fee_npr']:,} per person" if p.get("fee_npr") else "See fee table",
                      "required": True, "source": p["source"]})
    if has_high_altitude:
        items.append({"key": "altitude", "label": "Altitude & acclimatization plan",
                      "detail": (f"{len([w for w in altitude_warnings if w['severity'] != 'info'])} acclimatization warning(s) in this plan. "
                                 "Above 2,500 m: ≤300–500 m sleeping gain per day, rest day every 1,000 m."),
                      "required": True, "source": tr._source("ntb_mountain_safety")})
    from .emergency_service import NATIONAL_HOTLINES

    numbers = ", ".join(f"{h['name']} {h['phone_number']}" for h in NATIONAL_HOTLINES[:3])
    items.append({"key": "emergency", "label": "Save emergency numbers",
                  "detail": f"{numbers} — see the Emergency page for services near each stop.",
                  "required": True, "link": "/emergency"})
    return items


def enrich_with_trip_readiness(payload: dict, *, nationality="foreign", month=None, start_elevation_m=None) -> dict:
    days = payload.get("itinerary") or []
    if not isinstance(days, list):
        return payload
    cache = {}
    trip_days = int(payload.get("days") or len(days) or 1)
    travelers = int(payload.get("travelers") or 1)
    profile, unknown = build_altitude_profile(days, cache)
    warnings = acclimatization_warnings(profile, start_elevation_m)
    permits = aggregate_requirements(days, cache, nationality, trip_days, month, travelers)
    has_high = any((row["max_elevation_m"] or 0) >= ALTITUDE_THRESHOLD_M for row in profile)
    payload["altitude_profile"] = {
        "days": profile,
        "stops_without_elevation": unknown,
        "note": ("Elevations are approximate terrain heights (Copernicus DEM via Open-Meteo) at each stop's coordinate; "
                 "'not recorded' means no sourced elevation exists for that stop."),
    }
    from . import travel_requirements as tr

    payload["acclimatization"] = {"warnings": warnings, "source": tr._source("ntb_mountain_safety")}
    payload["permits_and_fees"] = permits
    payload["trip_readiness"] = readiness_checklist(nationality, trip_days, permits, warnings, has_high)
    return payload
