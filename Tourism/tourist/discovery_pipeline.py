"""
Tourism/tourist/discovery_pipeline.py

Nepal Place Intelligence & Destination Discovery Engine.
Implements multi-source discovery, name normalization, spatial proximity matching,
multi-signal duplicate detection, quality scoring, and human-in-the-loop review.
"""

import os
import re
import csv
import math
import uuid
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .models import (
    Destination, Category, DestinationCandidate, DiscoveryJob,
    DestinationSourceField, DestinationAuditLog, DestinationSource
)
from .administrative_boundaries import NEPAL_DISTRICTS_DATA

ALL_DISTRICTS = list(NEPAL_DISTRICTS_DATA.keys())
DISTRICTS_BY_PROVINCE = {}
for _dist, _info in NEPAL_DISTRICTS_DATA.items():
    _prov = _info.get("province", "Bagmati")
    DISTRICTS_BY_PROVINCE.setdefault(_prov, []).append(_dist)

logger = logging.getLogger(__name__)

# Bounding box for Nepal: ~26.3°N to 30.5°N, 80.0°E to 88.2°E
NEPAL_BBOX = {
    "min_lat": 26.3, "max_lat": 30.5,
    "min_lon": 80.0, "max_lon": 88.2
}

# Common noise words and suffixes to strip during name normalization
SUFFIX_STRIP_REGEX = re.compile(
    r"\b(temple|mandir|mandirji|stupa|chorten|gompa|monastery|gumba|himal|peak|mountain|"
    r"lake|tal|taal|kund|kunda|waterfall|falls|chhango|viewpoint|view point|danda|hill|"
    r"resort|hotel|guest house|homestay|cottage|camp|camping|park|national park|"
    r"conservation area|cave|gupha|pass|la|bhanjyang|valley|river|khola|koshi|nadi|"
    r"fort|gadhi|durbar|palace|museum|memorial|bazaar|bazar|chowk|marga)\b",
    re.IGNORECASE
)

# Place Type classification rules from keywords/tags
TYPE_KEYWORD_MAP = [
    (["peak", "summit", "himal", "mountain"], DestinationCandidate.PlaceType.MOUNTAIN, "Mountain Peaks"),
    (["lake", "tal", "taal", "kund", "kunda", "pokhari"], DestinationCandidate.PlaceType.LAKE, "Lakes & Water Activities"),
    (["waterfall", "falls", "chhango"], DestinationCandidate.PlaceType.WATERFALL, "Waterfalls"),
    (["viewpoint", "view point", "danda", "hilltop", "sarangkot", "nagarkot"], DestinationCandidate.PlaceType.VIEWPOINT, "Photography Spots"),
    (["monastery", "gompa", "gumba", "chorten"], DestinationCandidate.PlaceType.MONASTERY, "Religious Sites"),
    (["stupa", "boudha", "swayambhu"], DestinationCandidate.PlaceType.STUPA, "Heritage & Temples"),
    (["temple", "mandir", "devalaya", "shrine"], DestinationCandidate.PlaceType.TEMPLE, "Heritage & Temples"),
    (["trek", "trail", "pass", "la", "bhanjyang"], DestinationCandidate.PlaceType.TREK_ROUTE, "Nature & Trekking"),
    (["national park", "wildlife reserve", "conservation area"], DestinationCandidate.PlaceType.NATIONAL_PARK, "National Parks"),
    (["cave", "gupha"], DestinationCandidate.PlaceType.CAVE, "Nature & Trekking"),
    (["hot spring", "tatopani"], DestinationCandidate.PlaceType.HOT_SPRING, "Nature & Trekking"),
    (["durbar", "palace", "fort", "gadhi", "heritage"], DestinationCandidate.PlaceType.HISTORIC_SITE, "Heritage & Temples"),
    (["museum", "gallery", "memorial"], DestinationCandidate.PlaceType.MUSEUM, "Museums"),
    (["village", "homestay", "settlement"], DestinationCandidate.PlaceType.VILLAGE, "Heritage & Temples"),
]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance in kilometers between two GPS coordinates."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 9999.0
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def normalize_place_name(raw_name: str) -> str:
    """
    Standardize place names by stripping punctuation, extra spaces,
    and trailing geographic descriptors for robust fuzzy matching.
    """
    if not raw_name:
        return ""
    text = str(raw_name).strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = SUFFIX_STRIP_REGEX.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or str(raw_name).strip().lower()


def string_similarity_ratio(str1: str, str2: str) -> float:
    """Levenshtein-based token string similarity ratio between 0.0 and 1.0."""
    s1, s2 = str1.strip().lower(), str2.strip().lower()
    if not s1 or not s2:
        return 0.0
    if s1 == s2:
        return 1.0
    if s1 in s2 or s2 in s1:
        return max(len(s1), len(s2)) / (len(s1) + len(s2) + 0.1) * 1.8
    # Bigram Jaccard similarity
    b1 = set([s1[i:i+2] for i in range(len(s1)-1)])
    b2 = set([s2[i:i+2] for i in range(len(s2)-1)])
    if not b1 or not b2:
        return 0.0
    intersection = len(b1.intersection(b2))
    union = len(b1.union(b2))
    return intersection / union if union > 0 else 0.0


def classify_place_taxonomy(name: str, tags: dict = None) -> Tuple[str, str]:
    """Classify a place into PlaceType and corresponding Category name."""
    text = f"{name} {str(tags or '')}".lower()
    for keywords, ptype, cat_name in TYPE_KEYWORD_MAP:
        if any(kw in text for kw in keywords):
            return ptype, cat_name
    return DestinationCandidate.PlaceType.ATTRACTION, "Heritage & Temples"


def detect_duplicates_and_score(
    name: str,
    lat: Optional[float],
    lon: Optional[float],
    district: str = "",
    province: str = "",
    existing_destinations: List[dict] = None,
) -> Tuple[str, float, str, Optional[int]]:
    """
    Multi-signal spatial and phonetic deduplication algorithm.
    Returns (duplicate_status, match_score_pct, duplicate_reason, matched_dest_id)
    """
    if existing_destinations is None:
        existing_destinations = list(
            Destination.objects.values("id", "name", "aliases", "latitude", "longitude", "district", "province")
        )

    norm_name = normalize_place_name(name)
    raw_lower = name.strip().lower()

    best_score = 0.0
    best_match = None
    best_reason = ""
    best_status = DestinationCandidate.DuplicateStatus.NONE

    for dest in existing_destinations:
        dest_name = dest["name"]
        dest_norm = normalize_place_name(dest_name)
        dest_aliases = [str(a).strip().lower() for a in (dest.get("aliases") or [])]
        dest_lat = float(dest["latitude"]) if dest.get("latitude") is not None else None
        dest_lon = float(dest["longitude"]) if dest.get("longitude") is not None else None
        dest_dist = (dest.get("district") or "").strip().lower()

        # 1. Exact string match or known alias match
        if raw_lower == dest_name.strip().lower() or raw_lower in dest_aliases:
            return (
                DestinationCandidate.DuplicateStatus.EXACT_MATCH,
                100.0,
                f"✓ Exact name match with '{dest_name}' (ID #{dest['id']})",
                dest["id"]
            )

        # 2. Multi-signal scoring
        name_sim = string_similarity_ratio(norm_name, dest_norm)
        alias_sim = max([string_similarity_ratio(raw_lower, a) for a in dest_aliases], default=0.0)
        final_name_sim = max(name_sim, alias_sim)

        # Calculate GPS distance
        dist_km = haversine_distance_km(lat, lon, dest_lat, dest_lon) if (lat and dest_lat) else 999.0
        same_district = bool(district and dest_dist and district.strip().lower() == dest_dist)

        # Composite score
        score = 0.0
        reasons = []

        # Name component (0 - 45 pts)
        score += final_name_sim * 45.0
        if final_name_sim > 0.8:
            reasons.append(f"Similar name ({final_name_sim*100:.0f}%)")

        # Spatial proximity component (0 - 40 pts)
        if dist_km < 0.3:
            score += 40.0
            reasons.append(f"Immediate proximity ({dist_km*1000:.0f}m)")
        elif dist_km < 1.0:
            score += 30.0
            reasons.append(f"Close proximity ({dist_km:.2f}km)")
        elif dist_km < 5.0:
            score += 15.0
            reasons.append(f"Same local area ({dist_km:.1f}km)")
        elif dist_km > 30.0 and (lat and dest_lat):
            score -= 20.0  # Far away penalization

        # District match component (0 - 15 pts)
        if same_district:
            score += 15.0
            reasons.append(f"Same district ({district})")

        score = max(0.0, min(100.0, score))

        if score > best_score:
            best_score = score
            best_match = dest
            best_reason = " | ".join(reasons) if reasons else "No strong match signals"

    # Evaluate decision tier
    matched_id = best_match["id"] if best_match else None

    if best_score >= 90.0:
        best_status = DestinationCandidate.DuplicateStatus.HIGH_SIMILARITY
        best_reason = f"High confidence duplicate of '{best_match['name']}': {best_reason}"
    elif best_score >= 75.0:
        best_status = DestinationCandidate.DuplicateStatus.PROXIMITY_OVERLAP
        best_reason = f"Possible duplicate of '{best_match['name']}': {best_reason} — Requires admin review"
    elif best_score >= 50.0:
        best_status = DestinationCandidate.DuplicateStatus.ALIAS_OF
        best_reason = f"Potential alias or nearby feature of '{best_match['name']}': {best_reason}"
    else:
        best_status = DestinationCandidate.DuplicateStatus.NONE
        best_reason = f"Unique candidate (Highest match {best_score:.0f}% with '{best_match['name'] if best_match else 'None'}')"
        matched_id = None

    return best_status, round(best_score, 1), best_reason, matched_id


def compute_candidate_quality_score(
    lat: Optional[float],
    lon: Optional[float],
    district: str,
    municipality: str,
    source: str,
    evidence_data: dict,
    duplicate_status: str,
) -> float:
    """
    Quality Scoring Engine (0-100).
    Evaluates geographic accuracy, administrative resolution, source evidence, and uniqueness.
    """
    quality = 0.0

    # 1. Geographic accuracy (+25 pts)
    if lat is not None and lon is not None:
        if NEPAL_BBOX["min_lat"] <= lat <= NEPAL_BBOX["max_lat"] and NEPAL_BBOX["min_lon"] <= lon <= NEPAL_BBOX["max_lon"]:
            quality += 25.0
        else:
            quality += 10.0  # Coordinates outside strict Nepal box

    # 2. Administrative resolution (+25 pts)
    if district and district in ALL_DISTRICTS:
        quality += 15.0
    elif district:
        quality += 8.0
    if municipality:
        quality += 10.0

    # 3. Source authority & evidence depth (+25 pts)
    if source in ["OSM", "Wikidata", "Nepal_Govt_Gazetteer", "Topo_Survey"]:
        quality += 15.0
    else:
        quality += 10.0
    if evidence_data and len(evidence_data) >= 3:
        quality += 10.0
    elif evidence_data:
        quality += 5.0

    # 4. Uniqueness / Deduplication status (+25 pts)
    if duplicate_status == DestinationCandidate.DuplicateStatus.NONE:
        quality += 25.0
    elif duplicate_status == DestinationCandidate.DuplicateStatus.ALIAS_OF:
        quality += 15.0
    elif duplicate_status == DestinationCandidate.DuplicateStatus.PROXIMITY_OVERLAP:
        quality += 8.0
    else:  # High similarity / exact match
        quality += 0.0

    return max(0.0, min(100.0, round(quality, 1)))


# =============================================================================
# MULTI-SOURCE DISCOVERY INGESTION PIPELINE
# =============================================================================

class DestinationDiscoveryPipeline:
    """
    Autonomous and batch-oriented discovery pipeline.
    Reads multi-source datasets, normalizes records, detects duplicates,
    enriches attributes, and populates DestinationCandidate staging.
    """

    def __init__(self, job_id: str = None):
        self.job_id = job_id or f"disc_{uuid.uuid4().hex[:10]}"
        self.cat_cache = {c.name.lower(): c for c in Category.objects.all()}

        # Build high-performance lookup indexes over existing Destination records
        self.dest_list = list(
            Destination.objects.values("id", "name", "aliases", "latitude", "longitude", "district", "province")
        )
        self.exact_name_index = {}
        self.norm_name_index = {}
        self.district_index = {}
        self.spatial_grid = {}

        for dest in self.dest_list:
            raw_name_lower = dest["name"].strip().lower()
            norm = normalize_place_name(dest["name"])
            self.exact_name_index[raw_name_lower] = dest
            self.norm_name_index[norm] = dest

            # Index aliases
            for alt in (dest.get("aliases") or []):
                alt_clean = str(alt).strip().lower()
                if alt_clean:
                    self.exact_name_index[alt_clean] = dest
                    self.norm_name_index[normalize_place_name(alt_clean)] = dest

            # Index district
            dist = (dest.get("district") or "").strip().lower()
            if dist:
                self.district_index.setdefault(dist, []).append(dest)

            # Index spatial grid (~11km buckets at 0.1 degree)
            if dest.get("latitude") is not None and dest.get("longitude") is not None:
                grid_key = (round(float(dest["latitude"]), 1), round(float(dest["longitude"]), 1))
                self.spatial_grid.setdefault(grid_key, []).append(dest)

    def _get_or_create_category(self, cat_name: str) -> Optional[Category]:
        c = self.cat_cache.get(cat_name.lower())
        if c:
            return c
        first = Category.objects.first()
        return first

    def detect_candidate_duplicate(
        self,
        name: str,
        lat: Optional[float],
        lon: Optional[float],
        district: str = "",
        province: str = "",
    ) -> Tuple[str, float, str, Optional[int]]:
        """
        Sub-millisecond indexed spatial & phonetic deduplication.
        """
        raw_lower = name.strip().lower()
        norm_name = normalize_place_name(name)

        # 1. Instant exact name or known alias match
        if raw_lower in self.exact_name_index:
            m = self.exact_name_index[raw_lower]
            return (
                DestinationCandidate.DuplicateStatus.EXACT_MATCH,
                100.0,
                f"✓ Exact name match with '{m['name']}' (ID #{m['id']})",
                m["id"],
            )

        if norm_name in self.norm_name_index:
            m = self.norm_name_index[norm_name]
            return (
                DestinationCandidate.DuplicateStatus.HIGH_SIMILARITY,
                98.0,
                f"✓ Normalized token match with '{m['name']}' (ID #{m['id']})",
                m["id"],
            )

        # 2. Gather candidates from spatial grid (±0.1 deg = ~11 km) and district
        candidates_to_check = []
        seen_ids = set()

        if lat is not None and lon is not None:
            r_lat, r_lon = round(lat, 1), round(lon, 1)
            for d_lat in [-0.1, 0.0, 0.1]:
                for d_lon in [-0.1, 0.0, 0.1]:
                    key = (round(r_lat + d_lat, 1), round(r_lon + d_lon, 1))
                    for dest in self.spatial_grid.get(key, []):
                        if dest["id"] not in seen_ids:
                            seen_ids.add(dest["id"])
                            candidates_to_check.append(dest)

        if district:
            for dest in self.district_index.get(district.strip().lower(), []):
                if dest["id"] not in seen_ids:
                    seen_ids.add(dest["id"])
                    candidates_to_check.append(dest)

        # 3. Check gathered subset
        best_score = 0.0
        best_match = None
        best_reasons = []

        for dest in candidates_to_check:
            dest_name = dest["name"]
            dest_norm = normalize_place_name(dest_name)
            dest_lat = float(dest["latitude"]) if dest.get("latitude") is not None else None
            dest_lon = float(dest["longitude"]) if dest.get("longitude") is not None else None
            dest_dist = (dest.get("district") or "").strip().lower()

            name_sim = string_similarity_ratio(norm_name, dest_norm)
            dist_km = haversine_distance_km(lat, lon, dest_lat, dest_lon) if (lat and dest_lat) else 999.0
            same_district = bool(district and dest_dist and district.strip().lower() == dest_dist)

            score = 0.0
            reasons = []

            score += name_sim * 45.0
            if name_sim > 0.75:
                reasons.append(f"Similar name ({name_sim*100:.0f}%)")

            if dist_km < 0.3:
                score += 40.0
                reasons.append(f"Immediate proximity ({dist_km*1000:.0f}m)")
            elif dist_km < 1.0:
                score += 30.0
                reasons.append(f"Close proximity ({dist_km:.2f}km)")
            elif dist_km < 5.0:
                score += 15.0
                reasons.append(f"Same area ({dist_km:.1f}km)")

            if same_district:
                score += 15.0
                reasons.append(f"Same district ({district})")

            score = max(0.0, min(100.0, score))

            if score > best_score:
                best_score = score
                best_match = dest
                best_reasons = reasons

        if best_score >= 88.0 and best_match:
            return (
                DestinationCandidate.DuplicateStatus.HIGH_SIMILARITY,
                round(best_score, 1),
                f"High confidence duplicate of '{best_match['name']}': " + " | ".join(best_reasons),
                best_match["id"],
            )
        elif best_score >= 70.0 and best_match:
            return (
                DestinationCandidate.DuplicateStatus.PROXIMITY_OVERLAP,
                round(best_score, 1),
                f"Possible duplicate of '{best_match['name']}': " + " | ".join(best_reasons),
                best_match["id"],
            )
        elif best_score >= 50.0 and best_match:
            return (
                DestinationCandidate.DuplicateStatus.ALIAS_OF,
                round(best_score, 1),
                f"Potential alias/feature of '{best_match['name']}': " + " | ".join(best_reasons),
                best_match["id"],
            )

        return (
            DestinationCandidate.DuplicateStatus.NONE,
            round(best_score, 1),
            f"Unique candidate (Highest match {best_score:.0f}% with '{best_match['name'] if best_match else 'None'}')",
            None,
        )

    def ingest_candidate(
        self,
        name: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        altitude: str = "",
        district: str = "",
        municipality: str = "",
        province: str = "",
        source: str = "OSM",
        source_id: str = "",
        source_url: str = "",
        evidence_data: dict = None,
        alternate_names: list = None,
        description: str = "",
    ) -> Tuple[Optional[DestinationCandidate], bool, str]:
        """
        Process a single candidate place through the discovery, normalization,
        duplicate detection, and quality scoring workflow.
        """
        if not name or len(str(name).strip()) < 2:
            return None, False, "Invalid or empty name"

        clean_name = str(name).strip()
        norm_name = normalize_place_name(clean_name)
        alt_names = [str(a).strip() for a in (alternate_names or []) if str(a).strip()]

        # Resolve Province if district is known
        if district and not province:
            for prov, dists in DISTRICTS_BY_PROVINCE.items():
                if any(d.lower() == district.strip().lower() for d in dists):
                    province = prov
                    break

        # High-performance indexed duplicate check
        dup_status, match_score, dup_reason, matched_dest_id = self.detect_candidate_duplicate(
            clean_name, lat, lon, district, province
        )

        # Classify taxonomy & category
        place_type, cat_name = classify_place_taxonomy(clean_name, evidence_data)
        category_obj = self._get_or_create_category(cat_name)

        # Compute Quality Score
        quality_score = compute_candidate_quality_score(
            lat, lon, district, municipality, source, evidence_data or {}, dup_status
        )

        # Determine Discovery Status
        if dup_status in [DestinationCandidate.DuplicateStatus.EXACT_MATCH, DestinationCandidate.DuplicateStatus.HIGH_SIMILARITY]:
            disc_status = DestinationCandidate.DiscoveryStatus.MERGED_DUPLICATE
        elif quality_score >= 70.0 and dup_status == DestinationCandidate.DuplicateStatus.NONE:
            disc_status = DestinationCandidate.DiscoveryStatus.VERIFIED
        elif quality_score >= 45.0:
            disc_status = DestinationCandidate.DiscoveryStatus.CANDIDATE
        else:
            disc_status = DestinationCandidate.DiscoveryStatus.NEEDS_REVIEW

        defaults = {
            "normalized_name": norm_name,
            "alternate_names": alt_names,
            "latitude": Decimal(str(round(lat, 6))) if lat is not None else None,
            "longitude": Decimal(str(round(lon, 6))) if lon is not None else None,
            "altitude": altitude or "",
            "province": province or "",
            "district": district or "",
            "municipality": municipality or "",
            "place_type": place_type,
            "category": category_obj,
            "suggested_category_name": cat_name,
            "description": description or f"A notable {place_type.replace('_', ' ')} in {district or 'Nepal'}.",
            "source": source,
            "source_url": source_url or "",
            "evidence_data": evidence_data or {},
            "confidence_score": max(50.0, min(100.0, 100.0 - match_score if dup_status == DestinationCandidate.DuplicateStatus.NONE else match_score)),
            "quality_score": quality_score,
            "discovery_status": disc_status,
            "duplicate_status": dup_status,
            "duplicate_reason": dup_reason,
            "match_score": match_score,
            "matched_destination_id": matched_dest_id,
            "audit_trail": [{
                "timestamp": timezone.now().isoformat(),
                "action": "ingested",
                "source": source,
                "score": quality_score,
                "reason": dup_reason,
            }]
        }

        candidate, created = DestinationCandidate.objects.update_or_create(
            name=clean_name,
            source_id=source_id or f"{source}_{slugify(clean_name)[:40]}",
            defaults=defaults,
        )

        return candidate, created, dup_reason

    def run_discovery_from_datasets(
        self,
        target_province: str = "",
        target_district: str = "",
        limit: int = 5000,
    ) -> Dict[str, Any]:
        """
        Ingests places from all available local datasets (OSM, Geocoding Topography, Sample CSVs)
        matching the district/province filter up to `limit` records.
        """
        job = DiscoveryJob.objects.create(
            job_id=self.job_id,
            source_name="Multi_Source_Gazetteer",
            target_province=target_province,
            target_district=target_district,
            status=DiscoveryJob.Status.RUNNING,
            started_at=timezone.now(),
        )

        scanned = 0
        created_count = 0
        dup_count = 0
        verified_count = 0
        errors = 0

        data_files = [
            ("ml_service/processed_data/destinations_clean.csv", "OSM_Cleaned"),
            ("ml_service/data/destinations/nepal_destinations.csv", "OSM_Nepal"),
            ("ml_service/nepal_destination_sample.csv", "OSM_Sample"),
            ("Tourism/dataset/destinations_clean.csv", "Tourism_Dataset"),
            ("dataset/destinations_clean.csv", "Tourism_Dataset_Local"),
        ]

        # Search across candidate root directories
        from django.conf import settings
        roots = [
            "/home/user/Tourism",
            os.getcwd(),
            os.path.abspath(os.path.join(os.getcwd(), "..")),
            str(getattr(settings, "BASE_DIR", "")),
            os.path.abspath(os.path.join(str(getattr(settings, "BASE_DIR", "")), "..")),
        ]

        for rel_path, src_tag in data_files:
            actual_path = None
            for root in roots:
                test_path = os.path.join(root, rel_path)
                if os.path.exists(test_path):
                    actual_path = test_path
                    break

            if not actual_path or not os.path.exists(actual_path):
                continue
            if scanned >= limit:
                break

            try:
                with open(actual_path, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if scanned >= limit:
                            break
                        scanned += 1

                        name = row.get("Name") or row.get("name") or row.get("place")
                        if not name or len(str(name).strip()) < 2:
                            continue

                        district = row.get("District") or row.get("district") or ""
                        province = row.get("Province") or row.get("province") or ""
                        city = row.get("City") or row.get("city") or ""

                        if target_district and district and target_district.lower() not in district.lower():
                            continue
                        if target_province and province and target_province.lower() not in province.lower():
                            continue

                        try:
                            lat = float(row.get("Latitude") or row.get("latitude") or 0) or None
                            lon = float(row.get("Longitude") or row.get("longitude") or 0) or None
                        except (ValueError, TypeError):
                            lat, lon = None, None

                        source_id = str(row.get("ID") or row.get("osm_id") or f"{src_tag}_{scanned}")
                        evidence = {k: v for k, v in row.items() if v and k not in ["Name", "Latitude", "Longitude"]}

                        cand, is_created, reason = self.ingest_candidate(
                            name=name,
                            lat=lat,
                            lon=lon,
                            district=district,
                            municipality=city,
                            province=province,
                            source=src_tag,
                            source_id=source_id,
                            evidence_data=evidence,
                        )

                        if cand:
                            if is_created:
                                created_count += 1
                            if cand.duplicate_status != DestinationCandidate.DuplicateStatus.NONE:
                                dup_count += 1
                            if cand.discovery_status == DestinationCandidate.DiscoveryStatus.VERIFIED:
                                verified_count += 1

            except Exception as e:
                logger.error("Error reading %s: %s", filepath, e)
                errors += 1

        job.records_scanned = scanned
        job.candidates_created = created_count
        job.duplicates_found = dup_count
        job.verified_count = verified_count
        job.errors_count = errors
        job.status = DiscoveryJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.log_summary = {
            "scanned": scanned,
            "created": created_count,
            "duplicates": dup_count,
            "verified": verified_count,
            "errors": errors,
        }
        job.save()

        return job.log_summary


# =============================================================================
# CANDIDATE ACTIONS & PROMOTION SERVICES
# =============================================================================

@transaction.atomic
def publish_candidate_to_destination(candidate_id: int, user=None) -> Tuple[bool, str]:
    """
    Promotes a verified candidate to the production Destination table.
    Ensures all 24-point blueprint fields and audit trail are populated.
    """
    try:
        candidate = DestinationCandidate.objects.select_for_update().get(id=candidate_id)
    except DestinationCandidate.DoesNotExist:
        return False, "Candidate record not found"

    if candidate.discovery_status == DestinationCandidate.DiscoveryStatus.PUBLISHED:
        return False, "Candidate is already published"

    # Check if existing destination with exact slug/name exists
    slug = slugify(candidate.name)
    existing = Destination.objects.filter(slug=slug).first()
    if not existing:
        existing = Destination.objects.filter(name__iexact=candidate.name).first()

    category = candidate.category or Category.objects.first()

    if existing:
        # Merge candidate details & aliases into existing destination
        aliases = existing.aliases or []
        if candidate.name not in aliases:
            aliases.append(candidate.name)
        for a in candidate.alternate_names:
            if a not in aliases:
                aliases.append(a)
        existing.aliases = aliases
        if not existing.altitude and candidate.altitude:
            existing.altitude = candidate.altitude
        if not existing.municipality and candidate.municipality:
            existing.municipality = candidate.municipality
        existing.save()
        dest_obj = existing
        action_note = f"Merged into existing Destination #{existing.id} ({existing.name})"
    else:
        # Create brand new production Destination
        dest_obj = Destination.objects.create(
            name=candidate.name,
            slug=slug,
            category=category,
            description=candidate.description or f"Verified {candidate.place_type} in {candidate.district or 'Nepal'}.",
            short_description=candidate.short_description or f"Scenic {candidate.place_type} in {candidate.district or 'Nepal'}.",
            latitude=candidate.latitude,
            longitude=candidate.longitude,
            altitude=candidate.altitude or "1,200m",
            province=candidate.province or "Bagmati",
            district=candidate.district or "Kathmandu",
            municipality=candidate.municipality or "",
            aliases=candidate.alternate_names or [],
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
            is_user_submitted=False,
            created_by=user,
        )
        action_note = f"Published as new Destination #{dest_obj.id}"

    # Log Source Field
    DestinationSourceField.objects.create(
        destination=dest_obj,
        field_name="discovery_provenance",
        field_value=f"Source: {candidate.source} (ID: {candidate.source_id})",
        source_name=candidate.source,
        source_url=candidate.source_url or "https://digitalnepal.gov.np",
        confidence="High" if candidate.quality_score >= 70 else "Medium",
        verification_status="Verified",
    )

    # Log in DestinationAuditLog
    DestinationAuditLog.objects.create(
        destination=dest_obj,
        action=DestinationAuditLog.Action.CREATE if not existing else DestinationAuditLog.Action.UPDATE,
        performed_by=user,
        details={"source": candidate.source, "quality_score": candidate.quality_score, "note": action_note},
    )

    # Update candidate status
    candidate.discovery_status = DestinationCandidate.DiscoveryStatus.PUBLISHED
    candidate.matched_destination = dest_obj
    candidate.audit_trail.append({
        "timestamp": timezone.now().isoformat(),
        "action": "published",
        "destination_id": dest_obj.id,
        "performed_by": user.email if user else "system",
    })
    candidate.save()

    return True, action_note


@transaction.atomic
def merge_candidate_as_alias(candidate_id: int, target_destination_id: int, user=None) -> Tuple[bool, str]:
    """
    Merges candidate name and aliases as alternate names for target destination.
    """
    try:
        candidate = DestinationCandidate.objects.get(id=candidate_id)
        target = Destination.objects.get(id=target_destination_id)
    except (DestinationCandidate.DoesNotExist, Destination.DoesNotExist):
        return False, "Candidate or Target Destination not found"

    aliases = target.aliases or []
    if candidate.name not in aliases:
        aliases.append(candidate.name)
    for alt in candidate.alternate_names:
        if alt not in aliases:
            aliases.append(alt)
    target.aliases = aliases
    target.save()

    candidate.discovery_status = DestinationCandidate.DiscoveryStatus.MERGED_DUPLICATE
    candidate.duplicate_status = DestinationCandidate.DuplicateStatus.ALIAS_OF
    candidate.matched_destination = target
    candidate.duplicate_reason = f"Manually linked as verified alias of #{target.id} ({target.name})"
    candidate.audit_trail.append({
        "timestamp": timezone.now().isoformat(),
        "action": "merged_as_alias",
        "target_id": target.id,
        "performed_by": user.email if user else "admin",
    })
    candidate.save()

    return True, f"Successfully merged '{candidate.name}' as alias for '{target.name}'"
