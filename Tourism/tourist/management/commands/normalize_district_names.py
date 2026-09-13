"""Normalize Destination.district to the canonical 77 English district names.

The OSM/imported dataset stores many district values in Nepali script
(e.g. 'काठमाडौं', 'अछाम जिल्ला') or legacy variants ('Nawalparasi W',
'Nawalpur District'), which made district-based features (77-district
explorer, itineraries, district galleries) silently miss records.

The mapping is the official Nepali->English district name table; it never
rewrites anything else and is idempotent. Records whose district still
does not match a canonical district after mapping are reported, not
guessed.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models.functions import Lower

from tourist.models import Destination
from tourist.location.administrative_boundaries import NEPAL_DISTRICTS

import unicodedata

CANON = sorted(d for lst in NEPAL_DISTRICTS.values() for d in lst)

# official Nepali spellings -> canonical English district names
NEPALI_MAP = {
    "अछाम": "Achham", "अर्घाखाँची": "Arghakhanchi", "बागलुङ": "Baglung",
    "बैतडी": "Baitadi", "बझाङ": "Bajhang", "बाजुरा": "Bajura",
    "बाँके": "Banke", "बारा": "Bara", "बर्दिया": "Bardiya",
    "भक्तपुर": "Bhaktapur", "भोजपुर": "Bhojpur", "चितवन": "Chitwan",
    "दादेलधुरा": "Dadeldhura", "डडेलधुरा": "Dadeldhura", "दैलेख": "Dailekh",
    "दाङ": "Dang", "दार्चुला": "Darchula", "धादिङ": "Dhading",
    "धनकुटा": "Dhankuta", "धनुषा": "Dhanusha", "दोलखा": "Dolakha",
    "डोल्पा": "Dolpa", "डोटी": "Doti", "गोरखा": "Gorkha",
    "गुल्मी": "Gulmi", "हुम्ला": "Humla", "इलाम": "Ilam",
    "जाजरकोट": "Jajarkot", "झापा": "Jhapa", "कैलाली": "Kailali",
    "कालीकोट": "Kalikot", "कञ्चनपुर": "Kanchanpur", "कपिलवस्तु": "Kapilvastu",
    "काठमाडौं": "Kathmandu", "काभ्रेपलाञ्चोक": "Kavrepalanchok",
    "खोटाङ": "Khotang", "ललितपुर": "Lalitpur", "लमजुङ": "Lamjung",
    "महोत्तरी": "Mahottari", "मकवानपुर": "Makwanpur", "मनाङ": "Manang",
    "मोरङ": "Morang", "मुगु": "Mugu", "मुस्ताङ": "Mustang",
    "म्याग्दी": "Myagdi", "नुवाकोट": "Nuwakot", "ओखलढुङ्गा": "Okhaldhunga",
    "पाल्पा": "Palpa", "पाँचथर": "Panchthar", "परसी": "Parasi",
    "पर्सा": "Parsa", "प्युठान": "Pyuthan", "रामेछाप": "Ramechhap",
    "रसुवा": "Rasuwa", "रौतहट": "Rautahat", "रोल्पा": "Rolpa",
    "पूर्वी रुकुम": "Rukum East", "पश्चिमी रुकुम": "Rukum West",
    "रुपन्देही": "Rupandehi", "सल्यान": "Salyan", "सङ्खुवासभा": "Sankhuwasabha",
    "सप्तरी": "Saptari", "सर्लाही": "Sarlahi", "सिन्धुली": "Sindhuli",
    "सिन्धुपाल्चोक": "Sindhupalchok", "सिराहा": "Siraha",
    "सोलुखुम्बु": "Solukhumbu", "सुनसरी": "Sunsari", "सुर्खेत": "Surkhet",
    "स्याङ्जा": "Syangja", "ताप्लेजुङ": "Taplejung", "तेह्रथुम": "Terhathum",
    "उदयपुर": "Udayapur", "कास्की": "Kaski", "जुम्ला": "Jumla",
    "पर्वत": "Parbat", "रौतहट ": "Rautahat", "तनहुँ": "Tanahun",
    "तनहूँ": "Tanahun", "रूकुम": "Rukum West", "संखुवासभा": "Sankhuwasabha",
    "ओखलढुंगा": "Okhaldhunga", "पांचथर": "Panchthar", "पाचथर": "Panchthar",
    "कपिलबस्तु": "Kapilvastu", "बारा जिल्ला": "Bara", "सिरहा": "Siraha",
    "धनुसा": "Dhanusha", "महोतरी": "Mahottari", "सर्लाही ": "Sarlahi",
}

# legacy English variants -> canonical
VARIANT_MAP = {
    "nawalparasi w": "Parasi", "nawalparasi west": "Parasi",
    "nawalparasi e": "Nawalpur", "nawalparasi east": "Nawalpur",
    "nawalpur district": "Nawalpur", "nawalparasi": "Parasi",
    "rukum east": "Rukum East", "rukum west": "Rukum West",
    "eastern rukum": "Rukum East", "western rukum": "Rukum West",
    "kavre": "Kavrepalanchok", "kathmandu district": "Kathmandu",
    "rasuwa district": "Rasuwa", "tanahu": "Tanahun", "tanahun district": "Tanahun",
    "kanchanpur district": "Kanchanpur", "kaski district": "Kaski",
}


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").strip()


def canonical_district(raw: str):
    if not raw:
        return None
    name = _nfc(raw)
    if name in CANON:
        return name
    nep = {_nfc(k): v for k, v in NEPALI_MAP.items()}
    if name in nep:
        return nep[name]
    base = name.replace(" जिल्ला", "").strip()
    if base in nep:
        return nep[base]
    low = name.lower()
    if low in VARIANT_MAP:
        return VARIANT_MAP[low]
    low_base = base.lower()
    if low_base in VARIANT_MAP:
        return VARIANT_MAP[low_base]
    for canon in CANON:
        if low == canon.lower():
            return canon
    return None


class Command(BaseCommand):
    help = "Normalize Destination.district to the canonical 77 English names."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        values = sorted(set(_nfc(v) for v in Destination.objects
                            .exclude(district="").values_list("district", flat=True).distinct()))
        renamed, kept, unknown = 0, 0, []
        for raw in values:
            canon = canonical_district(raw)
            if canon is None:
                unknown.append((raw, Destination.objects.filter(district=raw).count()))
                continue
            n = Destination.objects.filter(district=raw).count()
            if canon != raw:
                if not dry:
                    Destination.objects.filter(district=raw).update(district=canon)
                renamed += n
                self.stdout.write(f"  {raw!r} -> {canon} ({n})")
            else:
                kept += n
        covered = set(
            Destination.objects.exclude(district="")
            .values_list("district", flat=True).distinct()
        )
        empty = sorted(set(CANON) - covered)
        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] ' if dry else ''}renamed {renamed}, already canonical {kept}, "
            f"unknown {len(unknown)}"))
        seen = {}
        for raw, n in unknown:
            seen[_nfc(raw)] = seen.get(_nfc(raw), 0) + n
        for raw, n in sorted(seen.items()):
            self.stdout.write(f"  UNKNOWN district value {raw!r} ({n} records) — left untouched")
        self.stdout.write(f"canonical districts covered: {len(covered & set(CANON))}/77")
        if empty:
            self.stdout.write(self.style.WARNING(
                "districts with zero destinations (NOT fabricated): " + ", ".join(empty)))
