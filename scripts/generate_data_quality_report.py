"""Generate reports/live_data_quality.{json,csv} from the ACTUAL database.

Every number in the report is the result of a live query — nothing is
estimated, rounded, or copied from documentation. Run:

    python manage.py shell < scripts/generate_data_quality_report.py
"""
import csv
import importlib.util
import json
import os
import re
from datetime import datetime, timezone

from django.db.models import Count, Q

from tourist.models import Category, Destination, Hospital, PoliceStation

BASE = os.environ.get("TOURISM_BASE") or os.getcwd()
if not os.path.isdir(os.path.join(BASE, "tourist")):
    raise SystemExit("Run from the Tourism/Tourism directory (or set TOURISM_BASE)")
OUT_DIR = os.path.join(BASE, "..", "reports")
os.makedirs(OUT_DIR, exist_ok=True)

# canonical districts + provinces from the project's own normalizer
spec = importlib.util.spec_from_file_location(
    "ndn", os.path.join(BASE, "tourist", "management", "commands",
                        "normalize_district_names.py"))
ndn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ndn)
DISTRICT_PROVINCE = {}
for province, districts in ndn.NEPAL_DISTRICTS.items():
    for d in districts:
        DISTRICT_PROVINCE[d] = province

pub = Destination.objects.filter(status="approved", is_active=True)
all_dest = Destination.objects.all()


def coord_problems(qs):
    bad = qs.exclude(latitude=None).exclude(longitude=None)
    return {
        "missing_coordinates": qs.filter(Q(latitude=None) | Q(longitude=None)).count(),
        "outside_nepal_bbox": bad.exclude(
            latitude__gte=26.3, latitude__lte=30.5,
            longitude__gte=80.0, longitude__lte=88.2).count(),
        "invalid_zero_zero": bad.filter(latitude=0, longitude=0).count(),
    }


report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "database": str(Destination.objects.db),
    "destinations": {
        "total": all_dest.count(),
        "by_status": {r["status"] or "null": r["n"] for r in
                      all_dest.values("status").annotate(n=Count("id"))},
        "public_approved_active": pub.count(),
        "by_provenance": {r["provenance"] or "null": r["n"] for r in
                          pub.values("provenance").annotate(n=Count("id"))},
        "missing_category": pub.filter(category=None).count(),
        "missing_district": pub.filter(Q(district="") | Q(district=None)).count(),
        "missing_coordinate_provenance": pub.filter(
            Q(coordinate_source="") | Q(coordinate_source=None)).count(),
        "approximate_area_points": pub.filter(coordinate_status="APPROXIMATE").count(),
        **coord_problems(pub),
        "duplicate_coordinates": (
            pub.exclude(latitude=None)
            .values("latitude", "longitude")
            .annotate(n=Count("id")).filter(n__gt=3).count()),
        "duplicate_names_same_district": (
            pub.values("name", "district").annotate(n=Count("id"))
            .filter(n__gt=1).count()),
    },
    "taxonomy": {"categories": Category.objects.count()},
    "emergency": {
        "hospitals": Hospital.objects.count(),
        "police_stations": PoliceStation.objects.count(),
        **{"hospital_" + k: v for k, v in coord_problems(Hospital.objects.all()).items()},
    },
    "placeholder_scan": {},
    "district_coverage": [],
}

# placeholder / suspicious-text scan (counts only; nothing deleted blindly)
PATTERNS = ["placeholder", "lorem", "dummy", "fake", "sample data",
            "example.com", "N/A", "unknown"]
scan = {}
for pat in PATTERNS:
    scan[pat] = pub.filter(
        Q(name__icontains=pat) | Q(description__icontains=pat)).count()
suspicious_phones = 0
for phone in Hospital.objects.values_list("phone", flat=True):
    if phone and re.fullmatch(r"(\d)\1{4,}", phone.replace("-", "").strip()):
        suspicious_phones += 1
scan["hospital_phones_repeated_digit"] = suspicious_phones
report["placeholder_scan"] = scan

# district coverage (verified = approved+active public records)
per_district = {r["district"]: r["n"] for r in
                pub.exclude(district="").exclude(district=None)
                .values("district").annotate(n=Count("id"))}
for district, province in sorted(DISTRICT_PROVINCE.items()):
    n = per_district.get(district, 0)
    status = ("well_covered" if n >= 20 else
              "partially_covered" if n >= 5 else
              "limited_data" if n >= 1 else "no_verified_data")
    report["district_coverage"].append({
        "district": district, "province": province,
        "verified_destinations": n, "coverage_status": status})

extra_district_values = sorted(set(per_district) - set(DISTRICT_PROVINCE))
report["non_canonical_district_values"] = extra_district_values

with open(os.path.join(OUT_DIR, "live_data_quality.json"), "w") as fh:
    json.dump(report, fh, indent=2)

with open(os.path.join(OUT_DIR, "live_data_quality.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["district", "province", "verified_destinations", "coverage_status"])
    for row in report["district_coverage"]:
        w.writerow([row["district"], row["province"],
                    row["verified_destinations"], row["coverage_status"]])

print("wrote reports/live_data_quality.json + .csv")
print(json.dumps({k: report[k] for k in ("destinations", "emergency",
                                         "taxonomy")}, indent=1))
print("coverage summary:", {s: sum(1 for r in report['district_coverage']
                                   if r['coverage_status'] == s)
                            for s in ("well_covered", "partially_covered",
                                      "limited_data", "no_verified_data")})
