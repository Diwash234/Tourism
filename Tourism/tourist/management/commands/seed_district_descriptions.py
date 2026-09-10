"""Curated district descriptions for the most-visited districts.

Every sentence below states long-established public facts (administrative
seat, region, UNESCO-inscribed landmarks) of the kind published on the
districts' Wikipedia pages (checked 2026-09-10 for Chitwan; the remaining
entries carry only equally basic, uncontested facts). No promotional or
invented tourism prose.

The command is idempotent and only fills EMPTY descriptions — curated or
admin-entered content is never overwritten, and districts without an entry
here keep the honest "Information unavailable" + auto-composed
administrative summary behaviour.
"""
from django.core.management.base import BaseCommand

from tourist.models import District

DESCRIPTIONS = {
    # Kathmandu District - https://en.wikipedia.org/wiki/Kathmandu_District
    "kathmandu": (
        "Kathmandu District, in Bagmati Province, is the capital district of "
        "Nepal and the core of the Kathmandu Valley. It is home to the "
        "UNESCO World Heritage sites of Kathmandu Durbar Square, "
        "Swayambhunath, Pashupatinath and Boudhanath."
    ),
    # Lalitpur District - https://en.wikipedia.org/wiki/Lalitpur_District
    "lalitpur": (
        "Lalitpur District lies immediately south of Kathmandu in Bagmati "
        "Province, centred on the old Newar city of Patan (Lalitpur). Patan "
        "Durbar Square is part of the UNESCO-inscribed Kathmandu Valley "
        "monument zone, and the district is renowned for Newar metalwork "
        "and craftsmanship."
    ),
    # Bhaktapur District - https://en.wikipedia.org/wiki/Bhaktapur_District
    "bhaktapur": (
        "Bhaktapur District occupies the eastern Kathmandu Valley in Bagmati "
        "Province. Its seat, Bhaktapur city, is a preserved medieval Newar "
        "city known for Bhaktapur Durbar Square, the Nyatapola temple and a "
        "living pottery tradition."
    ),
    # Kaski District - https://en.wikipedia.org/wiki/Kaski_District
    "kaski": (
        "Kaski District in Gandaki Province is centred on Pokhara, Nepal's "
        "second-largest city. Phewa Lake, Sarangkot and the district's "
        "position as the trailhead for the Annapurna trekking region make it "
        "one of the country's most-visited districts."
    ),
    # Chitwan District - https://en.wikipedia.org/wiki/Chitwan_District (checked 2026-09-10)
    "chitwan": (
        "Chitwan District covers the south-western corner of Bagmati "
        "Province in the Terai lowlands, with Bharatpur as its "
        "administrative centre. It hosts Chitwan National Park, Nepal's "
        "first national park and a UNESCO World Heritage site, and is known "
        "for Tharu culture."
    ),
    # Rupandehi District - https://en.wikipedia.org/wiki/Rupandehi_District
    "rupandehi": (
        "Rupandehi District in Lumbini Province contains Lumbini, the birth "
        "place of the Buddha and a UNESCO World Heritage site. The district "
        "borders India and also includes the archaeological site of "
        "Tilaurakot (ancient Kapilavastu)."
    ),
    # Solukhumbu District - https://en.wikipedia.org/wiki/Solukhumbu_District
    "solukhumbu": (
        "Solukhumbu District in Koshi Province contains Mount Everest "
        "(Sagarmatha) and the UNESCO-inscribed Sagarmatha National Park. The "
        "Khumbu valley, Namche Bazar and Lukla airstrip sit here, and the "
        "district is the homeland of the Sherpa people."
    ),
    # Mustang District - https://en.wikipedia.org/wiki/Mustang_District
    "mustang": (
        "Mustang District in Gandaki Province lies in the rain shadow of the "
        "Annapurna and Dhaulagiri ranges along the Kali Gandaki valley, with "
        "Jomsom as its seat. Upper Mustang, with the walled town of "
        "Lo Manthang, and the pilgrimage site of Muktinath are its "
        "best-known landmarks."
    ),
    # Tanahun District - https://en.wikipedia.org/wiki/Tanahun_District
    "tanahun": (
        "Tanahun District in Gandaki Province sits along the Prithvi "
        "Highway between Kathmandu and Pokhara, with Damauli (Vyasa) as its "
        "seat. It is known for the preserved hill town of Bandipur."
    ),
    # Sindhupalchok District - https://en.wikipedia.org/wiki/Sindhupalchok_District
    "sindhupalchok": (
        "Sindhupalchok District in Bagmati Province stretches from the "
        "outskirts of Kathmandu to the Tibetan border and contains part of "
        "Langtang National Park, with Chautara as its seat. The district was "
        "near the epicentre of the 2015 Gorkha earthquake."
    ),
}


class Command(BaseCommand):
    help = "Fill empty District descriptions with curated, source-noted text (never overwrites)."

    def handle(self, *args, **options):
        filled = 0
        skipped = 0
        for slug, text in DESCRIPTIONS.items():
            district = District.objects.filter(slug=slug).first()
            if district is None:
                self.stdout.write(self.style.WARNING(f"district '{slug}' not seeded - skipped"))
                continue
            if (district.description or "").strip():
                skipped += 1
                continue
            district.description = text
            district.save(update_fields=["description", "updated_at"])
            filled += 1
        self.stdout.write(self.style.SUCCESS(
            f"filled {filled} description(s), kept {skipped} existing one(s)"
        ))
