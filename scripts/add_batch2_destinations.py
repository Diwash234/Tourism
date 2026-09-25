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

BATCH2_DESTINATIONS = [
    {
        "name": "Muktinath Temple & Eternal Flame",
        "slug": "muktinath-temple-eternal-flame",
        "district": "Mustang",
        "province": "Gandaki Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 28.8167,
        "longitude": 83.8719,
        "altitude": "3,710 m",
        "description": "Muktinath is a sacred Vishnu temple revered by both Hindus and Buddhists as Chumig Gyatsa ('Hundred Waters'). Located at the foot of Thorong La pass in Mustang, it features 108 bull-headed holy water spouts and an eternal natural gas flame.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Muktinath Temple & 108 Spouts | Mustang, Nepal",
        "meta_description": "Sacred high altitude Vishnu shrine with 108 bull spouts and eternal flame in Mustang."
    },
    {
        "name": "Tilicho Glacier Lake Sanctuary",
        "slug": "tilicho-glacier-lake-sanctuary",
        "district": "Manang",
        "province": "Gandaki Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 28.6917,
        "longitude": 83.8444,
        "altitude": "4,919 m",
        "description": "Tilicho Lake is one of the highest alpine lakes in the world, sitting beneath the formidable north face of Tilicho Peak in Manang. A highlight of the Annapurna Circuit trek with vivid deep blue waters and glacial ice walls.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Tilicho Alpine Lake Trek | Manang, Nepal",
        "meta_description": "Glacial high-altitude lake (4,919m) beneath Tilicho Peak on the Annapurna Circuit."
    },
    {
        "name": "Simikot Valley & Kailash Gateway",
        "slug": "simikot-valley-kailash-gateway",
        "district": "Humla",
        "province": "Karnali Province",
        "category_name": "Trekking & Nature",
        "latitude": 29.9706,
        "longitude": 81.8267,
        "altitude": "2,910 m",
        "description": "Simikot is the remote district headquarters of Humla in far-western Nepal. Accessible primarily by mountain flights, it serves as the primary gateway for pilgrimage treks along the Karnali river route to Mount Kailash and Lake Manasarovar.",
        "cover_image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Simikot Gateway | Humla, Karnali",
        "meta_description": "Remote mountain gateway to Mount Kailash pilgrimage and Karnali river gorge treks."
    },
    {
        "name": "Chandannath Temple & Red Paddy Hub",
        "slug": "chandannath-temple-jumla",
        "district": "Jumla",
        "province": "Karnali Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 29.2750,
        "longitude": 82.1833,
        "altitude": "2,514 m",
        "description": "Chandannath Temple is a historic pagoda shrine in Jumla Bazaar dedicated to Lord Dattatreya. Jumla valley is world-famous for cultivating unique high-altitude red rice (Marshi Dhan) and organic apples.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Chandannath Shrine | Jumla, Nepal",
        "meta_description": "Historic pagoda temple in Jumla valley famous for Marshi red rice and alpine orchards."
    },
    {
        "name": "Api Nampa Alpine Conservation Area",
        "slug": "api-nampa-conservation-area",
        "district": "Darchula",
        "province": "Sudurpashchim Province",
        "category_name": "Trekking & Nature",
        "latitude": 29.8500,
        "longitude": 80.9000,
        "altitude": "3,400 m",
        "description": "Api Nampa Conservation Area in Darchula encompasses Mount Api (7,132m) and Mount Nampa. Features unexplored wilderness, snow leopards, medicinal yarsagumba gathering grounds, and Byansi ethnic heritage.",
        "cover_image": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Api Nampa Conservation Area | Darchula, Nepal",
        "meta_description": "Wilderness conservation area surrounding Mt. Api with snow peaks and Byansi culture."
    },
    {
        "name": "Makalu Barun Valley National Park",
        "slug": "makalu-barun-national-park",
        "district": "Sankhuwasabha",
        "province": "Koshi Province",
        "category_name": "Trekking & Nature",
        "latitude": 27.7500,
        "longitude": 87.1500,
        "altitude": "2,200 m",
        "description": "Makalu Barun National Park protects the pristine Barun river gorge beneath Mount Makalu (8,485m), the fifth highest peak in the world. Known for extreme biodiversity, cascading waterfalls, and rare orchids.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Makalu Barun National Park | Sankhuwasabha",
        "meta_description": "Pristine eastern Nepal wilderness around Mt. Makalu with rich bio-diversity and waterfalls."
    },
    {
        "name": "Mai Pokhari Ramsar Wetland Lake",
        "slug": "mai-pokhari-ramsar-lake",
        "district": "Ilam",
        "province": "Koshi Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 26.9667,
        "longitude": 87.9333,
        "altitude": "2,100 m",
        "description": "Mai Pokhari is a holy Ramsar wetland lake in Ilam encircled by sacred oak and rhododendron forests. Revered as the home of Goddess Maipokhari, it features nine lake corners and endemic salamander species.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Mai Pokhari Wetland | Ilam, Nepal",
        "meta_description": "Sacred Ramsar wetland lake in Ilam surrounded by lush tea hills and rhododendron forests."
    },
    {
        "name": "Kagbeni Medieval Mustang Fortress",
        "slug": "kagbeni-medieval-fortress-village",
        "district": "Mustang",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.8375,
        "longitude": 83.7828,
        "altitude": "2,804 m",
        "description": "Kagbeni is a 500-year-old mud-brick fortress village standing at the confluence of Mustang Khola and Jhong River. Serves as the gateway to restricted Upper Mustang with ancient chortens and monasteries.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Kagbeni Medieval Village | Mustang, Nepal",
        "meta_description": "Historic mud-brick fortress town and gateway to Upper Mustang along the Kali Gandaki."
    },
    {
        "name": "Triveni Dham & Valmiki Ashram",
        "slug": "triveni-dham-valmiki-ashram",
        "district": "Nawalparasi West",
        "province": "Lumbini Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.4431,
        "longitude": 83.9014,
        "altitude": "100 m",
        "description": "Triveni Dham is a sacred river confluence of Narayani, Sona, and Tamasa rivers near Chitwan National Park border. Nearby Valmiki Ashram is the legendary hermitage where Sage Valmiki composed the Ramayana.",
        "cover_image": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1565354084224-a745814578b9?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Triveni Dham & Valmiki Ashram | Nawalparasi",
        "meta_description": "Holy Narayani river confluence and ancient Ramayana hermitage of Sage Valmiki."
    },
    {
        "name": "Resunga Sacred Hillstation & Ashram",
        "slug": "resunga-sacred-hillstation-gulmi",
        "district": "Gulmi",
        "province": "Lumbini Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 28.0667,
        "longitude": 83.2500,
        "altitude": "2,320 m",
        "description": "Resunga Hill is a sacred mountain forest overlooking Tamghas bazaar in Gulmi. Features Yajna Kund, ancient hermitages of Rishis, panoramic views of Dhaulagiri and Annapurna, and cool pine air.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Resunga Sacred Hill | Gulmi, Nepal",
        "meta_description": "Sacred hilltop forest with Yajna Kund, Rishi ashrams, and panoramas of Dhaulagiri."
    },
    {
        "name": "Supadeurali Cliffside Temple Pass",
        "slug": "supadeurali-cliffside-temple",
        "district": "Arghakhanchi",
        "province": "Lumbini Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.9167,
        "longitude": 83.1500,
        "altitude": "1,200 m",
        "description": "Supadeurali Temple is a revered Bhagwati shrine set between dramatic rock cliffs along the Gorusinghe-Sandhikharka highway in Arghakhanchi. Famous for fulfilling vows made by travelers and soldiers.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Supadeurali Temple | Arghakhanchi, Nepal",
        "meta_description": "Famous cliffside pilgrimage shrine fulfilling traveler vows along the Arghakhanchi highway."
    },
    {
        "name": "Rani Mahal Riverfront Palace",
        "slug": "rani-mahal-riverfront-palace",
        "district": "Palpa",
        "province": "Lumbini Province",
        "category_name": "Heritage & Culture",
        "latitude": 27.8833,
        "longitude": 83.5167,
        "altitude": "400 m",
        "description": "Rani Mahal, dubbed the 'Taj Mahal of Nepal', is a 19th-century neoclassical palace built on a massive rock along the Kali Gandaki river by General Khadga Shamsher in memory of his beloved wife Tej Kumari.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Rani Mahal Palace | Palpa, Nepal",
        "meta_description": "Historic riverfront neoclassical palace along the Kali Gandaki river in Palpa."
    },
    {
        "name": "Ghalegaun Gurung Cultural Village",
        "slug": "ghalegaun-gurung-cultural-village",
        "district": "Lamjung",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.2583,
        "longitude": 84.3208,
        "altitude": "2,070 m",
        "description": "Ghalegaun is an award-winning model eco-homestay village in Lamjung inhabited by the indigenous Gurung community. Offers traditional cultural dances, wild honey hunting views, and vistas of Annapurna and Manaslu.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Ghalegaun Gurung Homestay | Lamjung, Nepal",
        "meta_description": "Model homestay village in Lamjung celebrating Gurung heritage and honey hunting."
    },
    {
        "name": "Sindhuligadhi Historic Hill Fort",
        "slug": "sindhuligadhi-historic-hill-fort",
        "district": "Sindhuli",
        "province": "Bagmati Province",
        "category_name": "Heritage & Culture",
        "latitude": 27.2833,
        "longitude": 85.9667,
        "altitude": "1,400 m",
        "description": "Sindhuligadhi is a historic hilltop fort where the Gorkhali army led by Kaji Kalu Pande defeated the British East India Company forces in 1767. Features a military war museum and panoramic valley views.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Sindhuligadhi Hill Fort | Sindhuli, Nepal",
        "meta_description": "Historic hill fort and war museum celebrating the Gorkhali victory of 1767."
    },
    {
        "name": "Kankrebihar Monolithic Buddhist Shrine",
        "slug": "kankrebihar-monolithic-buddhist-shrine",
        "district": "Surkhet",
        "province": "Karnali Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.5833,
        "longitude": 81.6333,
        "altitude": "650 m",
        "description": "Kankrebihar is a 12th-century stone Buddhist temple structure nestled inside a protected dense forest near Birendranagar in Surkhet valley. Often referred to as the 'Sanchi of Nepal' for its ancient stone carvings.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Kankrebihar Stone Temple | Surkhet, Karnali",
        "meta_description": "12th-century Buddhist stone carvings and forest sanctuary in Surkhet valley."
    },
    {
        "name": "Lomanthang Ancient Walled City",
        "slug": "lomanthang-ancient-walled-city",
        "district": "Mustang",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 29.1819,
        "longitude": 83.9567,
        "altitude": "3,840 m",
        "description": "Lomanthang is the walled historic capital of the former Kingdom of Lo in Upper Mustang. Features 15th-century royal palace, Jampa Lakhang, Thubchen Gompa, sky caves, and rich Tibetan Bon and Buddhist traditions.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Lomanthang Walled Capital | Upper Mustang",
        "meta_description": "Walled royal capital of Upper Mustang with 15th-century monasteries and sky caves."
    },
    {
        "name": "Panchthar Chhintang Devi Shrine",
        "slug": "panchthar-chhintang-devi-shrine",
        "district": "Panchthar",
        "province": "Koshi Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.0500,
        "longitude": 87.7500,
        "altitude": "1,650 m",
        "description": "Chhintang Devi Temple is a hilltop pilgrimage shrine in Panchthar surrounded by cardamom farms, orange orchards, and pine ridges. Offers views of the Tamor river valley and Kanchenjunga.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Chhintang Devi Shrine | Panchthar, Nepal",
        "meta_description": "Hilltop shrine in Panchthar set among cardamom fields with views of Tamor river."
    },
    {
        "name": "Bhojpur Taksar Bronze Craft Hub",
        "slug": "bhojpur-taksar-bronze-craft-hub",
        "district": "Bhojpur",
        "province": "Koshi Province",
        "category_name": "Heritage & Culture",
        "latitude": 27.1667,
        "longitude": 87.0500,
        "altitude": "1,500 m",
        "description": "Taksar in Bhojpur is a historic Newari artisan settlement famous across Nepal for handcrafting traditional bronze Karuwa spouts, brass kitchenware, and world-renowned Gorkha Khukuri blades.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Bhojpur Taksar Artisan Town | Koshi Province",
        "meta_description": "Historic artisan town famous for handmade bronze Karuwa spouts and Gorkha Khukuris."
    },
    {
        "name": "Kakani Hillstation & Strawberry Ridge",
        "slug": "kakani-hillstation-strawberry-ridge",
        "district": "Nuwakot",
        "province": "Bagmati Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 27.8083,
        "longitude": 85.2556,
        "altitude": "2,073 m",
        "description": "Kakani is a scenic hillstation on the northern rim of Kathmandu Valley in Nuwakot. Renowned for strawberry farming, rainbow trout hatcheries, Thai Airways memorial park, and Langtang mountain vistas.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Kakani Hillstation & Trout Farms | Nuwakot, Nepal",
        "meta_description": "Scenic hill station famous for strawberry farms, trout hatcheries, and Langtang views."
    },
    {
        "name": "Syarpu Lake Eco Retreat",
        "slug": "syarpu-lake-eco-retreat",
        "district": "Rukum West",
        "province": "Karnali Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 28.6333,
        "longitude": 82.4500,
        "altitude": "1,370 m",
        "description": "Syarpu Lake is a serene freshwater natural lake in Rukum West. Encircled by green pine hills and traditional villages, it offers boating, local organic fish delicacies, and quiet natural relaxation.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Syarpu Lake | Rukum West, Karnali",
        "meta_description": "Pristine freshwater natural lake in Rukum West for eco-boating and quiet retreats."
    }
]

def run():
    print("--- Adding Batch 2: 20 authentic high-value destinations ---")
    created_count = 0
    updated_count = 0

    for item in BATCH2_DESTINATIONS:
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
