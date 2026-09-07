"""Round 15: Assign district + province to the 270 Wikidata-imported destinations
(ids 7248-7517) that were created with province=None/district=None, so they
become visible in province filters. Also fixes legacy district-only rows,
the broken Bindabasini Temple entry, and adds the last missing named places
from the Koshi + Madhesh ward-by-ward data (Surunga Baba, Birtamod, Damak).

Mappings verified against Wikidata P131 (located in the administrative
territorial entity) for the ambiguous entries during Round 15 research.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

# ---------------------------------------------------------------------------
# 1) Wikidata-imported destinations: id -> (district, province, city)
#    (district=None means "province-only", e.g. province entities)
# ---------------------------------------------------------------------------
WIKIDATA_MAP = {
    # ---------------- Koshi ----------------
    7251: ("Jhapa", "Koshi", "Gauradaha"),
    7256: ("Udayapur", "Koshi", "Gaighat"),
    7268: ("Jhapa", "Koshi", "Arjundhara"),
    7269: ("Okhaldhunga", "Koshi", "Rumjatar"),
    7270: ("Sunsari", "Koshi", "Prakashpur"),
    7278: ("Dhankuta", "Koshi", "Pakhribas"),
    7279: ("Khotang", "Koshi", "Sungdel"),
    7280: ("Jhapa", "Koshi", "Baniyani"),
    7292: ("Solukhumbu", "Koshi", "Ombigaichan"),
    7293: ("Solukhumbu", "Koshi", "Ngozumpa Glacier"),
    7299: ("Taplejung", "Koshi", "Tapethok"),
    7303: ("Jhapa", "Koshi", "Rajgadh"),
    7308: ("Morang", "Koshi", "Jhurkiya"),
    7312: ("Taplejung", "Koshi", "Lelep"),
    7317: ("Morang", "Koshi", "Basantatar"),
    7319: ("Okhaldhunga", "Koshi", "Katunje"),
    7322: ("Dhankuta", "Koshi", "Mane Bhanjyang"),
    7325: ("Bhojpur", "Koshi", "Gupteshwor"),
    7333: ("Solukhumbu", "Koshi", "Chaurikharka"),
    7341: ("Sankhuwasabha", "Koshi", "Barun River"),
    7342: ("Udayapur", "Koshi", "Bashasa"),
    7347: ("Morang", "Koshi", "Urlabari"),
    7352: ("Jhapa", "Koshi", "Budhabare"),
    7354: ("Sankhuwasabha", "Koshi", "Chamlang"),
    7355: ("Ilam", "Koshi", "Naya Bazar"),
    7361: ("Taplejung", "Koshi", "Olangchung Gola"),
    7371: ("Taplejung", "Koshi", "Kabru"),
    7372: ("Ilam", "Koshi", "Sakfara"),
    7377: ("Sunsari", "Koshi", "Koshi Barrage"),
    7378: ("Khotang", "Koshi", "Khiji Chandeshwori"),
    7396: ("Solukhumbu", "Koshi", "Dole"),
    7398: ("Solukhumbu", "Koshi", "Imja Glacier"),
    7402: ("Solukhumbu", "Koshi", "Western Cwm"),
    7404: ("Udayapur", "Koshi", "Katari"),
    7405: ("Khotang", "Koshi", "Diktel"),
    7407: ("Jhapa", "Koshi", "Kolbung"),
    7408: ("Solukhumbu", "Koshi", "Lingtren"),
    7410: ("Jhapa", "Koshi", "Bhadrapur"),
    7411: ("Solukhumbu", "Koshi", "Mount Khumbila"),
    7412: ("Taplejung", "Koshi", "Kangbachen"),
    7413: ("Taplejung", "Koshi", "Kanchenjunga West"),
    7415: ("Sunsari", "Koshi", "Itahari"),
    7419: ("Solukhumbu", "Koshi", "Peak 38"),
    7420: ("Solukhumbu", "Koshi", "Num Ri"),
    7424: ("Solukhumbu", "Koshi", "Nuptse"),
    7426: ("Morang", "Koshi", "Rangeli"),
    7427: ("Solukhumbu", "Koshi", "Peak 41"),
    7428: ("Solukhumbu", "Koshi", "Kyashar"),
    7430: ("Sankhuwasabha", "Koshi", "Chainpur"),
    7431: ("Taplejung", "Koshi", "Gimmigela Chuli"),
    7432: ("Solukhumbu", "Koshi", "Khumbu Icefall"),
    7446: ("Sankhuwasabha", "Koshi", "Ripuk"),
    7450: ("Morang", "Koshi", "Ramailo"),
    7455: (None, "Koshi", "Koshi Province"),
    7456: ("Panchthar", "Koshi", "Kabeli River"),
    7457: ("Solukhumbu", "Koshi", "Lhotse Middle"),
    7458: ("Taplejung", "Koshi", "Kokthang"),
    7459: ("Solukhumbu", "Koshi", "South Summit"),
    7472: ("Solukhumbu", "Koshi", "Takargo"),
    7473: ("Solukhumbu", "Koshi", "Tengi Ragi Tau"),
    7475: ("Taplejung", "Koshi", "Ramthang Chang"),
    7476: ("Solukhumbu", "Koshi", "Pethang Tse"),
    7477: ("Solukhumbu", "Koshi", "Chumbu"),
    7480: ("Solukhumbu", "Koshi", "Khumbu Glacier"),
    7488: ("Solukhumbu", "Koshi", "Lho La"),
    7491: ("Okhaldhunga", "Koshi", "Siddhicharan"),
    7493: ("Solukhumbu", "Koshi", "Tenzing Peak"),
    7495: ("Solukhumbu", "Koshi", "Kyajo Ri"),
    7496: ("Solukhumbu", "Koshi", "Kongma Tse"),
    7501: ("Sunsari", "Koshi", "Khuwalung"),
    7503: ("Solukhumbu", "Koshi", "Syangboche"),
    7509: ("Solukhumbu", "Koshi", "Necha Salyan"),
    7515: ("Solukhumbu", "Koshi", "Tsoboje"),
    7516: ("Taplejung", "Koshi", "Nepal Peak"),
    # ---------------- Madhesh ----------------
    7253: ("Rautahat", "Madhesh", "Katahariya"),
    7282: ("Saptari", "Madhesh", "Bodebarsaien"),
    7285: ("Saptari", "Madhesh", "Shambhunath"),
    7346: ("Saptari", "Madhesh", "Mauwaha"),
    7353: ("Siraha", "Madhesh", "Khajuri Chanha"),
    7359: ("Saptari", "Madhesh", "Boriya"),
    7369: ("Sarlahi", "Madhesh", "Dudhouli"),
    7380: ("Saptari", "Madhesh", "Kataiya"),
    7382: ("Sarlahi", "Madhesh", "Karmaihiya"),
    7387: ("Saptari", "Madhesh", "Hariharpur"),
    7391: ("Mahottari", "Madhesh", "Gaushala"),
    7393: ("Rautahat", "Madhesh", "Gadhi"),
    7454: (None, "Madhesh", "Madhesh Province"),
    7465: ("Sarlahi", "Madhesh", "Barahathawa"),
    7466: ("Bara", "Madhesh", "Simraungadh"),
    7467: ("Bara", "Madhesh", "Mahagadhimai"),
    7490: ("Mahottari", "Madhesh", "Khayarmara"),
    7508: ("Saptari", "Madhesh", "Chandra Canal"),
    7305: ("Bara", "Madhesh", "Nijgadh"),
    7318: ("Bara", "Madhesh", "Amlekhganj"),
    # ---------------- Bagmati ----------------
    7250: ("Ramechhap", "Bagmati", "Gumdel"),
    7258: ("Makwanpur", "Bagmati", "Markhu"),
    7259: ("Nuwakot", "Bagmati", "Ratmate"),
    7262: ("Sindhupalchok", "Bagmati", "Melamchi"),
    7264: ("Makwanpur", "Bagmati", "Handikhola"),
    7265: ("Chitwan", "Bagmati", "Madi Kalyanpur"),
    7266: ("Chitwan", "Bagmati", "Pragatinagar"),
    7267: ("Kavre", "Bagmati", "Saping"),
    7272: ("Kathmandu", "Bagmati", "Balambu"),
    7273: ("Ramechhap", "Bagmati", "Namdu"),
    7276: ("Ramechhap", "Bagmati", "Babare"),
    7281: ("Sindhupalchok", "Bagmati", "Listikot"),
    7283: ("Lalitpur", "Bagmati", "Dalchoki"),
    7286: ("Kathmandu", "Bagmati", "Tangal Durbar"),
    7287: ("Kathmandu", "Bagmati", "Seto Durbar"),
    7288: ("Kathmandu", "Bagmati", "Lal Durbar"),
    7289: ("Ramechhap", "Bagmati", "Manthali"),
    7290: ("Kavre", "Bagmati", "Palanchok"),
    7291: ("Dhading", "Bagmati", "Nilkantha"),
    7294: ("Rasuwa", "Bagmati", "Thuman"),
    7297: ("Dhading", "Bagmati", "Naubise"),
    7301: ("Sindhupalchok", "Bagmati", "Haibung"),
    7304: ("Rasuwa", "Bagmati", "Rasuwa Fort"),
    7311: ("Kavre", "Bagmati", "Kushadevi"),
    7314: ("Sindhuli", "Bagmati", "Hariharpur Gadhi"),
    7315: ("Ramechhap", "Bagmati", "Sailungeswor"),
    7316: ("Sindhupalchok", "Bagmati", "Helumbu"),
    7321: ("Kavre", "Bagmati", "Mahadevsthan Mandan"),
    7324: ("Nuwakot", "Bagmati", "Khari"),
    7328: ("Ramechhap", "Bagmati", "Pawati"),
    7335: ("Sindhupalchok", "Bagmati", "Bhotechaur"),
    7338: ("Ramechhap", "Bagmati", "Bulung"),
    7340: ("Sindhupalchok", "Bagmati", "Dorje Lhakpa"),
    7348: ("Kathmandu", "Bagmati", "Thankot"),
    7349: ("Kavre", "Bagmati", "Simalchour Syampati"),
    7351: ("Dolakha", "Bagmati", "Kalinchowk"),
    7356: ("Nuwakot", "Bagmati", "Charghare"),
    7358: ("Kavre", "Bagmati", "Methinkot"),
    7362: ("Makwanpur", "Bagmati", "Bhimfedi"),
    7365: ("Sindhupalchok", "Bagmati", "Tauthali"),
    7367: ("Sindhupalchok", "Bagmati", "Jalbire"),
    7368: ("Kavre", "Bagmati", "Jaisithok Mandan"),
    7373: ("Kathmandu", "Bagmati", "Maru, Kathmandu"),
    7376: ("Dhading", "Bagmati", "Kumpur"),
    7381: ("Kathmandu", "Bagmati", "Kasthamandap"),
    7384: ("Sindhupalchok", "Bagmati", "Jyamire"),
    7388: ("Rasuwa", "Bagmati", "Haku"),
    7394: ("Chitwan", "Bagmati", "East Rapti River"),
    7395: ("Sindhupalchok", "Bagmati", "Dragmarpo Ri"),
    7399: ("Kavre", "Bagmati", "Dapcha Chhatrebangh"),
    7418: ("Kathmandu", "Bagmati", "Gokarneshwor"),
    7421: ("Kathmandu", "Bagmati", "Halchowk Stadium"),
    7429: ("Rasuwa", "Bagmati", "Langtang Ri"),
    7433: ("Kathmandu", "Bagmati", "Tundikhel"),
    7436: ("Kathmandu", "Bagmati", "Supreme Court of Nepal"),
    7439: ("Kathmandu", "Bagmati", "Shankarapur"),
    7448: ("Kathmandu", "Bagmati", "Ratna Park"),
    7469: ("Sindhupalchok", "Bagmati", "Gurkarpo Ri"),
    7471: ("Kathmandu", "Bagmati", "Tarakeshwor"),
    7479: ("Dolakha", "Bagmati", "Gauri Sankar"),
    7481: ("Rasuwa", "Bagmati", "Naya Kanga"),
    7482: ("Rasuwa", "Bagmati", "Langtang Himal"),
    7483: ("Rasuwa", "Bagmati", "Langshisa Ri"),
    7484: ("Rasuwa", "Bagmati", "Kimshung"),
    7485: ("Sindhupalchok", "Bagmati", "Jugal Himal"),
    7486: ("Sindhupalchok", "Bagmati", "Gangchempo"),
    7494: ("Kathmandu", "Bagmati", "Jhochhen"),
    7504: ("Kathmandu", "Bagmati", "Nautalle Durbar"),
    7517: ("Sindhupalchok", "Bagmati", "Lamo waterfall"),
    # ---------------- Gandaki ----------------
    7254: ("Parbat", "Gandaki", "Ratnechaur"),
    7257: ("Syangja", "Gandaki", "Arjun Chaupari"),
    7260: ("Syangja", "Gandaki", "Bahakot"),
    7261: ("Syangja", "Gandaki", "Pidikhola"),
    7263: ("Gorkha", "Gandaki", "Ghyalchok"),
    7271: ("Gorkha", "Gandaki", "Nyawal"),
    7274: ("Lamjung", "Gandaki", "Taghring"),
    7277: ("Syangja", "Gandaki", "Thapathana"),
    7284: ("Lamjung", "Gandaki", "Bhorletar"),
    7295: ("Baglung", "Gandaki", "Limgha"),
    7296: ("Gorkha", "Gandaki", "Sirdibas"),
    7298: ("Baglung", "Gandaki", "Kusmishera"),
    7300: ("Lamjung", "Gandaki", "Sildujure"),
    7306: ("Lamjung", "Gandaki", "Udipur"),
    7307: ("Lamjung", "Gandaki", "Ghermu"),
    7309: ("Manang", "Gandaki", "Tanki Manang"),
    7310: ("Lamjung", "Gandaki", "Hiletaksar"),
    7313: ("Gorkha", "Gandaki", "Aarupokhari"),
    7320: ("Lamjung", "Gandaki", "Ghansikuwa"),
    7326: ("Syangja", "Gandaki", "Arukharka"),
    7327: ("Manang", "Gandaki", "Thoche"),
    7329: ("Syangja", "Gandaki", "Aruchaur"),
    7330: ("Syangja", "Gandaki", "Tilahar"),
    7332: ("Baglung", "Gandaki", "Chhisti"),
    7337: ("Gorkha", "Gandaki", "Darechok"),
    7339: ("Gorkha", "Gandaki", "Chumchet"),
    7343: ("Myagdi", "Gandaki", "Dana"),
    7344: ("Syangja", "Gandaki", "Bange Phadke"),
    7350: ("Lamjung", "Gandaki", "Karapu"),
    7360: ("Tanahun", "Gandaki", "Dedgaun"),
    7363: ("Tanahun", "Gandaki", "Dulegaunda"),
    7364: ("Lamjung", "Gandaki", "Duradanda"),
    7366: ("Syangja", "Gandaki", "Phedikhola"),
    7370: ("Mustang", "Gandaki", "Chhusang"),
    7375: ("Mustang", "Gandaki", "Lete"),
    7379: ("Nawalpur", "Gandaki", "Kawasoti"),
    7385: ("Gorkha", "Gandaki", "Jaubari"),
    7392: ("Gorkha", "Gandaki", "Ganesh NW"),
    7397: ("Baglung", "Gandaki", "Dhorpatan"),
    7400: ("Syangja", "Gandaki", "Chapakot"),
    7409: ("Manang", "Gandaki", "Ngadi Chuli"),
    7414: ("Manang", "Gandaki", "Kang Guru"),
    7422: ("Myagdi", "Gandaki", "Dhaulagiri Himal"),
    7423: ("Gorkha", "Gandaki", "Himalchuli"),
    7434: ("Mustang", "Gandaki", "Tangbe"),
    7435: ("Syangja", "Gandaki", "Taksar"),
    7437: ("Syangja", "Gandaki", "Sorek"),
    7443: ("Gorkha", "Gandaki", "Salasungo"),
    7444: ("Syangja", "Gandaki", "Sakhar"),
    7447: ("Gorkha", "Gandaki", "Takukot"),
    7449: ("Syangja", "Gandaki", "Rampur"),
    7460: ("Kaski", "Gandaki", "Annapurna I East"),
    7461: ("Kaski", "Gandaki", "Annapurna I Middle"),
    7463: ("Nawalpur", "Gandaki", "Madhyabindu"),
    7474: ("Manang", "Gandaki", "Thulagi Chuli"),
    7478: ("Mustang", "Gandaki", "Nilgiri North"),
    7487: ("Mustang", "Gandaki", "Tashi Kang"),
    7489: ("Tanahun", "Gandaki", "Shuklagandaki"),
    7492: ("Mustang", "Gandaki", "Mustang Caves"),
    7497: ("Gorkha", "Gandaki", "Gyaji Kang"),
    7498: ("Syangja", "Gandaki", "Majuwa"),
    7499: ("Syangja", "Gandaki", "Bhattarai Danda"),
    7500: ("Syangja", "Gandaki", "Patasar"),
    7502: ("Kaski", "Gandaki", "Shiva Temple"),
    7505: ("Syangja", "Gandaki", "Saldanda"),
    7506: ("Mustang", "Gandaki", "Lo-Ghekar Damodarkunda"),
    7507: ("Mustang", "Gandaki", "Varagung Muktichhetra"),
    7510: ("Syangja", "Gandaki", "Chandikalika"),
    7512: ("Syangja", "Gandaki", "Biruwa"),
    7513: ("Syangja", "Gandaki", "Galyang"),
    7514: ("Syangja", "Gandaki", "Harinas"),
    # ---------------- Lumbini ----------------
    7248: ("Gulmi", "Lumbini", "Wamitaksar"),
    7252: ("Rolpa", "Lumbini", "Thawang"),
    7302: ("Arghakhanchi", "Lumbini", "Ranighat Palace"),
    7323: ("Pyuthan", "Lumbini", "Koldada"),
    7331: ("Kapilvastu", "Lumbini", "Tilaurakot"),
    7334: ("Palpa", "Lumbini", "Chhahara"),
    7336: ("Kapilvastu", "Lumbini", "Jahadi"),
    7374: ("Palpa", "Lumbini", "Pokharathok"),
    7416: ("Gulmi", "Lumbini", "Rupakot Gulmi"),
    7425: ("Arghakhanchi", "Lumbini", "Argali Darbar"),
    7441: ("Kapilvastu", "Lumbini", "Suryapura"),
    7453: (None, "Lumbini", "Lumbini Province"),
    7464: ("Rupandehi", "Lumbini", "Bhrikuti"),
    7468: ("Pyuthan", "Lumbini", "Jhimruk Khola"),
    7470: ("Rupandehi", "Lumbini", "Jama Masjid Bhairahawa"),
    7511: ("Palpa", "Lumbini", "Alam Devi"),
    # ---------------- Karnali ----------------
    7249: ("Jumla", "Karnali", "Tripurakot"),
    7255: ("Surkhet", "Karnali", "Latikoili"),
    7357: ("Jajarkot", "Karnali", "Syalakhadi"),
    7386: ("Jajarkot", "Karnali", "Jailwang"),
    7401: ("Rukum West", "Karnali", "Musikot Khalanga"),
    7403: ("Dolpa", "Karnali", "Chhonhup"),
    7406: ("Dolpa", "Karnali", "Dhami"),
    7438: ("Jumla", "Karnali", "Sinja Valley"),
    7445: ("Rukum East", "Karnali", "Rukumkot"),
    7452: ("Dolpa", "Karnali", "Dolpo"),
    # ---------------- Sudurpashchim ----------------
    7275: ("Doti", "Sudurpashchim", "Ladagada"),
    7345: ("Dadeldhura", "Sudurpashchim", "Amargadhi"),
    7383: ("Darchula", "Sudurpashchim", "Kalapani territory"),
    7389: ("Bajhang", "Sudurpashchim", "Gurans Himal"),
    7390: ("Kailali", "Sudurpashchim", "Ghodaghodi Tal"),
    7417: ("Baitadi", "Sudurpashchim", "Dasharathchand"),
    7440: ("Bajhang", "Sudurpashchim", "Seti River"),
    7442: ("Achham", "Sudurpashchim", "Sanphebagar"),
    7451: ("Bajura", "Sudurpashchim", "Kanda, Bajura"),
    7462: ("Dadeldhura", "Sudurpashchim", "Amaragadhi"),
}

# ---------------------------------------------------------------------------
# 2) Legacy rows that have a district but no province (older imports)
# ---------------------------------------------------------------------------
DISTRICT_PROVINCE = {
    # Koshi
    "Bhojpur": "Koshi", "Dhankuta": "Koshi", "Ilam": "Koshi", "Jhapa": "Koshi",
    "Khotang": "Koshi", "Morang": "Koshi", "Okhaldhunga": "Koshi",
    "Panchthar": "Koshi", "Sankhuwasabha": "Koshi", "Solukhumbu": "Koshi",
    "Sunsari": "Koshi", "Taplejung": "Koshi", "Terhathum": "Koshi",
    "Tekhathum": "Koshi", "Tapejung": "Koshi", "Udayapur": "Koshi",
    "Kanyam": "Koshi", "Itahari": "Koshi", "Dharan": "Koshi",
    "Pathibhara": "Koshi", "Olangchungola": "Koshi", "Taplejung/Koshi": "Koshi",
    # Madhesh
    "Saptari": "Madhesh", "Siraha": "Madhesh", "Dhanusha": "Madhesh",
    "Mahottari": "Madhesh", "Sarlahi": "Madhesh", "Rautahat": "Madhesh",
    "Bara": "Madhesh", "Parsa": "Madhesh",
    # Bagmati
    "Kathmandu": "Bagmati", "Bhaktapur": "Bagmati", "Lalitpur": "Bagmati",
    "Kavre": "Bagmati", "Kavrepalanchok": "Bagmati", "Sindhupalchok": "Bagmati",
    "Rasuwa": "Bagmati", "Nuwakot": "Bagmati", "Dhading": "Bagmati",
    "Makwanpur": "Bagmati", "Chitwan": "Bagmati", "Citwan": "Bagmati",
    "Sindhuli": "Bagmati", "Ramechhap": "Bagmati", "Dolakha": "Bagmati",
    "Nuwakot/Bhaktapur": "Bagmati",
    # Gandaki
    "Gorkha": "Gandaki", "Lamjung": "Gandaki", "Tanahun": "Gandaki",
    "Kaski": "Gandaki", "Manang": "Gandaki", "Syangja": "Gandaki",
    "Parbat": "Gandaki", "Mustang": "Gandaki", "Myagdi": "Gandaki",
    "Baglung": "Gandaki", "Nawalpur": "Gandaki", "Kaski/Gorkha": "Gandaki",
    "Kaski/Gandaki": "Gandaki", "Parbat/Gandaki": "Gandaki",
    "Syangja/Gandaki": "Gandaki",
    # Lumbini
    "Rupandehi": "Lumbini", "Palpa": "Lumbini", "Kapilvastu": "Lumbini",
    "Gulmi": "Lumbini", "Arghakhanchi": "Lumbini", "Rolpa": "Lumbini",
    "Pyuthan": "Lumbini", "Dang": "Lumbini", "Bardia": "Lumbini",
    "Gulmi/Lumbini": "Lumbini",
    # Karnali
    "Surkhet": "Karnali", "Salyan": "Karnali", "Rukum": "Karnali",
    "Rukum West": "Karnali", "Rukum East": "Karnali", "Jajarkot": "Karnali",
    "Kalikot": "Karnali", "Mugu": "Karnali", "Humla": "Karnali",
    "H umla": "Karnali", "Dailekh": "Karnali",
    # Sudurpashchim
    "Doti": "Sudurpashchim", "Darchula": "Sudurpashchim",
    "Bajhang": "Sudurpashchim", "Baitadi": "Sudurpashchim",
    "Dadeldhura": "Sudurpashchim", "Achham": "Sudurpashchim",
    "Kailali": "Sudurpashchim", "Bajura": "Sudurpashchim",
    # passthrough
    "Koshi": "Koshi", "Bagmati": "Bagmati", "Gandaki": "Gandaki",
    "Lumbini": "Lumbini", "Sudurpashchim": "Sudurpashchim",
}

DISTRICT_FIX = {
    "Tekhathum": "Terhathum", "Tapejung": "Taplejung",
    "Citwan": "Chitwan", "Kavrepalanchok": "Kavre",
    "Olangchungola": "Taplejung", "P Parsa": "Parsa",
    "Taplejung/Koshi": "Taplejung", "Rasuwa/Bajura": "Rasuwa",
}


def main():
    cats = {c.slug: c for c in Category.objects.all()}
    updated = 0
    for dest in Destination.objects.filter(id__in=WIKIDATA_MAP.keys()):
        dist, prov, city = WIKIDATA_MAP[dest.id]
        dest.district = dist
        dest.province = prov
        dest.city = city or dest.city
        dest.save(update_fields=["district", "province", "city"])
        updated += 1
    print(f"wikidata dests updated: {updated}")

    # legacy rows: district present, province missing
    fixed_legacy = 0
    for dest in Destination.objects.filter(
        province__isnull=True
    ).exclude(district__isnull=True).exclude(district=""):
        d = dest.district
        if d in ("District", "50-150", "Other Expenses (USD)"):
            continue
        d2 = DISTRICT_FIX.get(d, d)
        prov = DISTRICT_PROVINCE.get(d2) or DISTRICT_PROVINCE.get(d)
        if prov:
            dest.province = prov
            if d2 != d:
                dest.district = d2
            dest.save(update_fields=["province", "district"])
            fixed_legacy += 1
    # also empty-string province rows
    for dest in Destination.objects.filter(province="").exclude(district__isnull=True).exclude(district=""):
        d = dest.district
        if d in ("District", "50-150", "Other Expenses (USD)"):
            continue
        d2 = DISTRICT_FIX.get(d, d)
        prov = DISTRICT_PROVINCE.get(d2) or DISTRICT_PROVINCE.get(d)
        if prov:
            dest.province = prov
            if d2 != d:
                dest.district = d2
            dest.save(update_fields=["province", "district"])
            fixed_legacy += 1
    print(f"legacy district->province fixed: {fixed_legacy}")

    # ------------------------------------------------------------------
    # 3) Fix the broken Bindabasini Temple entry (Kathmandu coords on a
    #    Parsa temple) -> Birgunj's famous Bindabasini Temple (Madhesh)
    # ------------------------------------------------------------------
    b = Destination.objects.filter(id=5869).first()
    if b:
        b.district = "Parsa"
        b.province = "Madhesh"
        b.city = "Birgunj"
        b.city_english = "Birgunj"
        b.latitude = 27.004
        b.longitude = 84.870
        b.short_description = (
            "Famous Kali temple of Birgunj, a major Shakti pilgrimage site of Parsa district."
        )
        b.description = (
            "Bindabasini Temple is one of Birgunj's most revered Shakti temples, "
            "dedicated to Goddess Bindabasini (Kali). It is a major pilgrimage "
            "and Chhath destination in Parsa district, Madhesh Province."
        )
        b.save()
        print("Bindabasini Temple fixed -> Birgunj, Parsa, Madhesh")

    # ------------------------------------------------------------------
    # 4) Add the last missing named places from the Koshi/Madhesh ward data
    # ------------------------------------------------------------------
    NEW_PLACES = [
        ("Surunga Baba", "pilgrimage", "Saptari", "Madhesh", "Surunga", 26.60, 86.72,
         "Baba shrine of Surunga Municipality, a noted religious site of Saptari district."),
        ("Birtamod", "cities", "Jhapa", "Koshi", "Birtamod", 26.63, 87.98,
         "Largest city of Jhapa district, a major trade and business hub of eastern Nepal."),
        ("Damak", "cities", "Jhapa", "Koshi", "Damak", 26.66, 87.70,
         "Municipality of Jhapa district on the Mechi Highway, an industrial and trade town of eastern Nepal."),
    ]
    created = 0
    for name, cslug, dist, prov, city, lat, lon, short in NEW_PLACES:
        slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "").replace("'", "")
        if Destination.objects.filter(slug=slug).exists():
            print(f"skip (exists): {name}")
            continue
        cat = cats.get(cslug) or cats.get("attraction")
        Destination.objects.create(
            name=name, slug=slug, category=cat, district=dist, province=prov,
            city=city, city_english=city, latitude=lat, longitude=lon,
            short_description=short, description=short, country="Nepal",
            status="approved", is_active=True, source="round15-koshi-madhesh",
            views_count=0,
        )
        created += 1
    print(f"new places created: {created}")


if __name__ == "__main__":
    main()
