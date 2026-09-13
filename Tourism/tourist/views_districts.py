"""
views_districts.py — administrative geography API (task-79 §5/§24).

Read-only, public endpoints:

    GET /api/v1/provinces/              all 7 provinces + district counts
    GET /api/v1/districts/              all 77 districts (?search=, ?province=)
    GET /api/v1/districts/<slug>/       one district's tourism profile

Honesty rules (master prompt §5/§42):
- Tourism content is aggregated from REAL Destination/Hospital/PoliceStation
  rows recorded against the district — never generated here.
- Fields without verified data are explicitly labelled
  "Information unavailable" rather than filled with invented copy.
"""
from django.db.models import Count, Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .location_utils import haversine_km
from .models import Destination, District, Hospital, PoliceStation, Province

UNAVAILABLE = "Information unavailable"
MAX_PER_CATEGORY = 8


def _published_destinations():
    return Destination.objects.filter(
        status=Destination.SubmissionStatus.APPROVED, is_active=True
    )


def _destination_counts_by_district():
    """One grouped query: recorded district label -> published destination count."""
    rows = (
        _published_destinations()
        .exclude(district="")
        .values("district")
        .annotate(total=Count("id"))
    )
    lookup = {}
    for row in rows:
        lookup[str(row["district"]).strip().lower()] = row["total"]
    return lookup


def _count_for_district(district, lookup):
    """Count destinations recorded against this district (exact or as a
    contained label, e.g. 'Kaski' inside 'Kaski, Gandaki')."""
    name = district.name.strip().lower()
    return sum(total for label, total in lookup.items() if name == label or name in label)


def _compose_admin_summary(district, nearby):
    """Fact-based administrative summary composed from verified seed data —
    offered when no human-written description exists. States only recorded
    fields (province, region type, elevation, computed neighbour distances);
    never invents tourism prose."""
    region = (district.region_type or "").strip().lower()
    text = f"{district.name} is a {region + ' ' if region else ''}district in {district.province.name}, Nepal."
    if district.elevation_m is not None:
        text += f" The district seat sits at about {district.elevation_m:,.0f} m elevation."
    if nearby:
        pairs = ", ".join(f"{item['name']} ({item['distance_km']:.0f} km away)" for item in nearby[:3])
        text += f" Nearest districts: {pairs}."
    text += " Auto-generated from verified administrative data — curated description pending."
    return text


class ProvinceListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        counts = District.objects.values("province_id").annotate(total=Count("id"))
        count_map = {row["province_id"]: row["total"] for row in counts}
        data = [
            {
                "id": province.id,
                "name": province.name,
                "slug": province.slug,
                "capital": province.capital or UNAVAILABLE,
                "district_count": count_map.get(province.id, 0),
            }
            for province in Province.objects.all()
        ]
        return Response({"count": len(data), "results": data})


class DistrictListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = District.objects.select_related("province")
        province = (request.query_params.get("province") or "").strip()
        if province:
            queryset = queryset.filter(
                Q(province__name__icontains=province) | Q(province__slug__iexact=province)
            )
        search = (request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(region_type__icontains=search))

        lookup = _destination_counts_by_district()
        data = [
            {
                "id": district.id,
                "name": district.name,
                "slug": district.slug,
                "province": district.province.name,
                "region_type": district.region_type or UNAVAILABLE,
                "latitude": district.latitude,
                "longitude": district.longitude,
                "elevation_m": district.elevation_m,
                "destination_count": _count_for_district(district, lookup),
            }
            for district in queryset
        ]
        return Response({"count": len(data), "results": data})


class DistrictDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        district = District.objects.select_related("province").filter(slug=slug).first()
        if district is None:
            return Response({"detail": "District not found."}, status=status.HTTP_404_NOT_FOUND)

        destinations = (
            _published_destinations()
            .filter(district__icontains=district.name)
            .select_related("category")
            .order_by("-is_featured", "-average_rating", "name")
        )

        by_category = {}
        for destination in destinations[:120]:
            label = destination.category.name if destination.category_id else "Other"
            bucket = by_category.setdefault(label, [])
            if len(bucket) < MAX_PER_CATEGORY:
                bucket.append(
                    {
                        "name": destination.name,
                        "slug": destination.slug,
                        "city": destination.city_english or destination.district,
                        "rating": float(destination.average_rating) if destination.average_rating is not None else None,
                        "latitude": float(destination.latitude) if destination.latitude is not None else None,
                        "longitude": float(destination.longitude) if destination.longitude is not None else None,
                    }
                )

        hospitals = Hospital.objects.filter(
            destination__in=destinations
        ).select_related("destination")[:10]
        police = PoliceStation.objects.filter(
            destination__in=destinations
        ).select_related("destination")[:10]

        nearby = []
        if district.latitude is not None and district.longitude is not None:
            scored = []
            for other in District.objects.exclude(pk=district.pk):
                if other.latitude is None or other.longitude is None:
                    continue
                scored.append(
                    (
                        haversine_km(district.latitude, district.longitude, other.latitude, other.longitude),
                        other,
                    )
                )
            scored.sort(key=lambda pair: pair[0])
            nearby = [
                {"name": other.name, "slug": other.slug, "province": other.province.name,
                 "distance_km": round(distance_km, 1)}
                for distance_km, other in scored[:5]
            ]

        data = {
            "id": district.id,
            "name": district.name,
            "slug": district.slug,
            "province": district.province.name,
            "province_slug": district.province.slug,
            "region_type": district.region_type or UNAVAILABLE,
            "latitude": district.latitude,
            "longitude": district.longitude,
            "elevation_m": district.elevation_m,
            "description": district.description.strip() or UNAVAILABLE,
            "summary": _compose_admin_summary(district, nearby),
            "destinations_by_category": by_category,
            "destination_count": destinations.count(),
            "hospitals": [
                {"name": hospital.name, "phone": hospital.phone or UNAVAILABLE,
                 "address": hospital.address or UNAVAILABLE,
                 "destination": hospital.destination.name}
                for hospital in hospitals
            ],
            "police_stations": [
                {"name": station.name, "phone": station.phone or UNAVAILABLE,
                 "address": station.address or UNAVAILABLE,
                 "destination": station.destination.name}
                for station in police
            ],
            "emergency_numbers": {"police": "100", "ambulance": "102", "fire": "101"},
            "nearby_districts": nearby,
        }
        if not destinations.exists():
            data["data_note"] = (
                f"No verified tourism places are recorded for {district.name} yet. "
                "Fields above marked 'Information unavailable' are awaiting verified data — nothing is fabricated."
            )
        return Response(data)
