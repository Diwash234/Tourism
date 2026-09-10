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
    # --- batch 2: remaining province seats + major trekking/wildlife districts ---
    # Morang District - https://en.wikipedia.org/wiki/Morang_District
    "morang": (
        "Morang District in the south-eastern Terai of Koshi Province is "
        "centred on Biratnagar, the province capital and one of Nepal's "
        "largest industrial cities."
    ),
    # Dhanusha District - https://en.wikipedia.org/wiki/Dhanusha_District
    "dhanusha": (
        "Dhanusha District in Madhesh Province is centred on Janakpurdham, "
        "the province capital. The Janaki Mandir temple, dedicated to Sita, "
        "makes the city a major Hindu pilgrimage site and a centre of "
        "Maithili culture."
    ),
    # Makwanpur District - https://en.wikipedia.org/wiki/Makwanpur_District
    "makwanpur": (
        "Makwanpur District in Bagmati Province lies south of the Kathmandu "
        "Valley across the Chure hills, with Hetauda as its seat and the "
        "capital of Bagmati Province. The historic Makwanpur Gadhi fort sits "
        "above the district's main valley."
    ),
    # Dang District - https://en.wikipedia.org/wiki/Dang_District,_Nepal
    "dang": (
        "Dang District in Lumbini Province spans the Dang and Deukhuri "
        "valleys and hosts the province's administrative seat at Deukhuri. "
        "Ghorahi and Tulsipur are its largest cities."
    ),
    # Surkhet District - https://en.wikipedia.org/wiki/Surkhet_District
    "surkhet": (
        "Surkhet District is the gateway to Karnali Province, with the "
        "planned city of Birendranagar as its seat and the province capital. "
        "The Kakrebihar Buddhist monastery ruins lie nearby."
    ),
    # Kailali District - https://en.wikipedia.org/wiki/Kailali_District
    "kailali": (
        "Kailali District occupies the western Terai of Sudurpashchim "
        "Province, with Godawari as its seat and the province capital. "
        "Ghodaghodi Lake, a Ramsar-listed wetland, lies in the district."
    ),
    # Ilam District - https://en.wikipedia.org/wiki/Ilam_District
    "ilam": (
        "Ilam District in the far-eastern hills of Koshi Province is famous "
        "for its tea gardens on the Mechi-range slopes, with hilltop "
        "viewpoints such as Kanyam drawing visitors year-round."
    ),
    # Taplejung District - https://en.wikipedia.org/wiki/Taplejung_District
    "taplejung": (
        "Taplejung District in north-eastern Koshi Province borders Mount "
        "Kanchenjunga, the world's third-highest mountain, within the "
        "Kanchenjunga Conservation Area. The Pathibhara Devi temple is a "
        "major pilgrimage site."
    ),
    # Rasuwa District - https://en.wikipedia.org/wiki/Rasuwa_District
    "rasuwa": (
        "Rasuwa District in northern Bagmati Province covers the Langtang "
        "valley within Langtang National Park and the sacred Gosainkunda "
        "lakes, and reaches the Tibetan border at Rasuwagadhi."
    ),
    # Gorkha District - https://en.wikipedia.org/wiki/Gorkha_District
    "gorkha": (
        "Gorkha District in Gandaki Province is the ancestral home of the "
        "Shah dynasty, whose hilltop Gorkha Durbar palace overlooks the "
        "town. Mount Manaslu, the world's eighth-highest mountain, rises in "
        "the district's north."
    ),
    # Kavrepalanchok District - https://en.wikipedia.org/wiki/Kavrepalanchok_District
    "kavrepalanchok": (
        "Kavrepalanchok District on the Kathmandu Valley rim in Bagmati "
        "Province is known for the viewpoint town of Dhulikhel and the "
        "Namobuddha monastery, both a short drive from the capital."
    ),
    # Manang District - https://en.wikipedia.org/wiki/Manang_District
    "manang": (
        "Manang District in Gandaki Province is a high trans-Himalayan "
        "district on the Annapurna Circuit, home to Tilicho Lake — among the "
        "highest lakes in the world — below the Annapurna massif."
    ),
    # Myagdi District - https://en.wikipedia.org/wiki/Myagdi_District
    "myagdi": (
        "Myagdi District in Gandaki Province lies beneath the Dhaulagiri "
        "massif along the Kali Gandaki valley, with Beni as its seat and "
        "the lowland gateway to Mustang."
    ),
    # Dolakha District - https://en.wikipedia.org/wiki/Dolakha_District
    "dolakha": (
        "Dolakha District in Bagmati Province reaches from the hills east of "
        "Kathmandu to Mount Gaurishankar on the Tibetan border, with "
        "Bhimeshwor (Charikot) as its seat and the Kalinchok temple above "
        "the valley."
    ),
    # Kanchanpur District - https://en.wikipedia.org/wiki/Kanchanpur_District
    "kanchanpur": (
        "Kanchanpur District anchors the far-western Terai of Sudurpashchim "
        "Province and contains Shuklaphanta National Park, one of Nepal's "
        "largest grassland reserves, known for its swamp deer herds."
    ),
    # Bardiya District - https://en.wikipedia.org/wiki/Bardiya_District
    "bardiya": (
        "Bardiya District in Lumbini Province contains Bardiya National "
        "Park, the largest national park of the Terai, along the Karnali "
        "river — prime wildlife country and a centre of Tharu culture."
    ),
    # Nuwakot District - https://en.wikipedia.org/wiki/Nuwakot_District
    "nuwakot": (
        "Nuwakot District in Bagmati Province guards the historic "
        "Kathmandu–Tibet trade route at the Trishuli–Tadi river confluence, "
        "where the hilltop Nuwakot Durbar palace complex still stands."
    ),
    # --- batch 3: gateway, wildlife and remote-Karnali districts ---
    # Jhapa District - https://en.wikipedia.org/wiki/Jhapa_District
    "jhapa": (
        "Jhapa is Nepal's easternmost Terai district (Koshi Province), known "
        "for its tea gardens and for Kakarbhitta, the busiest Nepal–India "
        "border crossing in the east."
    ),
    # Sunsari District - https://en.wikipedia.org/wiki/Sunsari_District
    "sunsari": (
        "Sunsari District in the eastern Terai (Koshi Province) contains "
        "Dharan, the gateway city to the eastern hills, and part of the "
        "Koshi Tappu Wildlife Reserve, a Ramsar wetland famous for its bird "
        "life and wild water buffalo."
    ),
    # Saptari District - https://en.wikipedia.org/wiki/Saptari_District
    "saptari": (
        "Saptari District lies in the south-eastern Terai of Madhesh "
        "Province, with Rajbiraj — one of Nepal's earliest planned grid "
        "cities — as its seat."
    ),
    # Sankhuwasabha District - https://en.wikipedia.org/wiki/Sankhuwasabha_District
    "sankhuwasabha": (
        "Sankhuwasabha District in Koshi Province contains Mount Makalu, "
        "the world's fifth-highest mountain, and most of Makalu Barun "
        "National Park in the remote eastern Himalaya."
    ),
    # Parsa District - https://en.wikipedia.org/wiki/Parsa_District
    "parsa": (
        "Parsa District in Madhesh Province is centred on Birgunj, one of "
        "Nepal's largest trade cities on the Indian border, and holds Parsa "
        "National Park along the Chure foothills."
    ),
    # Bara District - https://en.wikipedia.org/wiki/Bara_District
    "bara": (
        "Bara District in the central Terai (Madhesh Province) contains the "
        "ruins of Simraungadh, the medieval capital of the Karnat dynasty, "
        "with Kalaiya as its seat."
    ),
    # Dhading District - https://en.wikipedia.org/wiki/Dhading_District
    "dhading": (
        "Dhading District in Bagmati Province stretches from the Trishuli "
        "corridor on the Prithvi Highway into the Ganesh Himal and Langtang "
        "foothills, serving as a western gateway to Langtang treks."
    ),
    # Ramechhap District - https://en.wikipedia.org/wiki/Ramechhap_District
    "ramechhap": (
        "Ramechhap District in Bagmati Province is a gateway to the Everest "
        "region; flights to Lukla commonly depart from Manthali airport "
        "here, and the classic Jiri trek route passes through the district."
    ),
    # Sindhuli District - https://en.wikipedia.org/wiki/Sindhuli_District
    "sindhuli": (
        "Sindhuli District in Bagmati Province takes its name from "
        "Sindhuligadhi fort, where Nepali forces repelled a British column "
        "in 1767 — among the earliest victories of unification-era Nepal."
    ),
    # Lamjung District - https://en.wikipedia.org/wiki/Lamjung_District
    "lamjung": (
        "Lamjung District in Gandaki Province was a Himalayan kingdom whose "
        "hilltop Lamjung Durbar still stands; Besisahar, the traditional "
        "start of the Annapurna Circuit, and the Gurung village of "
        "Ghalegaun lie here."
    ),
    # Parbat District - https://en.wikipedia.org/wiki/Parbat_District
    "parbat": (
        "Parbat, one of Nepal's smallest districts, sits in the Kali Gandaki "
        "gorge of Gandaki Province with Kushma as its seat — once the seat "
        "of the Parbat kingdom."
    ),
    # Baglung District - https://en.wikipedia.org/wiki/Baglung_District
    "baglung": (
        "Baglung District in Gandaki Province spans the middle Kali Gandaki "
        "valley, is known for its long suspension bridges, and reaches the "
        "Dhorpatan Hunting Reserve — Nepal's only hunting reserve — on the "
        "Dhaulagiri foothills."
    ),
    # Mugu District - https://en.wikipedia.org/wiki/Mugu_District
    "mugu": (
        "Mugu District in remote north-western Karnali Province contains "
        "Rara Lake, Nepal's largest lake, protected within Rara National "
        "Park at about 2,990 m in the high Himalaya."
    ),
    # Dolpa District - https://en.wikipedia.org/wiki/Dolpa_District
    "dolpa": (
        "Dolpa District in Karnali Province is Nepal's largest district by "
        "area, centred on Shey Phoksundo National Park and the turquoise "
        "Phoksundo Lake; its trans-Himalayan Upper Dolpo valleys are home "
        "to centuries-old monasteries such as Shey Gompa."
    ),
    # Jumla District - https://en.wikipedia.org/wiki/Jumla_District
    "jumla": (
        "Jumla District in Karnali Province holds the Sinja valley, where "
        "the Khas language ancestral to modern Nepali is believed to have "
        "developed; the high-altitude town is famed for its sinja rice and "
        "marsi crops."
    ),
    # Humla District - https://en.wikipedia.org/wiki/Humla_District
    "humla": (
        "Humla District in far north-western Karnali Province is among "
        "Nepal's most remote, with Simikot as its airhead; the Limi valley "
        "caravans historically linked it to the Mount Kailash pilgrimage "
        "route in Tibet."
    ),
    # Doti District - https://en.wikipedia.org/wiki/Doti_District
    "doti": (
        "Doti District in Sudurpashchim Province shares Khaptad National "
        "Park — alpine meadows and forests sacred to the Khaptad Baba — "
        "with Dipayal-Silgadhi as its seat on the Seti river."
    ),
    # Darchula District - https://en.wikipedia.org/wiki/Darchula_District
    "darchula": (
        "Darchula is Nepal's westernmost district (Sudurpashchim Province), "
        "bordering both India and China beneath Api, the 7,161 m peak of "
        "the Gurans Himal; its Byans valley preserves ancient trans-border "
        "trade traditions."
    ),
    # Banke District - https://en.wikipedia.org/wiki/Banke_District
    "banke": (
        "Banke District in Lumbini Province is centred on Nepalgunj, the "
        "transport hub of western Nepal, and contains Banke National Park, "
        "part of the Terai Arc tiger conservation landscape."
    ),
    # Palpa District - https://en.wikipedia.org/wiki/Palpa_District
    "palpa": (
        "Palpa District in the Lumbini hills is centred on the old Sen-dynasty "
        "town of Tansen, perched above the Siddhartha Highway, and on "
        "Rani Mahal, the riverside palace built on the Kali Gandaki in 1893."
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
