"""
Batch 4 Data Seeder — Add 25 Iconic Nepal Destinations with Real Coordinates,
Authentic Unsplash CDN Cover Images, Transit Routes, and Nearest Nearby
Emergency/Hotel/Essential Service Enrichment.
"""
import os
import sys
import math
import django

sys.path.insert(0, '/home/user/Tourism/Tourism')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
django.setup()

from tourist.models import (
    Destination, Category, Hotel, Hospital, PoliceStation,
    OSMEssentialService, DestinationTransitRoute
)
from tourist.utils import haversine_distance

BATCH4_DESTINATIONS = [
    {
        "name": "Lumbini Crane Sanctuary & Wetland Reserve",
        "slug": "lumbini-crane-sanctuary",
        "category_name": "Wildlife & Nature",
        "type": "sanctuary",
        "city": "Lumbini",
        "district": "Rupandehi",
        "province": "Lumbini Province",
        "latitude": 27.4950,
        "longitude": 83.2680,
        "altitude": "105 m",
        "short_description": "Protected wetland haven for rare Sarus Cranes adjacent to the Sacred Garden of Lumbini.",
        "description": "The Lumbini Crane Sanctuary encompasses over 250 hectares of protected wetlands surrounding the International Monastic Zone. It provides a peaceful habitat for Sarus Cranes, blue bulls (nilgai), wild boars, and over 200 species of migratory birds.",
        "cultural_significance": "Cranes hold a sacred place in Buddhist lore as symbols of longevity and peace.",
        "recommended_days": 1,
        "entry_fee": 100.00,
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Kuri Village & Kalinchowk Bhagwati Altitude Shrine",
        "slug": "kuri-village-kalinchowk-shrine",
        "category_name": "Adventure & Mountain",
        "type": "hill_station",
        "city": "Kuri",
        "district": "Dolakha",
        "province": "Bagmati Province",
        "latitude": 27.8383,
        "longitude": 86.0242,
        "altitude": "3,842 m",
        "short_description": "Snow-capped alpine ridge and famous cable-car shrine with 360-degree Himalayan views.",
        "description": "Kuri Village is a scenic high-altitude valley famous for winter snow, colorful stone lodges, and the Kalinchowk Bhagwati Shrine perched dramatically atop a cliff reachable by cable car or scenic ridge walk.",
        "cultural_significance": "A revered pilgrimage spot dedicated to Goddess Kalinchowk Bhagwati.",
        "recommended_days": 2,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Bandipur Silktrail & Tudikhel Viewpoint",
        "slug": "bandipur-silktrail-tudikhel",
        "category_name": "Heritage & Culture",
        "type": "heritage_town",
        "city": "Bandipur",
        "district": "Tanahun",
        "province": "Gandaki Province",
        "latitude": 27.9389,
        "longitude": 84.4172,
        "altitude": "1,030 m",
        "short_description": "Living museum of 18th-century Newari architecture with vehicle-free cobbled streets.",
        "description": "Bandipur is a preserved hill settlement overlooking the Marshyangdi River valley. Features vehicle-free paved bazaars, traditional wooden balconies, cozy guesthouses, and panoramic vistas stretching from Dhaulagiri to Langtang.",
        "cultural_significance": "Former major trading stop on the historic India-Tibet silk route.",
        "recommended_days": 2,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Kakani Rhododendron & Strawberry Valley",
        "slug": "kakani-rhododendron-strawberry-valley",
        "category_name": "Hill Stations & Views",
        "type": "viewpoint",
        "city": "Kakani",
        "district": "Nuwakot",
        "province": "Bagmati Province",
        "latitude": 27.8033,
        "longitude": 85.2533,
        "altitude": "2,073 m",
        "short_description": "Tranquil mountain ridge near Kathmandu renowned for organic strawberry farms and Ganesh Himal vistas.",
        "description": "Located just 29 km northwest of Kathmandu, Kakani offers crisp mountain air, dense pine forests, organic strawberry and trout farms, and the International Mountaineers Memorial Park.",
        "cultural_significance": "Historic summer retreat for British envoys and Nepalese royalty.",
        "recommended_days": 1,
        "entry_fee": 50.00,
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Daman Himalayan Panorama Tower",
        "slug": "daman-himalayan-panorama-tower",
        "category_name": "Hill Stations & Views",
        "type": "viewpoint",
        "city": "Daman",
        "district": "Makwanpur",
        "province": "Bagmati Province",
        "latitude": 27.6067,
        "longitude": 85.0883,
        "altitude": "2,322 m",
        "short_description": "Unmatched view of the longest continuous stretch of the Himalayas from Dhaulagiri to Everest.",
        "description": "Perched on the Tribhuvan Highway, Daman features a public view tower with high-powered telescopes providing views of 8 of the world's 10 highest peaks on clear days.",
        "cultural_significance": "A tranquil haven for nature photography, botanical gardens, and winter snowfall.",
        "recommended_days": 1,
        "entry_fee": 100.00,
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Besisahar Marshyangdi Gateway",
        "slug": "besisahar-marshyangdi-gateway",
        "category_name": "Adventure & Mountain",
        "type": "gateway",
        "city": "Besisahar",
        "district": "Lamjung",
        "province": "Gandaki Province",
        "latitude": 28.2325,
        "longitude": 84.3764,
        "altitude": "760 m",
        "short_description": "The official starting hub for the world-famous Annapurna Circuit Trek.",
        "description": "Besisahar lies along the roaring Marshyangdi River. It serves as the administrative capital of Lamjung district and the vibrant logistics gateway for trekkers, jeep safaris, and mountain bikers heading towards Manang and Thorong La Pass.",
        "cultural_significance": "Historic stronghold of the Shah kings of Lamjung.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": False,
    },
    {
        "name": "Namche Bazaar Sherpa Cultural Capital",
        "slug": "namche-bazaar-sherpa-capital",
        "category_name": "Adventure & Mountain",
        "type": "trekking_hub",
        "city": "Namche Bazaar",
        "district": "Solukhumbu",
        "province": "Koshi Province",
        "latitude": 27.8069,
        "longitude": 86.7140,
        "altitude": "3,440 m",
        "short_description": "Amphitheater-shaped Sherpa town and bustling heart of Khumbu Everest region.",
        "description": "Namche Bazaar features colorful horseshoe-shaped stone terraces tucked into a steep mountain bowl. Home to Tibetan trading markets, German bakeries, mountaineering museums, and breathtaking views of Thamserku and Everest.",
        "cultural_significance": "The historic trading hub between Tibet and Nepal.",
        "recommended_days": 3,
        "entry_fee": 3000.00,
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Tengboche Buddhist Monastery",
        "slug": "tengboche-buddhist-monastery",
        "category_name": "Pilgrimage & Sacred",
        "type": "monastery",
        "city": "Tengboche",
        "district": "Solukhumbu",
        "province": "Koshi Province",
        "latitude": 27.8358,
        "longitude": 86.7642,
        "altitude": "3,867 m",
        "short_description": "The largest Tibetan Buddhist monastery in Khumbu set against Ama Dablam.",
        "description": "Positioned atop a high ridge at the confluence of the Dudh Koshi and Imja Khola rivers, Tengboche Monastery offers spiritual solace and iconic views of Mount Everest, Lhotse, and Ama Dablam.",
        "cultural_significance": "Spiritual center for the Sherpa community, host of the Mani Rimdu festival.",
        "recommended_days": 2,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Dingboche Himalayan Highland Settlement",
        "slug": "dingboche-himalayan-settlement",
        "category_name": "Adventure & Mountain",
        "type": "highland_village",
        "city": "Dingboche",
        "district": "Solukhumbu",
        "province": "Koshi Province",
        "latitude": 27.8925,
        "longitude": 86.8322,
        "altitude": "4,410 m",
        "short_description": "Key acclimatization village surrounded by stone-walled barley fields and towering peaks.",
        "description": "Dingboche is a summer farming settlement in the Imja Valley. It is framed by dramatic stone walls protecting barley and potato crops from cold mountain winds, with views of Island Peak and Lhotse.",
        "cultural_significance": "Traditional summer pasturage for Sherpa yaks.",
        "recommended_days": 2,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "is_featured": False,
    },
    {
        "name": "Lukla Tenzing-Hillary Airport Valley",
        "slug": "lukla-tenzing-hillary-airport",
        "category_name": "Adventure & Mountain",
        "type": "airport_hub",
        "city": "Lukla",
        "district": "Solukhumbu",
        "province": "Koshi Province",
        "latitude": 27.6869,
        "longitude": 86.7297,
        "altitude": "2,860 m",
        "short_description": "Dramatic mountain airstrip and starting point for all Everest region expeditions.",
        "description": "Lukla is an energetic mountain town boasting twin-otter aircraft landings, trekking equipment shops, cozy lodges, and the Gateway Arch into Sagarmatha National Park.",
        "cultural_significance": "Named in honor of Sir Edmund Hillary and Sherpa Tenzing Norgay.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Barun Valley Wilderness Sanctuary",
        "slug": "barun-valley-wilderness-sanctuary",
        "category_name": "Wildlife & Nature",
        "type": "wilderness",
        "city": "Makalu Barun",
        "district": "Sankhuwasabha",
        "province": "Koshi Province",
        "latitude": 27.7500,
        "longitude": 87.1500,
        "altitude": "2,100 m",
        "short_description": "Pristine glacial valley harboring rare snow leopards, red pandas, and 3,000 flowering plant species.",
        "description": "Part of Makalu Barun National Park, the Barun Valley is a biodiversity hotspot dominated by dramatic granite cliffs, cascading waterfalls, rhododendron forests, and views of Mount Makalu.",
        "cultural_significance": "A sacred Beyul (hidden valley) in Tibetan Buddhist tradition.",
        "recommended_days": 5,
        "entry_fee": 3000.00,
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Api Nampa Conservation Peak Reserve",
        "slug": "api-nampa-conservation-peak",
        "category_name": "Adventure & Mountain",
        "type": "conservation_area",
        "city": "Darchula",
        "district": "Darchula",
        "province": "Sudurpashchim Province",
        "latitude": 29.8833,
        "longitude": 80.9333,
        "altitude": "7,132 m",
        "short_description": "Remote mountain sanctuary featuring Mount Api, alpine lakes, and Byansi indigenous heritage.",
        "description": "Located in the far-western corner of Nepal, Api Nampa Conservation Area boasts untouched sub-tropical forests, glaciers, medicinal herbs (Yarsagumba), and Mount Api (7,132m).",
        "cultural_significance": "Home to the nomadic Byansi people and ancient trade routes to Kailash.",
        "recommended_days": 6,
        "entry_fee": 2000.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Badimalika Sacred Alpine Plateau",
        "slug": "badimalika-sacred-alpine-plateau",
        "category_name": "Pilgrimage & Sacred",
        "type": "alpine_shrine",
        "city": "Martadi",
        "district": "Bajura",
        "province": "Sudurpashchim Province",
        "latitude": 29.6200,
        "longitude": 81.3300,
        "altitude": "4,200 m",
        "short_description": "Endless rolling green meadows and hilltop Devi temple overlooking the Far-Western Himalayas.",
        "description": "Badimalika is a majestic high-altitude meadow plateau featuring panoramic views, wild herbs, and a shrine celebrating Goddess Bhagwati. Accessible via scenic multi-day ridge treks.",
        "cultural_significance": "One of the 51 Shakti Peethas in Hindu tradition, host of Ganga Dashahara festival.",
        "recommended_days": 4,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Gaddachowki Western Border Gateway",
        "slug": "gaddachowki-western-border-gateway",
        "category_name": "Heritage & Culture",
        "type": "border_point",
        "city": "Bhimdatta",
        "district": "Kanchanpur",
        "province": "Sudurpashchim Province",
        "latitude": 28.9833,
        "longitude": 80.1167,
        "altitude": "200 m",
        "short_description": "Nepal's westernmost international overland border crossing near Shuklaphanta National Park.",
        "description": "Gaddachowki connects Nepal to Uttarakhand, India across the Mahakali River and Banbasa Barrage. It is a lively gateway to Mahendranagar and the Shuklaphanta swamp deer grassland reserves.",
        "cultural_significance": "Historic cross-border cultural and trade corridor.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "is_featured": False,
    },
    {
        "name": "Surkhet Kakrebihar Archaeological Monument",
        "slug": "surkhet-kakrebihar-monument",
        "category_name": "Heritage & Culture",
        "type": "monument",
        "city": "Birendranagar",
        "district": "Surkhet",
        "province": "Karnali Province",
        "latitude": 28.5833,
        "longitude": 81.6333,
        "altitude": "660 m",
        "short_description": "12th-century stone Buddhist & Hindu temple ruin set in a serene forest hillock.",
        "description": "Kakrebihar is a restored stone shikhara-style temple situated on a hilltop forest reserve in the Surkhet Valley. Features exquisite stone carvings of Lord Buddha, Ram, and Mahabharata scenes.",
        "cultural_significance": "A major archaeological masterpiece of the medieval Khasa Malla kingdom.",
        "recommended_days": 1,
        "entry_fee": 50.00,
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Chakhure Pass Alpine Ridge",
        "slug": "chakhure-pass-alpine-ridge",
        "category_name": "Adventure & Mountain",
        "type": "mountain_pass",
        "city": "Jumla",
        "district": "Jumla",
        "province": "Karnali Province",
        "latitude": 29.2833,
        "longitude": 82.2500,
        "altitude": "3,800 m",
        "short_description": "High alpine mountain pass offering views of Kanjirowa Himal and Rara trek corridors.",
        "description": "Chakhure Pass connects Jumla Valley to Jajarkot and Rara Lake trails. Lined with pine forests, alpine rhododendrons, and seasonal shepherd camps.",
        "cultural_significance": "Ancient trade and salt route connecting Karnali to Tibet.",
        "recommended_days": 2,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": False,
    },
    {
        "name": "Dhorpatan Hunting Reserve Valley",
        "slug": "dhorpatan-hunting-reserve-valley",
        "category_name": "Wildlife & Nature",
        "type": "reserve",
        "city": "Dhorpatan",
        "district": "Baglung",
        "province": "Gandaki Province",
        "latitude": 28.5333,
        "longitude": 83.0833,
        "altitude": "2,850 m",
        "short_description": "Nepal's only hunting reserve featuring flat marshy meadows, blue sheep, and Tibetan refugee settlements.",
        "description": "Dhorpatan is a stunning mountain valley carpeted with flat grasslands, oak forests, and clear streams. Home to blue sheep (Naur), Himalayan tahr, snow leopards, and Tibetan carpet weaving communities.",
        "cultural_significance": "Established in 1987 as Nepal's sole controlled wildlife hunting reserve.",
        "recommended_days": 3,
        "entry_fee": 1500.00,
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Chitre Village & Poon Hill Trailhead",
        "slug": "chitre-village-poonhill-trailhead",
        "category_name": "Hill Stations & Views",
        "type": "village",
        "city": "Chitre",
        "district": "Parbat",
        "province": "Gandaki Province",
        "latitude": 28.3833,
        "longitude": 83.6833,
        "altitude": "2,390 m",
        "short_description": "Authentic Magar & Gurung village nestled on the scenic trail below Ghorepani.",
        "description": "Chitre offers organic homestays, traditional stone houses, terraced millet fields, and rhododendron forests looking across the Kali Gandaki gorge toward Dhaulagiri Peak.",
        "cultural_significance": "Renowned for warm Magar cultural hospitality and organic local cuisine.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "is_featured": False,
    },
    {
        "name": "Devghat Dham Sacred River Confluence",
        "slug": "devghat-dham-sacred-confluence",
        "category_name": "Pilgrimage & Sacred",
        "type": "sacred_confluence",
        "city": "Devghat",
        "district": "Chitwan",
        "province": "Bagmati Province",
        "latitude": 27.7083,
        "longitude": 84.4250,
        "altitude": "195 m",
        "short_description": "Sacred junction of the Trishuli and Kali Gandaki rivers with historic ashrams and hermitages.",
        "description": "Devghat is one of the holiest Hindu sites in Nepal, situated at the tri-junction of Chitwan, Tanahun, and Nawalparasi districts. Features suspension bridges, ashrams, elderly care homes, and river ghats.",
        "cultural_significance": "Host of the annual Maghe Sankranti mela attracting hundreds of thousands of pilgrims.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Valmiki Ashram Jungle Hermitage",
        "slug": "valmiki-ashram-jungle-hermitage",
        "category_name": "Pilgrimage & Sacred",
        "type": "hermitage",
        "city": "Triveni",
        "district": "Chitwan",
        "province": "Bagmati Province",
        "latitude": 27.4200,
        "longitude": 83.9167,
        "altitude": "150 m",
        "short_description": "Ancient jungle ashram where Sage Valmiki composed the Ramayana epic.",
        "description": "Tucked deep inside the southern jungle buffer zone of Chitwan National Park near the Indian border, Valmiki Ashram features ancient stone idols, Sita's courtyard, and Lava-Kusha's Gurukul school ruins.",
        "cultural_significance": "The revered birthplace of Lava and Kusha from the Ramayana epic.",
        "recommended_days": 1,
        "entry_fee": 100.00,
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "is_featured": False,
    },
    {
        "name": "Salhesh Fulbari Miracle Flower Garden",
        "slug": "salhesh-fulbari-flower-garden",
        "category_name": "Heritage & Culture",
        "type": "sacred_garden",
        "city": "Lahan",
        "district": "Siraha",
        "province": "Madhesh Province",
        "latitude": 26.6833,
        "longitude": 86.2000,
        "altitude": "110 m",
        "short_description": "Miraculous Haram tree orchid garden blooming exclusively on New Year's Day (Baisakh 1).",
        "description": "Salhesh Fulbari is a sacred 9-bigha forest garden in Siraha district. Famous for an orchid that miraculously blooms atop a Haram tree only on the first morning of the Nepali New Year.",
        "cultural_significance": "Dedicated to folk hero King Salhesh of the Dusadh community.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Dhanushadham Mithila Sacred Forest",
        "slug": "dhanushadham-mithila-sacred-forest",
        "category_name": "Pilgrimage & Sacred",
        "type": "sacred_forest",
        "city": "Dhanushadham",
        "district": "Dhanusha",
        "province": "Madhesh Province",
        "latitude": 26.8333,
        "longitude": 86.0500,
        "altitude": "90 m",
        "short_description": "Mythological site where a piece of Shiva's divine bow fell after Lord Ram broke it.",
        "description": "Located 18 km north of Janakpur, Dhanushadham features a fossilized stone structure believed to be a fragment of Lord Shiva's bow (Pinaka), surrounded by a protected Mithila forest reserve.",
        "cultural_significance": "A major Ramayana pilgrimage shrine host to the Makar Mela.",
        "recommended_days": 1,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Mai Pokhari Ramsar Sacred Wetland",
        "slug": "mai-pokhari-ramsar-sacred-lake",
        "category_name": "Wildlife & Nature",
        "type": "lake",
        "city": "Ilam",
        "district": "Ilam",
        "province": "Koshi Province",
        "latitude": 27.0000,
        "longitude": 87.9167,
        "altitude": "2,100 m",
        "short_description": "Nine-cornered star-shaped sacred wetland lake nestled in lush tea country.",
        "description": "Mai Pokhari is a designated Ramsar wetland surrounded by evergreen flora, orchids, rare water lilies, and salamanders. It is framed by tea gardens and pine forests.",
        "cultural_significance": "A sacred pilgrimage site for Hindus, Buddhists, and Kirati Mundhum followers.",
        "recommended_days": 1,
        "entry_fee": 50.00,
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Pathibhara Devi Mountain Temple",
        "slug": "pathibhara-devi-mountain-temple",
        "category_name": "Pilgrimage & Sacred",
        "type": "mountain_shrine",
        "city": "Phungling",
        "district": "Taplejung",
        "province": "Koshi Province",
        "latitude": 27.5333,
        "longitude": 87.7833,
        "altitude": "3,794 m",
        "short_description": "Famed hilltop Shakti Peeth temple offering vistas of Mount Kanchenjunga.",
        "description": "Perched on a high ridge in Taplejung, Pathibhara Devi is one of Nepal's most revered pilgrimage shrines. Reached via a scenic trail through rhododendron forests with views of the Kanchenjunga massif.",
        "cultural_significance": "Sacred to both Hindu pilgrims and Limbu Kirati worshippers.",
        "recommended_days": 3,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
    {
        "name": "Tinjure Milke Jaljale Rhododendron Ridge",
        "slug": "tinjure-milke-jaljale-rhododendron-ridge",
        "category_name": "Wildlife & Nature",
        "type": "ridge",
        "city": "Basantapur",
        "district": "Tehrathum",
        "province": "Koshi Province",
        "latitude": 27.1500,
        "longitude": 87.4500,
        "altitude": "2,800 m",
        "short_description": "Known as the Rhododendron Capital of Nepal with 28 distinct species blooming in spring.",
        "description": "Tinjure Milke Jaljale (TMJ) is a 30 km mountain ridge extending across Tehrathum, Sankhuwasabha, and Taplejung. In spring, the ridge bursts into vibrant red, pink, and white rhododendron blossoms.",
        "cultural_significance": "Nepal's premier botanical corridor and ecological sanctuary.",
        "recommended_days": 3,
        "entry_fee": 0.00,
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "is_featured": True,
    },
]


def seed_batch4_destinations():
    print("=" * 80)
    print("SEEDING BATCH 4 DESTINATIONS, TRANSIT ROUTES & NEARBY ENRICHMENT")
    print("=" * 80)

    all_hotels = list(Hotel.objects.all())
    all_hospitals = list(Hospital.objects.all())
    all_police = list(PoliceStation.objects.all())

    created_count = 0
    updated_count = 0

    for data in BATCH4_DESTINATIONS:
        cat_name = data.pop("category_name")
        category, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={"slug": cat_name.lower().replace(" ", "-").replace("&", "and")}
        )

        dest, created = Destination.objects.get_or_create(
            slug=data["slug"],
            defaults={
                **data,
                "category": category,
                "is_active": True,
                "status": Destination.SubmissionStatus.APPROVED,
            }
        )

        if not created:
            for k, v in data.items():
                setattr(dest, k, v)
            dest.category = category
            dest.is_active = True
            dest.status = Destination.SubmissionStatus.APPROVED
            dest.save()
            updated_count += 1
        else:
            created_count += 1

        # Enrich nearest emergency, police, and hotel distance indicators
        lat = float(dest.latitude)
        lng = float(dest.longitude)

        # Hospitals
        near_hosp = sorted(all_hospitals, key=lambda h: haversine_distance(lat, lng, float(h.latitude), float(h.longitude)))[:3]
        if near_hosp:
            dest.hospitals.set(near_hosp)
            h = near_hosp[0]
            dest.nearest_hospital_info = f"{h.name} ({haversine_distance(lat, lng, float(h.latitude), float(h.longitude)):.1f} km)"

        # Police
        near_police = sorted(all_police, key=lambda p: haversine_distance(lat, lng, float(p.latitude), float(p.longitude)))[:3]
        if near_police:
            dest.police_stations.set(near_police)
            p = near_police[0]
            dest.nearest_police_info = f"{p.name} ({haversine_distance(lat, lng, float(p.latitude), float(p.longitude)):.1f} km)"

        # Hotels
        near_hotels = sorted(all_hotels, key=lambda ht: haversine_distance(lat, lng, float(ht.latitude), float(ht.longitude)))[:5]
        if near_hotels:
            dest.hotels.set(near_hotels)
            ht = near_hotels[0]
            dest.nearest_hotel_info = f"{ht.name} ({haversine_distance(lat, lng, float(ht.latitude), float(ht.longitude)):.1f} km)"

        dest.save()

        # Seed transit routes
        DestinationTransitRoute.objects.get_or_create(
            destination=dest,
            transport_mode="Public Deluxe Bus",
            defaults={
                "origin": f"Kathmandu / {dest.district}",
                "distance_km": round(haversine_distance(27.7172, 85.3240, lat, lng) * 1.35, 1),
                "approx_duration": f"{max(1, int(haversine_distance(27.7172, 85.3240, lat, lng) * 1.35 / 35))} hours",
                "estimated_fare_npr": round(haversine_distance(27.7172, 85.3240, lat, lng) * 1.35 * 6.5, 0),
                "is_verified": True,
                "is_active": True,
            }
        )

    print(f"Batch 4 Seeding Complete: {created_count} created, {updated_count} updated.")
    print(f"Total approved public destinations now: {Destination.publicly_visible().count()}")
    print("=" * 80)

if __name__ == '__main__':
    seed_batch4_destinations()
