"""Round 21: Add Lumbini + Gandaki Province famous named places from the
ward-level destination pools (Rupandehi, Kapilvastu, Palpa, Gulmi,
Arghakhanchi, Nawalparasi West, Dang, Banke, Bardiya, Pyuthan, Rolpa,
Rukum East, Kaski, Gorkha, Lamjung, Manang, Mustang, Myagdi, Baglung,
Parbat, Syangja, Tanahun, Nawalpur). Skips existing, disambiguates slugs,
fixes the 'Seti River George' typo.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

DISTRICT_ALIASES = {
    "Rupandehi": {"Rupandehi", "रुपन्देही", "रुपन्देही जिल्ला", "Rupandehi District"},
    "Kapilvastu": {"Kapilvastu", "कपिलवस्तु", "कपिलवस्तु जिल्ला", "Kapilvastu District"},
    "Palpa": {"Palpa", "पाल्पा", "पाल्पा जिल्ला", "Palpa District"},
    "Gulmi": {"Gulmi", "गुल्मी", "गुल्मी जिल्ला", "Gulmi District"},
    "Arghakhanchi": {"Arghakhanchi", "अर्घाखाँची", "अर्घाखाँची जिल्ला", "Arghakhanchi District"},
    "Nawalparasi West": {"Nawalparasi West", "पश्चिम नवलपरासी", "पश्चिम नवलपरासी जिल्ला", "Nawalparasi West District"},
    "Dang": {"Dang", "दाङ", "दाङ जिल्ला", "Dang District"},
    "Banke": {"Banke", "बाँके", "बाँके जिल्ला", "Banke District"},
    "Bardiya": {"Bardiya", "बर्दिया", "बर्दिया जिल्ला", "Bardiya District"},
    "Pyuthan": {"Pyuthan", "प्युठान", "प्युठान जिल्ला", "Pyuthan District"},
    "Rolpa": {"Rolpa", "रोल्पा", "रोल्पा जिल्ला", "Rolpa District"},
    "Rukum East": {"Rukum East", "पूर्वी रुकुम", "पूर्वी रुकुम जिल्ला", "Rukum East District"},
    "Kaski": {"Kaski", "कास्की", "कास्की जिल्ला", "Kaski District"},
    "Gorkha": {"Gorkha", "गोरखा", "गोरखा जिल्ला", "Gorkha District"},
    "Lamjung": {"Lamjung", "लमजुङ", "लमजुङ जिल्ला", "Lamjung District"},
    "Manang": {"Manang", "मनाङ", "मनाङ जिल्ला", "Manang District"},
    "Mustang": {"Mustang", "मुस्ताङ", "मुस्ताङ जिल्ला", "Mustang District"},
    "Myagdi": {"Myagdi", "म्याग्दी", "म्याग्दी जिल्ला", "Myagdi District"},
    "Baglung": {"Baglung", "बागलुङ", "बागलुङ जिल्ला", "Baglung District"},
    "Parbat": {"Parbat", "पर्वत", "पर्वत जिल्ला", "Parbat District"},
    "Syangja": {"Syangja", "स्याङ्जा", "स्याङ्जा जिल्ला", "Syangja District"},
    "Tanahun": {"Tanahun", "तनहुँ", "तनहुँ जिल्ला", "Tanahun District"},
    "Nawalpur": {"Nawalpur", "नवलपुर", "नवलपुर जिल्ला", "Nawalpur District"},
}

PROVINCE_BY_DISTRICT = {
    "Rupandehi": "Lumbini", "Kapilvastu": "Lumbini", "Palpa": "Lumbini",
    "Gulmi": "Lumbini", "Arghakhanchi": "Lumbini", "Nawalparasi West": "Lumbini",
    "Dang": "Lumbini", "Banke": "Lumbini", "Bardiya": "Lumbini",
    "Pyuthan": "Lumbini", "Rolpa": "Lumbini", "Rukum East": "Lumbini",
    "Kaski": "Gandaki", "Gorkha": "Gandaki", "Lamjung": "Gandaki",
    "Manang": "Gandaki", "Mustang": "Gandaki", "Myagdi": "Gandaki",
    "Baglung": "Gandaki", "Parbat": "Gandaki", "Syangja": "Gandaki",
    "Tanahun": "Gandaki", "Nawalpur": "Gandaki",
}

# (name, category_slug, district, city, lat, lon, short_description)
PLACES = [
    # ================= RUPANDEHI =================
    ("Puskarini Pond", "lakes", "Rupandehi", "Lumbini Sanskritik", 27.469, 83.276, "Sacred bathing pond beside the Mayadevi Temple in the Lumbini garden."),
    ("Myanmar Golden Temple", "buddhist-sites", "Rupandehi", "Lumbini Sanskritik", 27.478, 83.282, "Myanmar Buddhist monastery in the Lumbini monastic zone."),
    ("Royal Thai Monastery", "buddhist-sites", "Rupandehi", "Lumbini Sanskritik", 27.481, 83.279, "Thai Buddhist temple of the Lumbini monastic zone."),
    ("Chinese Monastery Lumbini", "buddhist-sites", "Rupandehi", "Lumbini Sanskritik", 27.480, 83.280, "Chinese Buddhist temple of the Lumbini monastic zone."),
    ("German Monastery Lumbini", "buddhist-sites", "Rupandehi", "Lumbini Sanskritik", 27.476, 83.281, "German Buddhist monastery of the Lumbini monastic zone."),
    ("Jitgadhi Fort", "heritage", "Rupandehi", "Butwal", 27.700, 83.460, "Historic fort of Butwal associated with the Anglo-Nepalese war."),
    ("Manimukunda Sen Park", "parks-gardens", "Rupandehi", "Butwal", 27.705, 83.455, "Historic park of Butwal named after King Manimukunda Sen."),
    ("Butwal Hill Park", "parks-gardens", "Rupandehi", "Butwal", 27.710, 83.440, "Hill park of Butwal with city views."),
    ("Sainamaina", "heritage", "Rupandehi", "Sainamaina", 27.560, 83.330, "Archaeological area of Sainamaina near Lumbini."),
    ("Parroha Dham", "pilgrimage", "Rupandehi", "Tilottama", 27.600, 83.400, "Religious site of Parroha, Rupandehi."),
    ("Muktinath Dham Butwal", "pilgrimage", "Rupandehi", "Butwal", 27.690, 83.440, "Religious site of Butwal."),
    ("Santaneshwar Ghat", "pilgrimage", "Rupandehi", "Butwal", 27.710, 83.450, "Ghat on the Tinau river at Butwal."),
    ("Global Peace Park", "parks-gardens", "Rupandehi", "Lumbini Sanskritik", 27.485, 83.275, "Peace park near Lumbini."),
    ("Ban Batika", "parks-gardens", "Rupandehi", "Butwal", 27.695, 83.465, "Forest garden of Butwal."),
    ("Gajedi Lake", "lakes", "Rupandehi", "Devdaha", 27.570, 83.430, "Lake of the Devdaha area."),
    ("Danapur Lake", "lakes", "Rupandehi", "Devdaha", 27.565, 83.435, "Lake of Danapur, Rupandehi."),
    ("Gaidahawa Lake", "lakes", "Rupandehi", "Gaidahawa", 27.500, 83.380, "Lake of Gaidahawa rural municipality."),
    ("Nandabhoj Lake", "lakes", "Rupandehi", "Gaidahawa", 27.510, 83.390, "Lake of Rupandehi."),
    ("Karpakatti Lake", "lakes", "Rupandehi", "Gaidahawa", 27.520, 83.400, "Lake of Rupandehi."),
    ("Kotihawa", "heritage", "Rupandehi", "Kotihawa", 27.490, 83.340, "Archaeological site with an Ashoka pillar fragment near Lumbini."),
    ("Devdaha", "heritage", "Rupandehi", "Devdaha", 27.590, 83.450, "Ancient Shakya capital where Buddha spent his childhood, now an archaeological area."),
    # ================= KAPILVASTU =================
    ("Gotihawa", "heritage", "Kapilvastu", "Kapilvastu", 27.487, 83.166, "Buddhist archaeological site with an Ashoka pillar, south of Tilaurakot."),
    ("Aurorakot", "heritage", "Kapilvastu", "Kapilvastu", 27.520, 83.100, "Archaeological mound of ancient Aroura, Kapilvastu."),
    ("Piprahawa", "heritage", "Kapilvastu", "Krishnanagar", 27.430, 83.130, "Archaeological site of the Shakya area in Kapilvastu."),
    ("Taulihawa Bazaar", "cities", "Kapilvastu", "Kapilvastu", 27.545, 83.060, "Heritage bazaar town of Kapilvastu."),
    ("Tauleshwarnath Temple", "temples", "Kapilvastu", "Kapilvastu", 27.548, 83.055, "Shiva temple of Taulihawa."),
    ("Shivagadhi", "heritage", "Kapilvastu", "Shivraj", 27.600, 83.200, "Historic fort of Shivraj municipality."),
    ("Ramghat Kapilvastu", "pilgrimage", "Kapilvastu", "Kapilvastu", 27.580, 83.250, "Religious ghat of Kapilvastu."),
    ("Laxman Ghat", "pilgrimage", "Kapilvastu", "Banganga", 27.620, 83.330, "Religious ghat on the Banganga river with 108 Shiva lingas."),
    ("Samay Mai Temple", "temples", "Kapilvastu", "Kapilvastu", 27.560, 83.150, "Samay Mai temple of Kapilvastu."),
    ("Sisahaniya Kot", "heritage", "Kapilvastu", "Mayadevi", 27.510, 83.080, "Ancient archaeological mound complex of Mayadevi Ward 5."),
    ("Dohani", "heritage", "Kapilvastu", "Kapilvastu", 27.530, 83.090, "Archaeological site of Kapilvastu."),
    ("Kramukot", "heritage", "Kapilvastu", "Kapilvastu", 27.550, 83.120, "Archaeological site of the ancient Shakya area."),
    ("Banganga River", "rivers", "Kapilvastu", "Banganga", 27.620, 83.350, "River of Kapilvastu with religious ghats."),
    ("Shringighat Dham", "pilgrimage", "Kapilvastu", "Banganga", 27.640, 83.350, "Religious ghat of Banganga municipality."),
    ("Madhuban Dham", "pilgrimage", "Kapilvastu", "Banganga", 27.630, 83.340, "Religious site of Banganga municipality."),
    ("Kapil Dham", "pilgrimage", "Kapilvastu", "Banganga", 27.635, 83.345, "Religious site of Banganga municipality."),
    ("Ram Datiwan Dham", "pilgrimage", "Kapilvastu", "Banganga", 27.625, 83.330, "Ram Datiwan religious site of Banganga municipality."),
    ("Kharkhani", "parks-gardens", "Kapilvastu", "Banganga", 27.660, 83.360, "Picnic spot in the Pragati Community Forest, Banganga Ward 7."),
    ("Sonwagadh Temple", "temples", "Kapilvastu", "Shivraj", 27.590, 83.220, "Historical temple of Shivraj Ward 3."),
    ("Dudhdhari Baba Temple", "temples", "Kapilvastu", "Bijaynagar", 27.480, 83.200, "Baba temple of Bijaynagar."),
    ("Shankarpur Lake", "lakes", "Kapilvastu", "Bijaynagar", 27.470, 83.190, "Lake of Bijaynagar."),
    ("Puraina Baba Temple", "temples", "Kapilvastu", "Bijaynagar", 27.490, 83.210, "Baba temple of Bijaynagar."),
    ("Badki Mai Temple", "temples", "Kapilvastu", "Bijaynagar", 27.480, 83.220, "Goddess temple of Bijaynagar."),
    # ================= PALPA =================
    ("Shitalpati", "heritage", "Palpa", "Tansen", 27.867, 83.540, "Historic covered trading square of Tansen."),
    ("Ramdi", "villages", "Palpa", "Rampur", 27.800, 83.620, "Historic bazaar at the Kali Gandaki crossing, Palpa."),
    ("Nuwakot Fort Palpa", "heritage", "Palpa", "Nisdi", 27.830, 83.600, "Historic fort of Palpa district."),
    # ================= GULMI =================
    ("Bichitra Cave", "caves", "Gulmi", "Gulmi", 28.100, 83.250, "Cave of Gulmi district."),
    ("Khadgakot", "villages", "Gulmi", "Khadgakot", 28.050, 83.350, "Village of Gulmi on the Kali Gandaki."),
    ("Isma Durbar", "heritage", "Gulmi", "Isma", 28.050, 83.280, "Historic durbar of Isma, Gulmi."),
    ("Musikot Durbar Gulmi", "heritage", "Gulmi", "Musikot", 28.100, 83.150, "Historic durbar of Musikot, Gulmi."),
    ("Tamghas", "cities", "Gulmi", "Resunga", 28.070, 83.250, "District headquarters town of Gulmi."),
    ("Malika Banjhakateri", "viewpoints", "Gulmi", "Malika", 28.160, 83.350, "Hill viewpoint of Gulmi."),
    # ================= ARGHAKHANCHI =================
    ("Panini Tapobhumi", "heritage", "Arghakhanchi", "Panini", 27.950, 83.080, "Site associated with the ancient grammarian Panini."),
    ("Argha Durbar", "heritage", "Arghakhanchi", "Argha", 27.930, 83.050, "Historic durbar of Arghakhanchi."),
    ("Khanchi Durbar", "heritage", "Arghakhanchi", "Sandhikharka", 27.900, 83.100, "Historic durbar of Khanchi."),
    ("Narpani", "natural-wonders", "Arghakhanchi", "Narpani", 27.870, 83.150, "Snowfall viewpoint area of Arghakhanchi."),
    ("Chhatradev Devalaya", "temples", "Arghakhanchi", "Chhatradev", 27.920, 83.120, "Temple of Chhatradev."),
    # ================= NAWALPARASI WEST =================
    ("Somnath Temple Triveni", "temples", "Nawalparasi West", "Triveni", 27.710, 84.420, "Temple at the Triveni confluence."),
    ("Daunne Devi Temple", "temples", "Nawalparasi West", "Daunne", 27.650, 84.100, "Goddess temple of Daunne hill."),
    ("Palhi Bhagwati Temple", "temples", "Nawalparasi West", "Palhi", 27.600, 84.000, "Goddess temple of Palhi."),
    ("Sunwal", "cities", "Nawalparasi West", "Sunwal", 27.630, 83.900, "Town of western Nawalparasi."),
    ("Parasi", "cities", "Nawalparasi West", "Parasi", 27.520, 83.670, "District headquarters town of Nawalparasi West."),
    # ================= DANG =================
    ("Ambikeshwari Temple", "temples", "Dang", "Ghorahi", 28.030, 82.480, "Goddess temple of Ghorahi, Dang."),
    ("Barahakune Daha", "lakes", "Dang", "Dangisharan", 28.000, 82.300, "Sacred lake of Dang with twelve prongs."),
    ("Dangisharan Palace", "heritage", "Dang", "Dangisharan", 28.050, 82.400, "Historic palace and Tharu cultural site of Dang."),
    ("Chaughera", "villages", "Dang", "Dangisharan", 28.080, 82.280, "Historic bazaar of Dang."),
    ("Tulsipur", "cities", "Dang", "Tulsipur", 28.130, 82.300, "City of Dang district."),
    ("Ratnanath Temple", "temples", "Dang", "Ghorahi", 28.040, 82.500, "Temple of Ghorahi, Dang."),
    ("Jangalkuti", "villages", "Dang", "Ghorahi", 27.980, 82.350, "Village of Dang associated with the Gorakhnath legend."),
    ("Devikot", "heritage", "Dang", "Deukhuri", 27.970, 82.420, "Historic site of Dang."),
    ("Jakhera Lake", "lakes", "Dang", "Gadhawa", 28.020, 82.360, "Lake of Dang."),
    ("Bagar Baba", "pilgrimage", "Dang", "Rapti", 28.070, 82.450, "Religious area of Bagar Baba, Dang."),
    ("Dharapani Dham Dang", "temples", "Dang", "Ghorahi", 28.050, 82.470, "Religious dham of Dharapani, Dang."),
    # ================= BANKE =================
    ("Kohalpur", "cities", "Banke", "Kohalpur", 28.180, 81.600, "Town of Banke district."),
    ("Barfeni Baba Dham", "pilgrimage", "Banke", "Baijanath", 28.100, 81.750, "Religious site of Barfeni Baba, Banke."),
    ("Gavar Valley", "valleys", "Banke", "Rapti Sonari", 28.150, 81.850, "Valley of Banke with community-homestay tourism."),
    ("Khajura", "villages", "Banke", "Khajura", 28.120, 81.700, "Cultural village of Banke."),
    ("Narainapur", "villages", "Banke", "Narainapur", 28.050, 81.600, "Rural village of Banke promoted for tourism."),
    ("Sikta", "heritage", "Banke", "Rapti Sonari", 28.220, 81.900, "Sikta irrigation and reservoir area of Banke."),
    # ================= BARDIYA =================
    ("Badhaiya Lake", "lakes", "Bardiya", "Badhaiyatal", 28.200, 81.350, "Lake of Bardiya, a wetland near the national park."),
    ("Geruwa River", "rivers", "Bardiya", "Geruwa", 28.100, 81.400, "River branch of the Karnali along Bardiya National Park."),
    ("Dalla Community Homestay", "eco-tourism", "Bardiya", "Dalla", 28.250, 81.300, "Community homestay village of Bardiya."),
    ("Thakurdwara", "villages", "Bardiya", "Thakurbaba", 28.150, 81.250, "Gateway village of Bardiya National Park."),
    # ================= PYUTHAN =================
    ("Gaumukhi Dham", "natural-wonders", "Pyuthan", "Gaumukhi", 28.100, 82.900, "Water-source religious site of Pyuthan."),
    ("Naubahini Danda", "viewpoints", "Pyuthan", "Naubahini", 28.130, 82.850, "Hill viewpoint of Pyuthan."),
    ("Mallarani Danda", "mountains", "Pyuthan", "Mallarani", 28.050, 82.950, "Hill of Pyuthan district."),
    ("Jhimruk Hydropower", "heritage", "Pyuthan", "Jhimruk", 28.100, 82.850, "Hydropower area of the Jhimruk river."),
    # ================= ROLPA =================
    ("Holeri", "villages", "Rolpa", "Madi", 28.350, 82.600, "Village of Rolpa on the Jaljala trail."),
    ("Liwang", "cities", "Rolpa", "Liwang", 28.280, 82.720, "District headquarters town of Rolpa."),
    ("Jelbang", "villages", "Rolpa", "Jelbang", 28.200, 82.800, "Magar village of Rolpa."),
    ("Runtigadhi Fort", "heritage", "Rolpa", "Runtigadhi", 28.320, 82.680, "Historic fort of Rolpa."),
    ("Sunchhahari Waterfall", "waterfalls", "Rolpa", "Sunchhahari", 28.180, 82.900, "Waterfall of Rolpa district."),
    ("Tilachan Daha", "lakes", "Rolpa", "Tilachan", 28.400, 82.550, "Sacred lake of Rolpa."),
    ("Guerrilla Trek", "trekking", "Rolpa", "Liwang", 28.300, 82.700, "Trekking route through the history of the people's war in Rolpa."),
    # ================= RUKUM EAST =================
    ("Sundaha", "lakes", "Rukum East", "Sisne", 28.650, 82.400, "Lake of East Rukum."),
    ("Golde Waterfall", "waterfalls", "Rukum East", "Sisne", 28.600, 82.300, "Waterfall of East Rukum."),
    ("Lawang", "villages", "Rukum East", "Putha Uttarganga", 28.580, 82.550, "Settlement of East Rukum."),
    ("Taksera", "villages", "Rukum East", "Putha Uttarganga", 28.700, 82.600, "Village of East Rukum on the Dhorpatan trail."),
    ("Maikot", "villages", "Rukum East", "Sisne", 28.660, 82.500, "Village of East Rukum."),
    ("Pelma", "villages", "Rukum East", "Sisne", 28.680, 82.450, "Village of East Rukum."),
    ("Hukam", "villages", "Rukum East", "Sisne", 28.630, 82.420, "Village of East Rukum."),
    ("Rukumkot Durbar", "heritage", "Rukum East", "Rukumkot", 28.620, 82.600, "Historic palace of Rukumkot."),
    # ================= KASKI =================
    ("Gurkha Museum", "museums", "Kaski", "Pokhara", 28.210, 83.960, "Museum of Gurkha history at Pokhara."),
    ("Matepani Gumba", "buddhist-sites", "Kaski", "Pokhara", 28.230, 83.990, "Buddhist monastery of Pokhara."),
    ("Hemja", "villages", "Kaski", "Pokhara", 28.230, 83.970, "Village of Kaski on the Panchase route."),
    ("Naudanda", "viewpoints", "Kaski", "Pokhara", 28.200, 83.900, "Hill viewpoint of Kaski."),
    ("Kahun Danda", "viewpoints", "Kaski", "Pokhara", 28.190, 83.930, "Hill viewpoint of Pokhara."),
    ("Machhapuchhre Base Camp", "trekking", "Kaski", "Annapurna", 28.450, 83.870, "Base camp at the foot of Machhapuchhre."),
    ("Tangting", "villages", "Kaski", "Madi", 28.340, 84.000, "Gurung village of Kaski."),
    ("Dhital", "villages", "Kaski", "Pokhara", 28.280, 83.880, "Village of Kaski."),
    ("Lumle", "villages", "Kaski", "Pokhara", 28.300, 83.830, "Village of Kaski."),
    ("Pumdikot", "viewpoints", "Kaski", "Pokhara", 28.160, 83.930, "Hill viewpoint of Pokhara with a giant Shiva statue."),
    # ================= GORKHA =================
    ("Siranchok", "viewpoints", "Gorkha", "Siranchok", 27.900, 84.600, "Hill viewpoint of Gorkha with Himalayan views."),
    ("Mu Gompa", "buddhist-sites", "Gorkha", "Chum Nubri", 28.420, 85.000, "Monastery of the Tsum valley."),
    ("Rachen Gompa", "buddhist-sites", "Gorkha", "Chum Nubri", 28.400, 84.980, "Monastery of the Tsum valley."),
    ("Chhokangparo", "villages", "Gorkha", "Tsum Nubri", 28.350, 84.950, "Village of the Tsum valley."),
    ("Philim", "villages", "Gorkha", "Chum Nubri", 28.200, 84.900, "Village on the Manaslu trek."),
    ("Machha Khola", "villages", "Gorkha", "Sahid Lakhan", 28.220, 84.800, "Village and river on the Manaslu circuit."),
    ("Soti Khola", "villages", "Gorkha", "Dharche", 28.140, 84.780, "Trailhead village of the Manaslu circuit."),
    ("Aarughat", "villages", "Gorkha", "Aarughat", 28.000, 84.750, "Historic bazaar at the Budhi Gandaki, gateway to Manaslu."),
    ("Birendra Lake", "lakes", "Gorkha", "Chum Nubri", 28.300, 85.050, "Lake near Samagaun on the Manaslu route."),
    # ================= LAMJUNG =================
    ("Ghan Pokhara", "villages", "Lamjung", "Marsyangdi", 28.300, 84.380, "Gurung village of Lamjung."),
    ("Pasgaun", "villages", "Lamjung", "Marsyangdi", 28.320, 84.360, "Gurung village of Lamjung."),
    ("Rainas Kot", "heritage", "Lamjung", "Rainas", 28.200, 84.420, "Historic fort of Rainas, Lamjung."),
    ("Dordi Valley", "valleys", "Lamjung", "Dordi", 28.300, 84.300, "Valley of Lamjung district."),
    ("Tarkughat", "villages", "Lamjung", "Dordi", 28.250, 84.300, "Village of Lamjung."),
    ("Gaunshahar Durbar", "heritage", "Lamjung", "Dordi", 28.180, 84.350, "Historic palace site of Lamjung."),
    ("Purankot", "heritage", "Lamjung", "Dudhpokhari", 28.150, 84.400, "Historic fort of Lamjung."),
    ("Karaputar", "villages", "Lamjung", "Kwholasothar", 28.240, 84.450, "Village of Lamjung."),
    ("Sundarbazar", "cities", "Lamjung", "Sundarbazar", 28.150, 84.420, "Town of Lamjung district."),
    # ================= MANANG =================
    ("Ngawal", "villages", "Manang", "Narpa Bhumi", 28.630, 84.050, "Village of the Annapurna circuit."),
    ("Tal (Manang)", "villages", "Manang", "Chame", 28.390, 84.380, "Village at the entrance of the Manang valley."),
    ("Timang", "villages", "Manang", "Chame", 28.470, 84.280, "Village of the Annapurna circuit."),
    ("Koto", "villages", "Manang", "Chame", 28.460, 84.250, "Village of Manang."),
    ("Ledar", "villages", "Manang", "Nashong", 28.620, 83.960, "Village on the way to Thorong La."),
    ("Thorong Phedi", "villages", "Manang", "Nashong", 28.690, 83.900, "Base settlement below the Thorong La pass."),
    ("Kang La Pass", "mountains", "Manang", "Narpa Bhumi", 28.610, 84.120, "Pass connecting the Nar Phu valley."),
    ("Phu Village", "villages", "Manang", "Narpa Bhumi", 28.750, 84.200, "Village of the Nar Phu valley."),
    ("Nar Village", "villages", "Manang", "Narpa Bhumi", 28.710, 84.160, "Village of the Nar Phu valley."),
    # ================= MUSTANG =================
    ("Jwala Mai Temple", "temples", "Mustang", "Varagung Muktichhetra", 28.820, 83.870, "Eternal-flame temple beside Muktinath."),
    ("Tingkhar", "villages", "Mustang", "Lo Manthang", 29.150, 83.950, "Village of upper Mustang."),
    ("Nyphu Cave", "caves", "Mustang", "Lo Manthang", 29.200, 83.900, "Cave monastery of upper Mustang."),
    ("Konchok Ling Cave", "caves", "Mustang", "Lo Manthang", 29.180, 83.880, "Cave monastery of upper Mustang."),
    ("Dhakmar", "villages", "Mustang", "Ghami", 29.100, 83.920, "Red-cliff village of upper Mustang."),
    ("Tsarang Palace", "heritage", "Mustang", "Tsarang", 29.110, 83.950, "Historic palace of Tsarang, upper Mustang."),
    ("Chele", "villages", "Mustang", "Ghami", 28.950, 83.900, "Village on the upper Mustang trail."),
    ("Dhumba Lake", "lakes", "Mustang", "Thasang", 28.780, 83.700, "Lake near Thini, Mustang."),
    # ================= MYAGDI =================
    ("Galeshwor Temple", "temples", "Myagdi", "Beni", 28.350, 83.550, "Temple of Galeshwor on the Kali Gandaki."),
    # ================= BAGLUNG =================
    ("Galkot Durbar", "heritage", "Baglung", "Galkot", 28.200, 83.430, "Historic palace of Galkot, Baglung."),
    ("Balewa", "villages", "Baglung", "Baglung", 28.180, 83.530, "Village with the Balewa airport."),
    ("Bhakunde", "villages", "Baglung", "Baglung", 28.100, 83.480, "Village and viewpoint of Baglung."),
    ("Tamankhola Valley", "valleys", "Baglung", "Tamankhola", 28.220, 83.300, "Valley of Baglung district."),
    ("Nisi Valley", "valleys", "Baglung", "Nisi", 28.150, 83.350, "Valley of Baglung district."),
    ("Jaimini Dham", "pilgrimage", "Baglung", "Jaimini", 28.050, 83.450, "Religious site of Baglung."),
    ("Gaja Daha", "lakes", "Baglung", "Baglung", 28.120, 83.470, "Lake of Baglung district."),
    # ================= PARBAT =================
    ("Alapeshwor Cave", "caves", "Parbat", "Kushma", 28.200, 83.650, "Cave temple of Parbat."),
    ("Phalewas", "heritage", "Parbat", "Phalewas", 28.150, 83.630, "Historic area of Phalewas, Parbat."),
    ("Arthar Danda", "viewpoints", "Parbat", "Kushma", 28.100, 83.600, "Hill viewpoint of Parbat."),
    ("Paiyun", "villages", "Parbat", "Modi", 28.120, 83.680, "Village of Parbat."),
    ("Bihadi", "villages", "Parbat", "Bihadi", 28.080, 83.660, "Village of Parbat."),
    ("Seti Beni", "pilgrimage", "Parbat", "Jaljala", 28.050, 83.600, "Confluence of the Seti and Kali Gandaki, a shaligram site."),
    # ================= SYANGJA =================
    ("Putalibazar", "cities", "Syangja", "Putalibazar", 28.080, 83.850, "Town of Syangja district."),
    ("Panchamul", "viewpoints", "Syangja", "Galyang", 28.050, 83.700, "Hill viewpoint of Syangja."),
    ("Bhirkot Durbar", "heritage", "Syangja", "Bhirkot", 27.980, 83.720, "Historic durbar of Bhirkot, Syangja."),
    ("Aandhikhola River", "rivers", "Syangja", "Aandhikhola", 27.950, 83.780, "River of Syangja district."),
    ("Karkineta Viewpoint", "viewpoints", "Syangja", "Harinas", 28.020, 83.800, "Hill viewpoint of Syangja."),
    ("Chhangchhangdi Temple", "temples", "Syangja", "Chapakot", 28.020, 83.680, "Temple of Chhangchhangdi, Syangja."),
    # ================= TANAHUN =================
    ("Khadga Devi Temple", "temples", "Tanahun", "Bandipur", 27.940, 84.410, "Temple on the hill above Bandipur."),
    ("Thani Mai Temple", "temples", "Tanahun", "Bandipur", 27.940, 84.420, "Temple of Bandipur."),
    ("Damauli", "cities", "Tanahun", "Shuklagandaki", 27.970, 84.270, "Town of Tanahun district."),
    ("Chabdi Barahi Temple", "temples", "Tanahun", "Bandipur", 27.980, 84.200, "Barahi temple of Chabdi, Tanahun."),
    ("Dhorbarahi Temple", "temples", "Tanahun", "Devghat", 27.900, 84.150, "Barahi temple of Dhorbarahi, Tanahun."),
    ("Tanahun Durbar", "heritage", "Tanahun", "Devghat", 27.900, 84.200, "Historic durbar of Tanahun district."),
    ("Ghiring", "villages", "Tanahun", "Ghiring", 27.950, 84.300, "Village of Tanahun."),
    ("Rishing", "villages", "Tanahun", "Rishing", 27.970, 84.330, "Village of Tanahun."),
    ("Mukundeshwari Temple", "temples", "Tanahun", "Bandipur", 27.920, 84.360, "Temple of Tanahun."),
    ("Aakase Jharana", "waterfalls", "Tanahun", "Bhanu", 27.990, 84.350, "Sky waterfall of Tanahun."),
    # ================= NAWALPUR =================
    ("Gaindakot", "cities", "Nawalpur", "Gaindakot", 27.720, 84.410, "Town of Nawalpur on the Narayani river."),
    ("Hupsekot Waterfall", "waterfalls", "Nawalpur", "Hupsekot", 27.680, 84.100, "Waterfall of Hupsekot, Nawalpur."),
    ("Hupsekot Hill", "viewpoints", "Nawalpur", "Hupsekot", 27.690, 84.120, "Hill viewpoint of Hupsekot, Nawalpur."),
    ("CG Shashwat Dham", "temples", "Nawalpur", "Kawasoti", 27.600, 84.050, "Temple complex of Nawalpur."),
]

# name fixes for existing rows
NAME_FIXES = {
    4800: "Seti River Gorge",  # was "Seti River George"
}


def main():
    created = 0
    skipped = 0
    for name, cslug, dist, city, lat, lon, short in PLACES:
        aliases = DISTRICT_ALIASES.get(dist, {dist})
        existing = Destination.objects.filter(name__iexact=name).filter(
            district__in=list(aliases) + [None]
        )
        if existing.exists():
            skipped += 1
            continue
        base = (
            name.lower()
            .replace(" ", "-")
            .replace("(", "")
            .replace(")", "")
            .replace(",", "")
            .replace("'", "")
            .replace("/", "-")
            .replace("&", "and")
            .replace("\u2013", "-")
            .replace("\u0101", "a")
        )
        slug = base
        if Destination.objects.filter(slug=slug).exists():
            slug = f"{base}-{dist.lower()}"
            if Destination.objects.filter(slug=slug).exists():
                slug = f"{base}-{dist.lower()}-2"
        cat = cats.get(cslug) or cats.get("attraction")
        Destination.objects.create(
            name=name, slug=slug, category=cat, district=dist,
            province=PROVINCE_BY_DISTRICT[dist], city=city, city_english=city,
            latitude=lat, longitude=lon, short_description=short,
            description=short, country="Nepal", status="approved",
            is_active=True, source="round21-lumbini-gandaki", views_count=0,
        )
        created += 1

    for did, newname in NAME_FIXES.items():
        d = Destination.objects.filter(id=did).first()
        if d:
            d.name = newname
            d.save(update_fields=["name"])
            print(f"renamed {did} -> {newname}")

    print(f"created: {created} | skipped (already exist): {skipped}")


if __name__ == "__main__":
    main()
