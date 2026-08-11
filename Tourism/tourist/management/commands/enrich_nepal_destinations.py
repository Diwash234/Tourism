import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from tourist.models import (
    Destination, Category, DestinationImage, Hotel,
    Hospital, PoliceStation, BudgetEstimation, RiskAnalysis, User
)

DESTINATIONS_DATA = [
    {
        "name": "Pashupatinath Temple",
        "city": "Kathmandu",
        "district": "Kathmandu",
        "province": "Bagmati",
        "category_name": "Heritage & Temples",
        "latitude": 27.7104,
        "longitude": 85.3487,
        "altitude": "1,400m",
        "entry_fee": 1000.0,
        "best_time_to_visit": "October to March (Special: Maha Shivaratri in Feb/Mar)",
        "short_description": "Sacred 5th-century Hindu temple complex dedicated to Lord Shiva along the holy Bagmati River.",
        "description": "Pashupatinath Temple is one of the most sacred Hindu shrines in the world, dedicated to Lord Pashupatinath (Shiva). Spread across 246 hectares on the banks of the sacred Bagmati River, the main pagoda temple features a gilded two-tiered roof, silver-plated doors, and exquisite wood carvings. Non-Hindus can observe the ancient Arya Ghat cremation rituals, vibrant evening Bagmati Ganga Aarti, and meet holy Sadhus across the complex.",
        "history": "Origins date back to 400 CE during the Licchavi dynasty with mentions in the Mahabharata. Rebuilt in 1697 by King Bhupalendra Malla, it is a designated UNESCO World Heritage Site since 1979.",
        "daily_budget": 35.0,
        "trip_budget": 120.0,
        "risk_level": "LOW",
        "risk_index": 22.0,
        "hospital_name": "TUTH Teaching Hospital / Nepal Medical College",
        "hospital_phone": "+977-1-4412404",
        "police_name": "Gaushala Police Station & Tourist Police",
        "police_phone": "+977-1-4470126",
        "hotel_name": "The Dwarika's Heritage Hotel Kathmandu",
        "hotel_price": 220.0,
        "images": [
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Boudhanath Stupa",
        "city": "Kathmandu",
        "district": "Kathmandu",
        "province": "Bagmati",
        "category_name": "Heritage & Temples",
        "latitude": 27.7215,
        "longitude": 85.3620,
        "altitude": "1,400m",
        "entry_fee": 400.0,
        "best_time_to_visit": "All year round (Best: October to April, especially at sunset)",
        "short_description": "Massive 36-meter high Buddhist mandala stupa, the heartbeat of Tibetan Buddhism in Nepal.",
        "description": "Boudhanath Stupa is one of the largest spherical stupas in the world, dominating the skyline with Buddha's watchful eyes gazing across the valley. Surrounded by over 50 Tibetan Buddhist monasteries (Gompas), rooftop cafes, incense shops, and artisan thangka galleries, visitors join thousands of monks and pilgrims performing the ritual clockwise kora circumambulation under fluttering prayer flags.",
        "history": "Founded around 600 CE by King Shivadeva, it was a pivotal ancient trade route rest-point between Lhasa and the Kathmandu Valley for centuries. Recognized as a UNESCO World Heritage Site in 1979.",
        "daily_budget": 30.0,
        "trip_budget": 100.0,
        "risk_level": "LOW",
        "risk_index": 18.0,
        "hospital_name": "Boudha Stupa Clinic & Hospital",
        "hospital_phone": "+977-1-4470356",
        "police_name": "Boudha Police Station",
        "police_phone": "+977-1-4470033",
        "hotel_name": "Hyatt Regency Kathmandu",
        "hotel_price": 160.0,
        "images": [
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Swayambhunath Stupa (Monkey Temple)",
        "city": "Kathmandu",
        "district": "Kathmandu",
        "province": "Bagmati",
        "category_name": "Heritage & Temples",
        "latitude": 27.7149,
        "longitude": 85.2904,
        "altitude": "1,450m",
        "entry_fee": 200.0,
        "best_time_to_visit": "October to May (Morning sunrise or twilight for panoramic valley views)",
        "short_description": "Ancient hilltop temple complex overlooking Kathmandu, home to sacred holy monkeys.",
        "description": "Perched atop a hill west of Kathmandu city, Swayambhunath is one of Nepal's oldest religious sites. A 365-step stone stairway leads to the whitewashed stupa crown, surrounded by Chaityas, Hindu shrines like the Harati Devi temple, brass prayer wheels, and hundreds of revered rhesus macaques roaming the hill. Offers unobstructed 360-degree vistas across the entire Kathmandu bowl.",
        "history": "Mythology tells of Manjushree draining the ancient Kathmandu Lake with his flaming sword, where a self-arisen lotus flower blossomed into the holy Swayambhu hill over 2,000 years ago.",
        "daily_budget": 25.0,
        "trip_budget": 85.0,
        "risk_level": "LOW",
        "risk_index": 20.0,
        "hospital_name": "Manmohan Memorial Medical College",
        "hospital_phone": "+977-1-4286121",
        "police_name": "Swayambhu Metropolitan Police Circle",
        "police_phone": "+977-1-4271609",
        "hotel_name": "Vajra Eco Resort & Hotel",
        "hotel_price": 55.0,
        "images": [
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Phewa Lake & Tal Barahi",
        "city": "Pokhara",
        "district": "Kaski",
        "province": "Gandaki",
        "category_name": "Lakes & Water Activities",
        "latitude": 28.2163,
        "longitude": 83.9582,
        "altitude": "742m",
        "entry_fee": 0.0,
        "best_time_to_visit": "September to May (Boating at sunrise/sunset with Annapurna reflection)",
        "short_description": "Nepal's second largest freshwater lake with the two-story Tal Barahi island temple.",
        "description": "Phewa Lake is the crown jewel of Pokhara tourism. Wooden painted rowboats ('Doonga') drift across calm emerald waters with the mirror reflection of Mt. Machhapuchhre (Fishtail, 6,993m) and the Annapurna range. On a small island in the center stands the revered Tal Barahi Temple. The vibrant Lakeside strip is packed with live music cafes, artisanal bakeries, and gear shops.",
        "history": "Natural freshwater lake fed by Harpan Khola, dammed and expanded in the 1960s. Has served as the staging point for Himalayan expeditions since the 1950s.",
        "daily_budget": 40.0,
        "trip_budget": 160.0,
        "risk_level": "LOW",
        "risk_index": 15.0,
        "hospital_name": "Gandaki Medical College / Western Regional Hospital",
        "hospital_phone": "+977-61-520067",
        "police_name": "Tourist Police Pokhara Lakeside",
        "police_phone": "+977-61-462761",
        "hotel_name": "Temple Tree Resort & Spa Pokhara",
        "hotel_price": 110.0,
        "images": [
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Everest Base Camp (EBC)",
        "city": "Solukhumbu",
        "district": "Solukhumbu",
        "province": "Koshi",
        "category_name": "Nature & Trekking",
        "latitude": 27.9881,
        "longitude": 86.9250,
        "altitude": "5,364m",
        "entry_fee": 3000.0,
        "best_time_to_visit": "October to November & March to May (Clear skies, climbing expeditions active)",
        "short_description": "The world's most legendary trek to the foot of Mt. Everest (8,848.86m) through Sherpa heartlands.",
        "description": "Standing on the Khumbu Glacier beneath the sheer icefall of the highest peak on Earth is a lifelong dream for mountain lovers. The trek winds through pine-forested Dudh Koshi gorges, vibrant Sherpa capital Namche Bazaar, ancient Tengboche Buddhist Monastery, alpine pastures of Dingboche, and summits the panoramic Kala Patthar (5,545m) with breathtaking views of Everest, Lhotse, and Nuptse.",
        "history": "First reconnoitered in 1921 and established as the base for the historic 1953 first summit by Sir Edmund Hillary and Tenzing Norgay Sherpa. Sagarmatha National Park was inscribed as a World Heritage Site in 1979.",
        "daily_budget": 55.0,
        "trip_budget": 750.0,
        "risk_level": "MODERATE",
        "risk_index": 52.0,
        "hospital_name": "Himalayan Rescue Association Pheriche Clinic / Kunde Hospital",
        "hospital_phone": "+977-38-540123",
        "police_name": "Namche Bazaar Police Station & Tourist Police",
        "police_phone": "+977-38-540100",
        "hotel_name": "Hotel Everest View Syangboche (Highest 3-star in the world)",
        "hotel_price": 190.0,
        "images": [
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Annapurna Base Camp (ABC Sanctuary)",
        "city": "Kaski",
        "district": "Kaski",
        "province": "Gandaki",
        "category_name": "Nature & Trekking",
        "latitude": 28.5300,
        "longitude": 83.8780,
        "altitude": "4,130m",
        "entry_fee": 3000.0,
        "best_time_to_visit": "October to November & March to May (Rhododendron blooms & clear peaks)",
        "short_description": "Glacial natural amphitheater surrounded by Annapurna I (8,091m), Machhapuchhre, and Hiunchuli.",
        "description": "The Annapurna Sanctuary Trek is a spectacular journey into a natural 360-degree mountain amphitheater surrounded by towering 7,000m and 8,000m giants. Trek through Gurung stone villages (Ghandruk, Chomrong), lush bamboo and rhododendron forests, natural hot springs at Jhinu Danda, and Machhapuchhre Base Camp before reaching ABC at 4,130 meters.",
        "history": "First explored by British mountaineer Col. Jimmy Roberts in 1956, it opened Nepal's modern teahouse trekking culture. Part of the Annapurna Conservation Area Project (ACAP), Nepal's largest protected area.",
        "daily_budget": 45.0,
        "trip_budget": 420.0,
        "risk_level": "MODERATE",
        "risk_index": 44.0,
        "hospital_name": "Ghandruk Community Health Center / Pokhara Regional Hospital",
        "hospital_phone": "+977-61-520067",
        "police_name": "Ghandruk ACAP Police Post",
        "police_phone": "+977-61-462761",
        "hotel_name": "Sanctuary Mountain Lodge ABC",
        "hotel_price": 30.0,
        "images": [
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Chitwan National Park Safari",
        "city": "Sauraha",
        "district": "Chitwan",
        "province": "Bagmati",
        "category_name": "Wildlife",
        "latitude": 27.5341,
        "longitude": 84.4530,
        "altitude": "150m",
        "entry_fee": 2000.0,
        "best_time_to_visit": "October to March (Pleasant temperatures, grass cut for best wildlife visibility)",
        "short_description": "UNESCO World Heritage subtropical wilderness with One-Horned Rhinos and Bengal Tigers.",
        "description": "Nepal's first national park encompasses 952 sq km of dense sal forests, marshlands, and grasslands. Famous for the successful conservation of the endangered Greater One-Horned Rhinoceros (over 700 individuals) and Royal Bengal Tigers. Activities include open-top 4WD jeep safaris, tranquil wooden canoe rides down the Rapti River spotting Gharials and Mugger crocodiles, and vibrant evening Tharu cultural stick dances.",
        "history": "Established in 1973 as Nepal's first national park and designated a UNESCO World Heritage site in 1984. Once a royal hunting reserve, now a world benchmark for community-led anti-poaching success.",
        "daily_budget": 50.0,
        "trip_budget": 200.0,
        "risk_level": "LOW",
        "risk_index": 20.0,
        "hospital_name": "Bharatpur Hospital / Chitwan Medical College",
        "hospital_phone": "+977-56-521012",
        "police_name": "Sauraha Tourist Police Station",
        "police_phone": "+977-56-580100",
        "hotel_name": "Barahi Jungle Lodge & Kasara Resort",
        "hotel_price": 140.0,
        "images": [
            "https://images.unsplash.com/photo-1575550959106-5a7defe28b56?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Lumbini Sacred Garden & Maya Devi Temple",
        "city": "Lumbini",
        "district": "Rupandehi",
        "province": "Lumbini",
        "category_name": "Religious Sites",
        "latitude": 27.4699,
        "longitude": 83.2755,
        "altitude": "105m",
        "entry_fee": 500.0,
        "best_time_to_visit": "October to March (Pleasant dry winter, Buddha Jayanti in May)",
        "short_description": "The exact historical birthplace of Siddhartha Gautama (Lord Buddha) in 623 BC.",
        "description": "Lumbini is one of the four holiest pilgrimage destinations of Buddhism. The sacred complex features the Maya Devi Temple housing the marker stone of Buddha's exact birth spot, the sacred Pushkarini Pond where Queen Maya Devi bathed before giving birth, and the ancient Ashoka Pillar erected in 249 BC. Sprawling eastern and western monastic zones host monasteries constructed by over 25 nations.",
        "history": "Discovered in 1896 by archaeologists who identified Emperor Ashoka's Brahmi inscription identifying Lumbini as the Buddha's birthplace. UNESCO World Heritage Site since 1997.",
        "daily_budget": 35.0,
        "trip_budget": 110.0,
        "risk_level": "LOW",
        "risk_index": 14.0,
        "hospital_name": "Lumbini Provincial Hospital Butwal",
        "hospital_phone": "+977-71-540114",
        "police_name": "Lumbini Tourist Police Post",
        "police_phone": "+977-71-580199",
        "hotel_name": "Buddha Maya Garden by KGH Group",
        "hotel_price": 65.0,
        "images": [
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Rara Lake & National Park",
        "city": "Mugu",
        "district": "Mugu",
        "province": "Karnali",
        "category_name": "Lakes & Water Activities",
        "latitude": 29.5333,
        "longitude": 82.0833,
        "altitude": "2,990m",
        "entry_fee": 3000.0,
        "best_time_to_visit": "April to June & September to November (Mirror-calm waters and wildflower blooms)",
        "short_description": "Nepal's biggest and deepest high-altitude freshwater lake, surrounded by pine forests.",
        "description": "Often called the 'Queen of Lakes', Rara Lake is a pristine alpine marvel stretching 10.8 sq km at 2,990m elevation. Ringed by deep blue coniferous forests and snow-capped peaks of Chuchemara Danda, the crystal-clear water changes colors throughout the day from turquoise blue to deep indigo. Visitors enjoy horse riding around the rim, cycling, bird watching, and wilderness camping.",
        "history": "Designated a National Park in 1976 and declared a Ramsar Wetland of International Importance in 2007 to protect rare snow trout and musk deer habitats.",
        "daily_budget": 45.0,
        "trip_budget": 350.0,
        "risk_level": "MODERATE",
        "risk_index": 38.0,
        "hospital_name": "District Hospital Gamgadhi Mugu",
        "hospital_phone": "+977-87-460113",
        "police_name": "Rara National Park Army & Police Post",
        "police_phone": "+977-87-460100",
        "hotel_name": "Rara Village Resort & Lakeside Eco Tents",
        "hotel_price": 40.0,
        "images": [
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Bandipur Heritage Hill Station",
        "city": "Bandipur",
        "district": "Tanahun",
        "province": "Gandaki",
        "category_name": "Heritage & Temples",
        "latitude": 27.9333,
        "longitude": 84.4167,
        "altitude": "1,030m",
        "entry_fee": 0.0,
        "best_time_to_visit": "October to May (Pristine Himalayan panorama from Langtang to Dhaulagiri)",
        "short_description": "Preserved 18th-century Newari trading hilltop town with pedestrianized stone streets.",
        "description": "Bandipur is a living museum of Newari architecture. Situated on a high ridge midway between Kathmandu and Pokhara, its stone-paved main bazaar is completely vehicle-free, flanked by traditional multi-story brick houses with intricate wooden balconies, open-air cafes, and bougainvillea. Hike to Thani Mai Temple on Gurungche Hill for spectacular 180-degree Himalayan sunrises.",
        "history": "Flourished in the 1800s as a bustling mercantile hub for Newar traders after the Gorkhali conquest, trading cotton and silks between Tibet and British India.",
        "daily_budget": 35.0,
        "trip_budget": 120.0,
        "risk_level": "LOW",
        "risk_index": 16.0,
        "hospital_name": "Bandipur Hospital / Dumre Health Post",
        "hospital_phone": "+977-65-580123",
        "police_name": "Bandipur Police Post",
        "police_phone": "+977-65-580100",
        "hotel_name": "The Old Inn Bandipur Heritage Boutique",
        "hotel_price": 85.0,
        "images": [
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Upper Mustang & Lo Manthang",
        "city": "Lo Manthang",
        "district": "Mustang",
        "province": "Gandaki",
        "category_name": "Heritage & Temples",
        "latitude": 29.1822,
        "longitude": 83.9567,
        "altitude": "3,840m",
        "entry_fee": 5000.0,
        "best_time_to_visit": "May to November (Rain-shadow region, ideal during monsoon summer months)",
        "short_description": "The mystical 'Forbidden Kingdom' of walled royal palaces, red clay cliffs, and sky caves.",
        "description": "Upper Mustang is an extraordinary high-altitude desert world of ochre and red sandstone cliffs, deep canyons, ancient sky burial caves, and Tibetan Buddhist culture. The medieval walled capital of Lo Manthang features the 15th-century King's Palace, centuries-old monasteries (Jampa, Thubchen, Chode) with rare frescoes, and the colorful Tiji Festival celebrating the victory of good over evil.",
        "history": "Founded in 1380 by Ame Pal as the independent Kingdom of Lo. Remained closed to foreign travelers until 1992, preserving an intact 600-year-old Buddhist feudal culture.",
        "daily_budget": 90.0,
        "trip_budget": 1200.0,
        "risk_level": "MODERATE",
        "risk_index": 48.0,
        "hospital_name": "Jomsom Hospital / Lo Manthang Health Center",
        "hospital_phone": "+977-69-440114",
        "police_name": "Lo Manthang Armed Police Post",
        "police_phone": "+977-69-440100",
        "hotel_name": "Royal Mustang Resort & Hotel",
        "hotel_price": 95.0,
        "images": [
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Janakpurdham & Janaki Mandir",
        "city": "Janakpur",
        "district": "Dhanusha",
        "province": "Madhesh",
        "category_name": "Religious Sites",
        "latitude": 26.7271,
        "longitude": 85.9242,
        "altitude": "74m",
        "entry_fee": 50.0,
        "best_time_to_visit": "October to March (Vivaha Panchami & Chhath festivals)",
        "short_description": "Grand marble palace temple, ancient capital of Mithila Kingdom and birthplace of Goddess Sita.",
        "description": "Janakpur is the epic center of Mithila art and culture. The magnificent Janaki Mandir, also known as Nau Lakha Mandir (constructed for nine lakh rupees), is a three-storied white palace combining Mughal and Rajput architecture with 60 rooms. The town features over 70 sacred historic ponds (Dhanush Sagar, Ganga Sagar) and the vibrant Mithila Women's Art Center.",
        "history": "Ancient capital of the Videha dynasty mentioned in the Ramayana as King Janak's realm where Lord Rama broke Shiva's bow to wed Princess Sita. The present palace was built in 1910 by Queen Vrisha Bhanu of Tikamgarh.",
        "daily_budget": 25.0,
        "trip_budget": 75.0,
        "risk_level": "LOW",
        "risk_index": 18.0,
        "hospital_name": "Janakpur Zonal Hospital",
        "hospital_phone": "+977-41-520133",
        "police_name": "Janakpur Tourist Police",
        "police_phone": "+977-41-520100",
        "hotel_name": "Hotel Sita Sharan Janakpur",
        "hotel_price": 45.0,
        "images": [
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Ilam Tea Gardens & Kanyam",
        "city": "Ilam",
        "district": "Ilam",
        "province": "Koshi",
        "category_name": "Photography Spots",
        "latitude": 26.9117,
        "longitude": 87.9261,
        "altitude": "1,200m - 1,800m",
        "entry_fee": 100.0,
        "best_time_to_visit": "October to December & March to May (Lush green tea picking seasons)",
        "short_description": "Rolling emerald tea carpet hills in eastern Nepal overlooking Mt. Kanchenjunga.",
        "description": "Ilam is Nepal's premier tea plantation paradise. Endless slopes of manicured green tea bushes roll across misty hillsides at Kanyam and Mai Pokhari. Visitors can horseback ride through tea trails, taste world-renowned organic orthodox black and green teas, tour heritage processing factories, and enjoy homestays with warm Lepcha and Rai hospitality.",
        "history": "Tea cultivation began in 1863 when Col. Gajraj Singh Thapa planted the first tea saplings gifted by the Chinese Emperor, establishing Nepal's first tea estate.",
        "daily_budget": 30.0,
        "trip_budget": 110.0,
        "risk_level": "LOW",
        "risk_index": 12.0,
        "hospital_name": "Ilam District Hospital",
        "hospital_phone": "+977-27-520122",
        "police_name": "Ilam Police Station",
        "police_phone": "+977-27-520100",
        "hotel_name": "Kanyam Tea Garden Resort",
        "hotel_price": 50.0,
        "images": [
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Langtang Valley & Kyanjin Gompa",
        "city": "Rasuwa",
        "district": "Rasuwa",
        "province": "Bagmati",
        "category_name": "Nature & Trekking",
        "latitude": 28.2117,
        "longitude": 85.5683,
        "altitude": "3,870m",
        "entry_fee": 3000.0,
        "best_time_to_visit": "September to November & March to May (Alpine wild flowers and yak pastures)",
        "short_description": "The 'Valley of Glaciers' renowned for Tamang heritage, yak cheese factories, and Kyanjin Ri.",
        "description": "Langtang Valley is a stunning close-to-Kathmandu trek featuring dramatic glacial valleys, alpine pastures, and authentic Tamang-Tibetan Buddhist heritage. Passing through Syabrubesi, Lama Hotel, and the rebuilt Langtang Village, hikers reach Kyanjin Gompa beneath towering Langtang Lirung (7,227m). Summit Kyanjin Ri (4,773m) or Tserko Ri (4,984m) for panoramic Himalayan views.",
        "history": "According to legend, a Buddhist Lama pursuing a runaway yak discovered this fertile valley ('Lang' means Yak, 'Teng' means follow). Incredibly rebuilt by its resilient community after the 2015 earthquake.",
        "daily_budget": 40.0,
        "trip_budget": 320.0,
        "risk_level": "MODERATE",
        "risk_index": 42.0,
        "hospital_name": "Dhunche District Hospital Rasuwa",
        "hospital_phone": "+977-10-540115",
        "police_name": "Syabrubesi Police Checkpost",
        "police_phone": "+977-10-540100",
        "hotel_name": "Kyanjin Valley View Guest House",
        "hotel_price": 25.0,
        "images": [
            "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80"
        ]
    },
    {
        "name": "Nagarkot Himalayan Sunrise Viewpoint",
        "city": "Nagarkot",
        "district": "Bhaktapur",
        "province": "Bagmati",
        "category_name": "Photography Spots",
        "latitude": 27.7174,
        "longitude": 85.5204,
        "altitude": "2,175m",
        "entry_fee": 339.0,
        "best_time_to_visit": "October to April (Unmatched dawn sunrises illuminating 8 Himalayan ranges)",
        "short_description": "Famous hill station on Kathmandu's eastern rim with panoramic sunrise over 8 Himalayan ranges.",
        "description": "Nagarkot commands one of the broadest views of the Himalayas in the Kathmandu valley, encompassing 8 of Nepal's 13 mountain ranges including Annapurna, Manaslu, Ganesh Himal, Langtang, Jugal, Rolwaling, Mahalangur (Everest range), and Number. Pine-scented walking trails, paragliding, and luxury mountain resorts make it an ideal weekend escape.",
        "history": "Historically served as an ancient military watch-point for the Kathmandu Valley kings and later as a summer retreat for the Rana aristocracy.",
        "daily_budget": 45.0,
        "trip_budget": 135.0,
        "risk_level": "LOW",
        "risk_index": 15.0,
        "hospital_name": "Bhaktapur Hospital",
        "hospital_phone": "+977-1-6610798",
        "police_name": "Nagarkot Police Post",
        "police_phone": "+977-1-6680020",
        "hotel_name": "Club Himalaya Nagarkot & Mystic Mountain",
        "hotel_price": 120.0,
        "images": [
            "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1582650625119-3a31f8418b7d?w=1200&auto=format&fit=crop&q=80",
            "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80"
        ]
    }
]


class Command(BaseCommand):
    help = "Enrich Nepal destinations with complete datasets, 5-10 gallery images, history, budget, and risk data."

    def handle(self, *args, **options):
        # Create standard admin, staff, and tourist users if not existing
        admin_user, _ = User.objects.get_or_create(
            email="admin@tourism.gov.np",
            defaults={
                "first_name": "Nepal",
                "last_name": "Admin",
                "role": User.Role.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "is_verified": True,
            }
        )
        admin_user.set_password("Admin@12345")
        admin_user.save()

        staff_user, _ = User.objects.get_or_create(
            email="staff@tourism.gov.np",
            defaults={
                "first_name": "Tourism",
                "last_name": "Staff",
                "role": User.Role.STAFF,
                "is_staff": True,
                "is_active": True,
                "is_verified": True,
            }
        )
        staff_user.set_password("Staff@12345")
        staff_user.save()

        tourist_user, _ = User.objects.get_or_create(
            email="tourist@nepaltourism.com",
            defaults={
                "first_name": "Namaste",
                "last_name": "Traveler",
                "role": User.Role.TOURIST,
                "is_active": True,
                "is_verified": True,
            }
        )
        tourist_user.set_password("Tourist@12345")
        tourist_user.save()

        self.stdout.write(self.style.SUCCESS("Verified system users: Admin, Staff, Tourist ready."))

        # Process destinations
        for data in DESTINATIONS_DATA:
            category, _ = Category.objects.get_or_create(
                name=data["category_name"],
                defaults={"slug": slugify(data["category_name"])}
            )

            # Find existing by name or slug
            dest = Destination.objects.filter(name__icontains=data["name"][:12]).first()
            if not dest:
                base_slug = slugify(data["name"])
                dest_slug = base_slug
                c = 1
                while Destination.objects.filter(slug=dest_slug).exists():
                    dest_slug = f"{base_slug}-{c}"
                    c += 1
                dest = Destination.objects.create(
                    name=data["name"],
                    slug=dest_slug,
                    category=category,
                    city=data["city"],
                    district=data["district"],
                    province=data["province"],
                    country="Nepal",
                    latitude=Decimal(str(data["latitude"])),
                    longitude=Decimal(str(data["longitude"])),
                    altitude=data["altitude"],
                    entry_fee=Decimal(str(data["entry_fee"])),
                    best_time_to_visit=data["best_time_to_visit"],
                    short_description=data["short_description"],
                    description=data["description"],
                    history=data["history"],
                    nearest_hospital_info=f"{data['hospital_name']} (Phone: {data['hospital_phone']})",
                    nearest_police_info=f"{data['police_name']} (Phone: {data['police_phone']})",
                    nearest_hotel_info=f"{data['hotel_name']} (Est: ${data['hotel_price']}/night)",
                    status=Destination.SubmissionStatus.APPROVED,
                    is_active=True,
                    average_rating=Decimal("4.85"),
                    ratings_count=48,
                    views_count=random.randint(120, 850),
                )
            else:
                dest.name = data["name"]
                dest.category = category
                dest.city = data["city"]
                dest.district = data["district"]
                dest.province = data["province"]
                dest.country = "Nepal"
                dest.latitude = Decimal(str(data["latitude"]))
                dest.longitude = Decimal(str(data["longitude"]))
                dest.altitude = data["altitude"]
                dest.entry_fee = Decimal(str(data["entry_fee"]))
                dest.best_time_to_visit = data["best_time_to_visit"]
                dest.short_description = data["short_description"]
                dest.description = data["description"]
                dest.history = data["history"]
                dest.nearest_hospital_info = f"{data['hospital_name']} (Phone: {data['hospital_phone']})"
                dest.nearest_police_info = f"{data['police_name']} (Phone: {data['police_phone']})"
                dest.nearest_hotel_info = f"{data['hotel_name']} (Est: ${data['hotel_price']}/night)"
                dest.status = Destination.SubmissionStatus.APPROVED
                dest.is_active = True
                dest.save()

            # Ensure 5-10 images in gallery
            DestinationImage.objects.filter(destination=dest).delete()
            for idx, img_url in enumerate(data["images"]):
                DestinationImage.objects.create(
                    destination=dest,
                    external_url=img_url,
                    caption=f"{dest.name} - View {idx+1}",
                    is_cover=(idx == 0),
                    is_verified=True,
                    verification_status="approved",
                    source=DestinationImage.Source.ADMIN,
                )

            # Ensure BudgetEstimation
            BudgetEstimation.objects.update_or_create(
                destination=dest,
                defaults={
                    "district": dest.district or dest.city,
                    "province": dest.province or "Bagmati",
                    "transport_cost": Decimal(str(round(data["daily_budget"] * 0.35, 2))),
                    "food_cost_per_day": Decimal(str(round(data["daily_budget"] * 0.30, 2))),
                    "accommodation_per_night": Decimal(str(round(data["daily_budget"] * 0.35, 2))),
                    "local_transport": Decimal("5.00"),
                    "entry_fee": dest.entry_fee or Decimal("0.00"),
                    "estimated_daily_budget": Decimal(str(data["daily_budget"])),
                    "estimated_trip_budget": Decimal(str(data["trip_budget"])),
                }
            )

            def parse_alt(alt_str):
                try:
                    num_part = "".join([c for c in alt_str.split("-")[0] if c.isdigit()])
                    return int(num_part) if num_part else 1000
                except Exception:
                    return 1000

            alt_val = parse_alt(data["altitude"])

            # Ensure RiskAnalysis
            RiskAnalysis.objects.update_or_create(
                destination=dest,
                defaults={
                    "accidents": 2 if data["risk_level"] == "LOW" else 8,
                    "landslide": 1 if data["risk_level"] == "LOW" else 5,
                    "avalanche": 0 if alt_val < 3000 else 4,
                    "flood": 1,
                    "earthquake_damage": 2,
                    "hospital_count": 3,
                    "police_count": 2,
                    "fire_station_count": 1,
                    "emergency_risk": float(data["risk_index"] * 0.4),
                    "natural_disaster_risk": float(data["risk_index"] * 0.6),
                    "tourism_risk_index": float(data["risk_index"]),
                    "risk_category": data["risk_level"],
                }
            )

            # Ensure Hospital
            Hospital.objects.get_or_create(
                destination=dest,
                name=data["hospital_name"],
                defaults={
                    "address": f"{dest.city}, {dest.district}, Nepal",
                    "phone": data["hospital_phone"],
                    "latitude": dest.latitude + Decimal("0.005"),
                    "longitude": dest.longitude + Decimal("0.005"),
                    "district": dest.district or dest.city,
                }
            )

            # Ensure PoliceStation
            PoliceStation.objects.get_or_create(
                destination=dest,
                name=data["police_name"],
                defaults={
                    "address": f"{dest.city}, {dest.district}, Nepal",
                    "phone": data["police_phone"],
                    "latitude": dest.latitude - Decimal("0.003"),
                    "longitude": dest.longitude - Decimal("0.003"),
                }
            )

            # Ensure Hotel
            Hotel.objects.get_or_create(
                destination=dest,
                name=data["hotel_name"],
                defaults={
                    "address": f"Near {dest.name}, {dest.city}",
                    "price_per_night": Decimal(str(data["hotel_price"])),
                    "currency": "USD",
                    "rating": Decimal("4.8"),
                    "booking_status": Hotel.BookingStatus.AVAILABLE,
                    "booking_url": "https://www.booking.com",
                    "facilities": ["wifi", "breakfast", "hot_water", "mountain_view", "restaurant"],
                    "latitude": dest.latitude + Decimal("0.002"),
                    "longitude": dest.longitude + Decimal("0.002"),
                    "source": Hotel.Source.MANUAL,
                }
            )

            self.stdout.write(self.style.SUCCESS(f"Enriched '{dest.name}' with {len(data['images'])} images, budget, risk, hospital, police & hotel."))

        self.stdout.write(self.style.SUCCESS("All key Nepal destinations successfully enriched!"))
