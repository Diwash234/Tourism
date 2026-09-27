"""Report sourced emergency coverage at all 77 district reference points.

This command audits what is actually in the database. It never creates a
facility from a district name or centroid and never invents a phone number.
Every valid Nepal coordinate still receives the protected national hotlines;
local coverage is reported separately so gaps can be filled by an owner with
an official record.
"""
import json

from django.core.management.base import BaseCommand, CommandError

from tourist.emergency_service import build_emergency_directory, national_hotlines
from tourist.models import District


class Command(BaseCommand):
    help = "Audit sourced hospital, police and specialist emergency coverage for all district reference points."

    def add_arguments(self, parser):
        parser.add_argument("--radius-km", type=float, default=50)
        parser.add_argument("--json", action="store_true", dest="as_json")
        parser.add_argument("--strict-local", action="store_true", help="Exit 1 if any district has no local hospital or police record.")

    def handle(self, *args, **options):
        radius = max(1.0, min(float(options["radius_km"]), 300.0))
        districts = list(District.objects.select_related("province").order_by("name"))
        if len(districts) != 77:
            raise CommandError(f"Expected 77 districts, found {len(districts)}; seed the verified district dataset before auditing.")

        rows = []
        local_gaps = []
        for district in districts:
            if district.latitude is None or district.longitude is None:
                row = {
                    "district": district.name,
                    "province": district.province.name,
                    "latitude": district.latitude,
                    "longitude": district.longitude,
                    "status": "missing_district_reference_coordinate",
                    "national_hotlines": len(national_hotlines()),
                    "local_hospitals": 0,
                    "local_police": 0,
                    "local_specialized": 0,
                }
                local_gaps.append(row)
                rows.append(row)
                continue
            payload = build_emergency_directory(
                district.latitude, district.longitude, radius_km=radius, limit=8,
            )
            counts = payload["counts"]
            row = {
                "district": district.name,
                "province": district.province.name,
                "latitude": float(district.latitude),
                "longitude": float(district.longitude),
                "status": "local_coverage" if counts["hospitals_within_radius"] or counts["police_within_radius"] else "national_hotlines_only",
                "national_hotlines": len(payload["national_hotlines"]),
                "local_hospitals": counts["hospitals_within_radius"],
                "local_police": counts["police_within_radius"],
                "local_specialized": counts["specialized_contacts_within_radius"],
                "nearest_hospital_km": payload["hospitals"][0]["distance_km"] if payload["hospitals"] else None,
                "nearest_police_km": payload["police"][0]["distance_km"] if payload["police"] else None,
            }
            if row["status"] != "local_coverage":
                local_gaps.append(row)
            rows.append(row)

        report = {
            "district_count": len(rows),
            "radius_km": radius,
            "national_hotlines": national_hotlines(),
            "national_hotline_coverage": len(national_hotlines()) >= 5,
            "local_coverage_gap_count": len(local_gaps),
            "local_gaps": local_gaps,
            "districts": rows,
            "data_policy": "National numbers are sourced fallbacks; local facilities are listed only from records with coordinates and source provenance.",
        }
        if options["as_json"]:
            self.stdout.write(json.dumps(report, indent=2, default=str))
        else:
            self.stdout.write(f"Districts audited: {len(rows)}/77")
            self.stdout.write(f"Protected national hotlines: {len(national_hotlines())}")
            self.stdout.write(f"Districts with local hospital/police coverage within {radius:g} km: {len(rows) - len(local_gaps)}/77")
            if local_gaps:
                self.stdout.write("Districts with national-hotline fallback only:")
                for row in local_gaps:
                    self.stdout.write(f"  - {row['district']} ({row['province']})")
        if options["strict_local"] and local_gaps:
            raise CommandError(f"{len(local_gaps)} districts have no local hospital/police record within {radius:g} km; no data was invented.")
