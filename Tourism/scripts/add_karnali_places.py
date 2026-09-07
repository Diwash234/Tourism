"""Round 18: Add Karnali Province famous named places (Surkhet, Dailekh,
Jajarkot, Salyan, Rukum West, Kalikot, Jumla, Mugu, Dolpa, Humla) from the
ward-by-ward district data as real destinations with categories + coordinates.
Skips existing (name + district alias), disambiguates slug collisions.
Also deletes the duplicate 'Waterfall at Pachal' wrongly tagged Jajarkot
(the canonical Pachaljharana Waterfall is in Kalikot).
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, DestinationImage, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

DISTRICT_ALIASES = {
    "Surkhet": {"Surkhet", "सुर्खेत", "सुर्खेत जिल्ला", "Surkhet District"},
    "Dailekh": {"Dailekh", "दैलेख", "दैलेख जिल्ला", "Dailekh District"},
    "Jajarkot": {"Jajarkot", "जाजरकोट", "जाजरकोट जिल्ला", "Jajarkot District"},
    "Salyan": {"Salyan", "सल्यान", "सल्यान जिल्ला", "Salyan District"},
    "Rukum West": {"Rukum West", "रुकुम पश्चिम", "रुकुम पश्चिम जिल्ला", "Rukum West District"},
    "Kalikot": {"Kalikot", "कालिकोट", "कालिकोट जिल्ला", "Kalikot District"},
    "Jumla": {"Jumla", "जुम्ला", "जुम्ला जिल्ला", "Jumla District"},
    "Mugu": {"Mugu", "मुगु", "मुगु जिल्ला", "Mugu District"},
    "Dolpa": {"Dolpa", "Dolpo", "डोल्पा", "डोल्पा जिल्ला", "Dolpa District"},
    "Humla": {"Humla", "हुम्ला", "हुम्ला जिल्ला", "Humla District"},
}

# (name, category_slug, district, city, lat, lon, short_description)
PLACES = [
    # ================= SURKHET =================
    ("Kakrebihar", "heritage", "Surkhet", "Birendranagar", 28.620, 81.620, "12th-century Buddhist-Hindu archaeological complex in the Sal forest north of Birendranagar."),
    ("Bulbule Lake", "lakes", "Surkhet", "Birendranagar", 28.598, 81.628, "Recreation lake of Birendranagar, a popular picnic and walking destination."),
    ("Deuti Bajai Temple", "temples", "Surkhet", "Birendranagar", 28.595, 81.620, "One of western Nepal's important goddess temples, at Birendranagar."),
    ("Ghantaghar Birendranagar", "heritage", "Surkhet", "Birendranagar", 28.600, 81.630, "Clock-tower landmark of Birendranagar."),
    ("Province Museum Surkhet", "museums", "Surkhet", "Birendranagar", 28.597, 81.627, "Province Museum and Archives of Karnali Province at Birendranagar."),
    ("Sahid Park Birendranagar", "parks-gardens", "Surkhet", "Birendranagar", 28.599, 81.632, "Martyrs' memorial park of Birendranagar."),
    ("Latikoili Shiva Temple", "temples", "Surkhet", "Birendranagar", 28.545, 81.640, "Shiva temple of Latikoili, listed among Birendranagar's destinations."),
    ("Mangalgadhi", "heritage", "Surkhet", "Birendranagar", 28.560, 81.650, "Historic fort site of the Surkhet valley."),
    ("Bayalkanda Gadhi", "heritage", "Surkhet", "Birendranagar", 28.540, 81.600, "Historic hill fort near Birendranagar."),
    ("Chamere Gufa Panchapuri", "caves", "Surkhet", "Panchapuri", 28.680, 81.550, "Bat cave of Panchapuri municipality."),
    ("Baraha Tal", "lakes", "Surkhet", "Barahatal", 28.750, 81.680, "Largest lake of Surkhet district, surrounded by forest with bird and wildlife habitat."),
    ("Jajura Daha", "lakes", "Surkhet", "Panchapuri", 28.720, 81.580, "Natural lake at about 1,000 m with the Siddheshwor temple and nearby caves."),
    ("Panchatale Gufa", "caves", "Surkhet", "Panchapuri", 28.710, 81.570, "Five-storey cave of Panchapuri, an adventure and community-tourism site."),
    ("Kundilini Gufa", "caves", "Surkhet", "Panchapuri", 28.690, 81.560, "Cave tourism site of Salikot, Panchapuri."),
    ("Chhapre Lekha", "forests", "Surkhet", "Panchapuri", 28.740, 81.540, "Forest hill of Chhapre, Panchapuri with trekking, camping and birdwatching potential."),
    ("Raji Museum", "museums", "Surkhet", "Panchapuri", 28.700, 81.600, "Museum of Raji culture and heritage at Bidyapur, Panchapuri."),
    ("Bheri-Karnali Confluence", "rivers", "Surkhet", "Panchapuri", 28.660, 81.480, "Confluence of the Bheri and Karnali rivers at the western edge of Surkhet."),
    ("Malarani Gufa", "caves", "Surkhet", "Gurbhakot", 28.480, 81.520, "Cave of Gurbhakot with religious significance."),
    ("Khatang", "viewpoints", "Surkhet", "Gurbhakot", 28.450, 81.550, "Hill and temple viewpoint of Gurbhakot."),
    ("Gumi Chuli", "mountains", "Surkhet", "Gurbhakot", 28.430, 81.530, "Peak of Gurbhakot municipality."),
    ("Ramrikanda Daha", "lakes", "Surkhet", "Gurbhakot", 28.470, 81.540, "Lake of Gurbhakot municipality."),
    ("Dhage Chari Jharana", "waterfalls", "Surkhet", "Gurbhakot", 28.460, 81.560, "Waterfall of Gurbhakot municipality."),
    ("Bhote Chuli", "mountains", "Surkhet", "Gurbhakot", 28.440, 81.510, "Peak of Gurbhakot municipality."),
    ("Buruse Jharana", "waterfalls", "Surkhet", "Chingad", 28.340, 81.690, "Waterfall of the Buruse forest, Chingad."),
    ("Buruse Forest", "forests", "Surkhet", "Chingad", 28.350, 81.700, "Forest of Chingad with trekking and nature-tourism potential."),
    ("Malika Than Chingad", "pilgrimage", "Surkhet", "Chingad", 28.330, 81.680, "Sacred site of Chingad rural municipality."),
    ("Barahdanda Bheriganga", "viewpoints", "Surkhet", "Bheriganga", 28.500, 81.450, "Religious hill viewpoint of Bheriganga Ward 10."),
    ("Chhinchu Bazaar", "cities", "Surkhet", "Bheriganga", 28.470, 81.470, "Market town of Bheriganga with the Durga and Shiva temples."),
    ("Sattale Gufa Lekbeshi", "caves", "Surkhet", "Lekbeshi", 28.650, 81.400, "Cave of Lekbeshi municipality."),
    ("Bhotedarbar", "heritage", "Surkhet", "Lekbeshi", 28.680, 81.380, "Historic palace site of Lekbeshi."),
    ("Kotko Thumko", "heritage", "Surkhet", "Simta", 28.800, 81.520, "Hilltop fort of Simta, listed in the Karnali tourism master plan."),
    ("Koteshwar Temple Simta", "temples", "Surkhet", "Simta", 28.790, 81.510, "Shiva temple of Simta rural municipality."),
    ("Ranipakha Cave", "caves", "Surkhet", "Simta", 28.810, 81.530, "Cave of Simta rural municipality."),
    ("Rajkanda Darbar", "heritage", "Surkhet", "Simta", 28.785, 81.515, "Historic darbar area of Simta."),
    ("Lapu Village", "villages", "Surkhet", "Simta", 28.795, 81.505, "Village of Simta identified as the birthplace of Deuti Bajai."),
    # ================= DAILEKH =================
    ("Panchakoshi Dham", "pilgrimage", "Dailekh", "Dullu", 28.850, 81.700, "Sacred circuit of five Shiva shrines of Dullu: Shirshan, Nabhisthan, Dhuleshwar, Paduka and Siddheshwar."),
    ("Nabhisthan", "pilgrimage", "Dailekh", "Dullu", 28.840, 81.700, "One of the five Panchakoshi shrines of Dullu, near the natural flames."),
    ("Dhuleshwar Mahadev", "temples", "Dailekh", "Dullu", 28.860, 81.710, "Shiva shrine of the Panchakoshi circuit, Dullu Ward 8."),
    ("Paduka Sthan", "pilgrimage", "Dailekh", "Dullu", 28.850, 81.720, "One of the five Panchakoshi shrines of Dullu."),
    ("Bhurti Temple Complex", "heritage", "Dailekh", "Narayan", 28.838, 81.709, "Complex of 22 deval temples near Dailekh Bazaar, on UNESCO's tentative list."),
    ("Kotgadhi", "heritage", "Dailekh", "Narayan", 28.850, 81.720, "Historic fort of Dailekh."),
    ("Kotila Dailekh", "heritage", "Dailekh", "Narayan", 28.860, 81.730, "Historic site of Narayan municipality."),
    ("Belaspur Temple", "temples", "Dailekh", "Narayan", 28.830, 81.720, "Temple of Narayan municipality."),
    ("Kritideval Dailekh", "heritage", "Dailekh", "Narayan", 28.840, 81.710, "Ancient deval group (Panchadeval) of Dailekh."),
    ("Bagmani", "temples", "Dailekh", "Narayan", 28.820, 81.700, "Religious site of Narayan municipality."),
    ("Raili Tripani", "pilgrimage", "Dailekh", "Narayan", 28.810, 81.690, "Triple-confluence pilgrimage site of Dailekh."),
    ("Pallo Kalimati Viewpoint", "viewpoints", "Dailekh", "Narayan", 28.870, 81.750, "Viewpoint of Narayan Ward 3 with 360-degree valley views."),
    ("Mahabu Lek", "mountains", "Dailekh", "Mahabu", 28.950, 81.850, "High ridge of Dailekh with rhododendron forest and wildlife observation."),
    ("Rani Jharana", "waterfalls", "Dailekh", "Naumule", 28.780, 81.800, "Waterfall of Naumule Ward 2."),
    ("Dwari Khola Waterfall", "waterfalls", "Dailekh", "Naumule", 28.770, 81.810, "Waterfall of Dwari, Naumule Ward 3."),
    ("Giddha Nuhane Tal", "lakes", "Dailekh", "Naumule", 28.790, 81.820, "Pond of Naumule where vultures bathe."),
    ("Nau Mul Naumule", "natural-wonders", "Dailekh", "Naumule", 28.780, 81.790, "Nine water sources of Naumule."),
    ("Chamere Gufa Naumule", "caves", "Dailekh", "Naumule", 28.760, 81.800, "Bat cave of Naumule Ward 3."),
    ("Basudhara Temple", "temples", "Dailekh", "Naumule", 28.800, 81.780, "Temple of Sallery, Naumule Ward 6."),
    ("Shivatal Naumule", "lakes", "Dailekh", "Naumule", 28.810, 81.770, "Shiva pond of Paiti, Naumule Ward 7."),
    ("Gauni Dobilla", "viewpoints", "Dailekh", "Bhairabi", 28.900, 81.600, "Tourism site of Bhairabi Ward 5."),
    ("Akhanda Jwala", "natural-wonders", "Dailekh", "Bhairabi", 28.880, 81.680, "Naturally burning gas flames of the Panchakoshi area, a unique geological-religious site."),
    ("Dungel Temple", "temples", "Dailekh", "Gurans", 28.750, 81.950, "Temple of Gurans Ward 2 with a traveller rest house."),
    ("Ranimatta Guranshe Trail", "scenic-routes", "Dailekh", "Gurans", 28.760, 81.930, "Rhododendron footpath and botanical-garden trail of Gurans Wards 4-5."),
    ("Kotafara", "viewpoints", "Dailekh", "Dungeshwor", 28.700, 81.650, "Tourist site of Dungeshwor Ward 4."),
    ("Chupra Confluence", "natural-wonders", "Dailekh", "Narayan", 28.800, 81.660, "Confluence of the Lohore and Chhamgad rivers, a scenic spot of Dailekh."),
    ("Dhaukhani Cave", "caves", "Dailekh", "Dullu", 28.870, 81.740, "Cave of the Dullu area."),
    ("Madantal Cave", "caves", "Dailekh", "Dullu", 28.860, 81.730, "Cave of the Dullu area."),
    ("Badapokhara Dullu", "lakes", "Dailekh", "Dullu", 28.840, 81.680, "Pond of Dullu Ward 2."),
    ("Tiyadi Temple", "temples", "Dailekh", "Dullu", 28.850, 81.690, "Temple of Dullu Ward 3."),
    # ================= JAJARKOT =================
    ("Jajarkot Durbar", "heritage", "Jajarkot", "Bheri", 28.747, 82.199, "Historic palace of the Jajarkot kingdom above the Bheri river."),
    ("Jagatipur Darbar", "heritage", "Jajarkot", "Bheri", 28.760, 82.210, "Ruins of the historic Jagatipur palace of Jajarkot."),
    ("Kalika Temple Jajarkot", "temples", "Jajarkot", "Bheri", 28.740, 82.190, "Goddess temple of Jajarkot."),
    ("Chyortens of Jajarkot", "buddhist-sites", "Jajarkot", "Bheri", 28.750, 82.200, "Group of thirteen historic chyortens of Jajarkot."),
    ("Kalegaun Shivalaya", "temples", "Jajarkot", "Bheri", 28.740, 82.200, "Shiva shrines of Kalegaun, Jajarkot."),
    ("Suyada Malika", "temples", "Jajarkot", "Chhedagad", 28.900, 82.050, "Goddess temple of Chhedagad municipality."),
    ("Chhatryal Deval", "heritage", "Jajarkot", "Chhedagad", 28.890, 82.040, "Historic deval monument of Chhedagad."),
    ("Gurshe Khola", "rivers", "Jajarkot", "Nalgad", 28.650, 82.100, "River of Nalgad selected for a climate-model eco-tourism village."),
    ("Kusemuse", "villages", "Jajarkot", "Kushe", 28.950, 82.300, "Highland area of Kushe proposed for integrated tourism development."),
    ("Barekot Heritage Trail", "trekking", "Jajarkot", "Barekot", 28.800, 82.400, "High-mountain circuit of Barekot named after its twelve historic kot fort-hills."),
    ("Shivalaya Jajarkot", "temples", "Jajarkot", "Shivalaya", 28.850, 82.250, "Religious landscape giving Shivalaya Rural Municipality its name."),
    # ================= SALYAN =================
    ("Kupinde Lake", "lakes", "Salyan", "Bangad Kupinde", 28.350, 82.100, "Flagship lake of Salyan surrounded by green forests and peaceful hills."),
    ("Chhayakshetra Temple", "temples", "Salyan", "Salyan", 28.320, 82.150, "Religious site of Salyan district."),
    ("Shankh Park", "parks-gardens", "Salyan", "Sharada", 28.378, 82.160, "Park of Salyan district."),
    # ================= RUKUM WEST =================
    ("Syarpu Lake", "lakes", "Rukum West", "Bafikot", 28.560, 82.440, "Flagship lake of West Rukum with clean water, forests and homestay tourism."),
    ("Chitripatan Lake", "lakes", "Rukum West", "Aathbiskot", 28.650, 82.550, "Lake of Aathbiskot Ward 4."),
    ("Sattale Cave", "caves", "Rukum West", "Aathbiskot", 28.680, 82.570, "Cave of Aathbiskot Ward 14."),
    ("Masta Mahankal Temple", "temples", "Rukum West", "Aathbiskot", 28.690, 82.560, "Masto temple of Aathbiskot Ward 14."),
    ("Thuli Bheri River", "rivers", "Rukum West", "Aathbiskot", 28.620, 82.520, "River of West Rukum famous for rafting and mountain scenery."),
    ("Chaurjahari Valley", "valleys", "Rukum West", "Chaurjahari", 28.540, 82.380, "Flat valley along the Bheri river surrounded by mountains."),
    # ================= KALIKOT =================
    ("Pachaljharana Waterfall", "waterfalls", "Kalikot", "Pachal Jharana", 29.220, 81.780, "About 381 m waterfall of Kalikot, one of Nepal's tallest waterfalls."),
    ("Manma", "cities", "Kalikot", "Khandachakra", 29.170, 81.620, "District headquarters town of Kalikot on the Karnali river."),
    ("Kot Durbar Kalikot", "heritage", "Kalikot", "Khandachakra", 29.180, 81.630, "Historic fort-palace of Manma."),
    ("Chuli Malika", "mountains", "Kalikot", "Khandachakra", 29.250, 81.600, "Mountain and goddess site of Kalikot."),
    ("Puja Malika", "mountains", "Kalikot", "Khandachakra", 29.260, 81.620, "Highland pilgrimage site of Kalikot."),
    ("Pancha Deval Kalikot", "heritage", "Kalikot", "Khandachakra", 29.190, 81.640, "Group of five ancient devals near Manma."),
    ("Tiseli Gufa", "caves", "Kalikot", "Tilagufa", 29.150, 81.750, "Cave of Tilagufa municipality."),
    ("Tila Gufa", "caves", "Kalikot", "Tilagufa", 29.140, 81.730, "Cave giving Tilagufa municipality its name."),
    ("Pili War Tourism Area", "heritage", "Kalikot", "Khandachakra", 29.220, 81.580, "Site of the 2017 Pili massacre, developed as a war-tourism destination with memorial and view tower."),
    ("Raskot Durbar", "heritage", "Kalikot", "Raskot", 29.050, 81.850, "Historic palace of Raskot."),
    ("Deura Malika", "temples", "Kalikot", "Raskot", 29.080, 81.880, "Goddess site of Raskot."),
    ("Thigelni Temple", "temples", "Kalikot", "Raskot", 29.060, 81.860, "Temple of Raskot municipality."),
    ("Dademasta Temple", "temples", "Kalikot", "Naraharinath", 29.000, 81.700, "Masto temple of Naraharinath Ward 8."),
    ("Bayal Jharna", "waterfalls", "Kalikot", "Pachal Jharana", 29.240, 81.800, "Waterfall of the Pachal Jharana area."),
    ("Yengeli Chour", "natural-wonders", "Kalikot", "Pachal Jharana", 29.260, 81.820, "Highland meadow of Pachal Jharana municipality."),
    ("Mastadevi Temple Kalikot", "temples", "Kalikot", "Shubha Kalika", 28.980, 81.600, "Goddess temple of Shubha Kalika Ward 5."),
    ("Mahawai Lekh", "mountains", "Kalikot", "Mahawai", 29.300, 81.900, "High ridge of Mahawai with rhododendron forest, red panda habitat and medicinal herbs."),
    ("Bobka Than", "temples", "Kalikot", "Palata", 29.120, 81.950, "Religious site of Palata Ward 1."),
    ("Triveni Jyuli", "pilgrimage", "Kalikot", "Sanni Triveni", 29.080, 81.550, "Religious site of Sanni Triveni Ward 5."),
    # ================= JUMLA =================
    ("Chandannath Temple", "temples", "Jumla", "Chandannath", 29.275, 82.184, "Historic Dattatraya temple of Khalanga, one of western Nepal's major pilgrimage sites."),
    ("Bhairavnath Temple Jumla", "temples", "Jumla", "Chandannath", 29.276, 82.183, "Bhairav temple of Khalanga, Jumla."),
    ("Duddul Stupa", "buddhist-sites", "Jumla", "Chandannath", 29.260, 82.200, "Buddhist stupa of Duddul, Chandannath."),
    ("Khalanga Jumla", "cities", "Jumla", "Chandannath", 29.275, 82.184, "District headquarters town of Jumla."),
    ("Birat Durbar", "heritage", "Jumla", "Sinja", 29.320, 82.100, "Historic palace site of the Khasa kingdom in the Sinja valley."),
    ("Sinjapati Durbar", "heritage", "Jumla", "Sinja", 29.315, 82.105, "Historic durbar of the Sinja valley."),
    ("Narakot", "heritage", "Jumla", "Sinja", 29.325, 82.095, "Historic fortified settlement and headquarters of Sinja Rural Municipality."),
    ("Kanakasundari Temple", "temples", "Jumla", "Kanakasundari", 29.350, 82.150, "Historic temple of the Kanakasundari area."),
    ("Tatopani Hot Spring Jumla", "hot-springs", "Jumla", "Tatopani", 29.200, 82.080, "Natural hot spring of the Tila river valley."),
    ("Guru Phokto", "pilgrimage", "Jumla", "Tatopani", 29.210, 82.070, "Religious site of Tatopani Ward 2."),
    ("Budbudi Dham", "pilgrimage", "Jumla", "Tatopani", 29.220, 82.090, "Religious site of Tatopani Ward 4."),
    ("Patarasi Peak", "mountains", "Jumla", "Patarasi", 29.440, 82.240, "High peak of Patarasi with trekking and alpine pasture."),
    ("Chhum Jyulo", "villages", "Jumla", "Patarasi", 29.420, 82.220, "Highland village famous for Marshi rice cultivation."),
    ("Guthichaur", "villages", "Jumla", "Guthichaur", 29.340, 82.270, "Highland village of Jumla known for pastures and sheep farming."),
    ("Chimra Malika", "temples", "Jumla", "Guthichaur", 29.360, 82.260, "Goddess site of Guthichaur Ward 4."),
    ("Akashe Taal", "lakes", "Jumla", "Guthichaur", 29.380, 82.250, "Sky lake of Guthichaur, a high-altitude pond."),
    ("Pandav Gufa", "caves", "Jumla", "Kanakasundari", 29.330, 82.140, "Cave associated with the Pandavas near the Sinja area."),
    ("Rupichhada Waterfall", "waterfalls", "Jumla", "Hima", 29.200, 82.020, "Waterfall of Hima Ward 3."),
    ("Kedarnath Temple Hima", "temples", "Jumla", "Hima", 29.190, 82.010, "Kedarnath temple of Hima Ward 1."),
    ("Pugjhulaina Malika", "temples", "Jumla", "Hima", 29.210, 82.030, "Goddess site of Hima Ward 2."),
    ("Tila River", "rivers", "Jumla", "Tila", 29.280, 82.080, "River of Jumla with valley, kayaking and fishing tourism potential."),
    ("Jumla Apple Country", "agriculture", "Jumla", "Chandannath", 29.280, 82.180, "High-altitude apple orchards of Jumla, Nepal's organic apple country."),
    # ================= MUGU =================
    ("Rara Lake", "lakes", "Mugu", "Chhayanath Rara", 29.530, 82.090, "Nepal's largest natural lake at about 2,990 m, a Ramsar wetland."),
    ("Rara National Park", "national-park", "Mugu", "Chhayanath Rara", 29.500, 82.100, "National park protecting the Rara lake ecosystem with red panda, musk deer and 200+ bird species."),
    ("Chuchemara Peak", "mountains", "Mugu", "Chhayanath Rara", 29.555, 82.050, "4,097 m peak south of Rara Lake with panoramic views."),
    ("Ruma Kand", "mountains", "Mugu", "Chhayanath Rara", 29.500, 82.050, "About 3,731 m peak around Rara Lake."),
    ("Malika Kand", "mountains", "Mugu", "Chhayanath Rara", 29.560, 82.120, "About 3,444 m peak around Rara Lake."),
    ("Chhayanath Dham", "temples", "Mugu", "Chhayanath Rara", 29.650, 82.050, "Major religious site of Mugu."),
    ("Danda Bhumya Temple", "temples", "Mugu", "Chhayanath Rara", 29.600, 82.000, "Temple of Chhayanath Rara Ward 1."),
    ("Bhadali Park", "parks-gardens", "Mugu", "Chhayanath Rara", 29.610, 82.010, "Park of Chhayanath Rara Ward 1."),
    ("Talcha Mahadev", "temples", "Mugu", "Chhayanath Rara", 29.510, 82.060, "Mahadev temple at Talcha, near the Rara airport."),
    ("Khesma Malika", "temples", "Mugu", "Khatyad", 29.450, 82.200, "Goddess site spanning Khatyad Wards 1-3."),
    ("Dolphi Copper Mine", "heritage", "Mugu", "Mugum Karmarong", 29.750, 82.400, "Historic copper mine of Dolphi village."),
    ("Mugu Karnali River", "rivers", "Mugu", "Mugum Karmarong", 29.700, 82.300, "High-Himalayan river of Mugu with rafting and kayaking potential."),
    ("Gamgadhi", "cities", "Mugu", "Chhayanath Rara", 29.545, 82.120, "District headquarters town of Mugu near Rara Lake."),
    # ================= DOLPA =================
    ("Phoksundo Lake", "lakes", "Dolpa", "Shey Phoksundo", 29.210, 82.950, "Y-shaped alpine lake of Shey Phoksundo National Park, among the world's deepest."),
    ("Shey Phoksundo National Park", "national-park", "Dolpa", "Shey Phoksundo", 29.250, 82.900, "Nepal's largest national park, protecting snow leopard, blue sheep and Upper Dolpo."),
    ("Ringmo Village", "villages", "Dolpa", "Shey Phoksundo", 29.200, 82.950, "Bon-culture village above Phoksundo Lake."),
    ("Shey Gompa", "buddhist-sites", "Dolpa", "Shey Phoksundo", 29.320, 82.850, "Ancient Buddhist monastery of the Shey valley."),
    ("Kanjiroba Himal", "mountains", "Dolpa", "Shey Phoksundo", 29.390, 82.540, "Mountain of the Kanjiroba range above Phoksundo."),
    ("Dho-Tarap", "villages", "Dolpa", "Dolpo Buddha", 29.140, 82.980, "Among the world's highest settlements, a Bon-Buddhist village of Upper Dolpo."),
    ("Chharka Village", "villages", "Dolpa", "Chharka Tangsong", 29.080, 83.150, "High-altitude village of the Chharka Tangsong area."),
    ("Tinje Valley", "valleys", "Dolpa", "Chharka Tangsong", 29.060, 83.100, "High valley of Upper Dolpo."),
    ("Saldang Village", "villages", "Dolpa", "Shey Phoksundo", 29.300, 82.930, "Traditional Dolpo village north of Shey."),
    ("Jagadulla Lake", "lakes", "Dolpa", "Jagadulla", 29.150, 83.150, "High-altitude lake of the Jagadulla plateau."),
    ("Rakshas Tal", "lakes", "Dolpa", "Jagadulla", 29.160, 83.160, "Lake of the Jagadulla plateau."),
    ("Suligad Waterfall", "waterfalls", "Dolpa", "Shey Phoksundo", 29.140, 82.900, "Waterfall on the Suligad river on the Phoksundo trail."),
    ("Tripura Sundari Temple Dolpa", "temples", "Dolpa", "Tripurasundari", 28.900, 82.850, "Hindu temple of Tripurakot, a major religious site of Dolpa."),
    ("Thuli Bheri River", "rivers", "Dolpa", "Thuli Bheri", 28.900, 82.800, "Major river of western Dolpa flowing past Dunai."),
    # ================= HUMLA =================
    ("Simikot", "cities", "Humla", "Simkot", 29.970, 81.820, "Gateway town and airport hub of Humla."),
    ("Limi Valley", "valleys", "Humla", "Namkha", 30.130, 81.620, "Remote trans-Himalayan valley of Namkha with Tibetan-influenced villages."),
    ("Halji Village", "villages", "Humla", "Namkha", 30.140, 81.610, "Ancient village of the Limi Valley with the Rinchenling monastery."),
    ("Rinchenling Monastery", "buddhist-sites", "Humla", "Namkha", 30.140, 81.608, "Ancient Buddhist monastery of Halji in the Limi Valley."),
    ("Til Village", "villages", "Humla", "Namkha", 30.125, 81.635, "Traditional village of the Limi Valley."),
    ("Jang Village", "villages", "Humla", "Namkha", 30.155, 81.595, "Traditional village of the Limi Valley."),
    ("Kharpunath Temple", "temples", "Humla", "Kharpunath", 29.850, 81.950, "Temple giving Kharpunath Rural Municipality its name."),
    ("Hilsa", "villages", "Humla", "Namkha", 30.060, 81.440, "Border settlement on the Karnali near Tibet, a gateway to the Kailash-Mansarovar pilgrimage."),
    ("Humla Karnali River", "rivers", "Humla", "Simkot", 29.950, 81.850, "Upper Karnali river flowing through Humla."),
    ("Raling Gompa", "buddhist-sites", "Humla", "Simkot", 30.000, 81.800, "Buddhist monastery of Simkot Ward 4."),
    ("Muchu", "villages", "Humla", "Namkha", 30.200, 81.550, "Highland area of upper Humla near the Tibetan border."),
]

# duplicates to remove (wrong-district copies of the same waterfall; the
# canonical Pachaljharana Waterfall entry is in Kalikot)
DELETE_IDS = [6463]


def main():
    created = 0
    skipped = 0
    fixed = 0
    for name, cslug, dist, city, lat, lon, short in PLACES:
        aliases = DISTRICT_ALIASES.get(dist, {dist})
        existing = Destination.objects.filter(name__iexact=name).filter(
            district__in=list(aliases) + [None]
        )
        if existing.exists():
            skipped += 1
            for d in existing:
                if not d.province:
                    d.province = "Karnali"
                    d.save(update_fields=["province"])
                    fixed += 1
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
            .replace("\u0100", "a")
        )
        slug = base
        if Destination.objects.filter(slug=slug).exists():
            slug = f"{base}-{dist.lower()}"
            if Destination.objects.filter(slug=slug).exists():
                slug = f"{base}-{dist.lower()}-2"
        cat = cats.get(cslug) or cats.get("attraction")
        Destination.objects.create(
            name=name, slug=slug, category=cat, district=dist,
            province="Karnali", city=city, city_english=city,
            latitude=lat, longitude=lon, short_description=short,
            description=short, country="Nepal", status="approved",
            is_active=True, source="round18-karnali", views_count=0,
        )
        created += 1

    for did in DELETE_IDS:
        d = Destination.objects.filter(id=did).first()
        if d:
            DestinationImage.objects.filter(destination=d).delete()
            d.delete()
            print(f"deleted duplicate: {did} {d.name}")

    print(f"created: {created} | skipped (already exist): {skipped} | provinces fixed: {fixed}")


if __name__ == "__main__":
    main()
