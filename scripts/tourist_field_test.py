#!/usr/bin/env python3
"""Tourist field test — "you are standing at place X, what does the app give you?"

For every place in the lists below (real places supplied by the product owner,
grouped by district), this script exercises the LIVE public API exactly like
the tourist site does:

  1. SEARCH    GET /places/search/?q=<place>            -> is the place known?
  2. NAVIGATE  POST /navigation/road-route/             -> route, distance, ETA
               (tourist at the place -> district hub)       + honest source label
  3. SERVICES  GET /places/nearby/?category=...         -> nearest hospital,
               hospital / hotel / restaurant / bank /       hotel, restaurant,
               police                                       bank, police

Nothing is fabricated: a place the database does not know is reported as NOT
FOUND, a category with no records is reported as 0 (with the provider fallback
label when applicable). Results are written to reports/tourist_field_test.json
and reports/tourist_field_test.md.

Usage:  python3 scripts/tourist_field_test.py [--api http://127.0.0.1:8000/api/v1]
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# District hubs = where a tourist would typically head from a surrounding
# place. Coordinates are real town-centre points, used only as navigation
# destinations for this test (the platform itself resolves everything from
# its own database).
HUBS = {
    "Dhankuta":   ("Dhankuta Bazaar", 26.9833, 87.3333),
    "Kailali":    ("Dhangadhi", 28.7000, 80.5700),
    "Pokhara":    ("Phewa Lake", 28.2096, 83.9856),
    "Kathmandu":  ("Kathmandu Durbar Square", 27.7075, 85.3075),
    "Syangja":    ("Putalibazar", 28.1000, 83.8500),
    "Waling":     ("Waling Bazaar", 28.6300, 83.7700),
    "Parbat":     ("Kusma Bazaar", 28.2200, 83.6700),
    "Kanchanpur": ("Mahendranagar", 28.9300, 80.3000),
    "Kapilvastu": ("Taulihawa", 27.5300, 83.0500),
    "Doti":       ("Dipayal Silgadhi", 29.2000, 80.9000),
    "Darchula":   ("Khalanga", 29.9400, 80.7500),
    "Dadeldhura": ("Amargadhi", 29.3000, 80.4800),
    "Bajura":     ("Martadi", 29.4300, 81.4500),
    "Baitadi":    ("Dasharathchand", 29.5200, 80.4700),
    "Bajhang":    ("Chainpur", 29.7000, 81.2500),
    "Achham":     ("Mangalsen", 29.0300, 81.2500),
}

PLACES = {
    "Dhankuta": ["Hile", "Bhedetar", "Pakhribas", "Namaste Jharna", "Rajarani",
                 "Pathibhara Temple", "Dhankuta Bazaar", "Mulghat"],
    "Kailali": ["Jokhar Taal", "Dhangadhi Stadium", "Ghodaghodi Lake", "Godawari",
                "Tikapur", "Karnali Bridge", "Geta", "Mohana Bridge", "Tikapur Park",
                "Chisapani", "Rajghat", "Shivapuri Dham", "Bhada Village"],
    "Pokhara": ["Phewa Lake", "Lakeside", "Sarangkot", "World Peace Pagoda",
                "Davis Falls", "Gupteshwor Cave", "Begnas Lake", "Mahendra Cave",
                "International Mountain Museum", "Bindhyabasini Temple", "Seti Gorge",
                "Australian Camp"],
    "Kathmandu": ["Swayambhunath", "Boudhanath Stupa", "Pashupatinath Temple",
                  "Kathmandu Durbar Square", "Patan Durbar Square",
                  "Bhaktapur Durbar Square", "Garden of Dreams", "Thamel",
                  "Chandragiri Hills", "Nagarkot", "Kirtipur"],
    "Syangja": ["Putalibazar", "Waling", "Arjunchaupari", "Sirubari",
                "Chhangchhangdi", "Aandhikhola", "Bhirkot", "Galyang", "Ramkot",
                "Swasthani Temple"],
    "Waling": ["Waling Bazaar", "Ramdi", "Mirmi", "Keware Bhanjyang", "Huwas",
               "Setibeni"],
    "Parbat": ["Kusma Bazaar", "Kushma Suspension Bridge", "Modi Khola",
               "Pataley Chhango", "Panchase", "Durlung", "Phalebas",
               "Baglung Kalika"],
    "Kanchanpur": ["Shuklaphanta National Park", "Mahendranagar", "Dodhara Chandani",
                   "Gaddachauki", "Mahakali River", "Bedkot Lake", "Rani Tal",
                   "Jhilmila Lake", "Brahmadev", "Jogbudha", "Daiji",
                   "Siddhanath Temple"],
    "Kapilvastu": ["Tilaurakot", "Kudan", "Niglihawa", "Gotihawa", "Sagarhawa",
                   "Araurakot", "Banganga", "Taulihawa", "Jagdishpur Reservoir",
                   "Lumbini", "Ramgram", "Kapilvastu Museum"],
    "Doti": ["Dipayal Silgadhi", "Khaptad National Park", "Shaileshwari Temple",
             "Badimalika", "Seti River", "Doti Durbar", "Gopghat", "Sanfe",
             "Jorayal", "Budar"],
    "Darchula": ["Khalanga", "Api Nampa Conservation Area", "Api Himal",
                 "Malikarjun Temple", "Shailyashikhar", "Latinath", "Byas Valley",
                 "Tinkar", "Lipulekh", "Kalapani"],
    "Dadeldhura": ["Amargadhi", "Dadeldhura Bazaar", "Ugratara Temple", "Alital",
                   "Ganyapdhura", "Ajaymeru", "Amargadhi Fort", "Sahastralinga",
                   "Parshuram Dham"],
    "Bajura": ["Martadi", "Badimalika Temple", "Budhinanda", "Budhinanda Lake",
               "Kolti", "Nateshwori Temple", "Swamikartik", "Gaumul", "Ramaroshan"],
    "Baitadi": ["Dasharathchand", "Patan", "Tripura Sundari Temple",
                "Melauli Bhagwati Temple", "Dehimandau", "Surnaya", "Pancheswor",
                "Dogadakedar", "Shivanath", "Dilashaini"],
    "Bajhang": ["Chainpur", "Saipal Himal", "Surma Sarovar", "Surma Valley",
                "Thalara", "Chhabis Pathibhara", "Talkot", "Kedarsyu",
                "Jayaprithvi"],
    "Achham": ["Mangalsen", "Ramaroshan Lake", "Bannigadhi Jaygadh", "Sanfebagar",
               "Kamalbazar", "Turmakhad", "Panchadeval Binayak", "Baidyanath Dham",
               "Jaygadh"],
}

CATEGORIES = ["hospital", "hotel", "restaurant", "bank", "police"]


def _request_with_retry(req, tries=5):
    """The public API rate-limits anonymous clients (HTTP 429) — that is the
    platform working correctly, so the field test backs off and retries
    instead of recording a false failure."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < tries - 1:
                wait = min(60, 10 * (attempt + 1))
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")


def get_json(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    return _request_with_retry(req)


def post_json(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    return _request_with_retry(req)


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def find_place(api, name):
    """Return (result, match_quality) — exact / partial / None, honestly."""
    data = get_json(f"{api}/places/search/", {"q": name})
    results = data.get("results") or []
    target = norm(name)
    exact, partial = None, None
    for r in results:
        rn = norm(r.get("name") or "")
        lat, lng = r.get("latitude") or r.get("lat"), r.get("longitude") or r.get("lng")
        if lat is None or lng is None:
            continue
        if rn == target:
            exact = r
            break
        if partial is None and (target in rn or rn in target) and len(rn) >= 4:
            partial = r
    if exact:
        return exact, "exact"
    if partial:
        return partial, "partial"
    return None, "not-found"


def nearby_count(api, lat, lng, category):
    try:
        data = get_json(f"{api}/places/nearby/", {
            "lat": lat, "lng": lng, "category": category, "radius_km": 50})
    except Exception as exc:  # report honestly, never guess
        return {"error": str(exc)[:80]}
    results = data.get("results") or data.get("places") or []
    out = {"count": len(results)}
    if data.get("provider_error") or data.get("offline_fallback") or data.get("note"):
        out["note"] = data.get("note") or "offline fallback"
    if results:
        first = results[0]
        out["nearest"] = first.get("name")
        out["nearest_km"] = first.get("distance_km")
    return out


def route(api, start, end, mode="driving"):
    try:
        data = post_json(f"{api}/navigation/road-route/", {
            "start": {"latitude": start[0], "longitude": start[1]},
            "destination": {"latitude": end[0], "longitude": end[1]},
            "mode": mode})
    except Exception as exc:
        return {"error": str(exc)[:120]}
    r = data.get("route") or {}
    return {
        "distance_km": round((r.get("distance_m") or 0) / 1000, 1),
        "duration_min": round((r.get("duration_s") or 0) / 60),
        "source": r.get("source"),
        "navigation_grade": r.get("navigation_grade"),
        "geometry_points": len(r.get("geometry") or []),
        "note": r.get("note"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=os.environ.get("E2E_API", "http://127.0.0.1:8000/api/v1"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "reports"))
    args = ap.parse_args()

    report = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "api": args.api, "districts": {}}
    totals = {"places": 0, "found_exact": 0, "found_partial": 0, "not_found": 0,
              "routes_ok": 0, "routes_fallback": 0, "routes_failed": 0}

    for district, places in PLACES.items():
        hub_name, hub_lat, hub_lng = HUBS[district]
        rows = []
        seen = set()
        for place in places:
            if norm(place) in seen:
                continue
            seen.add(norm(place))
            totals["places"] += 1
            row = {"place": place}
            hit, quality = find_place(args.api, place)
            row["search"] = quality
            if hit:
                lat = hit.get("latitude") or hit.get("lat")
                lng = hit.get("longitude") or hit.get("lng")
                row["matched_name"] = hit.get("name")
                row["district_in_db"] = hit.get("district") or ""
                totals[f"found_{quality}"] += 1
                rt = route(args.api, (float(lat), float(lng)), (hub_lat, hub_lng))
                row["route_to_hub"] = rt
                if rt.get("error"):
                    totals["routes_failed"] += 1
                elif rt.get("source") == "osrm":
                    totals["routes_ok"] += 1
                else:
                    totals["routes_fallback"] += 1
                for cat in CATEGORIES:
                    row[f"nearby_{cat}"] = nearby_count(args.api, float(lat), float(lng), cat)
            else:
                totals["not_found"] += 1
            rows.append(row)
            print(f"  {district:<11} {place:<32} {quality}", flush=True)
        report["districts"][district] = {"hub": hub_name, "rows": rows}

    report["totals"] = totals
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "tourist_field_test.json"), "w") as fh:
        json.dump(report, fh, indent=2)

    # Markdown summary
    md = ["# Tourist field test — live API results", "",
          f"Generated: {report['generated_at']} · API: {args.api}",
          f"Totals: {totals['places']} places checked · exact {totals['found_exact']} · "
          f"partial {totals['found_partial']} · not found {totals['not_found']} · "
          f"routes osrm {totals['routes_ok']} / fallback {totals['routes_fallback']} / "
          f"failed {totals['routes_failed']}", ""]
    for district, block in report["districts"].items():
        md.append(f"## {district} (hub: {block['hub']})")
        md.append("| Place | Found | Route to hub | km | min | Source | Hosp | Hotel | Rest | Bank | Police |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for row in block["rows"]:
            if row["search"] == "not-found":
                md.append(f"| {row['place']} | — | — | — | — | — | — | — | — | — | — |")
                continue
            rt = row.get("route_to_hub", {})
            cells = [row["place"], row["search"] + (f" ({row.get('matched_name')})" if row["search"] == "partial" else ""),
                     "✓" if not rt.get("error") else "ERR",
                     rt.get("distance_km", "—"), rt.get("duration_min", "—"), rt.get("source", "—")]
            for cat in CATEGORIES:
                nb = row.get(f"nearby_{cat}", {})
                cells.append(nb.get("count", "ERR") if "count" in nb else "ERR")
            md.append("| " + " | ".join(str(c) for c in cells) + " |")
        md.append("")
    with open(os.path.join(args.out, "tourist_field_test.md"), "w") as fh:
        fh.write("\n".join(md))
    print(json.dumps(totals, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
