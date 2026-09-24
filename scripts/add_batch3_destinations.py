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

BATCH3_DESTINATIONS = [
    {
        "name": "Pashupatinath Sacred Hindu Sanctuary",
        "slug": "pashupatinath-sacred-sanctuary",
        "district": "Kathmandu",
        "province": "Bagmati Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.7106,
        "longitude": 85.3486,
        "altitude": "1,350 m",
        "description": "Pashupatinath Temple is a sacred UNESCO World Heritage Hindu temple complex dedicated to Lord Shiva situated along the holy Bagmati River in Kathmandu. Features pagoda architecture, silver-plated doors, holy sadhus, and evening Bagmati Aarati ceremonies.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Pashupatinath Temple | Kathmandu, Nepal",
        "meta_description": "UNESCO World Heritage Shiva temple along the Bagmati River with evening Aarati ceremonies."
    },
    {
        "name": "Boudhanath Stupa & Tibetan Monasteries",
        "slug": "boudhanath-stupa-monasteries",
        "district": "Kathmandu",
        "province": "Bagmati Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.7215,
        "longitude": 85.3620,
        "altitude": "1,380 m",
        "description": "Boudhanath is one of the largest spherical stupas in Nepal and a UNESCO World Heritage site. Surrounded by 50+ Tibetan monasteries, prayer wheels, rooftop cafes, and butter lamps, it serves as the focal point of Tibetan Buddhism in Kathmandu.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Boudhanath Stupa | Kathmandu, Nepal",
        "meta_description": "Massive UNESCO Buddhist mandala stupa encircled by Tibetan monasteries and prayer wheels."
    },
    {
        "name": "Swayambhunath Stupa (Monkey Temple)",
        "slug": "swayambhunath-stupa-monkey-temple",
        "district": "Kathmandu",
        "province": "Bagmati Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.7149,
        "longitude": 85.2903,
        "altitude": "1,420 m",
        "description": "Swayambhunath, fondly known as the 'Monkey Temple', crowns a hilltop overlooking Kathmandu Valley. Dates back over 2,000 years with Buddha's watchful eyes painted on four sides, ancient shrines, and panoramic valley views.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Swayambhunath Stupa | Kathmandu, Nepal",
        "meta_description": "Ancient hilltop Buddhist stupa with panoramic views over the Kathmandu valley."
    },
    {
        "name": "Pokhara Lakeside & Tal Barahi Island Temple",
        "slug": "pokhara-lakeside-tal-barahi",
        "district": "Kaski",
        "province": "Gandaki Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 28.2096,
        "longitude": 83.9580,
        "altitude": "822 m",
        "description": "Pokhara Lakeside stretches along the tranquil shores of Phewa Lake with reflections of Mount Machhapuchhre (Fishtail). Features wooden rowboats, Tal Barahi island pagoda temple, vibrant cafes, and lakeside promenades.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Pokhara Lakeside & Phewa Lake | Kaski, Nepal",
        "meta_description": "Tranquil lakefront resort hub with Tal Barahi island temple and Fishtail peak reflections."
    },
    {
        "name": "Sarangkot Paragliding & Sunrise Hillstation",
        "slug": "sarangkot-paragliding-sunrise-hill",
        "district": "Kaski",
        "province": "Gandaki Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 28.2439,
        "longitude": 83.9486,
        "altitude": "1,600 m",
        "description": "Sarangkot is Pokhara's premier hilltop viewpoint situated at 1,600m. Celebrated for golden sunrise over Dhaulagiri, Annapurna Massif, and Machhapuchhre, as well as world-class tandem paragliding takeoffs.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Sarangkot Paragliding & Sunrise | Pokhara",
        "meta_description": "Panoramas of Annapurna sunrise and world-famous tandem paragliding launches."
    },
    {
        "name": "Devi's Fall & Gupteshwor Mahadev Cave",
        "slug": "devis-fall-gupteshwor-cave",
        "district": "Kaski",
        "province": "Gandaki Province",
        "category_name": "Trekking & Nature",
        "latitude": 28.1900,
        "longitude": 83.9589,
        "altitude": "780 m",
        "description": "Devi's Fall (Patale Chhango) is an unusual underground waterfall where Pardi Khola stream disappears into a subterranean gorge. Across the street lies Gupteshwor Mahadev Cave with a natural rock Shiva lingam inside.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Devi's Fall & Gupteshwor Cave | Pokhara",
        "meta_description": "Underground waterfall and limestone cave shrine dedicated to Lord Shiva."
    },
    {
        "name": "Patan Durbar Square & Golden Temple",
        "slug": "patan-durbar-square-golden-temple",
        "district": "Lalitpur",
        "province": "Bagmati Province",
        "category_name": "Heritage & Culture",
        "latitude": 27.6732,
        "longitude": 85.3253,
        "altitude": "1,350 m",
        "description": "Patan Durbar Square in Lalitpur is a masterpiece of Malla Newari architecture. Home to the 21-pinnacle stone Krishna Mandir, Golden Temple (Hiranya Varna Mahavihar), Patan Museum, and bronze metal craft workshops.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Patan Durbar Square | Lalitpur, Nepal",
        "meta_description": "UNESCO Royal Palace Plaza featuring Krishna Mandir and historic Patan Museum."
    },
    {
        "name": "Bhaktapur Durbar Square & Nyatapola Temple",
        "slug": "bhaktapur-durbar-square-nyatapola",
        "district": "Bhaktapur",
        "province": "Bagmati Province",
        "category_name": "Heritage & Culture",
        "latitude": 27.6722,
        "longitude": 85.4281,
        "altitude": "1,401 m",
        "description": "Bhaktapur Durbar Square is a open-air living museum of ancient Newari culture. Highlights include the 55-Window Palace, Golden Gate, 5-tiered Nyatapola Temple, Pottery Square, and authentic Juju Dhau curd.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Bhaktapur Durbar Square | Bhaktapur, Nepal",
        "meta_description": "55-Window Palace, 5-story Nyatapola Temple, and traditional pottery squares."
    },
    {
        "name": "Nagarkot Himalayan Sunrise Viewpoint",
        "slug": "nagarkot-himalayan-sunrise-viewpoint",
        "district": "Bhaktapur",
        "province": "Bagmati Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 27.7011,
        "longitude": 85.5214,
        "altitude": "2,175 m",
        "description": "Nagarkot sits on the eastern rim of Kathmandu Valley at 2,175m. Famous for offering one of the broadest views of the Himalayas, including Mount Everest, Langtang, Ganesh Himal, and Gaurishankar at sunrise.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Nagarkot Sunrise Viewpoint | Nepal",
        "meta_description": "Broadest Himalayan sunrise views stretching from Annapurna to Mount Everest."
    },
    {
        "name": "Chitwan Sauraha Jungle Safari & Elephant Reserve",
        "slug": "chitwan-sauraha-jungle-safari",
        "district": "Chitwan",
        "province": "Bagmati Province",
        "category_name": "Trekking & Nature",
        "latitude": 27.5833,
        "longitude": 84.4833,
        "altitude": "150 m",
        "description": "Chitwan National Park in Sauraha is Nepal's premier wildlife safari destination and UNESCO World Heritage sanctuary. Home to the endangered Greater One-Horned Rhinoceros, Royal Bengal Tiger, Gharial crocodile, and Tharu cultural dances.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Chitwan Jungle Safari & Sauraha | Nepal",
        "meta_description": "UNESCO World Heritage national park with One-Horned Rhinos, Bengal Tigers, and canoeing."
    },
    {
        "name": "Bardiya Tiger Reserve & Wilderness Safari",
        "slug": "bardiya-tiger-reserve-safari",
        "district": "Bardiya",
        "province": "Lumbini Province",
        "category_name": "Trekking & Nature",
        "latitude": 28.5167,
        "longitude": 81.3333,
        "altitude": "152 m",
        "description": "Bardiya National Park in Thakurdwara is Nepal's largest undisturbed terai wilderness. Celebrated for high tiger sighting probabilities, wild Asian elephants, swamp deer, and Gangetic river dolphins on the Karnali River.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Bardiya National Park | Thakurdwara, Nepal",
        "meta_description": "Pristine western Nepal wilderness reserve renowned for wild Bengal Tiger sightings."
    },
    {
        "name": "Ghandruk Gurung Stone Heritage Village",
        "slug": "ghandruk-gurung-stone-village",
        "district": "Kaski",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.3761,
        "longitude": 83.8072,
        "altitude": "1,940 m",
        "description": "Ghandruk is a picturesque stone-roofed Gurung mountain village in the Annapurna Conservation Area. Features traditional slate-paved alleyways, Gurung cultural museum, organic apple orchards, and face-to-face views of Annapurna South and Machhapuchhre.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Ghandruk Gurung Village Trek | Kaski, Nepal",
        "meta_description": "Slate-paved traditional Gurung mountain village facing Annapurna South and Fishtail."
    },
    {
        "name": "Poon Hill Rhododendron Sunrise Viewpoint",
        "slug": "poon-hill-rhododendron-sunrise",
        "district": "Myagdi",
        "province": "Gandaki Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 28.3986,
        "longitude": 83.6983,
        "altitude": "3,210 m",
        "description": "Poon Hill near Ghorepani is one of Nepal's most famous trekking viewpoints (3,210m). Offers breathtaking 360-degree views of the Annapurna and Dhaulagiri mountain ranges framed by blooming spring rhododendron forests.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Poon Hill Ghorepani Trek | Myagdi, Nepal",
        "meta_description": "Celebrated 3,210m ridge viewpoint for Annapurna and Dhaulagiri golden sunrise."
    },
    {
        "name": "Gokyo Turquoise Lakes & Gokyo Ri Peak",
        "slug": "gokyo-lakes-gokyo-ri-peak",
        "district": "Solukhumbu",
        "province": "Koshi Province",
        "category_name": "Lakes & Water Bodies",
        "latitude": 27.9500,
        "longitude": 86.6833,
        "altitude": "4,750 m",
        "description": "Gokyo Lakes are six high-altitude glacial lakes in Sagarmatha National Park. Nearby Gokyo Ri peak (5,357m) offers vistas of four 8,000m giant peaks: Mount Everest, Lhotse, Makalu, and Cho Oyu.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Gokyo Lakes & Gokyo Ri Trek | Everest Region",
        "meta_description": "Turquoise glacial lakes at 4,750m with views of Everest, Lhotse, Makalu and Cho Oyu."
    },
    {
        "name": "Manakamana Wish-Fulfilling Temple Cable Car",
        "slug": "manakamana-temple-cable-car",
        "district": "Gorkha",
        "province": "Gandaki Province",
        "category_name": "Religious & Pilgrimage",
        "latitude": 27.9031,
        "longitude": 84.5842,
        "altitude": "1,302 m",
        "description": "Manakamana Temple is a revered pilgrimage shrine dedicated to Goddess Bhagwati, believed to fulfill the wishes of her devotees. Accessible via Nepal's first cable car system starting from Kurintar along the Trishuli River.",
        "cover_image": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1518002171953-a084ef817e0f?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Manakamana Temple Cable Car | Gorkha, Nepal",
        "meta_description": "Sacred wish-fulfilling Goddess shrine accessible by scenic cable car ride above Trishuli River."
    },
    {
        "name": "Kanyam Tea Estate & Horse Riding Ridge",
        "slug": "kanyam-tea-estate-ilam",
        "district": "Ilam",
        "province": "Koshi Province",
        "category_name": "Trekking & Nature",
        "latitude": 26.8633,
        "longitude": 88.0617,
        "altitude": "1,450 m",
        "description": "Kanyam is Nepal's most famous tea garden destination situated along the Mechi Highway in Ilam. Features manicured green tea hills, traditional horse riding trails, tea tasting cottage stalls, and cool mountain fog.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Kanyam Tea Gardens | Ilam, Nepal",
        "meta_description": "Rolling green orthodox tea plantation hills, horse rides, and fresh tea tasting in Ilam."
    },
    {
        "name": "Shree Antu Danda Sunrise Viewpoint",
        "slug": "shree-antu-danda-sunrise",
        "district": "Ilam",
        "province": "Koshi Province",
        "category_name": "Viewpoints & Hillstations",
        "latitude": 26.9000,
        "longitude": 88.0833,
        "altitude": "2,328 m",
        "description": "Shree Antu Danda in eastern Ilam is famous for receiving the very first rays of sunrise in Nepal. Offers vistas over Mount Kanchenjunga, Mirik tea hills, and Antu Pokhari lake.",
        "cover_image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Shree Antu Danda Sunrise | Ilam, Nepal",
        "meta_description": "First rays of golden sunrise over Mt. Kanchenjunga in easternmost Nepal."
    },
    {
        "name": "Koshi Tappu Wildlife Ramsar Reserve",
        "slug": "koshi-tappu-wildlife-ramsar-reserve",
        "district": "Sunsari",
        "province": "Koshi Province",
        "category_name": "Trekking & Nature",
        "latitude": 26.6500,
        "longitude": 86.9500,
        "altitude": "90 m",
        "description": "Koshi Tappu Wildlife Reserve is a Ramsar wetland on the floodplains of the Sapta Koshi River spanning Sunsari, Saptari, and Udayapur. Famous as the last refuge of wild water buffaloes (Arna) and over 500 migratory bird species.",
        "cover_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": True,
        "seo_title": "Koshi Tappu Wetland Sanctuary | Koshi Province",
        "meta_description": "Ramsar wetland sanctuary for wild water buffaloes (Arna) and 500+ migratory bird species."
    },
    {
        "name": "Manang Rain-Shadow Valley & Braga Monastery",
        "slug": "manang-valley-braga-monastery",
        "district": "Manang",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.6667,
        "longitude": 84.0167,
        "altitude": "3,540 m",
        "description": "Manang Valley sits in the rain shadow of the Annapurna range along the Marsyangdi River. Features ancient cliffside Braga Monastery (Brakha), Chame hot springs, Gangapurna Glacier Lake, and Tibetan Buddhist culture.",
        "cover_image": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1508672019048-805479767382?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Manang Valley & Braga Monastery | Annapurna Circuit",
        "meta_description": "High altitude rain-shadow Himalayan valley with 500-year-old Braga monastery."
    },
    {
        "name": "Gorkha Museum & Tallo Durbar Palace",
        "slug": "gorkha-museum-tallo-durbar",
        "district": "Gorkha",
        "province": "Gandaki Province",
        "category_name": "Heritage & Culture",
        "latitude": 28.0000,
        "longitude": 84.6200,
        "altitude": "1,000 m",
        "description": "Gorkha Museum is housed inside the historic 1835 Newari-style Tallo Durbar Palace in Gorkha Bazaar. Displays royal weaponry, Gorkhali military armor, ancient coins, and historical unification archives.",
        "cover_image": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "og_image_url": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
        "status": "approved",
        "is_featured": False,
        "seo_title": "Gorkha Museum & Tallo Durbar | Gorkha, Nepal",
        "meta_description": "Historical Newari palace museum showcasing Gorkhali royal weapons and unification archives."
    }
]

def run():
    print("--- Adding Batch 3: 20 Iconic Nepal Destinations ---")
    created_count = 0
    updated_count = 0

    for item in BATCH3_DESTINATIONS:
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
