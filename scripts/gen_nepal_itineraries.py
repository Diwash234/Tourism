import csv, yaml, pathlib
csv_path = pathlib.Path(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\nepal_cities_200.csv')
out_path = pathlib.Path(r'C:\Users\ADMIN\Desktop\Chatbot\Tourism\dataset\nepal_city_itineraries_200.yaml')

rows = list(csv.DictReader(csv_path.open(newline='', encoding='utf-8')))

# The project's canonical 200-city list lives in tourist/city_15_day_planner.py
# and asserts exactly 200 unique names. Generate from that list so the dataset
# and the planner can never drift apart, and drop the duplicate placeholder
# rows the hand-written CSV carries.
try:
    import sys as _sys
    _sys.path.insert(0, r"C:\Users\ADMIN\Desktop\Chatbot\Tourism\tourist")
    from city_15_day_planner import CITY_CATALOG
except Exception as _exc:  # pragma: no cover - fallback keeps the script usable
    print("WARN: could not load canonical city catalog:", _exc)
    CITY_CATALOG = ()

_seen = set()
_clean = []
for _r in rows:
    _name = (_r.get("city") or "").strip()
    if not _name or "(duplicate" in _name or _name.casefold() in _seen:
        continue
    _seen.add(_name.casefold())
    _clean.append(_r)
rows = _clean

if CITY_CATALOG:
    _by_name = {(_r.get("city") or "").strip().casefold(): _r for _r in rows}
    _merged = []
    for _planned in CITY_CATALOG:
        _name = (_planned.get("name") or "").strip()
        _row = _by_name.get(_name.casefold())
        if _row is None:
            _row = {
                "city": _name,
                "province": _planned.get("province", ""),
                "district": "",
                "population_2021": "",
                "type": "municipality",
            }
        _merged.append(_row)
    rows = _merged
# The verified, fully-written 15-day Pokhara itinerary (the reference sample).
# Every other city uses the generic province-aware template below.
DETAILED_POKHARA = {
    'Pokhara': [
        "Day 1 - Arrive Pokhara International Airport -> hotel -> Lakeside walk -> Phewa Lake sunset.",
        "Day 2 - Sarangkot sunrise (10-13 km, 30-40 min) -> optional tandem paragliding -> Lakeside.",
        "Day 3 - Davis Falls -> Gupteshwor Cave -> International Mountain Museum -> Lakeside.",
        "Day 4 - Phewa Lake boat -> World Peace Pagoda hike -> sunset boat ride.",
        "Day 5 - Pumdikot Shiva statue (6-8 km, uphill) -> Damside -> relaxed Lakeside evening.",
        "Day 6 - Begnas Lake -> Rupa Lake (14-15 km, 40-50 min) -> return Pokhara.",
        "Day 7 - Bindhyabasini Temple -> Old Bazaar -> Seti River Gorge viewpoint.",
        "Day 8 - Kande -> Australian Camp -> Dhampus (25 km to Kande; genuine hiking day).",
        "Day 9 - Rest day: sleep late, spa/massage, Phewa Lake kayaking.",
        "Day 10 - Pokhara -> Nayapul -> Birethanti -> Ghandruk village overnight.",
        "Day 11 - Ghandruk sunrise -> return via Nayapul to Pokhara.",
        "Day 12 - Lakeside -> Sarangkot overnight at a mountain lodge.",
        "Day 13 - Sarangkot sunrise -> return to Lakeside; last relaxed Phewa evening.",
        "Day 14 - Bandipur day trip (72-80 km, ~2-2.5 h each way).",
        "Day 15 - Lakeside morning -> shopping -> Pokhara International Airport (allow 30-45 min buffer).",
    ],
}

out = {
    'note': ("Machine-readable 15-day itinerary pack for 200 main cities. "
             "Pokhara carries the fully verified reference itinerary; the other "
             "cities carry a province-aware template. Hotel, hospital, image and "
             "destination fields are populated from the live database by "
             "scripts/enrich_itineraries_from_db.py and should be verified live."),
    'cities': []
}

def province_context(prov):
    return {
        'Bagmati': 'city/heritage day: Kathmandu Valley sights, Thamel dinner, Durbar Squares.',
        'Koshi': 'hill-tea/hillside day: Birtamod/Dharan/Ilam area, tea gardens, Himalayan views.',
        'Madhesh': 'south plains day: Birgunj/Janakpur/Kalaiya, Mithila craft and market day.',
        'Lumbini': 'Buddhist circuit day: Lumbini/Tilottama, Butwal/Tansen, village walk.',
        'Gandaki': 'Pokhara-style lake/mountain day: lakeside, Sarangkot, trekking to village lodge.',
        'Karnali': 'remote highland day: Birendranagar, lake Phe/Bagchaur, Rara-like scenic stay.',
        'Sudurpashchim': 'far west day: Dhangadhi, Kanchanpur, access to Ashtamangal/Punarbas.',
    }.get(prov.split()[0], 'city day: local market, temple tour, sunset view.')

for row in rows:
    city = row['city']
    prov = row['province']
    district = row['district']
    if city in DETAILED_POKHARA:
        days = DETAILED_POKHARA[city]
    else:
        days = [
            f"Day 1 - arrive in {city}; {city} hotel check-in; local orientation walk.",
            f"Day 2 - main cultural site in {district}/{city}.",
            "Day 3 - nearby hillside/scenic drive; sunset view.",
            "Day 4 - river/lake/forest activity and lunch.",
            "Day 5 - village/monastery/tea garden exploring.",
            "Day 6 - rest day at hotel; local spa/massage optional.",
            "Day 7 - day trip to adjacent town in same district.",
            "Day 8 - soft adventure day: hiking/kayak/paragliding if available.",
            "Day 9 - market shopping, handicraft centre, coffee.",
            "Day 10 - mountain views if weather allows; otherwise indoor museum.",
            "Day 11 - another scenic village or religious site.",
            "Day 12 - relaxed cafe morning, local dinner, last evening walk.",
            "Day 13 - pack; check out; drive to nearest major town/airport.",
            "Day 14 - buffer / contingency weather/road-day.",
            "Day 15 - departure transfer to nearest airport/highway.",
        ]
    entry = {
        'city': city,
        'province': prov,
        'district': district,
        'population_2021': (int(row['population_2021'])
                           if str(row.get('population_2021') or '').isdigit()
                           else row.get('population_2021') or ''),
        'type': row.get('type') or 'municipality',
        'sample_hotel': f'{city} Grand Palace Hotel / {city} Neighbourhood Guest House',
        'sample_hospital': f'{city} District Hospital / {city} Government Hospital',
        'sample_transport': 'Private taxi or shared jeep; local bus for intercity; airport shuttle where listed.',
        'approx_route_from_kathmandu': 'Kathmandu → main highway/east-west road to city (times vary)',
        'transport_notes': 'Road conditions vary; always allow extra time and confirm pickup times.',
        'day_by_day': days,
        'province_context': province_context(prov),
    }
    out['cities'].append(entry)

out_path.write_text(yaml.dump(out, sort_keys=False, allow_unicode=True), encoding='utf-8')
print('Wrote', out_path)
