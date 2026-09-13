"""
Seed comprehensive Nepal tourism categories and bulk destinations.

Creates the full taxonomy requested:
  Mountains, Hills, Valleys, Trekking, Temples, Buddhist Sites, Heritage,
  Lakes, Rivers, Waterfalls, Forests, Wildlife, Bird Watching, Caves,
  Viewpoints, Villages, Culture, Festivals, Spiritual & Wellness,
  Adventure, Air Sports, Water Sports, Agriculture, Tea & Coffee,
  Camping, Cycling, Snow & Winter, Hot Springs, Cities, Shopping,
  Food & Culinary, Scenic Routes, Eco-Tourism, Museums, Natural Wonders
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from tourist.models import Category, Destination

# All the top-level categories we want, mapping slug -> (display_name, icon_emoji, desc)
CATEGORIES = [
    ("mountains", "Mountains & Peaks", "🏔️", "Eight-thousanders and iconic Himalayan peaks including 8 of the world's 14 highest."),
    ("hills", "Hills & Hill Stations", "🏞️", "Scenic hill stations and ridges with Himalayan views."),
    ("valleys", "Valleys", "🌄", "Himalayan, river and cultural valleys."),
    ("trekking", "Trekking", "🥾", "Short, long-distance and high-altitude trekking routes."),
    ("temples", "Temples & Hindu Sites", "🛕", "Hindu temples, Shakti piths and shrines across Nepal."),
    ("buddhist-sites", "Buddhist Sites & Monasteries", "☸️", "Stupas, gompas, monasteries and Buddhist pilgrimage sites."),
    ("heritage", "UNESCO & Historical Heritage", "🏛️", "Durbar Squares, palaces, ancient settlements and UNESCO World Heritage Sites."),
    ("lakes", "Lakes", "💧", "Glacial, natural, sacred and boating lakes from Terai to Himalaya."),
    ("rivers", "Rivers & River Valleys", "🏞️", "Sacred and adventure rivers including Karnali, Gandaki, Koshi."),
    ("waterfalls", "Waterfalls", "💦", "Natural and seasonal waterfalls across the country."),
    ("forests", "Forests & Nature", "🌳", "Pine, rhododendron, sal and subtropical forests."),
    ("wildlife", "Wildlife & Safari", "🐅", "National parks, reserves and jungle safari destinations."),
    ("bird-watching", "Bird Watching", "🦜", "Prime birding areas including Koshi Tappu and Shivapuri."),
    ("caves", "Caves", "🕳️", "Natural, religious and limestone caves."),
    ("viewpoints", "Viewpoints & Lookouts", "🌅", "Sunrise, sunset and panoramic Himalayan viewpoints."),
    ("villages", "Villages & Rural Tourism", "🏘️", "Traditional, indigenous and homestay villages."),
    ("culture", "Cultural & Ethnic Tourism", "🎭", "Sherpa, Tamang, Gurung, Magar, Tharu, Newar, Rai/Limbu cultures."),
    ("festivals", "Festivals & Events", "🎉", "Hindu, Buddhist, Newar and indigenous jatras and celebrations."),
    ("spiritual-wellness", "Spiritual & Wellness", "🧘", "Meditation retreats, yoga, ashrams and wellness centres."),
    ("adventure", "Adventure Sports", "🧗", "Bungee, canyoning, rock climbing, ziplining and mountain biking."),
    ("air-sports", "Paragliding & Air Sports", "🪂", "Paragliding, ultra-light flights, mountain flights and skydiving."),
    ("water-sports", "Rafting & Water Sports", "🚣", "White-water rafting, kayaking, canoeing and fishing."),
    ("agriculture", "Agricultural & Farm Tourism", "🌾", "Rice terraces, organic farms, fruit orchards and farming experiences."),
    ("tea-coffee", "Tea & Coffee Gardens", "🍵", "Tea estates, tea factories and coffee farms in Ilam and beyond."),
    ("camping", "Camping & Glamping", "🏕️", "Lakeside, riverside, mountain and wilderness camping."),
    ("cycling", "Cycling & Mountain Biking", "🚴", "Road cycling, mountain biking trails and village cycling routes."),
    ("winter", "Snow & Winter Tourism", "❄️", "Snowfall destinations, winter trekking and frozen lakes."),
    ("hot-springs", "Hot Springs", "♨️", "Natural hot springs (tatopani) across the Himalayas."),
    ("cities", "City Tourism", "🏙️", "Kathmandu, Pokhara, Lalitpur, Bhaktapur and other urban destinations."),
    ("shopping", "Shopping & Handicrafts", "🛍️", "Thangka, pashmina, handicrafts, local markets and souvenirs."),
    ("food-culinary", "Food & Culinary Tourism", "🍛", "Newari, Thakali, Himalayan, Tharu cuisine and street food."),
    ("scenic-routes", "Road Trips & Scenic Drives", "🚗", "Mountain roads, scenic highways, jeep routes and motorcycle rides."),
    ("eco-tourism", "Eco & Community Tourism", "🌱", "Community-based tourism, conservation areas and eco-lodges."),
    ("museums", "Museums & Galleries", "🏺", "National, cultural, art and ethnographic museums."),
    ("natural-wonders", "Natural Wonders", "🗿", "Glaciers, gorges, rock formations and unique geological sites."),
    ("pilgrimage", "Pilgrimage Sites", "🕉️", "Sacred mountains, lakes, rivers and religious confluence sites."),
]


def _get_or_create_cat(slug, name, icon, desc):
    cat, created = Category.objects.get_or_create(
        slug=slug, defaults={"name": name, "icon": icon, "description": desc}
    )
    if not created and cat.name != name:
        cat.name = name
        cat.icon = icon
        cat.description = desc
        cat.save(update_fields=["name", "icon", "description"])
    return cat


# Curated lists of well-known places per category. Format:
#   (name, lat, lon, district, province, city, short_description, best_time)
MOUNTAINS = [
    ("Mount Everest (Sagarmatha)", 27.9881, 86.9250, "Solukhumbu", "Koshi", "Namche",
     "World's highest peak (8,848.86m).", "Apr-May / Oct-Nov"),
    ("Kanchenjunga", 27.7025, 88.1475, "Taplejung", "Koshi", "Taplejung",
     "Third highest peak (8,586m).", "Apr-May / Oct-Nov"),
    ("Lhotse", 27.9625, 86.9335, "Solukhumbu", "Koshi", "Namche",
     "Fourth highest peak (8,516m).", "Apr-May / Oct-Nov"),
    ("Makalu", 27.8897, 87.0888, "Sankhuwasabha", "Koshi", "Makalu",
     "Fifth highest peak (8,485m), classic pyramid shape.", "Apr-May / Oct-Nov"),
    ("Cho Oyu", 28.0946, 86.6625, "Solukhumbu", "Koshi", "Namche",
     "Sixth highest peak (8,188m) on Tibet border.", "Apr-May / Oct-Nov"),
    ("Dhaulagiri I", 28.6966, 83.4895, "Myagdi", "Gandaki", "Beni",
     "Seventh highest peak (8,167m), the White Mountain.", "Apr-May / Sep-Nov"),
    ("Manaslu", 28.5497, 84.5597, "Gorkha", "Gandaki", "Arughat",
     "Eighth highest peak (8,163m), Mountain of the Spirit.", "Sep-Nov / Mar-Apr"),
    ("Annapurna I", 28.5954, 83.8203, "Myagdi", "Gandaki", "Beni",
     "Tenth highest peak (8,091m).", "Oct-Nov / Apr"),
    ("Annapurna South", 28.5170, 83.8060, "Kaski", "Gandaki", "Pokhara",
     "Iconic 7,219m peak visible from Pokhara.", "Oct-Nov"),
    ("Machhapuchhre (Fishtail Mountain)", 28.4950, 83.9450, "Kaski", "Gandaki", "Pokhara",
     "Sacred 6,993m peak, closed to climbers.", "Oct-Nov / Mar-Apr"),
    ("Api Himal", 30.0020, 80.9330, "Darchula", "Sudurpashchim", "Darchula",
     "Westernmost 7,132m peak.", "May-Jun / Sep-Oct"),
    ("Saipal", 29.8833, 81.5000, "Bajhang", "Sudurpashchim", "Bajhang",
     "Remote 7,031m peak in far-western Nepal.", "May-Jun / Sep-Oct"),
    ("Mardi Himal", 28.4667, 83.9333, "Kaski", "Gandaki", "Pokhara",
     "Popular short trek to a 5,587m ridge.", "Oct-Nov / Mar-Apr"),
    ("Hiunchuli", 28.4800, 83.9170, "Kaski", "Gandaki", "Pokhara",
     "6,441m peak guarding Annapurna Sanctuary.", "Oct-Nov"),
    ("Ama Dablam", 27.8600, 86.8640, "Solukhumbu", "Koshi", "Namche",
     "6,812m iconic peak known as the Matterhorn of Nepal.", "Oct-Nov"),
    ("Imja Tse (Island Peak)", 27.9240, 86.9320, "Solukhumbu", "Koshi", "Chhukung",
     "Popular 6,189m trekking peak in Khumbu.", "Apr-May / Oct-Nov"),
    ("Lobuche", 27.9560, 86.8030, "Solukhumbu", "Koshi", "Lobuche",
     "6,119m trekking peak near Everest Base Camp.", "Apr-May / Oct-Nov"),
    ("Pisang Peak", 28.6430, 84.0060, "Manang", "Gandaki", "Pisang",
     "6,091m trekking peak on Annapurna Circuit.", "Apr-May / Oct-Nov"),
]
LAKES = [
    ("Begnas Lake", 28.1833, 84.0833, "Kaski", "Gandaki", "Pokhara", "Second largest lake in Pokhara valley.", "Sep-May"),
    ("Rupa Lake", 28.1667, 84.1000, "Kaski", "Gandaki", "Pokhara", "Freshwater lake known for lotus flowers.", "Sep-May"),
    ("Phoksundo Lake", 29.2167, 82.8833, "Dolpa", "Karnali", "Dunai", "Turquoise alpine lake (3,611m) in Shey Phoksundo National Park.", "May-Oct"),
    ("Gokyo Lakes", 27.9570, 86.7110, "Solukhumbu", "Koshi", "Namche", "Six sacred glacial lakes at 4,700-5,000m.", "Sep-Nov / Mar-May"),
    ("Gosaikunda", 28.0833, 85.4167, "Rasuwa", "Bagmati", "Dhunche", "Sacred alpine lake at 4,380m.", "Aug (Janai Purnima) / Sep-Oct"),
    ("Indra Sarovar (Kulekhani)", 27.5830, 85.0330, "Makwanpur", "Bagmati", "Kulekhani", "Largest man-made reservoir, popular for boating.", "Oct-Mar"),
    ("Panch Pokhari", 28.1330, 85.7330, "Sindhupalchok", "Bagmati", "Chautara", "Five sacred glacial lakes at ~4,100m.", "Mar-May / Sep-Nov"),
    ("Rara Lake", 29.5270, 82.0900, "Mugu", "Karnali", "Talcha", "Largest lake in Nepal (10.8 km²), 2,990m.", "Sep-Nov / Mar-May"),
    ("Tilicho Lake", 28.6833, 83.8500, "Manang", "Gandaki", "Chame", "One of highest lakes in the world (4,919m).", "Sep-Oct / Apr-May"),
    ("Phulchowki Lake", 27.5667, 85.3833, "Lalitpur", "Bagmati", "Godawari", "Scenic reservoir atop Phulchowki hill.", "Mar-May / Sep-Nov"),
    ("Gokyo Ri", 27.9540, 86.6960, "Solukhumbu", "Koshi", "Namche", "Viewpoint above Gokyo Lakes with Everest/Makalu views.", "Oct-Nov"),
    ("Ghodaghodi Lake", 28.7000, 80.6000, "Kailali", "Sudurpashchim", "Dhangadhi", "Ramsar wetland with rare birds and marsh crocodiles.", "Oct-Mar"),
    ("Jagadishpur Lake", 27.6000, 83.2000, "Kapilvastu", "Lumbini", "Kapilvastu", "Man-made reservoir; important bird area.", "Oct-Mar"),
    ("Mai Pokhari", 27.0167, 87.9333, "Ilam", "Koshi", "Ilam", "Ramsar wetland in middle-hills with pilgrimage significance.", "Mar-May / Sep-Nov"),
    ("Phoksundo Lake Lower", 29.2000, 82.9000, "Dolpa", "Karnali", "Dunai", "Outlet area below the main turquoise Phoksundo Lake.", "Jun-Sep"),
]
WATERFALLS = [
    ("Davis Falls (Patale Chhango)", 28.1890, 83.9570, "Kaski", "Gandaki", "Pokhara", "Famous waterfall exiting Phewa Lake into a tunnel.", "Sep-May"),
    ("Rupse Falls", 28.6833, 83.6500, "Myagdi", "Gandaki", "Beni", "300m tiered waterfall along Beni-Jomsom road.", "Sep-Nov"),
    ("Hyatung Falls", 27.1833, 87.2833, "Terhathum", "Koshi", "Basantapur", "365m waterfall in eastern Nepal.", "Sep-Nov / Mar-May"),
    ("Simba Falls", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Chandragiri", "Scenic roadside waterfall along Chandragiri hike.", "Jun-Sep"),
    ("Jalbire Jharana", 27.7833, 84.8167, "Chitwan", "Bagmati", "Jalbire", "100m natural waterfall and swimming pools.", "Sep-May"),
    ("Tindhare Jharana", 27.5167, 85.5333, "Kavrepalanchok", "Bagmati", "Panauti", "300m waterfall near Roshi village.", "Jun-Sep"),
    ("Pachal Waterfall", 28.8000, 82.2000, "Jajarkot", "Karnali", "Jajarkot", "Believed tallest in Nepal (381m+).", "Sep-Oct"),
    ("Sundarijal Waterfall", 27.7667, 85.4333, "Kathmandu", "Bagmati", "Sundarijal", "Popular waterfall and hiking spot near Kathmandu.", "Jun-Sep"),
    ("Manakamana Cable Car Waterfall", 27.8750, 84.5780, "Gorkha", "Gandaki", "Kurintar", "Waterfall visible from Manakamana cable car.", "Jun-Sep"),
    ("Chhahara Jharana (Gulmi)", 28.0500, 83.3000, "Gulmi", "Lumbini", "Tamghas", "Scenic waterfall in mid-hills.", "Jun-Sep"),
    ("Bhotekoshi Waterfall", 27.9000, 85.9100, "Sindhupalchok", "Bagmati", "Kodari", "Cascade alongside Araniko Highway near Tibet border.", "Jun-Sep"),
    ("Purandhara Waterfall", 28.0300, 82.4000, "Dang", "Lumbini", "Ghorahi", "Largest waterfall in Dang district.", "Jun-Sep"),
    ("Rupse Chhahara", 28.6800, 83.6500, "Myagdi", "Gandaki", "Beni", "Misty multi-tiered waterfall with Kali Gandaki views.", "Jul-Oct"),
    ("Lamo Jharana (Sindhuli)", 27.2500, 85.9000, "Sindhuli", "Bagmati", "Sindhulimadi", "Longest waterfall in Sindhuli district.", "Jun-Sep"),
    ("Aina Pahiro Jharana", 28.2000, 84.0000, "Kaski", "Gandaki", "Pokhara", "Reflective cliff waterfall near Pokhara.", "Jun-Sep"),
]
TREKKING = [
    ("Everest Base Camp Trek", 28.0025, 86.8525, "Solukhumbu", "Koshi", "Lukla", "Iconic trek to 5,364m EBC via Namche Bazaar.", "Mar-May / Oct-Dec"),
    ("Annapurna Base Camp (ABC)", 28.5333, 83.8833, "Kaski", "Gandaki", "Ghandruk", "Trek to 4,130m base camp in Annapurna Sanctuary.", "Oct-Nov / Mar-Apr"),
    ("Annapurna Circuit", 28.8000, 83.9333, "Manang", "Gandaki", "Chame", "160-230km circuit crossing Thorong La (5,416m).", "Oct-Nov / Apr"),
    ("Langtang Valley Trek", 28.2167, 85.5333, "Rasuwa", "Bagmati", "Syabrubesi", "Beautiful alpine valley trek close to Kathmandu.", "Mar-May / Oct-Dec"),
    ("Helambu Trek", 28.0667, 85.5167, "Sindhupalchok", "Bagmati", "Sundarijal", "Scenic Tamang heritage trek NE of Kathmandu.", "Mar-May / Oct-Dec"),
    ("Upper Mustang Trek", 29.1833, 83.9500, "Mustang", "Gandaki", "Jomsom", "Fenced ancient Tibetan kingdom of Lo (restricted).", "Mar-May / Oct-Nov"),
    ("Ghorepani Poon Hill Trek", 28.4000, 83.7333, "Myagdi", "Gandaki", "Ghorepani", "Short trek to 3,210m Poon Hill sunrise viewpoint.", "Oct-Nov / Mar-Apr"),
    ("Manaslu Circuit Trek", 28.5400, 84.5600, "Gorkha", "Gandaki", "Arughat", "Restricted trek around Mount Manaslu, crossing Larkya La.", "Sep-Nov / Mar-Apr"),
    ("Kanchenjunga Base Camp Trek", 27.7100, 88.0000, "Taplejung", "Koshi", "Taplejung", "Remote trek to north and south base camps of Kanchenjunga.", "Apr-May / Oct-Nov"),
    ("Makalu Base Camp Trek", 27.8000, 87.1000, "Sankhuwasabha", "Koshi", "Tumlingtar", "Remote trek into Makalu Barun valley.", "Apr-May / Oct-Nov"),
    ("Upper Dolpo Trek", 29.1000, 82.9000, "Dolpa", "Karnali", "Dunai", "Remote trans-Himalayan trek to Shey Gompa and Phoksundo.", "May-Sep"),
    ("Rara Lake Trek", 29.5200, 82.1000, "Mugu", "Karnali", "Jumla", "Trek to Nepal's largest lake through far-western hills.", "Sep-Nov / Mar-May"),
    ("Gosaikunda Trek", 28.1000, 85.4100, "Rasuwa", "Bagmati", "Dhunche", "Sacred lake trek via Lauribina La (4,610m).", "Aug-Oct / Mar-May"),
    ("Mardi Himal Trek", 28.4667, 83.9333, "Kaski", "Gandaki", "Pokhara", "Short trek to 5,587m ridge with Fishtail views.", "Oct-Nov / Mar-Apr"),
    ("Poon Hill-Ghorepani-Ghandruk Trek", 28.4000, 83.7500, "Myagdi", "Gandaki", "Nayapul", "Classic 5-day Gurung cultural trek.", "Oct-Nov / Mar-Apr"),
    ("Tsum Valley Trek", 28.4800, 84.7000, "Gorkha", "Gandaki", "Arughat", "Sacred hidden valley near Manaslu with ancient gompas.", "Mar-May / Oct-Nov"),
    ("Nar Phu Trek", 28.7500, 84.1000, "Manang", "Gandaki", "Chame", "Restricted remote valley trek on Annapurna Circuit.", "Mar-May / Sep-Nov"),
    ("Tamang Heritage Trail", 28.1000, 85.3000, "Rasuwa", "Bagmati", "Syabrubesi", "Cultural trek through Tamang villages near Langtang.", "Mar-May / Oct-Dec"),
]
TEMPLES = [
    ("Pashupatinath Temple", 27.7100, 85.3480, "Kathmandu", "Bagmati", "Kathmandu", "Sacred Hindu temple on Bagmati River; UNESCO.", "Feb-Mar (Shivaratri)"),
    ("Janaki Mandir (Janakpur)", 26.7280, 85.9250, "Dhanusha", "Madhesh", "Janakpur", "19th-century marble temple to Sita.", "Oct-Mar / Vivaha Panchami"),
    ("Manakamana Temple", 27.8833, 84.5833, "Gorkha", "Gandaki", "Kurintar", "Wish-fulfilling Bhagwati temple accessible by cable car.", "Oct-Mar / Dashain"),
    ("Muktinath Temple", 28.8167, 83.8667, "Mustang", "Gandaki", "Ranipauwa", "Sacred Vishnu temple at 3,762m with 108 water spouts.", "Mar-May / Sep-Oct"),
    ("Dakshinkali Temple", 27.6000, 85.2500, "Kathmandu", "Bagmati", "Pharping", "Famous Kali temple on southern valley rim.", "Oct-Mar / Dashain"),
    ("Guhyeshwari Temple", 27.7110, 85.3480, "Kathmandu", "Bagmati", "Gaushala", "One of 51 Shakti Peeths near Pashupatinath.", "Feb-Mar / Sep-Oct"),
    ("Bindhyabasini Temple (Pokhara)", 28.2333, 83.9833, "Kaski", "Gandaki", "Pokhara", "Popular Shaktipeeth atop a hill in old Pokhara.", "Oct-Mar"),
    ("Changunarayan Temple", 27.7080, 85.4260, "Bhaktapur", "Bagmati", "Bhaktapur", "Oldest datable temple in Nepal (325 AD), UNESCO.", "Oct-Mar"),
    ("Nyatapola Temple (Bhaktapur)", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Tallest pagoda in Nepal (30m, 5 tiers), 1702.", "Oct-Apr / Bisket Jatra"),
    ("Krishna Mandir (Patan)", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan", "17th-century stone Shikhara Krishna temple.", "Krishna Janmashtami"),
    ("Kumbheshwar Temple", 27.6750, 85.3240, "Lalitpur", "Bagmati", "Patan", "14th-century five-story Shiva temple with natural spring.", "Janai Purnima"),
    ("Taleju Bhawani Temple", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu", "Royal deity of Malla kings in Hanuman Dhoka.", "Dashain only"),
    ("Budhanilkantha Temple", 27.7730, 85.3570, "Kathmandu", "Bagmati", "Budhanilkantha", "Reclining Vishnu statue in a pool.", "Oct-Mar"),
    ("Pathibhara Devi", 27.4167, 87.7333, "Taplejung", "Koshi", "Taplejung", "Sacred hilltop shrine at 3,794m in far east.", "Mar-Jun / Sep-Nov"),
    ("Gorkha Durbar & Gorakhnath", 28.0000, 84.6333, "Gorkha", "Gandaki", "Gorkha", "Historic palace fort and Gorakhnath cave temple.", "Oct-Apr"),
    ("Doleshwor Mahadev", 27.6500, 85.4500, "Bhaktapur", "Bagmati", "Sipadol", "Believed to be the head portion of Kedarnath.", "Jun-Aug"),
    ("Siddha Gufa Temple (Bimalnagar)", 27.8833, 84.4000, "Tanahun", "Gandaki", "Bandipur", "Sacred cave with stalactites near Bandipur.", "Oct-Apr"),
    ("Swargadwari", 28.1833, 82.6833, "Pyuthan", "Lumbini", "Pyuthan", "Hilltop Hindu pilgrimage founded by Mahaprabhu Swami.", "Oct-Apr"),
    ("Devghat Dham", 27.7500, 84.4167, "Chitwan", "Bagmati", "Narayangarh", "Sacred confluence of Kali Gandaki and Trishuli.", "Maghe Sankranti"),
    ("Halesi Mahadev (Maratika Cave)", 27.2000, 86.6167, "Khotang", "Koshi", "Halesi", "Sacred cave revered by Hindus and Buddhists.", "Mar-May / Sep-Oct"),
]
BUDDHIST = [
    ("Boudhanath Stupa", 27.7210, 85.3620, "Kathmandu", "Bagmati", "Boudha", "Largest stupa in Nepal; UNESCO World Heritage.", "Oct-Mar"),
    ("Swayambhunath Stupa (Monkey Temple)", 27.7140, 85.2900, "Kathmandu", "Bagmati", "Kathmandu", "2,000-year-old hilltop stupa; UNESCO.", "Oct-Mar"),
    ("Lumbini (Maya Devi Temple)", 27.4690, 83.2740, "Rupandehi", "Lumbini", "Lumbini", "Birthplace of Buddha; UNESCO World Heritage.", "Oct-Mar"),
    ("World Peace Pagoda (Pokhara)", 28.2000, 83.9500, "Kaski", "Gandaki", "Pokhara", "White Buddhist stupa south of Phewa Lake.", "Oct-Mar"),
    ("Tengboche Monastery", 27.8350, 86.7680, "Solukhumbu", "Koshi", "Namche", "Largest gompa in Khumbu (3,867m); Mani Rimdu.", "Oct-Nov / Mar-Apr"),
    ("Khumjung Gompa", 27.8250, 86.7200, "Solukhumbu", "Koshi", "Namche", "Ancient monastery said to hold a yeti scalp.", "Oct-Nov / Mar"),
    ("Kopan Monastery", 27.7333, 85.3667, "Kathmandu", "Bagmati", "Boudha", "Tibetan Buddhist monastery with meditation courses.", "Oct-May"),
    ("Thrangu Tashi Yangtse (Namo Buddha)", 27.5833, 85.5667, "Kavrepalanchok", "Bagmati", "Panauti", "Legendary site of Buddha's self-sacrifice to a tigress.", "Oct-Mar"),
    ("Maratika Cave (Halesi)", 27.2000, 86.6167, "Khotang", "Koshi", "Halesi", "Sacred Padmasambhava pilgrimage cave.", "Mar-May / Sep-Oct"),
    ("Lo Manthang Gompas", 29.1833, 83.9560, "Mustang", "Gandaki", "Lo Manthang", "15th-century walled capital gompas of Upper Mustang.", "Mar-May / Oct-Nov"),
    ("Chhairo Gompa", 28.8400, 83.7300, "Mustang", "Gandaki", "Jomsom", "Restored 16th-century Nyingma gompa in Lower Mustang.", "Mar-May / Oct-Nov"),
    ("Braga Gompa", 28.6500, 83.9800, "Manang", "Gandaki", "Braga", "One of the oldest gompas in Manang with ancient murals.", "Sep-Oct"),
    ("Rinchenling Gompa (Dolpo)", 29.1600, 82.9100, "Dolpa", "Karnali", "Dunai", "Ancient Bon/Buddhist monastery in Upper Dolpo.", "May-Sep"),
    ("Shey Gompa", 29.0833, 82.8667, "Dolpa", "Karnali", "Dunai", "11th-century Crystal Mountain monastery.", "May-Sep"),
    ("Pema Namding Monastery", 27.6300, 86.6000, "Solukhumbu", "Koshi", "Phaplu", "Prominent Nyingma monastery in lower Khumbu.", "Oct-Nov / Apr"),
    ("Namobuddha Thrangu Monastery", 27.5800, 85.5700, "Kavrepalanchok", "Bagmati", "Panauti", "Large monastic complex at Namo Buddha site.", "Oct-Mar"),
    ("Kagbeni Gompa", 28.8400, 83.7400, "Mustang", "Gandaki", "Kagbeni", "Medieval red-walled village gompa; Kali Gandaki confluence.", "Mar-May / Sep-Nov"),
    ("Thubchen Gompa (Lo Manthang)", 29.1820, 83.9550, "Mustang", "Gandaki", "Lo Manthang", "15th-century monastery with exquisite mandalas.", "Mar-May / Oct-Nov"),
]
HERITAGE = [
    ("Kathmandu Durbar Square (Hanuman Dhoka)", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu", "Royal Malla/Shah palace complex; UNESCO.", "All year"),
    ("Patan Durbar Square", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan", "Malla-era royal square with Krishna Mandir; UNESCO.", "All year"),
    ("Bhaktapur Durbar Square", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Best-preserved Malla city with Nyatapola; UNESCO.", "All year"),
    ("Rani Mahal (Palpa)", 27.8333, 83.5500, "Palpa", "Lumbini", "Tansen", "\"Taj Mahal of Nepal\" palace on Kali Gandaki.", "Oct-Apr"),
    ("Nuwakot Saat Talle Durbar", 27.9167, 85.1667, "Nuwakot", "Bagmati", "Nuwakot", "Seven-storied hilltop palace of Prithvi Narayan Shah.", "Oct-Apr"),
    ("Gorkha Durbar", 28.0000, 84.6333, "Gorkha", "Gandaki", "Gorkha", "Hilltop palace fort; birthplace of modern Nepal.", "Oct-Apr"),
    ("Tansen Bazaar", 27.8667, 83.5500, "Palpa", "Lumbini", "Tansen", "Historic Newari hill town with traditional architecture.", "Sep-May"),
    ("Bandipur", 27.9333, 84.4167, "Tanahun", "Gandaki", "Bandipur", "Preserved 18th-century Newari trading village.", "Oct-Apr"),
    ("Kirtipur", 27.6710, 85.2780, "Kathmandu", "Bagmati", "Kirtipur", "Historic hilltop Newar town; Bagh Bhairab, Chilancho Stupa.", "Oct-Mar"),
    ("Panauti", 27.5833, 85.5167, "Kavrepalanchok", "Bagmati", "Panauti", "Ancient Newari trading town; Indreshwar Mahadev.", "Oct-Mar / Makar Mela"),
    ("Bungamati", 27.6250, 85.3000, "Lalitpur", "Bagmati", "Bungamati", "Medieval Newar village, home of Rato Machhindranath.", "Oct-Apr"),
    ("Khokana", 27.6400, 85.2900, "Lalitpur", "Bagmati", "Khokana", "Traditional mustard-oil milling Newari village.", "Oct-Apr"),
    ("Narayanhiti Palace Museum", 27.7180, 85.3210, "Kathmandu", "Bagmati", "Durbar Marg", "Former royal palace turned museum after 2008.", "Thu-Mon"),
    ("Lumbini Sacred Garden", 27.4690, 83.2750, "Rupandehi", "Lumbini", "Lumbini", "UNESCO site with Maya Devi temple and eternal flame.", "Oct-Mar"),
    ("Changu Narayan", 27.7080, 85.4260, "Bhaktapur", "Bagmati", "Bhaktapur", "Oldest Hindu temple in the Kathmandu Valley; UNESCO.", "Oct-Mar"),
    ("Bhaktapur 55-Window Palace", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "15th-century palace with master woodcarving.", "Oct-Apr"),
    ("Golden Gate (Bhaktapur)", 27.6720, 85.4300, "Bhaktapur", "Bagmati", "Bhaktapur", "Repousse gilt copper gate to 55-Window Palace.", "Oct-Apr"),
    ("Kakrebihar (Surkhet)", 28.6000, 81.6167, "Surkhet", "Karnali", "Birendranagar", "12th-century stone temple ruins in a park.", "Oct-Mar"),
    ("Sindhuli Gadhi", 27.2700, 85.9300, "Sindhuli", "Bagmati", "Sindhulimadi", "Historic Gorkha victory fort over British forces.", "Oct-Apr"),
    ("Makwanpur Gadhi", 27.4500, 85.1000, "Makwanpur", "Bagmati", "Hetauda", "Historic fort crucial to Nepal unification.", "Oct-Apr"),
]
VIEWPOINTS = [
    ("Sarangkot Viewpoint", 28.2500, 83.9500, "Kaski", "Gandaki", "Pokhara", "1,600m hilltop above Pokhara; sunrise over Annapurna.", "Oct-Nov / Mar-Apr"),
    ("Nagarkot View Tower", 27.7167, 85.5167, "Bhaktapur", "Bagmati", "Nagarkot", "2,175m hill station for Himalayan sunrise views.", "Oct-Mar"),
    ("Phulchowki Hill", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari", "Highest hill (2,782m) around Kathmandu Valley.", "Oct-Mar"),
    ("Chandragiri Hill", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Thankot", "2,551m hill with cable car and Bhaleshwor temple.", "Oct-Mar"),
    ("Shree Antu Viewpoint", 26.8833, 88.0833, "Ilam", "Koshi", "Ilam", "Sunrise over Kanchenjunga and tea gardens.", "Oct-Apr"),
    ("Kala Patthar", 27.9940, 86.8290, "Solukhumbu", "Koshi", "Gorakshep", "5,644m Everest viewpoint landmark.", "Oct-Nov / Apr"),
    ("Poon Hill", 28.4000, 83.7333, "Myagdi", "Gandaki", "Ghorepani", "Famous 3,210m sunrise viewpoint on Ghorepani trek.", "Oct-Nov / Mar-Apr"),
    ("Gokyo Ri", 27.9540, 86.6960, "Solukhumbu", "Koshi", "Gokyo", "5,357m viewpoint above Gokyo Lakes.", "Oct-Nov"),
    ("Kakani", 27.8167, 85.2667, "Nuwakot", "Bagmati", "Kakani", "2,030m hill station with trout farms and Himalayan views.", "Oct-Mar"),
    ("Daman", 27.6000, 85.0667, "Makwanpur", "Bagmati", "Daman", "Mountain viewpoint claiming broadest Himalayan panorama.", "Oct-Mar"),
    ("Siraichuli (Chitwan)", 27.7500, 84.6667, "Chitwan", "Bagmati", "Kaule", "1,945m highest point of Chitwan district.", "Oct-Mar"),
    ("Dhulikhel View Tower", 27.6167, 85.5500, "Kavrepalanchok", "Bagmati", "Dhulikhel", "Hilltop town with Himalayan panoramas and Newari culture.", "Oct-Mar"),
    ("Nagarjun Forest View Tower", 27.7400, 85.2700, "Kathmandu", "Bagmati", "Nagarjun", "2,096m forested ridge viewpoint above Kathmandu.", "Oct-Apr"),
    ("Tansen Shreenagar Hill", 27.8700, 83.5400, "Palpa", "Lumbini", "Tansen", "Ridge walk above Tansen with Himalayan and Madi valley views.", "Sep-May"),
    ("Jhorsingh Viewpoint (Kanyam)", 26.8333, 88.0167, "Ilam", "Koshi", "Kanyam", "Tea garden viewpoint overlooking Ilam hills.", "Mar-Nov"),
]
NATIONAL_PARKS_WILDLIFE = [
    ("Chitwan National Park (Sauraha)", 27.5730, 84.4970, "Chitwan", "Bagmati", "Sauraha", "UNESCO World Heritage; one-horned rhino, Bengal tiger.", "Oct-Mar"),
    ("Bardiya National Park", 28.3833, 81.5000, "Bardiya", "Lumbini", "Thakurdwara", "Largest Terai national park; tiger and wild elephants.", "Oct-Mar"),
    ("Sagarmatha National Park", 27.9500, 86.7500, "Solukhumbu", "Koshi", "Namche", "UNESCO park around Everest; snow leopard, red panda.", "Oct-Nov / Mar-May"),
    ("Langtang National Park", 28.1667, 85.5000, "Rasuwa", "Bagmati", "Syabrubesi", "First Himalayan national park; red panda, musk deer.", "Mar-May / Oct-Dec"),
    ("Shey Phoksundo National Park", 29.2167, 82.9333, "Dolpa", "Karnali", "Dunai", "Largest national park (3,555 km²); snow leopard, Phoksundo.", "May-Oct"),
    ("Rara National Park", 29.5333, 82.0500, "Mugu", "Karnali", "Talcha", "Smallest national park around pristine Rara Lake.", "Sep-Nov / Mar-May"),
    ("Khaptad National Park", 29.2667, 80.1667, "Doti", "Sudurpashchim", "Silgadhi", "Mid-western plateau at 3,000m; rhododendron forests.", "Mar-May / Oct-Nov"),
    ("Makalu Barun National Park", 27.7500, 87.1667, "Sankhuwasabha", "Koshi", "Tumlingtar", "Remote eastern park around Makalu; incredible biodiversity.", "Apr-May / Oct-Nov"),
    ("Shivapuri Nagarjun National Park", 27.8000, 85.4000, "Kathmandu", "Bagmati", "Budhanilkantha", "Northern ridge of Kathmandu Valley; hiking, Bagdwar.", "Oct-Apr"),
    ("Parsa National Park", 27.3330, 84.8330, "Parsa", "Madhesh", "Birgunj", "Eastern extension of Chitwan; tiger, elephant, gaur.", "Nov-Mar"),
    ("Banke National Park", 28.0833, 81.8833, "Banke", "Lumbini", "Nepalgunj", "Protected tiger habitat connected to Bardiya.", "Oct-Mar"),
    ("Shuklaphanta National Park", 28.8500, 80.2167, "Kanchanpur", "Sudurpashchim", "Mahendranagar", "Grassland reserve; largest swamp deer herd in world.", "Nov-Jun"),
    ("Koshi Tappu Wildlife Reserve", 26.6500, 87.0000, "Sunsari", "Koshi", "Itahari", "Ramsar wetland; wild water buffalo, 500+ bird species.", "Oct-Mar"),
    ("Annapurna Conservation Area (ACAP)", 28.6000, 83.9000, "Manang", "Gandaki", "Chame", "Largest protected area (7,629 km²); Annapurna Circuit.", "Oct-Nov / Mar-May"),
    ("Manaslu Conservation Area", 28.5500, 84.5600, "Gorkha", "Gandaki", "Arughat", "Around Mount Manaslu; Tsum Valley, restricted trek.", "Oct-Nov / Mar-Apr"),
    ("Kanchenjunga Conservation Area", 27.7000, 88.0000, "Taplejung", "Koshi", "Taplejung", "Easternmost conservation around Kanchenjunga massif.", "Apr-May / Oct-Nov"),
    ("Api Nampa Conservation Area", 29.9500, 80.8500, "Darchula", "Sudurpashchim", "Darchula", "Far-western conservation area around Api and Nampa.", "May-Jun / Sep-Oct"),
    ("Gaurishankar Conservation Area", 27.8800, 86.1600, "Dolakha", "Bagmati", "Charikot", "Conservation area around Gaurishankar peak.", "Mar-May / Oct-Nov"),
    ("Krishnasar Conservation Area", 29.5000, 82.2000, "Mugu", "Karnali", "Gamgadhi", "Established to protect endangered Tibetan antelope (Chiru).", "Sep-May"),
]
CAVES = [
    ("Mahendra Cave (Pokhara)", 28.2167, 83.9667, "Kaski", "Gandaki", "Pokhara", "Famous limestone cave with stalactites near Pokhara.", "Sep-May"),
    ("Bat Cave (Chamere Gufa)", 28.2167, 83.9667, "Kaski", "Gandaki", "Pokhara", "Limestone cave inhabited by thousands of bats.", "Sep-May"),
    ("Gupteshwor Mahadev Cave", 28.1890, 83.9570, "Kaski", "Gandaki", "Pokhara", "Sacred cave across from Davis Falls with Shiva lingam.", "Sep-May"),
    ("Siddha Cave (Siddha Gufa)", 27.8833, 84.4000, "Tanahun", "Gandaki", "Bandipur", "Largest cave in Nepal (437m deep).", "Oct-Apr"),
    ("Halesi Mahadev Cave", 27.2000, 86.6167, "Khotang", "Koshi", "Halesi", "Sacred cave (Maratika) for Hindus and Buddhists.", "Mar-May / Sep-Oct"),
    ("Chobhar Gorge Caves", 27.6500, 85.2800, "Kathmandu", "Bagmati", "Chobhar", "Limestone caves near the Bagmati gorge.", "Oct-Mar"),
    ("Maratika (Halesi) Buddhist Cave", 27.2000, 86.6150, "Khotang", "Koshi", "Halesi", "Padmasambhava meditation caves and pilgrimage.", "Mar-May / Sep-Oct"),
    ("Bagdwara Cave (Shivapuri)", 27.8050, 85.4100, "Kathmandu", "Bagmati", "Shivapuri", "Source of the Bagmati River; sacred Hindu cave.", "Oct-Apr"),
    ("Mahadev Parbat Cave", 28.6500, 82.2000, "Jajarkot", "Karnali", "Jajarkot", "Sacred Shiva cave in western hills.", "Sep-May"),
    ("Akhanda Dhuni Cave (Daman)", 27.6000, 85.0700, "Makwanpur", "Bagmati", "Daman", "Sacred eternal fire meditation cave.", "Oct-Mar"),
    ("Siddha Cave (Dolakha)", 27.7833, 86.0800, "Dolakha", "Bagmati", "Charikot", "Mystic meditation cave in Dolakha hills.", "Oct-Apr"),
    ("Dakshinkali Cave", 27.6000, 85.2500, "Kathmandu", "Bagmati", "Pharping", "Asura Cave and meditation caves near Pharping.", "Oct-Mar"),
    ("Gorakhnath Cave (Gorkha)", 28.0000, 84.6300, "Gorkha", "Gandaki", "Gorkha", "Cave of saint Gorakhnath near Gorkha Durbar.", "Oct-Apr"),
    ("Bhairav Kunda Cave", 28.1300, 85.7300, "Sindhupalchok", "Bagmati", "Chautara", "Cave system near Panch Pokhari.", "Sep-Nov"),
    ("Chamere Cave (Bandipur)", 27.9300, 84.4100, "Tanahun", "Gandaki", "Bandipur", "Bat cave on Siddha Gufa hike trail.", "Oct-Apr"),
]
MUSEUMS = [
    ("National Museum of Nepal (Chhauni)", 27.7050, 85.2880, "Kathmandu", "Bagmati", "Chhauni", "Oldest museum; historical weapons, art, natural history.", "All year"),
    ("Patan Museum", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan", "Renowned museum of sacred art in old Malla palace.", "All year"),
    ("Narayanhiti Palace Museum", 27.7180, 85.3210, "Kathmandu", "Bagmati", "Durbar Marg", "Former royal palace turned museum.", "Thu-Mon"),
    ("International Mountain Museum (Pokhara)", 28.2000, 83.9667, "Kaski", "Gandaki", "Pokhara", "Mountaineering history, Himalayan culture and 8000ers.", "All year"),
    ("Gurkha Memorial Museum", 28.2333, 83.9833, "Kaski", "Gandaki", "Pokhara", "Museum of the Brigade of Gurkhas.", "All year"),
    ("Natural History Museum (Swayambhu)", 27.7140, 85.2920, "Kathmandu", "Bagmati", "Swayambhu", "Nepal wildlife, fossils, butterflies and specimens.", "Sun-Fri"),
    ("Bhaktapur National Art Museum", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Paubha painting and Malla-era artifacts.", "All year"),
    ("Tribhuvan Museum (Hanuman Dhoka)", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu", "Memorial museum to King Tribhuvan.", "Sun-Fri"),
    ("Taragaon Museum (Boudha)", 27.7200, 85.3580, "Kathmandu", "Bagmati", "Boudha", "Modern cultural heritage archive in a 70s modernist building.", "All year"),
    ("Annapurna Butterfly Museum", 28.2200, 83.9700, "Kaski", "Gandaki", "Pokhara", "Butterfly specimens from the Annapurna region.", "All year"),
    ("Nepal Art Council Gallery", 27.7100, 85.3200, "Kathmandu", "Bagmati", "Baber Mahal", "Contemporary Nepali art exhibitions.", "All year"),
    ("NAFA Gallery (Nepal Academy)", 27.7000, 85.3200, "Kathmandu", "Bagmati", "Naxal", "National fine arts academy exhibitions.", "Sun-Fri"),
    ("Pokhara Regional Museum", 28.2100, 83.9700, "Kaski", "Gandaki", "Pokhara", "Ethnographic and natural history of western Nepal.", "All year"),
    ("Dharan Museum (BP Koirala)", 26.8100, 87.2800, "Sunsari", "Koshi", "Dharan", "Memorial museum to BP Koirala.", "All year"),
    ("Kapilvastu Museum", 27.5800, 83.0700, "Kapilvastu", "Lumbini", "Taulihawa", "Archaeological finds from ancient Shakya kingdom.", "Sun-Fri"),
    ("Lumbini Museum", 27.4700, 83.2760, "Rupandehi", "Lumbini", "Lumbini", "Buddhist art and artefacts from Lumbini excavations.", "All year"),
]
TEA_COFFEE = [
    ("Ilam Tea Gardens (Kanyam)", 26.8333, 88.0167, "Ilam", "Koshi", "Kanyam", "\"Queen of Ilam\" — most visited tea garden.", "Mar-Nov"),
    ("Shree Antu Tea Estates", 26.8833, 88.0833, "Ilam", "Koshi", "Shree Antu", "Tea estates with famous sunrise viewpoint.", "Oct-Apr"),
    ("Ilam Bazaar Tea Estates", 26.9167, 87.9167, "Ilam", "Koshi", "Ilam", "Rolling green tea estates; tea factory visits.", "Mar-Nov"),
    ("Jhapa Tea Gardens", 26.6000, 87.9500, "Jhapa", "Koshi", "Birtamod", "Lowland Terai tea estates (Camellia sinensis).", "All year"),
    ("Dhankuta Tea Gardens", 26.9833, 87.3333, "Dhankuta", "Koshi", "Dhankuta", "Himalayan organic tea estates in eastern hills.", "Mar-Nov"),
    ("Sindhupalchok Coffee Farms", 27.8500, 85.8500, "Sindhupalchok", "Bagmati", "Bahrabise", "High-altitude organic Arabica coffee.", "Nov-Feb"),
    ("Gulmi Coffee Farms", 28.0700, 83.2700, "Gulmi", "Lumbini", "Tamghas", "Premium Arabica coffee district in mid-western hills.", "Nov-Feb"),
    ("Palpa Coffee Farms", 27.8600, 83.5500, "Palpa", "Lumbini", "Tansen", "Organic high-altitude coffee in Palpa hills.", "Nov-Feb"),
    ("Lalitpur Coffee Patches", 27.6000, 85.3300, "Lalitpur", "Bagmati", "Godawari", "Suburban coffee growing at Godawari.", "Nov-Feb"),
    ("Nuwakot Coffee Farms", 27.9000, 85.2000, "Nuwakot", "Bagmati", "Bidur", "Mid-hill organic coffee with Trishuli views.", "Nov-Feb"),
    ("Syangja Orange & Coffee", 28.0000, 83.9000, "Syangja", "Gandaki", "Putalibazar", "Mixed orange orchards and coffee farms.", "Nov-Mar"),
    ("Chitlang Organic Farms", 27.6300, 85.1700, "Makwanpur", "Bagmati", "Chitlang", "Vegetable seed farms, goat cheese, organic produce.", "Feb-May"),
    ("Rasuwa Apple Orchards", 28.1000, 85.4000, "Rasuwa", "Bagmati", "Dhunche", "Himalayan apple orchards in Langtang region.", "Sep-Nov"),
    ("Mustang Apple Orchards", 28.8500, 83.7500, "Mustang", "Gandaki", "Marpha", "World-famous Marpha apples, brandy and orchards.", "Aug-Oct"),
    ("Humla Apple & Barley", 30.0000, 81.8000, "Humla", "Karnali", "Simikot", "High-altitude apple and traditional barley cultivation.", "Aug-Oct"),
]
HOT_SPRINGS = [
    ("Tatopani Hot Spring (Myagdi)", 28.5833, 83.7000, "Myagdi", "Gandaki", "Tatopani", "Natural hot springs on the Annapurna Circuit.", "Oct-May"),
    ("Tatopani Hot Spring (Kodari)", 27.9667, 85.9667, "Sindhupalchok", "Bagmati", "Kodari", "Natural hot springs near the Nepal-China border.", "Oct-May"),
    ("Chumling Hot Spring", 28.4300, 84.6000, "Gorkha", "Gandaki", "Arughat", "Hot springs on the Manaslu Circuit trek.", "Oct-May"),
    ("Singa Tatopani", 28.9500, 83.7500, "Mustang", "Gandaki", "Jomsom", "Natural hot spring in Lower Mustang.", "Mar-May / Sep-Nov"),
    ("Bhurung Tatopani", 28.5800, 83.6900, "Myagdi", "Gandaki", "Bhurung", "Popular hot spring pools near Beni.", "Oct-May"),
    ("Surkhot Tatopani (Darchula)", 29.8500, 80.7000, "Darchula", "Sudurpashchim", "Darchula", "Remote hot springs in far-western Nepal.", "Apr-Oct"),
    ("Ghunsa Hot Spring", 27.6300, 87.8500, "Taplejung", "Koshi", "Ghunsa", "Hot springs on the Kanchenjunga trek.", "Mar-May / Oct-Nov"),
    ("Jomsom Hot Springs", 28.7833, 83.7333, "Mustang", "Gandaki", "Jomsom", "Hot water springs near Jomsom airport.", "Mar-May / Sep-Nov"),
    ("Dhanachauri Hot Spring", 28.5000, 83.6500, "Parbat", "Gandaki", "Kusma", "Natural hot springs on the Kali Gandaki.", "Oct-May"),
    ("Lomangthang Hot Spring", 29.2200, 83.9500, "Mustang", "Gandaki", "Lo Manthang", "Remote hot spring in Upper Mustang.", "May-Oct"),
]
ADVENTURE = [
    ("The Last Resort (Bungee at Bhote Koshi)", 27.8833, 85.9167, "Sindhupalchok", "Bagmati", "Barabise", "160m bungee over Bhote Koshi gorge.", "Oct-May"),
    ("HighGround Adventures (Bungee Pokhara)", 28.2000, 83.9800, "Kaski", "Gandaki", "Pokhara", "70m tower bungee near Hemja.", "Oct-May"),
    ("Kushma Bungee & Swing", 28.2200, 83.7000, "Parbat", "Gandaki", "Kushma", "World's second-longest bungee at 228m over Kali Gandaki.", "Oct-May"),
    ("Canyoning at Jalbire", 27.7833, 84.8167, "Chitwan", "Bagmati", "Jalbire", "Waterfall canyoning and slides near Mugling.", "Sep-May"),
    ("Sundarijal Canyoning", 27.7667, 85.4333, "Kathmandu", "Bagmati", "Sundarijal", "Canyoning near Kathmandu.", "Sep-May"),
    ("ZipFlyer Nepal (Pokhara)", 28.2500, 83.9500, "Kaski", "Gandaki", "Sarangkot", "1.8km zipline from Sarangkot — world's steepest.", "Oct-May"),
    ("Dharan zipline", 26.8000, 87.3000, "Sunsari", "Koshi", "Dharan", "Zipline in eastern Nepal.", "Oct-May"),
    ("Rock Climbing (Nagarjun)", 27.7400, 85.2700, "Kathmandu", "Bagmati", "Nagarjun", "Natural rock climbing cliffs.", "Oct-Apr"),
    ("Rock Climbing (Hattiban)", 27.6300, 85.2800, "Lalitpur", "Bagmati", "Hattiban", "Rock climbing on Phulchowki foothills.", "Oct-Apr"),
    ("Mountain Biking (Kathmandu Valley Rim)", 27.7200, 85.3000, "Kathmandu", "Bagmati", "Kathmandu", "World-class mountain biking trails.", "Oct-Mar"),
    ("Bungy Kusma (Cliff Nepal)", 28.2200, 83.7000, "Parbat", "Gandaki", "Kushma", "Cliff swing and bungee over Kali Gandaki gorge.", "Oct-May"),
]
AIR_SPORTS = [
    ("Paragliding Sarangkot", 28.2500, 83.9500, "Kaski", "Gandaki", "Pokhara", "One of the world's best commercial paragliding spots.", "Oct-Apr"),
    ("Ultralight Flight Pokhara", 28.2000, 83.9800, "Kaski", "Gandaki", "Pokhara", "Ultralight flights over Phewa Lake and Annapurna.", "Oct-Apr"),
    ("Everest Mountain Flight", 27.7000, 85.3500, "Kathmandu", "Bagmati", "Kathmandu", "1-hour scenic flight past Everest peaks.", "Oct-May"),
    ("Skydiving Pokhara", 28.2000, 83.9600, "Kaski", "Gandaki", "Pokhara", "Tandem skydiving over Phewa Lake.", "Nov-May"),
    ("Everest Skydive", 27.9880, 86.9150, "Solukhumbu", "Koshi", "Namche", "World's highest commercial skydive at Syangboche.", "Oct-Nov"),
    ("Helicopter Tour Everest", 27.9880, 86.9150, "Solukhumbu", "Koshi", "Namche", "Helicopter landing at EBC / Kala Patthar area.", "Oct-May"),
    ("Hot Air Balloon Pokhara", 28.2000, 83.9800, "Kaski", "Gandaki", "Pokhara", "Balloon flights over Phewa Lake with Annapurna views.", "Nov-Apr"),
    ("Gyrocopter Pokhara", 28.2000, 83.9800, "Kaski", "Gandaki", "Pokhara", "Autogyro scenic flights.", "Nov-Apr"),
]
WATER_SPORTS = [
    ("Bhote Koshi Rafting", 27.8833, 85.9167, "Sindhupalchok", "Bagmati", "Barabise", "World-class grade IV-V whitewater.", "Oct-May"),
    ("Trishuli River Rafting", 27.8000, 85.1500, "Chitwan", "Bagmati", "Mugling", "Grade III+ rapids; most accessible from Kathmandu.", "Sep-Jun"),
    ("Seti River Rafting", 28.1800, 84.0000, "Kaski", "Gandaki", "Pokhara", "Short scenic grade II-III rafting near Pokhara.", "Sep-Jun"),
    ("Kali Gandaki Rafting", 28.0000, 83.7500, "Syangja", "Gandaki", "Ramdi", "Grade IV-V adventure rafting in deep gorge.", "Oct-May"),
    ("Karnali River Rafting", 28.5500, 81.3000, "Surkhet", "Karnali", "Birendranagar", "Multi-day wilderness expedition on Nepal's longest river.", "Oct-May"),
    ("Sun Koshi Rafting", 27.6000, 85.8000, "Sindhuli", "Bagmati", "Sukute", "Multi-day 'River of Gold' rafting expedition.", "Sep-Jun"),
    ("Marshyangdi Rafting", 28.1000, 84.4500, "Tanahun", "Gandaki", "Bimalnagar", "Grade IV-V whitewater, one of the world's best.", "Oct-May"),
    ("Phewa Lake Boating", 28.2100, 83.9450, "Kaski", "Gandaki", "Pokhara", "Colorful doonga boats and sailing on Phewa.", "All year"),
    ("Begnas Lake Boating", 28.1833, 84.0833, "Kaski", "Gandaki", "Pokhara", "Quiet boating on Begnas Lake.", "Sep-May"),
    ("Seti River Kayaking", 28.2000, 84.0000, "Kaski", "Gandaki", "Pokhara", "Beginner-friendly kayaking.", "Sep-Jun"),
]
WELLNESS = [
    ("Purna Yoga Retreat (Pokhara)", 28.2500, 83.9800, "Kaski", "Gandaki", "Pokhara", "Yoga, meditation, wellness retreats.", "All year"),
    ("Osho Tapoban (Kathmandu)", 27.7400, 85.3600, "Kathmandu", "Bagmati", "Nagarjun", "Osho meditation retreat centre.", "All year"),
    ("Kopan Monastery Courses", 27.7333, 85.3667, "Kathmandu", "Bagmati", "Boudha", "Buddhist meditation courses.", "Oct-May"),
    ("Asura Cave Retreat (Pharping)", 27.6000, 85.2500, "Kathmandu", "Bagmati", "Pharping", "Padmasambhava pilgrimage and meditation caves.", "All year"),
    ("Neydo Tashi Choling Monastery", 27.6200, 85.2800, "Lalitpur", "Bagmati", "Dakshinkali", "Tibetan Buddhist retreat centre.", "All year"),
    ("Vipassana Centre Dharamshala (Nepgunj)", 28.0500, 81.6000, "Banke", "Lumbini", "Nepalgunj", "10-day Vipassana meditation courses.", "All year"),
    ("Pranamaya Yoga Pokhara", 28.2100, 83.9600, "Kaski", "Gandaki", "Pokhara", "Drop-in yoga classes and retreats.", "All year"),
    ("Nepal Yoga Academy", 27.6300, 85.2700, "Lalitpur", "Bagmati", "Godawari", "Yoga teacher trainings and retreats.", "All year"),
    ("Aryal Yoga Retreat Nagarkot", 27.7167, 85.5167, "Bhaktapur", "Bagmati", "Nagarkot", "Himalayan-view yoga retreat.", "Mar-May / Oct-Dec"),
    ("Lumbini Meditation Retreat", 27.4700, 83.2750, "Rupandehi", "Lumbini", "Lumbini", "Buddhist meditation under the Bodhi tree.", "All year"),
]
VILLAGES = [
    ("Ghandruk", 28.3800, 83.7700, "Kaski", "Gandaki", "Pokhara", "Gurung village with mountain views and cultural museum.", "Oct-Apr"),
    ("Ghalegaun", 28.3333, 84.4000, "Lamjung", "Gandaki", "Besisahar", "Model Gurung hill village at 2,100m; homestays.", "Oct-Apr"),
    ("Sirubari", 28.1000, 83.6500, "Syangja", "Gandaki", "Waling", "First model homestay village in Nepal; Gurung culture.", "Oct-Apr"),
    ("Chitlang", 27.6300, 85.1700, "Makwanpur", "Bagmati", "Chitlang", "Newari village near Kathmandu with goat cheese.", "Feb-May"),
    ("Bhujung", 28.3300, 84.3000, "Lamjung", "Gandaki", "Besisahar", "Traditional Gurung village with honey hunting heritage.", "Oct-Apr"),
    ("Lho", 28.5000, 84.6800, "Gorkha", "Gandaki", "Arughat", "Tibetan-Buddhist village on the Manaslu Circuit.", "Oct-Nov"),
    ("Lo Manthang (Upper Mustang)", 29.1833, 83.9560, "Mustang", "Gandaki", "Lo Manthang", "Walled medieval Tibetan village; restricted.", "Mar-May / Oct-Nov"),
    ("Marpha", 28.7667, 83.7167, "Mustang", "Gandaki", "Marpha", "Whitewashed stone village; apple brandy, Thakali cuisine.", "Oct-May"),
    ("Kagbeni", 28.8400, 83.7400, "Mustang", "Gandaki", "Kagbeni", "Medieval walled village at Kali Gandaki junction.", "Mar-May / Sep-Nov"),
    ("Barpak", 28.2833, 84.7000, "Gorkha", "Gandaki", "Arughat", "Model Ghale/Gurung village rebuilt after 2015 quake.", "Oct-Apr"),
    ("Dhampus", 28.3200, 83.8600, "Kaski", "Gandaki", "Pokhara", "Gurung village near Sarangkot; Australian Camp trek.", "Oct-Apr"),
    ("Tukuche", 28.7500, 83.6800, "Mustang", "Gandaki", "Tukuche", "Historic Thakali trading village on Kali Gandaki.", "Mar-May / Sep-Nov"),
    ("Namche Bazaar", 27.8050, 86.7120, "Solukhumbu", "Koshi", "Namche", "Sherpa trading town at 3,440m; Everest gateway.", "Mar-May / Oct-Dec"),
    ("Khumjung", 27.8250, 86.7200, "Solukhumbu", "Koshi", "Namche", "Sherpa village with Hillary school and alleged yeti scalp.", "Mar-May / Oct-Dec"),
    ("Thini (Jharkot)", 28.7800, 83.7200, "Mustang", "Gandaki", "Jomsom", "Ancient fort village above Jomsom.", "Mar-May / Sep-Nov"),
    ("Balthali", 27.6000, 85.5200, "Kavrepalanchok", "Bagmati", "Panauti", "Newar, Tamang, Magar village near Panauti; homestays.", "Oct-Mar"),
    ("Nuwakot Durbar Village", 27.9167, 85.1667, "Nuwakot", "Bagmati", "Nuwakot", "Historic seven-story palace and traditional Newari village.", "Oct-Apr"),
    ("Siuri Ghale Gaun", 28.3333, 84.4000, "Lamjung", "Gandaki", "Besisahar", "Awarded best homestay village in South Asia.", "Oct-Apr"),
    ("Tsum Valley (Chhokang Paro)", 28.5100, 84.7500, "Gorkha", "Gandaki", "Arughat", "Ancient Tibetan-speaking villages in hidden Tsum Valley.", "Mar-May / Sep-Nov"),
    ("Daman Village", 27.6000, 85.0667, "Makwanpur", "Bagmati", "Daman", "High-mountain village with Everest-to-Dhaulagiri views.", "Oct-Mar"),
]
FOOD = [
    ("Thamel Food Street (Kathmandu)", 27.7150, 85.3120, "Kathmandu", "Bagmati", "Thamel", "Thamel street food, momo, thakali, global cuisine.", "All year"),
    ("Newari Bhoj (Bhaktapur)", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Traditional Newari feasts: yomari, choila, kwati, baji.", "Oct-Apr / Biska Jatra"),
    ("Bhojan Griha (Dilli Bazaar)", 27.7050, 85.3300, "Kathmandu", "Bagmati", "Dilli Bazaar", "Heritage Newari feast in a restored Rana palace.", "All year"),
    ("Thakali Kitchen (Pokhara)", 28.2100, 83.9800, "Kaski", "Gandaki", "Pokhara", "Classic Thakali khana set from Mustang/Thak Khola.", "All year"),
    ("Marpha Apple Brandy", 28.7667, 83.7167, "Mustang", "Gandaki", "Marpha", "Apple orchards and distilleries of Marpha.", "Aug-Oct"),
    ("Juju Dhau (Bhaktapur)", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "King Curd — famous Bhaktapur yogurt in clay pots.", "All year"),
    ("Dal Bhat Trail (Teahouse Trek)", 28.2000, 83.9600, "Kaski", "Gandaki", "Pokhara", "Classic Nepali dal-bhat-tarkari at trekking teahouses.", "Trekking seasons"),
    ("Chhyaang (Tibetan millet beer)", 28.7667, 83.7167, "Mustang", "Gandaki", "Marpha", "Traditional Himalayan millet beer at high altitude.", "All year"),
    ("Sel Roti & Street Food", 27.7000, 85.3100, "Kathmandu", "Bagmati", "New Road", "Street snacks: sel roti, chatpate, panipuri, kulfi.", "All year"),
    ("Nepali Chiya (Tea)", 26.9167, 87.9167, "Ilam", "Koshi", "Ilam", "Traditional milk tea with Ilam-grown tea leaves.", "All year"),
    ("Dhindo Thali", 28.2500, 82.3000, "Surkhet", "Karnali", "Birendranagar", "Traditional buckwheat/millet dhindo thali.", "All year"),
    ("Fish Curry Phewa", 28.2100, 83.9450, "Kaski", "Gandaki", "Pokhara", "Fresh lake fish from Phewa at lakeside restaurants.", "All year"),
]
SCENIC_ROUTES = [
    ("Prithvi Highway (Mugling Road)", 27.7500, 84.8000, "Chitwan", "Bagmati", "Mugling", "Scenic highway from Kathmandu to Pokhara.", "Oct-May"),
    ("Araniko Highway (Tibet Road)", 27.8000, 85.9000, "Sindhupalchok", "Bagmati", "Barabise", "Mountain road to Tibet border via Kodari.", "Oct-May"),
    ("Siddhartha Highway (Butwal-Pokhara)", 27.9000, 83.7000, "Syangja", "Gandaki", "Waling", "Scenic hill highway with river gorges.", "Oct-May"),
    ("Kali Gandaki Corridor", 28.8000, 83.6000, "Myagdi", "Gandaki", "Beni", "World's deepest gorge road up to Mustang.", "Mar-Nov"),
    ("BP Koirala Highway (Banepa-Bardibas)", 27.5300, 85.8000, "Sindhuli", "Bagmati", "Sindhulimadi", "Scenic east-west hill highway.", "Oct-May"),
    ("Karnali Corridor (Hilsa Road)", 29.4000, 81.7000, "Mugu", "Karnali", "Gamgadhi", "Remote highway into far-western Karnali.", "Apr-Oct"),
    ("Pasang Lhamu Highway (Kerung)", 28.0000, 85.5000, "Rasuwa", "Bagmati", "Dhunche", "Scenic route to Tibet via Rasuwagadhi.", "Oct-May"),
    ("Mid-Hill Highway (Pushpalal)", 28.5000, 81.7000, "Dailekh", "Karnali", "Dailekh", "East-west mid-hill highway across Nepal.", "Oct-May"),
    ("Jomsom Sadak (Benni-Jomsom-Korala)", 28.7500, 83.7500, "Mustang", "Gandaki", "Jomsom", "Windy trans-Himalayan highway to Lo Manthang.", "Mar-Nov"),
    ("Rajmarg (Mahendra Highway East-West)", 27.6000, 83.4000, "Rupandehi", "Lumbini", "Butwal", "Terai east-west highway across Nepal.", "Oct-May"),
]
CITIES = [
    ("Kathmandu Durbar Square & Old City", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu", "Capital city, Durbar Squares, Thamel, Pashupati.", "Oct-Mar"),
    ("Pokhara Lakeside", 28.2100, 83.9600, "Kaski", "Gandaki", "Pokhara", "Adventure capital of Nepal on Phewa Lake.", "Sep-May"),
    ("Patan (Lalitpur) Old City", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan", "City of fine arts, temples and metalwork.", "Oct-Mar"),
    ("Bhaktapur", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Well-preserved medieval Newari city.", "Oct-Mar"),
    ("Janakpur", 26.7280, 85.9250, "Dhanusha", "Madhesh", "Janakpur", "Mithila culture, Janaki Mandir, Maithili arts.", "Oct-Mar"),
    ("Dharan", 26.8100, 87.2800, "Sunsari", "Koshi", "Dharan", "Eastern city with Dantakali, Budha Subba, BP Koirala Institute.", "Oct-Mar"),
    ("Biratnagar", 26.4500, 87.2800, "Morang", "Koshi", "Biratnagar", "Industrial capital of eastern Nepal.", "Oct-Mar"),
    ("Nepalgunj", 28.0500, 81.6200, "Banke", "Lumbini", "Nepalgunj", "Gateway to western Nepal; mixed Hindu-Muslim culture.", "Oct-Mar"),
    ("Butwal", 27.7000, 83.4500, "Rupandehi", "Lumbini", "Butwal", "Intersection of Mahendra and Siddhartha Highways.", "Oct-Mar"),
    ("Bharatpur", 27.6833, 84.4333, "Chitwan", "Bagmati", "Bharatpur", "Gateway to Chitwan National Park.", "Oct-Mar"),
    ("Tansen (Palpa)", 27.8667, 83.5500, "Palpa", "Lumbini", "Tansen", "Historic Newari hill town with Dhaka fabric.", "Sep-May"),
    ("Hetauda", 27.4300, 85.0300, "Makwanpur", "Bagmati", "Hetauda", "Industrial town with Sahid Smarak park.", "Oct-Mar"),
    ("Dhangadhi", 28.7000, 80.6000, "Kailali", "Sudurpashchim", "Dhangadhi", "Gateway to far-west Nepal and Shuklaphanta.", "Oct-Mar"),
    ("Bhimdatta (Mahendranagar)", 28.9000, 80.1800, "Kanchanpur", "Sudurpashchim", "Bhimdatta", "Far-western border town near Shuklaphanta.", "Oct-Mar"),
    ("Birgunj", 27.0200, 84.8800, "Parsa", "Madhesh", "Birgunj", "Major India-Nepal trade gateway.", "Oct-Mar"),
]
SHOPPING = [
    ("Asan Bazaar (Kathmandu)", 27.7070, 85.3110, "Kathmandu", "Bagmati", "Asan", "Historic market square with spices, textiles.", "All year"),
    ("Thamel Souvenir Strip", 27.7150, 85.3120, "Kathmandu", "Bagmati", "Thamel", "Trekking gear, pashmina, thangka, souvenirs.", "All year"),
    ("Patan Handicraft Shops", 27.6740, 85.3270, "Lalitpur", "Bagmati", "Patan", "Metalwork, woodcarving, thangka, paubha painting.", "All year"),
    ("Bhaktapur Pottery Square", 27.6710, 85.4280, "Bhaktapur", "Bagmati", "Bhaktapur", "Traditional black-red pottery; demonstrations.", "Oct-Apr"),
    ("Mahendrapul & Lakeside (Pokhara)", 28.2100, 83.9700, "Kaski", "Gandaki", "Pokhara", "Trekking gear, souvenirs, handicrafts.", "All year"),
    ("Indra Chowk Beads & Textiles", 27.7060, 85.3090, "Kathmandu", "Bagmati", "Indra Chowk", "Beads, dhaka fabric, traditional textiles.", "All year"),
    ("Dhaka Topi Weaving (Palpa)", 27.8667, 83.5500, "Palpa", "Lumbini", "Tansen", "Handwoven Dhaka fabric for topis and shawls.", "All year"),
    ("Jumli Wool & Carpet (Jumla)", 29.2700, 82.1800, "Jumla", "Karnali", "Chandannath", "High-altitude sheep wool products.", "Oct-May"),
    ("Khukuri Crafts (Bhojpur)", 27.1700, 87.0500, "Bhojpur", "Koshi", "Bhojpur", "Traditional Nepali kukri knife makers.", "All year"),
    ("Ilam Tea Sales", 26.9167, 87.9167, "Ilam", "Koshi", "Ilam", "Orthodox black, green and white tea direct from estates.", "Mar-Nov"),
]
CAMPING = [
    ("Bhairab Kunda Camping", 28.1330, 85.7330, "Sindhupalchok", "Bagmati", "Chautara", "Alpine camping near Panch Pokhari lakes.", "Sep-Nov / Mar-May"),
    ("Sarangkot Camping", 28.2500, 83.9500, "Kaski", "Gandaki", "Pokhara", "Camp with sunrise Himalayan views over Pokhara.", "Oct-Apr"),
    ("Chandragiri Camping", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Chandragiri", "Ridge camping above Kathmandu.", "Oct-Mar"),
    ("Kulekhani Lakeside Camping", 27.5830, 85.0330, "Makwanpur", "Bagmati", "Kulekhani", "Lakefront camping and boating.", "Oct-Mar"),
    ("Kakani International Scout Camp", 27.8167, 85.2667, "Nuwakot", "Bagmati", "Kakani", "Scout and youth camp at 2,030m.", "Mar-May / Oct-Dec"),
    ("Rara Lake Camping", 29.5270, 82.0900, "Mugu", "Karnali", "Talcha", "Wilderness camping on Rara Lake shores.", "Sep-Nov / Apr-May"),
    ("Phoksundo Lakeshore Camp", 29.2167, 82.8833, "Dolpa", "Karnali", "Dunai", "Riverside and lakeshore camping in Dolpo.", "May-Oct"),
    ("Gosaikunda Trek Camp", 28.0833, 85.4167, "Rasuwa", "Bagmati", "Dhunche", "High-altitude trekking camps near sacred lake.", "Sep-Oct / Apr-May"),
    ("Chitwan Jungle Camping", 27.5730, 84.4970, "Chitwan", "Bagmati", "Sauraha", "Jungle camps inside the national park.", "Oct-Mar"),
    ("Nagarkot Camping", 27.7167, 85.5167, "Bhaktapur", "Bagmati", "Nagarkot", "Camp for sunrise Himalayan views.", "Oct-Mar"),
]
CYCLING = [
    ("Kathmandu Valley Rim Loop", 27.7200, 85.3200, "Kathmandu", "Bagmati", "Kathmandu", "Classic single-track around the valley rim.", "Oct-Mar"),
    ("Pokhara Lakeside Cycling", 28.2100, 83.9600, "Kaski", "Gandaki", "Pokhara", "Easy scenic ride around Phewa Lake.", "Sep-May"),
    ("Nagarkot-Dhulikhel Mountain Biking", 27.7000, 85.5300, "Kavrepalanchok", "Bagmati", "Dhulikhel", "Ridge single-track with Himalayan views.", "Oct-Mar"),
    ("Annapurna Circuit by Bike", 28.6000, 83.8800, "Manang", "Gandaki", "Chame", "World-class high-altitude mountain biking route.", "Sep-Oct / Apr-May"),
    ("Kakani-Shivapuri MTB", 27.8000, 85.3000, "Kathmandu", "Bagmati", "Budhanilkantha", "Forested single-track to Kakani.", "Oct-Mar"),
    ("Phulchowki Descent", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari", "Tough climb to Phulchowki summit, long descent.", "Oct-Mar"),
    ("Hetauda to Kathmandu (Tribhuvan Rajpath)", 27.6000, 85.1000, "Makwanpur", "Bagmati", "Daman", "Historic highway climb over Daman pass.", "Oct-Mar"),
    ("Chitwan National Park Jungle Cycle", 27.5730, 84.4970, "Chitwan", "Bagmati", "Sauraha", "Safari cycling on buffer-zone trails.", "Oct-Mar"),
    ("Lumbini Sacred Garden Cycling", 27.4700, 83.2750, "Rupandehi", "Lumbini", "Lumbini", "Cycle between monastic zones in Lumbini.", "Oct-Mar"),
    ("Bandipur Village Loop", 27.9333, 84.4167, "Tanahun", "Gandaki", "Bandipur", "Ridge cycling around heritage Newari village.", "Oct-Apr"),
]
WINTER = [
    ("Kalinchowk Bhagwati Snow", 27.7500, 86.0200, "Dolakha", "Bagmati", "Charikot", "Closest snow-viewing hill from Kathmandu; cable car.", "Dec-Feb"),
    ("Daman Snow View", 27.6000, 85.0667, "Makwanpur", "Bagmati", "Daman", "Occasional snow and panoramic Himalayan views in winter.", "Dec-Feb"),
    ("Phulchowki Snow", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari", "Snowfall at 2,782m during winter cold snaps.", "Dec-Feb"),
    ("Chandragiri Snow", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Chandragiri", "Snow views from cable car in winter.", "Dec-Feb"),
    ("Shivapuri Snow", 27.7800, 85.4000, "Kathmandu", "Bagmati", "Budhanilkantha", "Winter snow hiking on Kathmandu's northern ridge.", "Dec-Feb"),
    ("Sailung Winter Trek", 27.6500, 86.0000, "Dolakha/Ramechhap", "Bagmati", "Dolakha", "High plateau '1000 hills' viewpoint with winter snow.", "Dec-Feb"),
    ("Gosaikunda Frozen Lake", 28.0833, 85.4167, "Rasuwa", "Bagmati", "Dhunche", "Frozen glacial lake in winter (advanced trekking).", "Dec-Feb"),
    ("Annapurna Circuit Winter", 28.6000, 83.9000, "Manang", "Gandaki", "Chame", "Winter trekking with snow scenes (lower sections).", "Dec-Feb"),
    ("Everest Base Camp Winter", 27.8000, 86.7000, "Solukhumbu", "Koshi", "Namche", "Winter EBC trekking with snow-capped peaks.", "Dec-Feb"),
    ("Jomsom-Muktinath Winter", 28.7833, 83.7333, "Mustang", "Gandaki", "Jomsom", "Cold but clear; ideal for views; snow passes minimal.", "Dec-Feb"),
]
ECO = [
    ("ACAP Ghandruk Eco-Lodges", 28.3800, 83.7700, "Kaski", "Gandaki", "Ghandruk", "NTB-supported eco-lodges run by local communities.", "Oct-Apr"),
    ("Tsum Valley Community Lodges", 28.5100, 84.7500, "Gorkha", "Gandaki", "Arughat", "Community-managed eco-lodges in restricted valley.", "Mar-May / Sep-Nov"),
    ("Blackbuck Conservation Area", 28.3000, 81.3000, "Bardiya", "Lumbini", "Gulariya", "Blackbuck conservation eco-tourism in Khairapur.", "Oct-Mar"),
    ("Bird Education Society (Koshi)", 26.6500, 87.0000, "Sunsari", "Koshi", "Itahari", "Community-based bird-watching eco-tourism.", "Oct-Mar"),
    ("Chitwan Tharu Homestays", 27.5700, 84.5000, "Chitwan", "Bagmati", "Sauraha", "Tharu community-run home stays and jungle walks.", "Oct-Mar"),
    ("Sirubari Community Homestay", 28.1000, 83.6500, "Syangja", "Gandaki", "Waling", "Nepal's first award-winning community homestay village.", "Oct-Apr"),
    ("Ghalegaun Community Eco-Village", 28.3333, 84.4000, "Lamjung", "Gandaki", "Besisahar", "Awarded Asia's best model eco-cultural tourism village.", "Oct-Apr"),
    ("Barauli Community Homestay", 27.6000, 84.3333, "Chitwan", "Bagmati", "Sauraha", "Tharu-run community homestay near Chitwan buffer zone.", "Oct-Mar"),
    ("Ilam Community Tea Homestays", 26.8800, 88.0800, "Ilam", "Koshi", "Shree Antu", "Community homestays in tea gardens.", "Oct-Apr"),
    ("Khaptad Eco-Trail", 29.2667, 80.1667, "Doti", "Sudurpashchim", "Silgadhi", "Khaptad Baba ashram and community-managed trekking.", "Mar-May / Oct-Nov"),
]
BIRD_WATCHING = [
    ("Koshi Tappu Birding", 26.6500, 87.0000, "Sunsari", "Koshi", "Itahari", "Ramsar site; 500+ bird species including watercock.", "Oct-Mar"),
    ("Shivapuri Nagarjun Birding", 27.8000, 85.4000, "Kathmandu", "Bagmati", "Budhanilkantha", "318 bird species including spiny babbler.", "Oct-Apr"),
    ("Phulchowki Birding", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari", "Kathmandu Valley's premier birding spot; 300+ species.", "Oct-Apr"),
    ("Chitwan National Park Birding", 27.5730, 84.4970, "Chitwan", "Bagmati", "Sauraha", "500+ species including giant hornbill and Bengal florican.", "Oct-Mar"),
    ("Bardiya National Park Birding", 28.3833, 81.5000, "Bardiya", "Lumbini", "Thakurdwara", "Over 400 species; Bengal florican, sarus crane.", "Oct-Mar"),
    ("Shuklaphanta Birding", 28.8500, 80.2167, "Kanchanpur", "Sudurpashchim", "Mahendranagar", "Grassland specialists: swamp francolin, Jerdon's babbler.", "Nov-Jun"),
    ("Godawari Botanical Garden Birding", 27.6000, 85.3800, "Lalitpur", "Bagmati", "Godawari", "Sub-tropical forest birding at valley's botanical garden.", "Oct-Apr"),
    ("Jagadishpur Reservoir", 27.6000, 83.2000, "Kapilvastu", "Lumbini", "Kapilvastu", "Ramsar site; ducks, waders, migratory species.", "Nov-Feb"),
    ("Mai Pokhari", 27.0167, 87.9333, "Ilam", "Koshi", "Ilam", "Ramsar wetland in Ilam; white-rumped vulture sightings.", "Oct-Mar"),
    ("Ghodaghodi Lake", 28.7000, 80.6000, "Kailali", "Sudurpashchim", "Dhangadhi", "Ramsar wetland system with marsh birds.", "Oct-Mar"),
]
FORESTS = [
    ("Shivapuri Nagarjun Forest", 27.8000, 85.4000, "Kathmandu", "Bagmati", "Budhanilkantha", "Subtropical and temperate forests on Kathmandu rim.", "Oct-Apr"),
    ("Phulchowki Community Forest", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari", "Subtropical forest with orchids and rhododendron.", "Mar-May / Oct-Nov"),
    ("Chitwan Sal Forest", 27.5730, 84.4970, "Chitwan", "Bagmati", "Sauraha", "Dense Sal (Shorea robusta) jungle habitat.", "Oct-Mar"),
    ("Annapurna Rhododendron Forests (Ghorepani)", 28.4000, 83.7333, "Myagdi", "Gandaki", "Ghorepani", "Rhododendron forests blooming red/pink in April.", "Apr-Rhododendron"),
    ("Langtang Subalpine Forest", 28.1667, 85.5000, "Rasuwa", "Bagmati", "Syabrubesi", "Oak, maple and rhododendron forests; red panda habitat.", "Mar-May / Oct-Dec"),
    ("Makalu Barun Arun Valley Forests", 27.7500, 87.1667, "Sankhuwasabha", "Koshi", "Tumlingtar", "World's deepest valley with 8 eco-zones in 40 km.", "Apr-May / Oct-Nov"),
    ("Khaptad Mixed Forests", 29.2667, 80.1667, "Doti", "Sudurpashchim", "Silgadhi", "Mid-western plateau forests with rhododendron.", "Mar-May / Oct-Nov"),
    ("Sagarmatha Alpine Pine/Fir", 27.8500, 86.7500, "Solukhumbu", "Koshi", "Namche", "Himalayan pine, fir and juniper timberline.", "Oct-Nov"),
    ("Panchase Protected Forest", 28.2500, 83.8500, "Kaski", "Gandaki", "Pokhara", "31 km² protected forest near Pokhara; rich biodiversity.", "Oct-Apr"),
    ("Tinpipli Bhanjyang Community Forest", 27.6800, 85.5000, "Kavrepalanchok", "Bagmati", "Dhulikhel", "Community-managed forest with hiking trails.", "Oct-Mar"),
]
RIVERS = [
    ("Koshi River (Sapta Kosi)", 26.5500, 87.0000, "Sunsari", "Koshi", "Barahakshetra", "Largest river in Nepal; seven Himalayan tributaries.", "Oct-May"),
    ("Gandaki (Narayani) River", 27.5500, 84.2000, "Chitwan", "Bagmati", "Narayangarh", "Seven tributaries including Kali Gandaki.", "Oct-May"),
    ("Karnali River", 28.6000, 81.2000, "Kailali", "Sudurpashchim", "Chisapani", "Nepal's longest and largest river by volume.", "Oct-May"),
    ("Trishuli River", 27.8000, 85.1500, "Chitwan", "Bagmati", "Mugling", "Sacred and rafting river from Tibet to Narayani.", "Sep-Jun"),
    ("Bhote Koshi", 27.8800, 85.9200, "Sindhupalchok", "Bagmati", "Barabise", "Tibetan-source tributary of Sun Kosi; bungee/rafting.", "Oct-May"),
    ("Sun Kosi", 27.4000, 85.8000, "Sindhuli", "Bagmati", "Sukute", "'River of Gold' — multi-day rafting expedition.", "Sep-Jun"),
    ("Arun River", 27.3300, 87.2000, "Bhojpur", "Koshi", "Tumlingtar", "Major trans-Himalayan river through Makalu Barun.", "Oct-May"),
    ("Kali Gandaki Gorge", 28.7500, 83.6500, "Myagdi", "Gandaki", "Beni", "World's deepest gorge between Dhaulagiri and Annapurna.", "Mar-Nov"),
    ("Seti Gandaki Gorge", 28.2300, 83.9600, "Kaski", "Gandaki", "Pokhara", "Mysterious disappearing river gorge through Pokhara.", "All year"),
    ("Marshyangdi River", 28.2000, 84.4000, "Tanahun", "Gandaki", "Bimalnagar", "Turbulent rafting river from Manang.", "Oct-May"),
    ("Mahakali River", 29.0000, 80.2000, "Darchula", "Sudurpashchim", "Darchula", "Western border river with India; rafting and fishing.", "Oct-May"),
    ("Bagmati River (Pashupati)", 27.7100, 85.3500, "Kathmandu", "Bagmati", "Pashupatinath", "Sacred river; cremation ghats at Pashupatinath.", "All year"),
]
VALLEYS = [
    ("Pokhara Valley", 28.2100, 83.9800, "Kaski", "Gandaki", "Pokhara", "Lakeside valley surrounded by Annapurna range.", "Sep-May"),
    ("Kathmandu Valley", 27.7200, 85.3200, "Kathmandu", "Bagmati", "Kathmandu", "Historic valley with 7 UNESCO heritage sites.", "Oct-Mar"),
    ("Langtang Valley", 28.2167, 85.5333, "Rasuwa", "Bagmati", "Syabrubesi", "Glacial valley close to Kathmandu; Kyanjin Gompa.", "Mar-May / Oct-Dec"),
    ("Arun Valley", 27.5000, 87.2500, "Sankhuwasabha", "Koshi", "Tumlingtar", "Deepest valley on Earth from Makalu to plains.", "Apr-May / Oct-Nov"),
    ("Kali Gandaki Valley", 28.6000, 83.7000, "Mustang", "Gandaki", "Jomsom", "World's deepest gorge valley; fossil shaligram belt.", "Mar-Nov"),
    ("Manang Valley", 28.6700, 84.0200, "Manang", "Gandaki", "Chame", "Trans-Himalayan rain-shadow valley north of Annapurna.", "Sep-Oct"),
    ("Tsum Valley", 28.5100, 84.7500, "Gorkha", "Gandaki", "Arughat", "Hidden Buddhist valley; restricted, 33 villages.", "Mar-May / Sep-Nov"),
    ("Dolpo Valley", 29.1000, 82.9000, "Dolpa", "Karnali", "Dunai", "High trans-Himalayan Tibetan valley; Shey Gompa.", "May-Sep"),
    ("Barun Valley", 27.7800, 87.1200, "Sankhuwasabha", "Koshi", "Tumlingtar", "Pristine valley beneath Makalu in Makalu Barun NP.", "Apr-May / Oct-Nov"),
    ("Rolwaling Valley", 27.9000, 86.3333, "Dolakha", "Bagmati", "Suri Dhoban", "Sacred valley east of Langtang; Tsho Rolpa glacial lake.", "Mar-May / Oct-Nov"),
    ("Thak Khola Valley", 28.7800, 83.7200, "Mustang", "Gandaki", "Jomsom", "Windy Kali Gandaki valley between Annapurna and Dhaulagiri.", "Mar-Nov"),
    ("Humla Karnali Valley", 30.0000, 81.7000, "Humla", "Karnali", "Simikot", "Remote far-western high-Himalayan valley.", "May-Oct"),
]
FESTIVALS = [
    ("Dashain Ghatasthapana (Nuwakot)", 27.9167, 85.1667, "Nuwakot", "Bagmati", "Nuwakot", "Nepal's biggest festival — royal dashain celebrations in historic Nuwakot.", "Sep-Oct (Ashwin)"),
    ("Tihar (Laxmi Puja)", 27.7000, 85.3100, "Kathmandu", "Bagmati", "Kathmandu", "Festival of lights; dogs, crows, cows worshiped; Bhai Tika.", "Oct-Nov (Kartik)"),
    ("Indra Jatra (Kathmandu)", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu", "Historic Newar festival; Kumari displayed, Lakhe dance.", "Sep"),
    ("Bisket Jatra (Bhaktapur)", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Nepali New Year chariot festival in Bhaktapur.", "April"),
    ("Rato Machhindranath Jatra (Patan)", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan", "Longest chariot festival of Patan; Bhoto Jatra finale.", "May-Jun"),
    ("Holi (Fagu Purnima)", 27.7000, 85.3200, "Kathmandu", "Bagmati", "Kathmandu", "Festival of colors; Terai and hill celebrations.", "Feb-Mar"),
    ("Mani Rimdu (Tengboche)", 27.8350, 86.7680, "Solukhumbu", "Koshi", "Tengboche", "Sherpa masked dance festival at Tengboche Monastery.", "Oct-Nov"),
    ("Janai Purnima (Gosaikunda)", 28.0833, 85.4167, "Rasuwa", "Bagmati", "Dhunche", "Sacred thread festival; thousands bathe in Gosaikunda.", "August"),
    ("Teej (Pashupatinath)", 27.7100, 85.3480, "Kathmandu", "Bagmati", "Kathmandu", "Women's fasting festival in red sarees.", "Aug-Sep"),
    ("Buddha Jayanti (Lumbini)", 27.4690, 83.2740, "Rupandehi", "Lumbini", "Lumbini", "Birth of Buddha; grand celebrations at Lumbini.", "May"),
    ("Shivaratri (Pashupatinath)", 27.7100, 85.3480, "Kathmandu", "Bagmati", "Kathmandu", "Great night of Shiva; thousands of sadhus gather.", "Feb-Mar"),
    ("Tiji Festival (Lo Manthang)", 29.1833, 83.9560, "Mustang", "Gandaki", "Lo Manthang", "Three-day masked Tibetan festival in Upper Mustang.", "May"),
    ("Yomari Punhi (Newar)", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur", "Newar harvest festival with yomari sweets.", "Dec"),
    ("Maghe Sankranti (Devghat)", 27.7500, 84.4167, "Chitwan", "Bagmati", "Devghat", "Holy bathing at Devghat confluence; yam festival.", "Jan"),
    ("Chhath (Terai)", 27.0000, 84.9000, "Parsa", "Madhesh", "Birgunj", "Terai sun worship festival at riverbanks.", "Oct-Nov"),
]
PILGRIMAGE = [
    ("Muktinath", 28.8167, 83.8667, "Mustang", "Gandaki", "Ranipauwa", "Sacred Vishnu temple with 108 waterspouts; 3,762m.", "Mar-May / Sep-Oct"),
    ("Pashupatinath", 27.7100, 85.3480, "Kathmandu", "Bagmati", "Kathmandu", "Most sacred Shiva temple; UNESCO.", "Feb-Mar (Shivaratri)"),
    ("Janakpurdham", 26.7280, 85.9250, "Dhanusha", "Madhesh", "Janakpur", "Birthplace of Sita; Janaki Mandir.", "Vivaha Panchami"),
    ("Halesi Mahadev", 27.2000, 86.6167, "Khotang", "Koshi", "Halesi", "Pashupati of the east; Hindu-Buddhist cave shrine.", "Mar-May / Sep-Oct"),
    ("Gosaikunda", 28.0833, 85.4167, "Rasuwa", "Bagmati", "Dhunche", "Sacred glacial lake of Shiva.", "Aug (Janai Purnima)"),
    ("Lumbini", 27.4690, 83.2740, "Rupandehi", "Lumbini", "Lumbini", "Birthplace of Buddha; UNESCO.", "Buddha Jayanti"),
    ("Devghat Dham", 27.7500, 84.4167, "Chitwan", "Bagmati", "Devghat", "Sacred confluence of Kali Gandaki and Trishuli.", "Maghe Sankranti"),
    ("Swargadwari", 28.1833, 82.6833, "Pyuthan", "Lumbini", "Pyuthan", "Hilltop pilgrimage founded by Swami Mahaprabhu.", "Oct-Apr"),
    ("Barahakshetra", 26.5500, 87.0000, "Sunsari", "Koshi", "Barahakshetra", "One of four Char Dham of Nepal; Vishnu boar avatar.", "Nov-Dec"),
    ("Chhatra Dham", 26.6600, 87.1500, "Sunsari", "Koshi", "Chatra", "Sacred confluence of Kosi and Arun rivers.", "Nov-Mar"),
    ("Muktinath to Damodar Kunda", 28.9500, 83.9200, "Mustang", "Gandaki", "Muktinath", "Sacred glacial kunda beyond Muktinath.", "Aug-Sep"),
    ("Salinadi (Sankhu)", 27.7200, 85.4500, "Kathmandu", "Bagmati", "Sankhu", "Sacred river and pilgrimage near Swasthani.", "Jan-Feb (Swasthani)"),
    ("Doleshwor Mahadev", 27.6500, 85.4500, "Bhaktapur", "Bagmati", "Sipadol", "Head of Kedarnath.", "Jun-Aug"),
    ("Budhasubba (Dharan)", 26.8200, 87.2800, "Sunsari", "Koshi", "Dharan", "Sacred bamboo grove shrine in Dharan.", "All year"),
    ("Kagbeni Muktinath Route", 28.8400, 83.7400, "Mustang", "Gandaki", "Kagbeni", "Pilgrim trail along Kali Gandaki to Muktinath.", "Mar-May / Sep-Nov"),
]
NATURAL_WONDERS = [
    ("Kali Gandaki Gorge", 28.7500, 83.6500, "Myagdi", "Gandaki", "Beni", "Deepest gorge on Earth between Dhaulagiri and Annapurna.", "Mar-Nov"),
    ("Tilicho Lake", 28.6833, 83.8500, "Manang", "Gandaki", "Chame", "One of the highest glacial lakes (4,919m).", "Sep-Oct / Apr-May"),
    ("Phoksundo Waterfall (Suligad)", 29.2300, 82.8800, "Dolpa", "Karnali", "Dunai", "300+ m twin waterfalls below Phoksundo Lake.", "May-Oct"),
    ("Dhaulagiri Icefall", 28.6966, 83.4895, "Myagdi", "Gandaki", "Beni", "Massive icefall visible from French Pass.", "Apr-May / Oct"),
    ("Makalu Barun Arun Valley", 27.5000, 87.2500, "Sankhuwasabha", "Koshi", "Tumlingtar", "8 eco-zones in 40km vertical range.", "Apr-May / Oct-Nov"),
    ("Seti Gandaki Gorge (Pokhara)", 28.2300, 83.9600, "Kaski", "Gandaki", "Pokhara", "Mysterious underground gorge running through Pokhara.", "All year"),
    ("Siddha Cave (Bimalnagar)", 27.8833, 84.4000, "Tanahun", "Gandaki", "Bimalnagar", "Largest cave in Nepal (437m).", "Oct-Apr"),
    ("Shaligram Belt (Kali Gandaki)", 28.7500, 83.6800, "Mustang", "Gandaki", "Tukuche", "Ammonite fossil belt sacred to Vishnu.", "Mar-Nov"),
    ("Kyanjin Ri Panorama", 28.2167, 85.5800, "Rasuwa", "Bagmati", "Kyanjin", "360° Langtang views from Kyanjin Ri (4,773m).", "Mar-May / Oct-Dec"),
    ("Kala Patthar Everest View", 27.9940, 86.8290, "Solukhumbu", "Koshi", "Gorakshep", "Best Everest viewpoint (5,644m).", "Oct-Nov / Apr"),
    ("Tsho Rolpa Glacial Lake", 27.8700, 86.3300, "Dolakha", "Bagmati", "Suri Dhoban", "Glacial lake at 4,580m; engineering study site.", "Apr-May / Oct-Nov"),
    ("Gokyo Lakes System", 27.9570, 86.7110, "Solukhumbu", "Koshi", "Gokyo", "Six interconnected glacial lakes at 4,700-5,000m.", "Sep-Nov / Mar-May"),
]
HILLS = [
    ("Nagarkot", 27.7167, 85.5167, "Bhaktapur", "Bagmati", "Nagarkot", "2,175m hill station for sunrise Himalayan views.", "Oct-Mar"),
    ("Sarangkot", 28.2500, 83.9500, "Kaski", "Gandaki", "Pokhara", "1,600m paragliding and sunrise viewpoint above Pokhara.", "Oct-Nov / Mar-Apr"),
    ("Phulchowki", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari", "Highest hill (2,782m) around Kathmandu.", "Oct-Mar"),
    ("Chandragiri", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Thankot", "2,551m hill with cable car and Bhaleshwor temple.", "Oct-Mar"),
    ("Shree Antu", 26.8833, 88.0833, "Ilam", "Koshi", "Shree Antu", "Sunrise over Kanchenjunga and tea gardens.", "Oct-Apr"),
    ("Kakani", 27.8167, 85.2667, "Nuwakot", "Bagmati", "Kakani", "2,030m hill station on Kathmandu NW rim.", "Oct-Mar"),
    ("Daman", 27.6000, 85.0667, "Makwanpur", "Bagmati", "Daman", "Viewpoint with broadest Himalayan panorama.", "Oct-Mar"),
    ("Dhulikhel", 27.6167, 85.5500, "Kavrepalanchok", "Bagmati", "Dhulikhel", "1,550m Newari hill town with Himalayan views.", "Oct-Mar"),
    ("Bandipur", 27.9333, 84.4167, "Tanahun", "Gandaki", "Bandipur", "Preserved 18th-century Newari trading village.", "Oct-Apr"),
    ("Tansen Shreenagar", 27.8700, 83.5400, "Palpa", "Lumbini", "Tansen", "Ridge walk above Tansen with Himalayan views.", "Sep-May"),
    ("Gorkha Durbar Hill", 28.0000, 84.6333, "Gorkha", "Gandaki", "Gorkha", "1,000m hill with historic Gorkha palace.", "Oct-Apr"),
    ("Suryabinayak Hill", 27.6500, 85.4300, "Bhaktapur", "Bagmati", "Suryabinayak", "Forest hill with Ganesha temple near Bhaktapur.", "Oct-Mar"),
    ("Sailung (1000 Hills)", 27.6500, 86.0000, "Dolakha/Ramechhap", "Bagmati", "Dolakha", "High plateau viewpoint at ~3,100m.", "Mar-May / Oct-Nov"),
    ("Kanyam Hill (Ilam)", 26.8333, 88.0167, "Ilam", "Koshi", "Kanyam", "Tea garden viewpoint; picnics and horse rides.", "Mar-Nov"),
    ("Bhairabsthan (Palpa)", 27.8500, 83.5400, "Palpa", "Lumbini", "Tansen", "Hilltop Bhairab temple; Himalayan and Madi views.", "Sep-May"),
]


# Map which category each destination list belongs to
SEED_MAP = [
    ("mountains", MOUNTAINS),
    ("lakes", LAKES),
    ("waterfalls", WATERFALLS),
    ("trekking", TREKKING),
    ("temples", TEMPLES),
    ("buddhist-sites", BUDDHIST),
    ("heritage", HERITAGE),
    ("viewpoints", VIEWPOINTS),
    ("wildlife", NATIONAL_PARKS_WILDLIFE),
    ("caves", CAVES),
    ("museums", MUSEUMS),
    ("tea-coffee", TEA_COFFEE),
    ("hot-springs", HOT_SPRINGS),
    ("adventure", ADVENTURE),
    ("air-sports", AIR_SPORTS),
    ("water-sports", WATER_SPORTS),
    ("spiritual-wellness", WELLNESS),
    ("villages", VILLAGES),
    ("food-culinary", FOOD),
    ("scenic-routes", SCENIC_ROUTES),
    ("cities", CITIES),
    ("shopping", SHOPPING),
    ("camping", CAMPING),
    ("cycling", CYCLING),
    ("winter", WINTER),
    ("eco-tourism", ECO),
    ("bird-watching", BIRD_WATCHING),
    ("forests", FORESTS),
    ("rivers", RIVERS),
    ("valleys", VALLEYS),
    ("festivals", FESTIVALS),
    ("pilgrimage", PILGRIMAGE),
    ("natural-wonders", NATURAL_WONDERS),
    ("hills", HILLS),
]


class Command(BaseCommand):
    help = "Create comprehensive Nepal tourism categories and seed curated destinations (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Create categories
        cat_objs = {}
        for slug, name, icon, desc in CATEGORIES:
            cat_objs[slug] = _get_or_create_cat(slug, name, icon, desc)
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(CATEGORIES)} categories exist."))

        # Make sure the existing standard categories are still there too
        for slug in ["attraction", "nature-trekking", "photography-spots", "religious-sites",
                     "heritage-temples", "lakes-water-activities", "wildlife", "viewpoint",
                     "museum", "information", "hotel", "guest_house"]:
            if slug not in cat_objs and Category.objects.filter(slug=slug).exists():
                cat_objs[slug] = Category.objects.get(slug=slug)

        # Ensure attraction category is a sensible default
        if "attraction" not in cat_objs:
            cat_objs["attraction"] = _get_or_create_cat("attraction", "Attraction", "📍", "General tourist attraction")

        added_total = 0
        skipped_total = 0

        for slug, items in SEED_MAP:
            cat = cat_objs.get(slug)
            if not cat:
                continue
            for (name, lat, lon, district, province, city, desc, best_time) in items:
                # Idempotent: match by name + district combo (or exact name)
                existing = (
                    Destination.objects.filter(name__iexact=name).first()
                    or Destination.objects.filter(name__icontains=name.split("(")[0].strip(), district=district).first()
                )
                if existing:
                    # Fill missing fields without clobbering
                    changes = []
                    if not existing.category:
                        existing.category = cat; changes.append("category")
                    if not existing.latitude and lat:
                        existing.latitude = lat; changes.append("latitude")
                    if not existing.longitude and lon:
                        existing.longitude = lon; changes.append("longitude")
                    if not existing.district and district:
                        existing.district = district; changes.append("district")
                    if not existing.province and province:
                        existing.province = province; changes.append("province")
                    if not existing.city and city:
                        existing.city = city; changes.append("city")
                    if not existing.country:
                        existing.country = "Nepal"; changes.append("country")
                    if not existing.short_description and desc:
                        existing.short_description = desc[:300]; changes.append("short_description")
                    if not existing.best_time_to_visit and best_time:
                        existing.best_time_to_visit = best_time; changes.append("best_time_to_visit")
                    if not existing.is_active:
                        existing.is_active = True; changes.append("active")
                    if existing.status != Destination.SubmissionStatus.APPROVED:
                        existing.status = Destination.SubmissionStatus.APPROVED; changes.append("status")
                    if changes:
                        existing.save(update_fields=changes)
                    skipped_total += 1
                    continue

                Destination.objects.create(
                    name=name,
                    category=cat,
                    latitude=lat,
                    longitude=lon,
                    district=district,
                    province=province,
                    city=city,
                    country="Nepal",
                    short_description=desc[:300],
                    description=f"{desc} Located in {district} district, {province} province, Nepal.",
                    best_time_to_visit=best_time,
                    is_active=True,
                    status=Destination.SubmissionStatus.APPROVED,
                    is_user_submitted=False,
                    source="curated-taxonomy",
                )
                added_total += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Added {added_total} new destinations; updated/skipped {skipped_total}. "
            f"Total: {Destination.objects.count()} destinations, {Category.objects.count()} categories."
        ))
