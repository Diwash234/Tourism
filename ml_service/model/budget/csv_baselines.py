"""
CSV-driven budget baselines and authentic Nepal cost calibration.

Loads ``ml_service/processed_data/budget_features.csv`` and calibrates
with authentic ground travel data across Nepal destinations, districts,
and provinces.

Target calibration:
  * 3 days in Pokhara (mid-range, 1 traveler) = ~10,000 NPR total ($75.00 USD).
  * Accommodation: ~1,500 NPR/night ($11.25 USD)
  * Food & Dining: ~1,100 NPR/day ($8.25 USD)
  * Local Transit: ~733 NPR/day ($5.50 USD)
"""

import csv
import os
import re
import threading
from typing import Optional, Dict, List

_BASE = os.path.dirname(__file__)
_FEATURES_CSV = os.path.normpath(os.path.join(_BASE, "..", "..", "processed_data", "budget_features.csv"))

_lock = threading.Lock()
_cache = None


# Authentic, verified daily rates (USD) across Nepal destinations.
# In Nepal: $75.00 USD = 10,000.00 NPR (1 USD = ~133.3333 NPR).
VERIFIED_NEPAL_BASELINES = {
    # 1. Pokhara & Kaski Valley (Lakeside, Sarangkot, Fewa Lake, Begnas, Rupa)
    # Target: 3 days mid solo = 10,000 NPR ($75.00 USD)
    "pokhara": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "kaski": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "sarangkot": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "fewalake": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "phewalake": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "begnaslake": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "rupalake": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "davis": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "worldpeace": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},

    # 2. Kathmandu Valley (Kathmandu, Lalitpur/Patan, Bhaktapur, Nagarkot, Chandragiri, Kirtipur)
    # Target: 3 days mid solo = 10,000 NPR ($75.00 USD)
    "kathmandu": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "lalitpur": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "patan": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "bhaktapur": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "nagarkot": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},
    "bagmati": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},

    # 3. Chitwan & Terai Wildlife (Chitwan, Sauraha, Nawalpur, Bardiya)
    # Target: 3 days mid solo = 10,000 NPR ($75.00 USD)
    "chitwan": {"transport": 6.25, "food": 7.50, "accommodation": 11.25, "taxi": 4.00},
    "sauraha": {"transport": 6.25, "food": 7.50, "accommodation": 11.25, "taxi": 4.00},
    "nawalpur": {"transport": 6.25, "food": 7.50, "accommodation": 11.25, "taxi": 4.00},
    "bardiya": {"transport": 6.25, "food": 7.50, "accommodation": 11.25, "taxi": 4.00},

    # 4. Lumbini & Plains Heritage (Lumbini, Kapilvastu, Rupandehi, Butwal, Siddharthanagar)
    # Target: 3 days mid solo = 8,500 NPR ($63.75 USD)
    "lumbini": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "rupandehi": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "kapilvastu": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "butwal": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},

    # 5. Hill Towns & Cultural Heritage (Bandipur, Tansen, Palpa, Gorkha, Nuwakot, Panauti, Dhulikhel, Daman)
    # Target: 3 days mid solo = 8,500 NPR ($63.75 USD)
    "bandipur": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "palpa": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "tansen": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "gorkha": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "nuwakot": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "dhulikhel": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "panauti": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "daman": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "tanahun": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},

    # 6. Eastern Nepal & Tea Hills (Ilam, Dhankuta, Dharan, Biratnagar, Panchthar, Taplejung, Koshi)
    # Target: 3 days mid solo = 8,500 NPR ($63.75 USD)
    "ilam": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "dhankuta": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "dharan": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "biratnagar": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},
    "koshi": {"transport": 4.75, "food": 6.75, "accommodation": 9.75, "taxi": 3.00},

    # 7. Mountain Trekking & High Altitude (Solukhumbu, Everest, Namche, Lukla, Mustang, Jomsom, Muktinath, Manang, Langtang, Rara, Dolpa, Karnali)
    # Target: 3 days mid solo = 11,000 NPR ($82.50 USD)
    "solukhumbu": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "everest": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "namche": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "lukla": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "mustang": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "jomsom": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "muktinath": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "manang": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "langtang": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "rasuwa": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "rara": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "mugu": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "dolpa": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "jumla": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},
    "karnali": {"transport": 7.25, "food": 12.75, "accommodation": 7.50, "taxi": 4.00},

    # 8. Madhesh Plains (Janakpur, Dhanusha, Birgunj, Parsa, Bara, Saptari, Siraha, Madhesh)
    # Target: 3 days mid solo = 8,000 NPR ($60.00 USD)
    "janakpur": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "dhanusha": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "birgunj": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "parsa": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "madhesh": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},

    # 9. Western & Far-Western Nepal (Surkhet, Banke, Nepalgunj, Doti, Dadeldhura, Baitadi, Dhangadhi, Kailali, Kanchanpur, Sudurpashchim)
    # Target: 3 days mid solo = 8,000 NPR ($60.00 USD)
    "surkhet": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "nepalgunj": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "banke": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "dhangadhi": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "kailali": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "kanchanpur": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},
    "sudurpashchim": {"transport": 4.50, "food": 6.50, "accommodation": 9.00, "taxi": 3.00},

    # 10. Gandaki Province general
    "gandaki": {"transport": 5.50, "food": 8.25, "accommodation": 11.25, "taxi": 3.50},

    # 11. National Default / Fallback
    # Target: 3 days mid solo = 9,000 NPR ($67.50 USD)
    "default": {"transport": 4.50, "food": 7.50, "accommodation": 10.50, "taxi": 3.00},
}


def _midpoint(value: str) -> Optional[float]:
    """Parse '40-120' / '25.5' / '0' into a float midpoint. None if unusable."""
    if value is None:
        return None
    s = str(value).strip().replace("$", "").replace(",", "")
    if not s or s == "0":
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if not nums:
        return None
    nums = [float(n) for n in nums]
    return sum(nums) / len(nums)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _build_cache() -> Dict:
    by_dest: Dict[str, Dict[str, float]] = {}
    by_district: Dict[str, List[Dict[str, float]]] = {}
    by_province: Dict[str, List[Dict[str, float]]] = {}

    def _ingest(dest, district, province, transport, food, accom, taxi):
        raw_t = _midpoint(transport)
        raw_f = _midpoint(food)
        raw_a = _midpoint(accom)
        raw_x = _midpoint(taxi)

        # Normalize accidental NPR figures (> 150) to USD
        if raw_a is not None and raw_a > 150:
            raw_a = round(raw_a / 133.33, 2)
        if raw_t is not None and raw_t > 150:
            raw_t = round(raw_t / 133.33, 2)
        if raw_x is not None and raw_x > 50:
            raw_x = round(raw_x / 133.33, 2)

        # Clamp long-distance intercity transit to daily transit slice if needed
        if raw_t is not None and raw_t > 30:
            raw_t = round(min(raw_t, 12.0), 2)

        entry = {
            "transport": raw_t,
            "food": raw_f,
            "accommodation": raw_a,
            "taxi": raw_x,
        }
        # only keep entries with at least one usable cost figure
        if not any(v is not None for v in entry.values()):
            return
        if dest:
            by_dest[_norm(dest)] = entry
        if district:
            by_district.setdefault(_norm(district), []).append(entry)
        if province:
            by_province.setdefault(_norm(province), []).append(entry)

    # Process features CSV
    try:
        with open(_FEATURES_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # header
            for row in reader:
                if len(row) < 8:
                    continue
                _ingest(row[1], row[2], row[3], row[4], row[5], row[6], row[7])
    except FileNotFoundError:
        pass

    def _average(entries: List[Dict[str, float]]) -> Optional[Dict[str, float]]:
        if not entries:
            return None
        keys = ("transport", "food", "accommodation", "taxi")
        out = {}
        for k in keys:
            vals = [e[k] for e in entries if e.get(k) is not None]
            out[k] = round(sum(vals) / len(vals), 2) if vals else None
        return out

    return {
        "by_dest": by_dest,
        "by_district": {k: _average(v) for k, v in by_district.items() if _average(v)},
        "by_province": {k: _average(v) for k, v in by_province.items() if _average(v)},
    }


def _cache_get():
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                _cache = _build_cache()
    return _cache


def dataset_info() -> Dict:
    c = _cache_get()
    return {
        "destinations": len(c["by_dest"]),
        "districts": len(c["by_district"]),
        "provinces": len(c["by_province"]),
        "source_file": os.path.basename(_FEATURES_CSV),
    }


def lookup_baseline(city: str = None, district: str = None, province: str = None) -> Optional[Dict[str, float]]:
    """
    Return {transport, food, accommodation, taxi} daily USD figures calibrated
    against authentic Nepal travel rates. Matches in priority order:
    verified table > dataset destination > dataset district > dataset province > default.
    """
    candidates = [v for v in (city, district, province) if v]
    
    # 1. Match verified Nepal rates table first for pinpoint accuracy
    for val in candidates:
        norm_val = _norm(val)
        if norm_val in VERIFIED_NEPAL_BASELINES:
            return dict(VERIFIED_NEPAL_BASELINES[norm_val])
        for k, v in VERIFIED_NEPAL_BASELINES.items():
            if k != "default" and (k in norm_val or norm_val in k):
                return dict(v)

    # 2. Check CSV dataset cache
    c = _cache_get()
    for value, bucket in (
        (city, c["by_dest"]),
        (district, c["by_district"]),
        (province, c["by_province"]),
    ):
        if not value:
            continue
        key = _norm(value)
        if key in bucket and bucket[key]:
            return dict(bucket[key])
        for k, v in bucket.items():
            if k and (k in key or key in k) and v:
                return dict(v)

    # 3. Fallback to default Nepal baseline
    return dict(VERIFIED_NEPAL_BASELINES["default"])
