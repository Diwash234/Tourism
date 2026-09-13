"""Municipality → district/province mapping utilities.

Two ingestion paths, both auditable and never fabricated:

1. ``import_csv(text)`` — admin-supplied CSV (name,district[,province]).
   Rows are validated against the canonical 77-district table; province is
   derived from the district when omitted. Imported rows are verified.

2. ``build_coordinate_mappings(sample_limit=5)`` — derives candidate
   mappings for municipality-level ``district`` strings by reverse-geocoding
   the coordinates of the destinations that carry them (majority vote over a
   small sample). Candidates are stored ``verified=False`` for admin review
   and never overwrite an admin-provided mapping.
"""

import csv
import io
from collections import Counter

from .administrative_boundaries import NEPAL_DISTRICTS_DATA
from .location import reverse_geocode
from .models import Destination, MunicipalityMapping

CANON_DISTRICTS = {k.lower(): k for k in NEPAL_DISTRICTS_DATA}  # lowercase -> canonical name

# Documented 2018-era administrative renames (not guesses): data uses both
# old and new spellings; map them onto the canonical 77-district table.
DISTRICT_ALIASES = {
    "rukum east": "Eastern Rukum",
    "eastern rukum district": "Eastern Rukum",
    "rukum west": "Western Rukum",
    "western rukum district": "Western Rukum",
    "nawalparasi west": "Parasi",
    "nawalparasi (west)": "Parasi",
    "parasi district": "Parasi",
    "nawalparasi east": "Nawalpur",
    "nawalparasi (east)": "Nawalpur",
}

# Official Devanagari names of the 77 districts (as published with the 2015
# constitution / federal restructuring), plus spelling variants observed in
# the bundled OSM dataset. OSM-sourced destinations store ``district`` in
# Devanagari (sometimes suffixed "जिल्ला"); without these aliases, English
# district queries silently miss that data. Substring matching means the base
# form also covers the "जिल्ला" suffix. Compound names (पूर्वी/पश्चिम रुकुम)
# must precede the bare "रुकुम" so the substring scan resolves them first.
NEPALI_DISTRICT_ALIASES = {
    "ताप्लेजुङ": "Taplejung", "पाँचथर": "Panchthar", "इलाम": "Ilam", "झापा": "Jhapa",
    "मोरङ": "Morang", "सुनसरी": "Sunsari", "धनकुटा": "Dhankuta", "तेह्रथुम": "Terhathum",
    "सङ्खुवासभा": "Sankhuwasabha", "भोजपुर": "Bhojpur", "सोलुखुम्बु": "Solukhumbu",
    "ओखलढुङ्गा": "Okhaldhunga", "खोटाङ": "Khotang", "उदयपुर": "Udayapur",
    "सप्तरी": "Saptari", "सिरहा": "Siraha", "सिराहा": "Siraha", "धनुषा": "Dhanusha",
    "महोत्तरी": "Mahottari", "सर्लाही": "Sarlahi", "रौतहट": "Rautahat", "बारा": "Bara",
    "पर्सा": "Parsa",
    "सिन्धुली": "Sindhuli", "रामेछाप": "Ramechhap", "दोलखा": "Dolakha",
    "भक्तपुर": "Bhaktapur", "धादिङ": "Dhading", "काठमाडौं": "Kathmandu",
    "काठमाडौँ": "Kathmandu", "काभ्रेपलाञ्चोक": "Kavrepalanchok", "ललितपुर": "Lalitpur",
    "सिन्धुपाल्चोक": "Sindhupalchok", "चितवन": "Chitwan", "चितवान": "Chitwan",
    "नुवाकोट": "Nuwakot", "रसुवा": "Rasuwa", "मकवानपुर": "Makwanpur",
    "गोरखा": "Gorkha", "कास्की": "Kaski", "लमजुङ": "Lamjung", "मनाङ": "Manang",
    "मुस्ताङ": "Mustang", "म्याग्दी": "Myagdi", "नवलपुर": "Nawalpur", "पर्वत": "Parbat",
    "स्याङ्जा": "Syangja", "तनहुँ": "Tanahun", "बागलुङ": "Baglung",
    "कपिलवस्तु": "Kapilvastu", "नवलपरासी": "Parasi", "रुपन्देही": "Rupandehi",
    "अर्घाखाँची": "Arghakhanchi", "गुल्मी": "Gulmi", "पाल्पा": "Palpa", "दाङ": "Dang",
    "प्युठान": "Pyuthan", "रोल्पा": "Rolpa", "पूर्वी रुकुम": "Eastern Rukum",
    "बाँके": "Banke", "बर्दिया": "Bardiya",
    "पश्चिम रुकुम": "Western Rukum", "सल्यान": "Salyan", "डोल्पा": "Dolpa",
    "जुम्ला": "Jumla", "कालिकोट": "Kalikot", "कालीकोट": "Kalikot", "मुगु": "Mugu",
    "हुम्ला": "Humla", "दैलेख": "Dailekh", "जाजरकोट": "Jajarkot", "सुर्खेत": "Surkhet",
    "दार्चुला": "Darchula", "बझाङ": "Bajhang", "बाजुरा": "Bajura", "डोटी": "Doti",
    "अछाम": "Achham", "कैलाली": "Kailali", "बैतडी": "Baitadi",
    "डडेल्धुरा": "Dadeldhura", "डडेलधुरा": "Dadeldhura", "कञ्चनपुर": "Kanchanpur",
    # bare "रुकुम" last: it is ambiguous but the dataset uses it for the
    # former unified Rukum district whose remainder is Western Rukum.
    "रुकुम": "Western Rukum",
}
DISTRICT_ALIASES.update(NEPALI_DISTRICT_ALIASES)
for _alias, _canon in DISTRICT_ALIASES.items():
    CANON_DISTRICTS.setdefault(_alias, _canon)

# Nepali province names as they appear in the bundled OSM dataset.
NEPALI_PROVINCE_ALIASES = {
    "कोशी प्रदेश": "Koshi", "मधेश प्रदेश": "Madhesh", "बागमती प्रदेश": "Bagmati",
    "गण्डकी प्रदेश": "Gandaki", "लुम्बिनी प्रदेश": "Lumbini",
    "कर्णाली प्रदेश": "Karnali", "सुदूरपश्चिम प्रदेश": "Sudurpashchim",
}


def canonical_district(text):
    """Map any known district spelling (incl. Devanagari, "जिल्ला" suffix) to
    the canonical 77-district name. Unknown text is returned unchanged."""
    t = (text or "").strip()
    if not t:
        return ""
    hit = CANON_DISTRICTS.get(t.lower())
    if hit:
        return hit
    for alias, canon in DISTRICT_ALIASES.items():
        if alias and alias in t:
            return canon
    return t


def canonical_province(text):
    """Map a Nepali (or English) province name to the canonical English name.
    Unknown text is returned unchanged."""
    t = (text or "").strip()
    if not t:
        return ""
    hit = NEPALI_PROVINCE_ALIASES.get(t)
    if hit:
        return hit
    low = t.lower()
    for name in ("Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"):
        if name.lower() == low:
            return name
    return t


def import_csv(text):
    """Parse and upsert admin CSV rows. Returns {created, updated, rejected}."""
    created = updated = 0
    rejected = []
    reader = csv.DictReader(io.StringIO(text or ""))
    for i, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        district = (row.get("district") or "").strip()
        province = (row.get("province") or "").strip()
        if not name or not district:
            rejected.append({"row": i, "reason": "name and district are required"})
            continue
        canon_name = CANON_DISTRICTS.get(district.lower())
        if not canon_name:
            rejected.append({"row": i, "reason": f"unknown district '{district}'"})
            continue
        resolved_province = province or NEPAL_DISTRICTS_DATA[canon_name]["province"]
        obj, was_created = MunicipalityMapping.objects.update_or_create(
            name=name,
            defaults={
                "district": canon_name,
                "province": resolved_province,
                "source": "csv_import",
                "verified": True,
            },
        )
        created += was_created
        updated += not was_created
    return {"created": created, "updated": updated, "rejected": rejected}


def build_coordinate_mappings(sample_limit=5):
    """Derive unverified candidate mappings from destination coordinates.

    For every distinct municipality-level ``district`` string, reverse-geocode
    a small sample of destination coordinates and take the majority province
    /district result. Existing verified mappings are never touched.
    """
    from django.db.models import Count

    rows = (
        Destination.objects.exclude(district="")
        .exclude(district__isnull=True)
        .values("district")
        .annotate(n=Count("id"))
    )
    created = skipped_verified = 0
    for r in rows:
        name = r["district"]
        if name.lower() in CANON_DISTRICTS:
            continue  # already a canonical district name
        existing = MunicipalityMapping.objects.filter(name=name).first()
        if existing and existing.verified:
            skipped_verified += 1
            continue
        samples = list(
            Destination.objects.filter(district=name)
            .exclude(latitude__isnull=True)
            .exclude(longitude__isnull=True)
            .values_list("latitude", "longitude")[:sample_limit]
        )
        if not samples:
            continue
        votes = Counter()
        for lat, lng in samples:
            info = reverse_geocode(lat, lng)
            if info and info.get("district"):
                votes[(info["district"], info["province"])] += 1
        if not votes:
            continue
        (district, province), _ = votes.most_common(1)[0]
        canon_name = CANON_DISTRICTS.get(district.lower())
        if not canon_name:
            continue
        obj, was_created = MunicipalityMapping.objects.update_or_create(
            name=name,
            defaults={
                "district": canon_name,
                "province": province,
                "source": "coordinate_derived",
                "verified": False,
                "matched_destination_count": r["n"],
            },
        )
        created += was_created
    return {"candidates": MunicipalityMapping.objects.filter(verified=False).count(),
            "created": created, "skipped_verified": skipped_verified}


def backfill_provinces(dry_run=True):
    """Fill NULL/empty destination.province using VERIFIED mappings only.

    Unverified (coordinate-derived) candidates never write to destinations —
    an admin must verify a mapping first. Returns counts.
    """
    verified = {m.name: m for m in MunicipalityMapping.objects.filter(verified=True)}
    targets = Destination.objects.filter(province__isnull=True) | Destination.objects.filter(province="")
    filled = 0
    pending = 0
    for d in targets.iterator():
        m = verified.get(d.district or "")
        if m:
            if not dry_run:
                d.province = m.province
                d.save(update_fields=["province"])
            filled += 1
        else:
            pending += 1
    return {"filled": filled, "pending_verification": pending, "dry_run": dry_run}
