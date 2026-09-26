"""Entry, permit, fee, altitude and insurance requirements for travellers.

Data: ``dataset/travel_requirements.json`` -- transcribed from Department
of Immigration and Nepal Tourism Board pages, every block carrying its
source URL and retrieval date.

Honesty rules:
  * The catalogue has no park/restricted-area boundary polygons, so a
    destination is linked to a protected area / permit by *place-name
    keywords within the right district* (or a whole district for areas
    such as Manang/Mustang in the Annapurna Conservation Area). Every such
    link is returned with ``status="likely"`` and a human-readable
    ``basis`` -- never as a certainty.
  * Fees are the official published figures for the traveller's
    nationality category. Restricted-area fees are estimated for the
    number of days the traveller says they will spend in the area and
    labelled as an estimate.
  * Altitude guidance is attached only when a sourced elevation exists
    (see tourist/elevation.py); otherwise elevation is "not recorded".
"""

from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .elevation import ALTITUDE_THRESHOLD_M, best_elevation

DATA_FILE = Path(settings.BASE_DIR) / "dataset" / "travel_requirements.json"
NATIONALITIES = ("foreign", "saarc", "chinese", "nepali")
NATIONALITY_LABELS = {
    "foreign": "Foreign national (non-SAARC)",
    "saarc": "SAARC national",
    "chinese": "Chinese national",
    "nepali": "Nepali citizen",
}
LIKELY_LABEL = "Likely applies — confirm with the official source"


@lru_cache(maxsize=1)
def load_dataset() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def normalize_nationality(value) -> str:
    v = str(value or "").strip().lower()
    if v in NATIONALITIES:
        return v
    if v in {"np", "nepal", "nepalese"}:
        return "nepali"
    if v in {"cn", "china"}:
        return "chinese"
    if v in {"in", "india", "indian", "bd", "bangladesh", "bt", "bhutan", "lk", "sri lanka",
             "pk", "pakistan", "mv", "maldives", "af", "afghanistan"}:
        return "saarc"
    return "foreign"


def _source(key: str) -> dict:
    src = (load_dataset().get("sources") or {}).get(key) or {}
    return {"key": key, **src}


def _norm(text) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().replace("-", " ")).strip()


def _district(dest) -> str:
    return _norm(getattr(dest, "district", "")).replace(" district", "")


def _haystack(dest) -> str:
    parts = [getattr(dest, f, "") for f in ("name", "aliases", "municipality", "city")]
    return _norm(" ".join(str(p or "") for p in parts))


def _kw_hit(keyword: str, text: str) -> bool:
    kw = _norm(keyword)
    return bool(kw) and re.search(rf"(?<![a-z]){re.escape(kw)}(?![a-z])", text) is not None


def match_rule(rule: dict, dest) -> str | None:
    """Return a human-readable basis if ``rule`` likely applies to ``dest``."""
    district = _district(dest)
    districts = [_norm(d) for d in rule.get("districts") or []]
    whole = [_norm(d) for d in rule.get("whole_districts") or []]
    if district and district in whole:
        return f"The destination is in {dest.district} district, which lies within this area."
    text = _haystack(dest)
    hits = [k for k in rule.get("name_keywords") or [] if _kw_hit(k, text)]
    if not hits:
        return None
    if districts and district and district not in districts:
        return None
    where = f" in {dest.district} district" if getattr(dest, "district", "") else ""
    return f"Place name matches “{hits[0]}”{where}."


def _fee_for(fees: dict, nationality: str):
    if not fees:
        return None
    value = fees.get(nationality)
    if value is None and nationality == "chinese":
        value = fees.get("foreign")
    return value


def estimate_restricted_fee_usd(rule: dict, days: int | None, month: int | None) -> dict | None:
    """Estimate a restricted-area permit fee for ``days`` in the area."""
    if not rule or not days or days < 1:
        return None
    kind = rule.get("type")
    note = ""
    if kind == "per_day":
        usd = rule["usd"] * days
    elif kind == "first_days_then_daily":
        usd = rule["first_usd"] + max(0, days - rule["first_days"]) * rule["daily_usd_after"]
    elif kind == "seasonal_weekly":
        peak = month in (rule.get("peak_months") or []) if month else True
        week, extra = (rule["peak_week_usd"], rule["peak_extra_day_usd"]) if peak else (rule["off_week_usd"], rule["off_extra_day_usd"])
        usd = week + max(0, days - 7) * extra
        note = "Sep–Nov rate" if peak else "Dec–Aug rate"
        if not month:
            note += " (no travel month given — higher season rate shown)"
    elif kind == "weekly":
        extra = rule.get("extra_day_usd")
        usd = rule["week_usd"] + max(0, days - 7) * extra if extra is not None else rule["week_usd"] * math.ceil(days / 7)
    elif kind == "weekly_tiered":
        weeks = math.ceil(days / 7)
        base = min(weeks, rule["weeks_at_base"])
        usd = base * rule["week_usd"] + max(0, weeks - rule["weeks_at_base"]) * rule["week_usd_after"]
    else:
        return None
    return {"usd": usd, "days": days, "note": note}


def visa_summary(nationality: str, stay_days: int | None = None) -> dict:
    visa = load_dataset()["visa"]
    voa = visa["tourist_visa_on_arrival"]
    out = {
        "source": _source(visa["source"]),
        "summary": voa["summary"],
        "steps": voa["steps"],
        "apply_url": voa["apply_url"],
        "mission_visa_rule": voa["mission_visa_rule"],
        "gratis": visa["gratis"],
        "gratis_note": visa.get("gratis_note", ""),
        "contact": visa["contact"],
        "fees_usd": voa["fees_usd"],
        "fee_usd_for_stay": None,
        "applies": True,
    }
    if nationality == "nepali":
        out.update({"applies": False, "note": "Nepali citizens do not need a Nepal visa."})
        return out
    if nationality == "chinese":
        out["note"] = "Chinese nationals are on the Department of Immigration's gratis (free) visa list."
        return out
    if nationality == "saarc":
        out["note"] = ("SAARC citizens (except Afghanistan) get a gratis visa for up to 30 days on the first visit "
                       "in a visa year; standard fees apply otherwise.")
        return out
    if stay_days:
        tier = next((f for f in voa["fees_usd"] if stay_days <= f["days"]), None)
        out["fee_usd_for_stay"] = tier
        if tier is None:
            out["note"] = "Stays longer than 90 days need an extension — check with the Department of Immigration."
    return out


def destination_requirements(dest, nationality="foreign", days: int | None = None,
                             month: int | None = None, travelers: int = 1) -> dict:
    data = load_dataset()
    nationality = normalize_nationality(nationality)
    travelers = max(int(travelers or 1), 1)
    elev = best_elevation(dest)
    fees = []
    sources = {}

    def use(key):
        sources[key] = _source(key)
        return sources[key]

    protected = []
    for pa in data["protected_areas"]:
        basis = match_rule(pa["match"], dest)
        if not basis:
            continue
        fee = _fee_for(pa["fees_npr"], nationality)
        protected.append({
            "name": pa["name"], "type": pa["type"], "status": "likely", "status_label": LIKELY_LABEL,
            "basis": basis, "fee_npr": fee, "fees_npr": pa["fees_npr"], "fee_basis": pa["fee_basis"],
            "child_policy": pa["child_policy"], "note": pa.get("note", ""), "source": use("ntb_parks"),
        })
        if fee:
            fees.append({"label": f"{pa['name']} entry", "currency": "NPR", "amount_per_person": fee,
                         "basis": basis, "source_key": "ntb_parks", "estimate": False})

    restricted = []
    for ra in data["restricted_areas"]:
        basis = match_rule(ra["match"], dest)
        if not basis:
            continue
        est = estimate_restricted_fee_usd(ra["fee_rule"], days, month) if nationality != "nepali" else None
        restricted.append({
            "name": ra["name"], "status": "likely", "status_label": LIKELY_LABEL, "basis": basis,
            "fee_text": ra["fee_text"], "covered_areas": ra["covered_areas"], "estimate": est,
            "applies_to": "Foreign trekkers (issued by the Department of Immigration via a registered agency)",
            "source": use("doi_permits"),
        })
        if est:
            fees.append({"label": f"Restricted-area permit — {ra['name']}", "currency": "USD",
                         "amount_per_person": est["usd"], "basis": f"{basis} Estimate for {est['days']} day(s) in the area. {est['note']}".strip(),
                         "source_key": "doi_permits", "estimate": True})

    tims = None
    if nationality != "nepali":
        for region in data["tims"]["regions"]:
            basis = match_rule(region["match"], dest)
            if basis:
                fee = _fee_for(data["tims"]["fees_npr"], nationality)
                tims = {
                    "status": "likely", "status_label": LIKELY_LABEL, "region": region["region"], "treks": region["treks"],
                    "basis": basis, "rule": data["tims"]["rule"], "how": data["tims"]["how"], "fee_npr": fee,
                    "licensed_guide_required": True, "source": use("ntb_tims"),
                }
                if fee:
                    fees.append({"label": "TIMS card (via registered trekking agency)", "currency": "NPR",
                                 "amount_per_person": fee, "basis": basis, "source_key": "ntb_tims", "estimate": False})
                fees.append({"label": "Licensed trekking guide", "currency": None, "amount_per_person": None,
                             "basis": "Required with TIMS on this route; price is set by the agency — not estimated here.",
                             "source_key": "ntb_tims", "estimate": True})
                break

    heritage = []
    for site in data["heritage_sites"]:
        basis = match_rule(site["match"], dest)
        if not basis:
            continue
        fee = _fee_for(site["fees_npr"], nationality)
        heritage.append({"name": site["name"], "status": "likely", "status_label": LIKELY_LABEL, "basis": basis,
                         "fee_npr": fee, "fees_npr": site["fees_npr"], "notes": site["notes"], "source": use("ntb_heritage")})
        if fee:
            fees.append({"label": f"{site['name']} entry", "currency": "NPR", "amount_per_person": fee,
                         "basis": basis, "source_key": "ntb_heritage", "estimate": False})

    alt = data["altitude"]
    altitude = {
        "elevation_m": elev["elevation_m"], "elevation_source": elev["source"], "elevation_kind": elev["kind"],
        "elevation_retrieved_at": elev["retrieved_at"], "threshold_m": alt["threshold_m"],
        "above_threshold": bool(elev["elevation_m"] and elev["elevation_m"] >= ALTITUDE_THRESHOLD_M),
        "recorded": elev["elevation_m"] is not None,
    }
    if altitude["above_threshold"]:
        altitude.update({k: alt[k] for k in ("headline", "prevention", "early_symptoms", "what_to_do",
                                              "worsening_symptoms", "worsening_action", "hra")})
        altitude["source"] = use("ntb_mountain_safety")

    insurance = dict(data["insurance"])
    insurance["source"] = use(insurance.pop("source"))
    insurance["priority"] = "high" if (altitude["above_threshold"] or tims or restricted) else "standard"

    return {
        "destination": {"id": dest.id, "name": dest.name, "slug": getattr(dest, "slug", ""), "district": dest.district or ""},
        "nationality": nationality,
        "nationality_label": NATIONALITY_LABELS[nationality],
        "visa": visa_summary(nationality, days),
        "protected_areas": protected,
        "restricted_areas": restricted,
        "restricted_area_note": data.get("restricted_area_note", ""),
        "tims": tims,
        "heritage_sites": heritage,
        "altitude": altitude,
        "insurance": insurance,
        "fees": fees,
        "travelers": travelers,
        "matching_note": ("Matched by place name and district — Nepal Yatra has no official park boundary data. "
                          "Confirm with the linked official source before you travel."),
        "sources": list(sources.values()),
        "disclaimer": data["disclaimer"],
        "retrieved_at": data["retrieved_at"],
    }


def fee_totals(fees: list, travelers: int, fx_snapshot=None) -> dict:
    """Sum fee lines per person / group in NPR (USD lines converted at NRB rate)."""
    from . import fx

    snap = fx_snapshot if fx_snapshot is not None else fx.latest_snapshot()
    usd_rate = fx.npr_per_unit(snap, "USD") if snap else None
    per_person = 0.0
    unconverted = []
    lines = []
    for line in fees:
        if line.get("source_key") and "source" not in line:
            line = {**line, "source": _source(line["source_key"])}
        amount = line.get("amount_per_person")
        if amount is None:
            lines.append({**line, "amount_npr_per_person": None})
            continue
        if line["currency"] == "USD":
            if usd_rate is None:
                unconverted.append(line["label"])
                lines.append({**line, "amount_npr_per_person": None})
                continue
            npr = float(amount) * float(usd_rate)
        else:
            npr = float(amount)
        per_person += npr
        lines.append({**line, "amount_npr_per_person": round(npr, 2)})
    return {
        "lines": lines,
        "per_person_npr": round(per_person, 2),
        "group_npr": round(per_person * max(int(travelers or 1), 1), 2),
        "unconverted": unconverted,
        "fx": fx.snapshot_meta(snap),
    }


def general_requirements(nationality="foreign") -> dict:
    data = load_dataset()
    nationality = normalize_nationality(nationality)
    return {
        "nationality": nationality,
        "nationality_label": NATIONALITY_LABELS[nationality],
        "nationalities": [{"value": k, "label": v} for k, v in NATIONALITY_LABELS.items()],
        "visa": visa_summary(nationality),
        "tims": {**{k: data["tims"][k] for k in ("rule", "how", "fees_npr", "fee_basis", "regions")}, "source": _source("ntb_tims")},
        "protected_areas": [{k: pa[k] for k in ("name", "type", "fees_npr", "fee_basis", "child_policy", "note")} for pa in data["protected_areas"]],
        "protected_areas_source": _source("ntb_parks"),
        "restricted_areas": [{k: ra[k] for k in ("name", "fee_text", "covered_areas")} for ra in data["restricted_areas"]],
        "restricted_area_note": data.get("restricted_area_note", ""),
        "restricted_areas_source": _source("doi_permits"),
        "heritage_sites": [{k: s[k] for k in ("name", "fees_npr", "notes")} for s in data["heritage_sites"]],
        "heritage_note": data.get("heritage_note", ""),
        "heritage_source": _source("ntb_heritage"),
        "altitude": {**{k: v for k, v in data["altitude"].items() if k != "source"}, "source": _source("ntb_mountain_safety")},
        "insurance": {**{k: v for k, v in data["insurance"].items() if k != "source"}, "source": _source("ntb_faq")},
        "safety_advice": {"items": data["safety_advice"]["items"], "source": _source("ntb_emergency")},
        "official_contacts": {**{k: v for k, v in data["official_contacts"].items() if k != "source"}, "source": _source("ntb_emergency")},
        "tourist_police": {"summary": data["tourist_police"]["summary"], "source": _source("ntb_tourist_police")},
        "disclaimer": data["disclaimer"],
        "retrieved_at": data["retrieved_at"],
        "sources": list((data.get("sources") or {}).values()),
    }
