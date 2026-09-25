import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/home/user/Tourism/Tourism')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
django.setup()

from tourist.models import Destination, Category
from tourist.management.commands.seed_destination_transit_routes import Command as TransitCommand
from tourist.management.commands.enrich_destination_nearby_services import Command as EnrichCommand

NEW_DESTINATIONS = [
    {
        "name": "Panchase Peak & Sacred Lake",
        "slug": "panchase-peak-sacred-lake",
        "district": "Kaski",
        "province": "Gandaki Province",
        "category_name": "Trekking & Nature",
        "latitude": 28.2250,
        "longitude": 83.8050,
        "altitude": "2,500 m",
        "description": "Panchase Peak is a serene eco-trekking destination bordering Kaski, Parbat, and Syangja. Famous for its sacred Panchase Lake, ancient Shiva temple, bio-dense rhododendron forests, and panoramic views of Annapurna, Dhaulagiri, and Manaslu ranges.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Panchase Peak Eco Trek | Kaski, Nepal",
        "meta_description": "Trek through lush rhododendron forests to Panchase Lake with vistas of Annapurna and Dhaulagiri."
    },
    {
        "name": "Pathibhara Devi Temple",
        "slug": "pathibhara-devi-temple-taplejung",
        "district": "Taplejung",
        "province": "Koshi Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.4261,
        "longitude": 87.7719,
        "altitude": "3,794 m",
        "description": "Pathibhara Devi Temple is one of Nepal's most revered Shakti Peeths situated high in eastern Taplejung district. Pilgrims flock here to worship Goddess Pathibhara while enjoying sweeping views of Mount Kanchenjunga.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Pathibhara Devi Shrine | Taplejung, Nepal",
        "meta_description": "Holy Shakti Peeth in Taplejung offering divine blessings and Kanchenjunga mountain panoramas."
    },
    {
        "name": "Barahachhetra Temple Sanctuary",
        "slug": "barahachhetra-temple-sanctuary",
        "district": "Sunsari",
        "province": "Koshi Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 26.8394,
        "longitude": 87.1606,
        "altitude": "180 m",
        "description": "Barahachhetra is an ancient pilgrimage site situated at the confluence of the Koka and Saptakoshi rivers in Sunsari. It is dedicated to Lord Vishnu's Varaha (boar) avatar and mentioned in classical Puranas.",
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Barahachhetra Temple | Sunsari, Nepal",
        "meta_description": "Ancient sacred river confluence shrine dedicated to Varaha Avatar in eastern Nepal."
    },
    {
        "name": "Kalinchowk Bhagwati Temple",
        "slug": "kalinchowk-bhagwati-temple",
        "district": "Dolakha",
        "province": "Bagmati Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.8286,
        "longitude": 86.0275,
        "altitude": "3,842 m",
        "description": "Kalinchowk Bhagwati Temple sits perched on a high cliff ridge in Dolakha district. Known for winter snow, cable car access from Kuri village, and stunning panoramas of Mount Gaurishankar and Langtang range.",
        "cover_image": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Kalinchowk Bhagwati Shrine | Dolakha, Nepal",
        "meta_description": "High altitude shrine with cable car rides, winter snow, and Gaurishankar Himalayan vistas."
    },
    {
        "name": "Namobuddha Thrangu Tashi Yangtse Monastery",
        "slug": "namobuddha-monastery-kavre",
        "district": "Kavrepalanchok",
        "province": "Bagmati Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.5683,
        "longitude": 85.5800,
        "altitude": "1,750 m",
        "description": "Namobuddha is one of Nepal's four major Buddhist holy pilgrimage sites. Located atop a lush ridge in Kavre, it marks the sacred spot where the Bodhisattva fed his body to a starving tigress and her cubs.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Namobuddha Monastery | Kavre, Nepal",
        "meta_description": "Sacred Buddhist pilgrimage destination with grand golden stupas and quiet mountain air."
    },
    {
        "name": "Chandragiri Hill & Bhaleshwor Temple",
        "slug": "chandragiri-hill-bhaleshwor-temple",
        "district": "Kathmandu",
        "province": "Bagmati Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 27.6622,
        "longitude": 85.2289,
        "altitude": "2,551 m",
        "description": "Chandragiri Hill lies on the south-west rim of Kathmandu Valley. Accessible by scenic cable car, it features the historic Bhaleshwor Mahadev Temple and panoramic views stretching from Mount Everest to Annapurna.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Chandragiri Hill Cable Car | Kathmandu, Nepal",
        "meta_description": "Panoramas of the Everest range and Kathmandu valley with Bhaleshwor Mahadev temple."
    },
    {
        "name": "Sailung Peak & Rolling Mounds",
        "slug": "sailung-peak-mounds",
        "district": "Ramechhap",
        "province": "Bagmati Province",
        "category_name": "Trekking & Nature",
        "latitude": 27.5258,
        "longitude": 86.0583,
        "altitude": "3,146 m",
        "description": "Sailung Peak, meaning 'Hundred Mounds', features unique grassy hillocks, ancient Buddhist stupas, and sacred Hindu caves along the Ramechhap-Dolakha border. Offers 360-degree views of Everest and Langtang mountains.",
        "cover_image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Sailung Peak | Ramechhap, Nepal",
        "meta_description": "Explore the hundred grassy mounds of Sailung with panoramic Himalayan mountain vistas."
    },
    {
        "name": "Gosainkunda Sacred Alpine Lakes",
        "slug": "gosainkunda-sacred-alpine-lakes",
        "district": "Rasuwa",
        "province": "Bagmati Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 28.0833,
        "longitude": 85.4167,
        "altitude": "4,380 m",
        "description": "Gosainkunda is an alpine glacier lake complex inside Langtang National Park. Revered by Hindus and Buddhists as the abode of Lord Shiva, it attracts thousands of pilgrims during Janai Purnima festival.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Gosainkunda Lake Trek | Rasuwa, Nepal",
        "meta_description": "High altitude holy glacier lake in Langtang National Park for spiritual pilgrimages and trekking."
    },
    {
        "name": "Devghat Dham River Confluence",
        "slug": "devghat-dham-confluence",
        "district": "Chitwan",
        "province": "Bagmati Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.7125,
        "longitude": 84.4258,
        "altitude": "190 m",
        "description": "Devghat Dham is a sacred holy river confluence where the Trishuli and Kali Gandaki rivers meet. It features ancient ashrams, Sanskrit pathshalas, and hosts massive Makar Sankranti bathing fairs.",
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Devghat Dham | Chitwan & Tanahun, Nepal",
        "meta_description": "Holy river confluence of Trishuli and Kali Gandaki with ancient ashrams and spiritual retreats."
    },
    {
        "name": "Bandipur Newari Hilltop Heritage",
        "slug": "bandipur-newari-hilltop-town",
        "district": "Tanahun",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 27.9389,
        "longitude": 84.4172,
        "altitude": "1,030 m",
        "description": "Bandipur is a living museum of traditional Newari architecture perched high above the Marsyangdi river valley. Features vehicle-free cobblestone streets, wooden carvings, Siddha Cave, and mountain views.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Bandipur Hill Town | Tanahun, Nepal",
        "meta_description": "Preserved Newari heritage hill town with traditional slate roofs and Annapurna views."
    },
    {
        "name": "Gorkha Durbar Fortress Palace",
        "slug": "gorkha-durbar-fortress-palace",
        "district": "Gorkha",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.0053,
        "longitude": 84.6292,
        "altitude": "1,060 m",
        "description": "Gorkha Durbar is a historic 16th-century palace, fortress, and temple complex overlooking the Gorkha valley. The birthplace of King Prithvi Narayan Shah, founder of unified modern Nepal.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Gorkha Durbar | Gorkha, Nepal",
        "meta_description": "Historic hill fortress palace and ancestral home of the Shah dynasty in central Nepal."
    },
    {
        "name": "Galeshwor Dham Monolithic Shiva Shrine",
        "slug": "galeshwor-dham-myagdi",
        "district": "Myagdi",
        "province": "Gandaki Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 28.3750,
        "longitude": 83.5683,
        "altitude": "900 m",
        "description": "Galeshwor Dham is a sacred Shiva temple built atop a single continuous 9-ropani solid rock along the Kali Gandaki river. Serves as the gateway to the Annapurna Circuit and Mustang pilgrimages.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Galeshwor Dham | Myagdi, Nepal",
        "meta_description": "Sacred monolithic rock Shiva shrine along the Kali Gandaki river route."
    },
    {
        "name": "Shey Phoksundo Turquoise Alpine Lake",
        "slug": "shey-phoksundo-turquoise-lake",
        "district": "Dolpa",
        "province": "Karnali Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 29.2083,
        "longitude": 82.9500,
        "altitude": "3,611 m",
        "description": "Shey Phoksundo Lake is an alpine freshwater lake in Shey Phoksundo National Park. Famous for its striking turquoise waters, Ringmo Bon village, ancient monasteries, and zero aquatic life.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Shey Phoksundo Lake | Dolpa, Nepal",
        "meta_description": "Turquoise alpine lake inside Shey Phoksundo National Park in remote Karnali."
    },
    {
        "name": "Rara Lake National Park Sanctuary",
        "slug": "rara-lake-national-park-sanctuary",
        "district": "Mugu",
        "province": "Karnali Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 29.5333,
        "longitude": 82.0833,
        "altitude": "2,990 m",
        "description": "Rara Lake is the largest freshwater lake in Nepal, often called the 'Queen of Lakes'. Nestled inside Rara National Park, it features pristine crystal waters surrounded by pine forests and snow peaks.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Rara Lake Sanctuary | Mugu, Karnali",
        "meta_description": "Nepal's largest pristine alpine lake surrounded by pine forests and wildlife."
    },
    {
        "name": "Khaptad High Meadows & Ashram",
        "slug": "khaptad-high-meadows-ashram",
        "district": "Bajhang",
        "province": "Sudurpashchim Province",
        "category_name": "Trekking & Nature",
        "latitude": 29.3667,
        "longitude": 81.1167,
        "altitude": "3,200 m",
        "description": "Khaptad National Park is a high-altitude plateau spanning Bajhang, Bajura, Doti, and Achham. Features 22 rolling green moorlands ('Patan'), Khaptad Baba's spiritual ashram, and diverse medicinal flora.",
        "cover_image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Khaptad National Park | Sudurpashchim, Nepal",
        "meta_description": "Alpine moorlands, Khaptad Baba spiritual ashram, and wild medicinal flora meadows."
    },
    {
        "name": "Champa Devi Sanctuary Peak",
        "slug": "champa-devi-sanctuary-peak",
        "district": "Kathmandu",
        "province": "Bagmati Province",
        "category_name": "Trekking & Nature",
        "latitude": 27.6186,
        "longitude": 85.2536,
        "altitude": "2,278 m",
        "description": "Champa Devi Peak is a popular day hike on the south rim of Kathmandu Valley above Pharping. Offers pine trail ridge walks, Champa Devi Goddess Shrine, and views of Langtang and Ganesh Himal.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Champa Devi Peak Hike | Kathmandu, Nepal",
        "meta_description": "Ridge hike through pine forests to Champa Devi shrine overlooking Kathmandu valley."
    },
    {
        "name": "Tinjure Milke Jaljale Rhododendron Forest",
        "slug": "tinjure-milke-jaljale-rhododendron-forest",
        "district": "Tehrathum",
        "province": "Koshi Province",
        "category_name": "Trekking & Nature",
        "latitude": 27.1667,
        "longitude": 87.4500,
        "altitude": "2,900 m",
        "description": "TMJ (Tinjure-Milke-Jaljale) ridge is widely celebrated as the 'Rhododendron Capital of Nepal'. Home to 28 out of 32 native Nepalese rhododendron species in full bloom during spring.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Tinjure Milke Jaljale | Tehrathum, Nepal",
        "meta_description": "Explore Nepal's rhododendron capital featuring 28 native blooming flower species."
    },
    {
        "name": "Bhedetar Hillstation Viewpoint",
        "slug": "bhedetar-hillstation-viewpoint",
        "district": "Sunsari",
        "province": "Koshi Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 26.8528,
        "longitude": 87.3292,
        "altitude": "1,420 m",
        "description": "Bhedetar is a famous cool hillstation village situated on the ridge connecting Sunsari and Dhankuta. Features Charles Tower, Namaste Falls, and sweeping views of the Tamor river valley.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Bhedetar Hillstation | Sunsari & Dhankuta",
        "meta_description": "Cool hill station with Charles Tower viewpoint overlooking Eastern Terai and Tamor river."
    },
    {
        "name": "Janaki Mandir Palace Temple Complex",
        "slug": "janaki-mandir-palace-temple",
        "district": "Dhanusha",
        "province": "Madhesh Province",
        "category_name": "Heritage & Culture",
        "latitude": 26.7300,
        "longitude": 85.9261,
        "altitude": "74 m",
        "description": "Janaki Mandir is a magnificent 19th-century Mughal-Koiri marble palace temple in Janakpurdham dedicated to Goddess Sita. Major pilgrimage destination for Vivaha Panchami and Ram Navami.",
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Janaki Mandir | Janakpurdham, Nepal",
        "meta_description": "Mughal-style bright marble palace temple dedicated to Goddess Sita in Madhesh Province."
    },
    {
        "name": "Swargadwari Sacred Hilltop Temple",
        "slug": "swargadwari-sacred-hilltop-temple",
        "district": "Pyuthan",
        "province": "Lumbini Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 28.0892,
        "longitude": 82.5292,
        "altitude": "2,120 m",
        "description": "Swargadwari ('Door to Heaven') is a hilltop pilgrimage complex in Pyuthan founded by Swami Hansananda. Features unbroken Yajna sacrificial fires, Vedic pathshalas, and thousands of sacred cows.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Swargadwari Temple | Pyuthan, Nepal",
        "meta_description": "Ancient hilltop sanctuary with eternal Yajna fires, Veda pathshala, and holy gaushala."
    }
]

def run():
    print("--- Adding 20 authentic high-value destinations ---")
    created_count = 0
    updated_count = 0

    for item in NEW_DESTINATIONS:
        data = dict(item)
        cat_name = data.pop("category_name", "Attraction")
        category_obj, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={"slug": cat_name.lower().replace(" & ", "-").replace(" ", "-")}
        )
        data["category"] = category_obj

        dest, created = Destination.objects.update_or_create(
            slug=data["slug"],
            defaults=data
        )
        if created:
            created_count += 1
            print(f"[CREATED] {dest.name} ({dest.district}, {dest.province})")
        else:
            updated_count += 1
            print(f"[UPDATED] {dest.name} ({dest.district}, {dest.province})")

    print(f"\nResult: {created_count} created, {updated_count} updated.")

    print("\n--- Seeding Transit Routes ---")
    transit_cmd = TransitCommand()
    transit_cmd.handle()

    print("\n--- Enriching Nearest Emergency & Hotel Distance Indicators ---")
    enrich_cmd = EnrichCommand()
    enrich_cmd.handle()

if __name__ == "__main__":
    run()
