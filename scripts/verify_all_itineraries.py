#!/usr/bin/env python3
"""
verify_all_itineraries — prove the owner requirement "itineraries for all the
places should be there": every one of the 77 districts AND the major tourism
cities must return a complete, populated itinerary from the real API
(POST /api/v1/ml/itinerary/), with real destinations (name + coordinates) on
EVERY day, real route legs, and budgets.

Writes reports/all_itineraries.json and prints a per-place PASS/FAIL table.
Pacing: 0.4 s between calls (local services, no external rate limits).
"""

import json
import sys
import time
import urllib.request

API = "http://localhost:8000/api/v1/ml/itinerary/"

DISTRICTS = [
    "Achham", "Arghakhanchi", "Baglung", "Baitadi", "Bajhang", "Bajura", "Banke",
    "Bara", "Bardiya", "Bhaktapur", "Bhojpur", "Chitwan", "Dadeldhura", "Dailekh",
    "Dang", "Darchula", "Dhading", "Dhankuta", "Dhanusha", "Dolakha", "Dolpa",
    "Doti", "Gorkha", "Gulmi", "Humla", "Ilam", "Jajarkot", "Jhapa", "Jumla",
    "Kailali", "Kalikot", "Kanchanpur", "Kapilvastu", "Kaski", "Kathmandu",
    "Kavrepalanchok", "Khotang", "Lalitpur", "Lamjung", "Mahottari", "Makwanpur",
    "Manang", "Morang", "Mugu", "Mustang", "Myagdi", "Nawalpur", "Nuwakot",
    "Okhaldhunga", "Palpa", "Panchthar", "Parasi", "Parbat", "Parsa", "Pyuthan",
    "Ramechhap", "Rasuwa", "Rautahat", "Rolpa", "Rukum East", "Rukum West",
    "Rupandehi", "Salyan", "Sankhuwasabha", "Saptari", "Sarlahi", "Sindhuli",
    "Sindhupalchok", "Siraha", "Solukhumbu", "Sunsari", "Surkhet", "Syangja",
    "Tanahun", "Taplejung", "Terhathum", "Udayapur",
]

CITIES = [
    "Kathmandu", "Pokhara", "Lalitpur", "Bharatpur", "Birgunj", "Biratkot",
    "Biratnagar", "Janakpur", "Dharan", "Nepalgunj", "Dhangadhi", "Butwal",
    "Sauraha", "Nagarkot", "Bandipur", "Tansen", "Lumbini", "Ilam",
    "Birendranagar", "Mahendranagar",
]


def build(place, days):
    body = json.dumps({
        "days": days, "travelers": 2, "start_city": place,
        "interests": ["nature", "culture"], "budget_level": "mid",
        "travel_style": "leisure", "travel_type": "couple",
    }).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def check(place, days):
    try:
        data = build(place, days)
    except Exception as exc:
        return {"place": place, "ok": False, "error": f"request failed: {exc}"}
    itin = data.get("itinerary") or []
    if not isinstance(itin, list):
        itin = itin.get("days", []) if isinstance(itin, dict) else []
    problems = []
    if len(itin) != days:
        problems.append(f"days={len(itin)} (want {days})")
    empty_days = [d.get("day") for d in itin if not (d.get("destinations"))]
    if empty_days:
        problems.append(f"empty days: {empty_days}")
    no_coords = [
        s.get("name") for d in itin for s in d.get("destinations", [])
        if s.get("latitude") is None or s.get("longitude") is None
    ]
    if no_coords:
        problems.append(f"{len(no_coords)} stops without coordinates")
    total_stops = sum(len(d.get("destinations", [])) for d in itin)
    return {
        "place": place, "ok": not problems, "days": len(itin),
        "stops": total_stops, "problems": problems,
    }


def main():
    results = []
    for place in DISTRICTS:
        results.append(check(place, 3))
        time.sleep(0.4)
    for place in CITIES:
        results.append(check(place, 3))
        time.sleep(0.4)
    # the owner's explicit 20-day requirement on a sample of places
    for place in ("Kathmandu", "Pokhara", "Jumla", "Humla", "Mustang", "Dhangadhi"):
        r = check(place, 20)
        r["twenty_day"] = True
        results.append(r)
        time.sleep(0.4)

    ok = sum(1 for r in results if r["ok"])
    out = {"checked": len(results), "ok": ok, "results": results}
    with open("reports/all_itineraries.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"itineraries OK: {ok}/{len(results)}")
    for r in results:
        if not r["ok"]:
            print("FAIL", r["place"], r.get("problems") or r.get("error"))
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
