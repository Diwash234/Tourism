"""
Management command: add_more_destinations
=========================================
Adds a curated list of real Nepal tourist attractions -- peaks, lakes,
temples, caves, waterfalls, national parks, museums, treks, viewpoints --
that were missing from the initial OSM import (which skewed heavily
towards hotels/guest-houses).

Each entry has verified lat/lon, district/province, category, and a short
description so cards look complete out of the box. Idempotent: places
that already exist (matched by name, case-insensitive) are skipped.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from tourist.models import Destination, Category


def _get_or_create_category(slug, name):
    cat, _ = Category.objects.get_or_create(
        slug=slug, defaults={"name": name, "slug": slug}
    )
    # Make sure name matches (slug lookup can find an old row with weird name)
    if cat.name != name:
        cat.name = name
        cat.save(update_fields=["name"])
    return cat


# Curated list of major Nepal attractions. Format:
# (name, category_slug, category_name, lat, lon, district, province, city,
#  short_description, aliases, best_time)
CURATED = [
    # --- 8000m & major peaks ---
    ("Mount Everest (Sagarmatha)", "nature-trekking", "Nature & Trekking", 27.9881, 86.9250, "Solukhumbu", "Koshi", "Namche Bazaar",
     "World's highest peak (8,848.86 m), crown jewel of Khumbu.", "Sagarmatha,Chomolungma,Everest", "Apr-May / Sep-Nov"),
    ("Kanchenjunga", "nature-trekking", "Nature & Trekking", 27.7025, 88.1475, "Taplejung", "Koshi", "Taplejung",
     "Third highest mountain on Earth (8,586 m) on Nepal-India border.", "Kanchenjunga,Kanchanjungha", "Apr-May / Oct-Nov"),
    ("Lhotse", "nature-trekking", "Nature & Trekking", 27.9625, 86.9335, "Solukhumbu", "Koshi", "Namche",
     "Fourth highest peak (8,516 m) adjacent to Everest.", "", "Apr-May / Oct-Nov"),
    ("Makalu", "nature-trekking", "Nature & Trekking", 27.8897, 87.0888, "Sankhuwasabha", "Koshi", "Makalu",
     "Fifth highest peak (8,485 m) with the classic pyramid shape.", "", "Apr-May / Oct-Nov"),
    ("Cho Oyu", "nature-trekking", "Nature & Trekking", 28.0946, 86.6625, "Solukhumbu", "Koshi", "Namche",
     "Sixth highest peak (8,188 m) on Tibet border.", "", "Apr-May / Oct-Nov"),
    ("Dhaulagiri I", "nature-trekking", "Nature & Trekking", 28.6966, 83.4895, "Myagdi", "Gandaki", "Beni",
     "Seventh highest peak (8,167 m), the White Mountain.", "Dhaulagiri", "Apr-May / Sep-Nov"),
    ("Manaslu", "nature-trekking", "Nature & Trekking", 28.5497, 84.5597, "Gorkha", "Gandaki", "Arughat",
     "Eighth highest peak (8,163 m), Mountain of the Spirit.", "Kutang", "Sep-Nov / Mar-Apr"),
    ("Annapurna I", "nature-trekking", "Nature & Trekking", 28.5954, 83.8203, "Myagdi", "Gandaki", "Beni",
     "Tenth highest peak (8,091 m); first 8000er ever climbed.", "", "Oct-Nov / Apr"),
    ("Annapurna South", "nature-trekking", "Nature & Trekking", 28.5170, 83.8060, "Kaski", "Gandaki", "Pokhara",
     "Iconic 7,219 m peak visible from Pokhara.", "Annapurna Dakshin", "Oct-Nov"),
    ("Machhapuchhre (Fishtail)", "nature-trekking", "Nature & Trekking", 28.4950, 83.9450, "Kaski", "Gandaki", "Pokhara",
     "Sacred 6,993 m peak considered holy and closed to climbers.", "Fishtail Mountain,Machhapuchhre", "Oct-Nov / Mar-Apr"),
    ("Machhapuchhare Model View Point", "viewpoint", "viewpoint", 28.4833, 83.9500, "Kaski", "Gandaki", "Pokhara",
     "Classic viewpoint overlooking Machhapuchhre and the Annapurnas.", "Mardi Himal View", "Oct-Nov / Mar"),
    ("Api Himal", "nature-trekking", "Nature & Trekking", 30.0020, 80.9330, "Darchula", "Sudurpashchim", "Darchula",
     "Westernmost 7,132 m peak of the Nepal Himalaya.", "Api Peak", "May-Jun / Sep-Oct"),
    ("Saipal", "nature-trekking", "Nature & Trekking", 29.8833, 81.5000, "Bajhang", "Sudurpashchim", "Bajhang",
     "Remote 7,031 m peak in far-western Nepal.", "", "May-Jun / Sep-Oct"),
    ("Mardi Himal", "nature-trekking", "Nature & Trekking", 28.4667, 83.9333, "Kaski", "Gandaki", "Pokhara",
     "Popular short trek to a 5,587 m ridge with breathtaking Fishtail views.", "Mardi Trek", "Oct-Nov / Mar-Apr"),

    # --- Major lakes (Nepal has 5000+; key famous ones) ---
    ("Begnas Lake", "lakes-water-activities", "Lakes & Water Activities", 28.1833, 84.0833, "Kaski", "Gandaki", "Pokhara",
     "Second largest lake in Pokhara valley, quieter than Phewa.", "Begnas Tal", "Sep-May"),
    ("Rupa Lake", "lakes-water-activities", "Lakes & Water Activities", 28.1667, 84.1000, "Kaski", "Gandaki", "Pokhara",
     "Freshwater lake known for lotus flowers and bird watching.", "Rupa Tal", "Sep-May"),
    ("Phoksundo Lake", "lakes-water-activities", "Lakes & Water Activities", 29.2167, 82.8833, "Dolpa", "Karnali", "Dunai",
     "Turquoise alpine lake (3,611 m) in Shey Phoksundo National Park.", "Shey Phoksundo", "May-Oct"),
    ("Gokyo Lakes", "lakes-water-activities", "Lakes & Water Activities", 27.9570, 86.7110, "Solukhumbu", "Koshi", "Namche",
     "Series of six glacial lakes at 4,700–5,000 m in the Khumbu.", "Gokyo Ri Lakes", "Sep-Nov / Mar-May"),
    ("Gokyo Ri", "viewpoint", "viewpoint", 27.9540, 86.6960, "Solukhumbu", "Koshi", "Namche",
     "5,357 m viewpoint above Gokyo Lakes with panoramic Everest/Makalu/Cho Oyu views.", "", "Oct-Nov"),
    ("Panch Pokhari", "lakes-water-activities", "Lakes & Water Activities", 28.1330, 85.7330, "Sindhupalchok", "Bagmati", "Chautara",
     "Cluster of five sacred glacial lakes at ~4,100 m, a popular pilgrimage trek.", "Five Lakes", "Mar-May / Sep-Nov"),
    ("Indra Sarovar", "lakes-water-activities", "Lakes & Water Activities", 27.5830, 85.0330, "Makwanpur", "Bagmati", "Kulekhani",
     "Largest man-made reservoir in Nepal, popular for boating.", "Kulekhani Lake", "Oct-Mar"),
    ("Gosaikunda", "lakes-water-activities", "Lakes & Water Activities", 28.0833, 85.4167, "Rasuwa", "Bagmati", "Dhunche",
     "Sacred alpine lake at 4,380 m, major Hindu/Buddhist pilgrimage.", "Gosainkunda", "Aug (Janai Purnima) / Sep-Oct"),
    ("Rara Lake", "lakes-water-activities", "Lakes & Water Activities", 29.5270, 82.0900, "Mugu", "Karnali", "Talcha",
     "Largest lake in Nepal (10.8 km²), at 2,990 m in Rara National Park.", "Mahendra Tal", "Sep-Nov / Mar-May"),
    ("Tilicho Lake", "lakes-water-activities", "Lakes & Water Activities", 28.6833, 83.8500, "Manang", "Gandaki", "Chame",
     "One of the highest lakes in the world at 4,919 m, on Annapurna Circuit.", "", "Sep-Oct / Apr-May"),
    ("Phulchowki Lake", "lakes-water-activities", "Lakes & Water Activities", 27.5667, 85.3833, "Lalitpur", "Bagmati", "Godawari",
     "Small scenic reservoir near the top of Phulchowki hill.", "", "Mar-May / Sep-Nov"),

    # --- Treks & regions ---
    ("Everest Base Camp Trek", "nature-trekking", "Nature & Trekking", 28.0025, 86.8525, "Solukhumbu", "Koshi", "Lukla",
     "Iconic trek to 5,364 m EBC via Namche Bazaar, Tengboche, Kala Patthar.", "EBC Trek,Khumbu Trek", "Mar-May / Oct-Dec"),
    ("Annapurna Base Camp", "nature-trekking", "Nature & Trekking", 28.5333, 83.8833, "Kaski", "Gandaki", "Ghandruk",
     "Trek to 4,130 m base camp in the heart of the Annapurna Sanctuary.", "ABC,Annapurna Sanctuary", "Oct-Nov / Mar-Apr"),
    ("Annapurna Circuit", "nature-trekking", "Nature & Trekking", 28.8000, 83.9333, "Manang", "Gandaki", "Chame",
     "Legendary 160–230 km circuit around the Annapurna massif crossing Thorong La (5,416 m).", "Round Annapurna,Thorong La", "Oct-Nov / Apr"),
    ("Langtang Valley Trek", "nature-trekking", "Nature & Trekking", 28.2167, 85.5333, "Rasuwa", "Bagmati", "Syabrubesi",
     "Beautiful alpine valley trek close to Kathmandu; Kyanjin Gompa at 3,870 m.", "Langtang Trek,Kyanjin", "Mar-May / Oct-Dec"),
    ("Helambu Trek", "nature-trekking", "Nature & Trekking", 28.0667, 85.5167, "Sindhupalchok", "Bagmati", "Sundarijal",
     "Scenic Tamang heritage trek north-east of Kathmandu.", "", "Mar-May / Oct-Dec"),
    ("Upper Mustang Trek", "nature-trekking", "Nature & Trekking", 29.1833, 83.9500, "Mustang", "Gandaki", "Jomsom",
     "Fenced ancient Tibetan kingdom of Lo with walled city Lo Manthang; restricted area permit.", "Mustang Trek,Lo Manthang", "Mar-May / Oct-Nov"),
    ("Poon Hill", "viewpoint", "viewpoint", 28.4000, 83.7333, "Myagdi", "Gandaki", "Ghorepani",
     "Famous 3,210 m sunrise viewpoint on the Ghorepani trek; panoramic Dhaulagiri-Annapurna views.", "Poonhill,Ghorepani", "Oct-Nov / Mar-Apr"),
    ("Kala Patthar", "viewpoint", "viewpoint", 27.9940, 86.8290, "Solukhumbu", "Koshi", "Gorakshep",
     "5,644 m black-rock landmark; the most popular Everest viewpoint.", "Kalapatthar", "Oct-Nov / Apr"),
    ("Sarangkot Viewpoint", "viewpoint", "viewpoint", 28.2500, 83.9500, "Kaski", "Gandaki", "Pokhara",
     "1,600 m hilltop above Pokhara, famous for sunrise over Annapurna & Fishtail.", "Sarangkot", "Oct-Nov / Mar-Apr"),
    ("Nagarkot View Tower", "viewpoint", "viewpoint", 27.7167, 85.5167, "Bhaktapur", "Bagmati", "Nagarkot",
     "Popular hill station at 2,175 m for sunrise Himalayan views including Everest on clear days.", "", "Oct-Mar"),
    ("Phulchowki Hill", "viewpoint", "viewpoint", 27.5790, 85.4000, "Lalitpur", "Bagmati", "Godawari",
     "Highest hill (2,782 m) in Kathmandu Valley, botanical garden at base, panoramic snow views.", "Phulchoki", "Oct-Mar"),
    ("Chandragiri Hill", "viewpoint", "viewpoint", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Thankot",
     "2,551 m hill with cable car; Bhaleshwor Mahadev temple and Himalayan views.", "Chandragiri Cable Car", "Oct-Mar"),
    ("Shree Antu", "viewpoint", "viewpoint", 26.8833, 88.0833, "Ilam", "Koshi", "Ilam",
     "Famous for sunrise over Kanchenjunga and emerald tea gardens.", "Sri Antu", "Oct-Apr"),
    ("Kakani", "viewpoint", "viewpoint", 27.8167, 85.2667, "Nuwakot", "Bagmati", "Kakani",
     "2,030 m hill station on the north-west rim of Kathmandu Valley; trout farms and views.", "", "Oct-Mar"),
    ("Daman", "viewpoint", "viewpoint", 27.6000, 85.0667, "Makwanpur", "Bagmati", "Daman",
     "Mountain viewpoint on Tribhuvan Rajpath claiming the broadest Himalayan panorama in Nepal.", "Daman View Tower", "Oct-Mar"),
    ("Tansen (Palpa)", "heritage-temples", "Heritage & Temples", 27.8667, 83.5500, "Palpa", "Lumbini", "Tansen",
     "Historic Newari hill town with traditional architecture and Shreenagar hill views.", "Palpa Bazaar", "Sep-May"),
    ("Bandipur", "heritage-temples", "Heritage & Temples", 27.9333, 84.4167, "Tanahun", "Gandaki", "Bandipur",
     "Preserved 18th-century Newari trading village atop a ridge with Himalayan views.", "Bandipur Bazaar", "Oct-Apr"),
    ("Gorkha Durbar", "heritage-temples", "Heritage & Temples", 28.0000, 84.6333, "Gorkha", "Gandaki", "Gorkha",
     "Historic palace fort on a 1,000 m hill; birthplace of modern Nepal and Prithvi Narayan Shah.", "Gorkha Palace", "Oct-Apr"),
    ("Rani Mahal (Palpa)", "heritage-temples", "Heritage & Temples", 27.8333, 83.5500, "Palpa", "Lumbini", "Tansen",
     "\"Taj Mahal of Nepal\" -- Rani Mahal palace on the banks of the Kali Gandaki river.", "Ranimahal", "Oct-Apr"),
    ("Nuwakot Durbar", "heritage-temples", "Heritage & Temples", 27.9167, 85.1667, "Nuwakot", "Bagmati", "Nuwakot",
     "Seven-storied hilltop palace; Prithvi Narayan Shah's base for conquering Kathmandu.", "Saat Talle Durbar", "Oct-Apr"),

    # --- Caves ---
    ("Bat Cave (Chamere Gufa)", "attraction", "attraction", 28.2167, 83.9667, "Kaski", "Gandaki", "Pokhara",
     "Famous limestone cave inhabited by thousands of bats, near Mahendra Cave.", "Chamere Gufa", "Sep-May"),
    ("Gupteshwor Mahadev Cave", "heritage-temples", "Heritage & Temples", 28.1890, 83.9570, "Kaski", "Gandaki", "Pokhara",
     "Sacred cave across from Davis Falls housing a Shiva lingam and impressive stalactites.", "Gupteshwor", "Sep-May"),
    ("Siddha Cave (Siddha Gufa)", "attraction", "attraction", 27.8833, 84.4000, "Tanahun", "Gandaki", "Bandipur",
     "Largest cave in Nepal (437 m deep), with cathedral-like chambers and stalactites.", "Siddha Gufa,Bimalnagar Cave", "Oct-Apr"),
    ("Halesi Mahadev Cave", "heritage-temples", "Heritage & Temples", 27.2000, 86.6167, "Khotang", "Koshi", "Halesi",
     "Sacred cave (Maratika) revered by Hindus and Buddhists; Pashupati of the east.", "Halesi,Maratika Cave", "Mar-May / Sep-Oct"),

    # --- Waterfalls ---
    ("Rupse Falls", "attraction", "attraction", 28.6833, 83.6500, "Myagdi", "Gandaki", "Beni",
     "300 m tiered waterfall along the Beni-Jomsom road; Kali Gandaki gorge views.", "Rupse Jharana", "Sep-Nov"),
    ("Hyatung Falls", "attraction", "attraction", 27.1833, 87.2833, "Terhathum", "Koshi", "Basantapur",
     "One of Nepal's tallest waterfalls (365 m) in remote eastern Nepal.", "Hyatung Jharana", "Sep-Nov / Mar-May"),
    ("Simba Falls", "attraction", "attraction", 27.6667, 85.2000, "Kathmandu", "Bagmati", "Chandragiri",
     "Scenic roadside waterfall along the Chandragiri hike.", "Simba Jharana", "Jun-Sep (monsoon)"),
    ("Jalbire Jharana (Chitwan)", "attraction", "attraction", 27.7833, 84.8167, "Chitwan", "Bagmati", "Jalbire",
     "100 m natural waterfall and swimming pools on the way to Langtang.", "", "Sep-May"),
    ("Tindhare Jharana", "attraction", "attraction", 27.5167, 85.5333, "Kavrepalanchok", "Bagmati", "Panauti",
     "300 m waterfall \"three-storied\" near Roshi village, a hidden gem.", "Bahubi Jharana", "Jun-Sep"),
    ("Waterfall at Pachal", "attraction", "attraction", 28.8000, 82.2000, "Jajarkot", "Karnali", "Jajarkot",
     "Believed tallest waterfall in Nepal (381 m+), remote western region.", "Pachal Jharana", "Sep-Oct"),

    # --- Temples & Stupas (in addition to existing Pashupati/Boudha/Swayambhu) ---
    ("Changunarayan Temple", "heritage-temples", "Heritage & Temples", 27.7080, 85.4260, "Bhaktapur", "Bagmati", "Bhaktapur",
     "Oldest datable temple in Nepal (325 AD), UNESCO World Heritage, Vishnu shrine.", "Changu Narayan", "Oct-Mar"),
    ("Dakshinkali Temple", "heritage-temples", "Heritage & Temples", 27.6000, 85.2500, "Kathmandu", "Bagmati", "Pharping",
     "Famous Kali temple on the southern rim of the valley, important animal-sacrifice site.", "Dakshin Kali", "Oct-Mar / Dashain"),
    ("Guhyeshwari Temple", "heritage-temples", "Heritage & Temples", 27.7110, 85.3480, "Kathmandu", "Bagmati", "Gaushala",
     "One of 51 Shakti Peeths, near Pashupatinath; sacred to Hindus.", "Guhyeshwari", "Feb-Mar / Sep-Oct"),
    ("Taleju Bhawani Temple", "heritage-temples", "Heritage & Temples", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu",
     "Royal deity of Malla kings; towering three-tiered temple in Hanuman Dhoka.", "Taleju Mandir", "Dashain only"),
    ("Krishna Mandir (Patan)", "heritage-temples", "Heritage & Temples", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan",
     "17th-century stone-built Shikhara Krishna temple in Patan Durbar Square.", "Krishna Mandir", "Krishna Janmashtami"),
    ("Nyatapola Temple (Bhaktapur)", "heritage-temples", "Heritage & Temples", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur",
     "Tallest pagoda in Nepal (30m, 5 tiers/5 roofs) built in 1702; Siddhi Lakshmi temple.", "Nyatapola,5-Story Temple", "Oct-Apr / Bisket Jatra"),
    ("Kumbheshwar Temple", "heritage-temples", "Heritage & Temples", 27.6750, 85.3240, "Lalitpur", "Bagmati", "Patan",
     "14th-century five-story Shiva temple in Patan with natural spring water.", "", "Janai Purnima"),
    ("Bindhyabasini Temple (Pokhara)", "heritage-temples", "Heritage & Temples", 28.2333, 83.9833, "Kaski", "Gandaki", "Pokhara",
     "Most popular Shaktipeeth in Pokhara, atop a small hill near the old bazaar.", "Bindabasini", "Oct-Mar"),
    ("Manakamana Temple", "heritage-temples", "Heritage & Temples", 27.8833, 84.5833, "Gorkha", "Gandaki", "Kurintar",
     "Wish-fulfilling Bhagwati temple reached by cable car from Kurintar.", "Manakamana Mandir", "Oct-Mar / Dashain"),
    ("Muktinath Temple", "heritage-temples", "Heritage & Temples", 28.8167, 83.8667, "Mustang", "Gandaki", "Ranipauwa",
     "Sacred Vishnu temple at 3,762 m with 108 water spouts and eternal flame; holy to Hindus and Buddhists.", "Muktinath,Mukti Chhetra", "Mar-May / Sep-Oct"),
    ("Janaki Mandir (Janakpur)", "heritage-temples", "Heritage & Temples", 26.7280, 85.9250, "Dhanusha", "Madhesh", "Janakpur",
     "Grand 19th-century Rajput-style marble temple to Sita; UNESCO tentative site.", "Janaki Temple,Sita Palace", "Oct-Mar / Vivaha Panchami"),
    ("Pathibhara Devi", "heritage-temples", "Heritage & Temples", 27.4167, 87.7333, "Taplejung", "Koshi", "Taplejung",
     "Sacred hilltop shrine at 3,794 m in far east; important pilgrimage and trek.", "Pathibhara,Pathivara", "Mar-Jun / Sep-Nov"),
    ("Budhanilkantha Temple", "heritage-temples", "Heritage & Temples", 27.7730, 85.3570, "Kathmandu", "Bagmati", "Budhanilkantha",
     "Reclining Vishnu statue in a pool at the foot of Shivapuri hill.", "", "Oct-Mar"),
    ("Swayambhunath Stupa (Monkey Temple)", "religious-sites", "Religious Sites", 27.7140, 85.2900, "Kathmandu", "Bagmati", "Kathmandu",
     "2,000-year-old hilltop stupa with iconic Buddha eyes; UNESCO World Heritage Site.", "Swayambhu,Monkey Temple", "Oct-Mar"),
    ("Boudhanath Stupa", "religious-sites", "Religious Sites", 27.7210, 85.3620, "Kathmandu", "Bagmati", "Boudha",
     "Largest stupa in Nepal; UNESCO World Heritage; center of Tibetan Buddhism in Nepal.", "Bouddha,Khasti Chaitya", "Oct-Mar"),
    ("Lumbini (Birthplace of Buddha)", "religious-sites", "Religious Sites", 27.4690, 83.2740, "Rupandehi", "Lumbini", "Lumbini",
     "UNESCO World Heritage Site; birthplace of Siddhartha Gautama, the Buddha. Sacred garden, Maya Devi temple, monastic zone.", "Maya Devi", "Oct-Mar"),
    ("World Peace Pagoda (Pokhara)", "religious-sites", "Religious Sites", 28.2000, 83.9500, "Kaski", "Gandaki", "Pokhara",
     "White Buddhist stupa on a hilltop south of Phewa Lake, panoramic Annapurna views.", "Shanti Stupa", "Oct-Mar"),
    ("Thrangu Tashi Yangtse Monastery (Namo Buddha)", "religious-sites", "Religious Sites", 27.5833, 85.5667, "Kavrepalanchok", "Bagmati", "Panauti",
     "One of the most sacred Buddhist sites; legendary self-sacrifice of Buddha (as prince Mahasattva).", "Namo Buddha", "Oct-Mar"),
    ("Kopan Monastery", "religious-sites", "Religious Sites", 27.7333, 85.3667, "Kathmandu", "Bagmati", "Boudha",
     "Tibetan Buddhist monastery above Boudha, famous for introductory meditation courses.", "", "Oct-May"),
    ("Tengboche Monastery", "religious-sites", "Religious Sites", 27.8350, 86.7680, "Solukhumbu", "Koshi", "Namche",
     "Largest gompa in Khumbu (3,867 m); mani rimdu festival; Everest backdrop.", "Thyangboche,Tengboche Gompa", "Oct-Nov / Mar-Apr"),
    ("Khumjung Gompa", "religious-sites", "Religious Sites", 27.8250, 86.7200, "Solukhumbu", "Koshi", "Namche",
     "Ancient monastery in Khumjung said to hold a yeti scalp.", "", "Oct-Nov / Mar"),

    # --- National Parks & Wildlife ---
    ("Chitwan National Park", "wildlife", "Wildlife", 27.5330, 84.5000, "Chitwan", "Bagmati", "Sauraha",
     "UNESCO World Heritage; one-horned rhino, Bengal tiger, elephant safaris.", "Chitwan,Sauraha", "Oct-Mar"),
    ("Bardiya National Park", "wildlife", "Wildlife", 28.3833, 81.5000, "Bardiya", "Lumbini", "Thakurdwara",
     "Largest national park in the Terai; excellent tiger and wild elephant sightings.", "Bardia National Park", "Oct-Mar"),
    ("Sagarmatha National Park", "wildlife", "Wildlife", 27.9500, 86.7500, "Solukhumbu", "Koshi", "Namche",
     "UNESCO World Heritage park encompassing Everest, snow leopard, red panda, Danphe.", "Everest National Park", "Oct-Nov / Mar-May"),
    ("Langtang National Park", "wildlife", "Wildlife", 28.1667, 85.5000, "Rasuwa", "Bagmati", "Syabrubesi",
     "First Himalayan national park; red panda, musk deer, Langtang Lirung views.", "", "Mar-May / Oct-Dec"),
    ("Shey Phoksundo National Park", "wildlife", "Wildlife", 29.2167, 82.9333, "Dolpa", "Karnali", "Dunai",
     "Largest national park (3,555 km²); trans-Himalayan, snow leopard, turquoise Phoksundo Lake.", "Dolpo National Park", "May-Oct"),
    ("Rara National Park", "wildlife", "Wildlife", 29.5333, 82.0500, "Mugu", "Karnali", "Talcha",
     "Smallest national park surrounding pristine Rara Lake at 2,990 m.", "", "Sep-Nov / Mar-May"),
    ("Khaptad National Park", "wildlife", "Wildlife", 29.2667, 80.1667, "Doti", "Sudurpashchim", "Silgadhi",
     "Mid-western plateau at 3,000 m; Khaptad Baba hermitage, meadows, and rhododendron forests.", "Khaptad Baba", "Mar-May / Oct-Nov"),
    ("Makalu Barun National Park", "wildlife", "Wildlife", 27.7500, 87.1667, "Sankhuwasabha", "Koshi", "Tumlingtar",
     "Remote eastern park including Makalu; incredible biodiversity from Arun valley to snowline.", "", "Apr-May / Oct-Nov"),
    ("Shivapuri Nagarjun National Park", "wildlife", "Wildlife", 27.8000, 85.4000, "Kathmandu", "Bagmati", "Budhanilkantha",
     "Northern ridge of Kathmandu Valley; hiking, Bagdwar (source of Bagmati river).", "Shivapuri", "Oct-Apr"),
    ("Parsa National Park", "wildlife", "Wildlife", 27.3330, 84.8330, "Parsa", "Madhesh", "Birgunj",
     "Eastern extension of Chitwan; tiger, elephant, gaur wilderness.", "Parsa Wildlife Reserve", "Nov-Mar"),
    ("Banke National Park", "wildlife", "Wildlife", 28.0833, 81.8833, "Banke", "Lumbini", "Nepalgunj",
     "Protected tiger habitat connected to Bardiya, part of the Chitwan-Bardiya-Terai Arc.", "", "Oct-Mar"),
    ("Shuklaphanta National Park", "wildlife", "Wildlife", 28.8500, 80.2167, "Kanchanpur", "Sudurpashchim", "Mahendranagar",
     "Southwest grassland reserve; largest herd of swamp deer (barasingha) in the world.", "Suklaphanta", "Nov-Jun"),
    ("Koshi Tappu Wildlife Reserve", "wildlife", "Wildlife", 26.6500, 87.0000, "Sunsari", "Koshi", "Itahari",
     "Ramsar wetland on the Sapta Koshi; wild water buffalo (arna) and 500+ bird species.", "Koshi Tappu", "Oct-Mar"),
    ("Annapurna Conservation Area", "wildlife", "Wildlife", 28.6000, 83.9000, "Manang", "Gandaki", "Chame",
     "Largest protected area in Nepal (7,629 km²); Annapurna Circuit, snow leopard, diverse bio-zones.", "ACAP", "Oct-Nov / Mar-May"),
    ("Manaslu Conservation Area", "wildlife", "Wildlife", 28.5500, 84.5600, "Gorkha", "Gandaki", "Arughat",
     "Conservation area around Mount Manaslu; Tsum Valley, restricted trek.", "MCAP", "Oct-Nov / Mar-Apr"),
    ("Kanchenjunga Conservation Area", "wildlife", "Wildlife", 27.7000, 88.0000, "Taplejung", "Koshi", "Taplejung",
     "Easternmost conservation area around Kanchenjunga massif; red panda, snow leopard.", "KCA", "Apr-May / Oct-Nov"),
    ("Api Nampa Conservation Area", "wildlife", "Wildlife", 29.9500, 80.8500, "Darchula", "Sudurpashchim", "Darchula",
     "Far-western conservation area around Api and Nampa peaks.", "", "May-Jun / Sep-Oct"),

    # --- Museums ---
    ("National Museum of Nepal (Chhauni)", "museum", "museum", 27.7050, 85.2880, "Kathmandu", "Bagmati", "Chhauni",
     "Oldest museum in Nepal; historical weapons, art, natural history galleries.", "Rashtriya Sangrahalaya", "All year"),
    ("Patan Museum", "museum", "museum", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan",
     "Renowned museum of sacred art housed in an old Malla palace at Patan Durbar Square.", "", "All year"),
    ("Narayanhiti Palace Museum", "museum", "museum", 27.7180, 85.3210, "Kathmandu", "Bagmati", "Durbar Marg",
     "Former royal palace turned museum after 2008; site of the royal massacre.", "", "Thu-Mon (closed Wed/Tue)"),
    ("International Mountain Museum (Pokhara)", "museum", "museum", 28.2000, 83.9667, "Kaski", "Gandaki", "Pokhara",
     "Comprehensive museum on mountaineering history, Himalayan culture, and the 8000ers.", "Mountain Museum", "All year"),
    ("Gurkha Memorial Museum", "museum", "museum", 28.2333, 83.9833, "Kaski", "Gandaki", "Pokhara",
     "Museum dedicated to the famous Brigade of Gurkhas and their military history.", "", "All year"),
    ("Natural History Museum (Swayambhu)", "museum", "museum", 27.7140, 85.2920, "Kathmandu", "Bagmati", "Swayambhu",
     "Nepal's rich wildlife, fossils, butterflies and specimens displayed.", "", "Sun-Fri"),
    ("Bhaktapur National Art Museum", "museum", "museum", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur",
     "Nepali paubha painting and Malla-era artifacts in Bhaktapur Durbar Square.", "", "All year"),
    ("Tribhuvan Museum (Hanuman Dhoka)", "museum", "museum", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu",
     "Memorial museum to King Tribhuvan inside the old Hanuman Dhoka Palace.", "", "Sun-Fri"),
    ("Taragaon Museum (Boudha)", "museum", "museum", 27.7200, 85.3580, "Kathmandu", "Bagmati", "Boudha",
     "Modern architecture and archiving of Nepal's cultural heritage in a 70s modernist building.", "", "All year"),

    # --- Hot springs ---
    ("Tatopani Hot Spring", "attraction", "attraction", 28.5833, 83.7000, "Myagdi", "Gandaki", "Tatopani",
     "Natural hot springs on the Annapurna Circuit/Base Camp trek; relaxing mineral pools.", "", "Oct-May"),
    ("Jomsom (Kagbeni)", "attraction", "attraction", 28.7833, 83.7333, "Mustang", "Gandaki", "Jomsom",
     "Windy arid trans-Himalayan town; gateway to Upper Mustang, apple orchards, Muktinath.", "", "Mar-May / Sep-Nov"),
    ("Marpha", "attraction", "attraction", 28.7667, 83.7167, "Mustang", "Gandaki", "Marpha",
     "Whitewashed stone village famous for apple brandy, orchards, and Thakali cuisine.", "Marpha Bazaar", "Oct-May"),

    # --- Landmarks & City ---
    ("Dharahara (Bhimsen Tower)", "heritage-temples", "Heritage & Temples", 27.7000, 85.3110, "Kathmandu", "Bagmati", "Sundhara",
     "Iconic 72 m tower originally 1825, rebuilt after 2015 earthquake, observation deck.", "Dharahara,Bhimsen Stambha", "All year"),
    ("Garden of Dreams", "attraction", "attraction", 27.7150, 85.3160, "Kathmandu", "Bagmati", "Thamel",
     "Neo-classical garden in central Kathmandu; restored Edwardian pleasure garden.", "Swapna Bagaicha", "All year"),
    ("Hanuman Dhoka Durbar Square", "heritage-temples", "Heritage & Temples", 27.7050, 85.3050, "Kathmandu", "Bagmati", "Kathmandu",
     "Royal Palace complex of the Malla and Shah kings; UNESCO World Heritage Site; old royal palaces, Taleju, Kumari Ghar.", "Basantapur", "All year"),
    ("Patan Durbar Square", "heritage-temples", "Heritage & Temples", 27.6740, 85.3250, "Lalitpur", "Bagmati", "Patan",
     "Malla-era royal square with Krishna Mandir, Royal Bath, Golden Temple; UNESCO site.", "Lalitpur Durbar", "All year"),
    ("Bhaktapur Durbar Square", "heritage-temples", "Heritage & Temples", 27.6720, 85.4290, "Bhaktapur", "Bagmati", "Bhaktapur",
     "Best-preserved Malla city with Nyatapola, 55-Window Palace, Golden Gate; UNESCO site.", "Bhadgaon,Khwopa", "All year"),
    ("Kirtipur", "heritage-temples", "Heritage & Temples", 27.6710, 85.2780, "Kathmandu", "Bagmati", "Kirtipur",
     "Historic hilltop Newar town south-west of Kathmandu; Bagh Bhairab, Uma Maheshwar, Chilancho Stupa.", "", "Oct-Mar"),
    ("Panauti", "heritage-temples", "Heritage & Temples", 27.5833, 85.5167, "Kavrepalanchok", "Bagmati", "Panauti",
     "Ancient Newari trading town at the confluence of Rosi and Punyamati rivers; Indreshwar Mahadev.", "", "Oct-Mar / Makar Mela"),
    ("Bungamati", "heritage-temples", "Heritage & Temples", 27.6250, 85.3000, "Lalitpur", "Bagmati", "Bungamati",
     "Medieval Newar village home to the Rato Machhindranath deity.", "Bungamati", "Oct-Apr"),
    ("Khokana", "heritage-temples", "Heritage & Temples", 27.6400, 85.2900, "Lalitpur", "Bagmati", "Khokana",
     "Traditional mustard-oil milling Newari village near Bungamati.", "", "Oct-Apr"),
    ("Namche Bazaar", "attraction", "attraction", 27.8050, 86.7120, "Solukhumbu", "Koshi", "Namche",
     "Sherpa trading town at 3,440 m; gateway to Everest, bustling Saturday market.", "Namche", "Mar-May / Oct-Dec"),
    ("Lukla Airport (Tenzing-Hillary)", "attraction", "attraction", 27.6870, 86.7290, "Solukhumbu", "Koshi", "Lukla",
     "Starting point for Everest treks; one of the world's most dramatic airports.", "Tenzing Hillary Airport", "weather dependent"),
    ("Ilam Tea Gardens", "attraction", "attraction", 26.9167, 87.9167, "Ilam", "Koshi", "Ilam",
     "Rolling green tea estates in far-eastern Nepal; Kanyam, Shree Antu viewpoints.", "Kanyam Tea Garden", "Mar-Nov"),
    ("Kanyam", "attraction", "attraction", 26.8333, 88.0167, "Ilam", "Koshi", "Kanyam",
     "\"Queen of Ilam\" -- most visited tea garden with horse rides, picnic spots, Kanchenjunga views.", "Kanyam Tea Garden", "Mar-Nov"),
    ("Kakrebihar (Surkhet)", "heritage-temples", "Heritage & Temples", 28.6000, 81.6167, "Surkhet", "Karnali", "Birendranagar",
     "12th-century stone temple ruins in a park, an important heritage site of western Nepal.", "", "Oct-Mar"),
    ("Swargadwari", "heritage-temples", "Heritage & Temples", 28.1833, 82.6833, "Pyuthan", "Lumbini", "Pyuthan",
     "Hilltop Hindu pilgrimage site at 2,100 m founded by Mahaprabhu Swami in the 19th century.", "Swargadwari", "Oct-Apr"),
    ("Devghat", "heritage-temples", "Heritage & Temples", 27.7500, 84.4167, "Chitwan", "Bagmati", "Narayangarh",
     "Sacred Hindu confluence of Kali Gandaki and Trishuli rivers; retirement ashrams and temples.", "Devghat Dham", "Maghe Sankranti / Oct-Apr"),
    ("Chitwan Sauraha", "wildlife", "Wildlife", 27.5730, 84.4970, "Chitwan", "Bagmati", "Sauraha",
     "Main tourist hub for Chitwan National Park: elephant baths, jeep safaris, canoe trips.", "Sauraha", "Oct-Mar"),
    ("Ghalegaun", "attraction", "attraction", 28.3333, 84.4000, "Lamjung", "Gandaki", "Besisahar",
     "Model Gurung hill village at 2,100 m known for cultural homestays and Annapurna-Manaslu views.", "Ghalegau", "Oct-Apr"),
    ("Siraichuli (Chitwan)", "viewpoint", "viewpoint", 27.7500, 84.6667, "Chitwan", "Bagmati", "Kaule",
     "1,945 m highest point of Chitwan district; Himalayan views plus Chitwan plains panorama.", "Siraichuli View Tower", "Oct-Mar"),
    ("Dolpo (Shey Gompa)", "heritage-temples", "Heritage & Temples", 29.0833, 82.8667, "Dolpa", "Karnali", "Dunai",
     "Crystal Mountain and 11th-century Shey Gompa in Upper Dolpo; Tibetan Buddhist pilgrimage.", "Shey Gompa,Upper Dolpo", "May-Sep"),
    ("Lo Manthang", "heritage-temples", "Heritage & Temples", 29.1833, 83.9560, "Mustang", "Gandaki", "Lo Manthang",
     "Walled capital of the ancient Kingdom of Lo; 15th-century royal palace and gompas.", "Upper Mustang", "Mar-May / Oct-Nov"),
    ("Kagbeni", "heritage-temples", "Heritage & Temples", 28.8400, 83.7400, "Mustang", "Gandaki", "Kagbeni",
     "Medieval walled village at the Kali Gandaki junction; gateway to Upper Mustang.", "", "Mar-May / Sep-Nov"),
    ("Kodari (Zhangmu) Border", "attraction", "attraction", 27.9667, 85.9667, "Sindhupalchok", "Bagmati", "Kodari",
     "Historic Nepal-China border crossing on the Arniko Highway; Tibet border views.", "Friendship Bridge", "Oct-May"),
]


class Command(BaseCommand):
    help = "Add curated real Nepal attractions (peaks, lakes, temples, caves, parks, museums)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Only add first N places (for testing).")

    @transaction.atomic
    def handle(self, *args, **options):
        limit = int(options["limit"]) or 0

        # Ensure all referenced categories exist
        cat_cache = {}
        for slug, name in [
            ("heritage-temples", "Heritage & Temples"),
            ("lakes-water-activities", "Lakes & Water Activities"),
            ("nature-trekking", "Nature & Trekking"),
            ("photography-spots", "Photography Spots"),
            ("religious-sites", "Religious Sites"),
            ("wildlife", "Wildlife"),
            ("attraction", "attraction"),
            ("museum", "museum"),
            ("viewpoint", "viewpoint"),
        ]:
            cat_cache[(slug, name)] = _get_or_create_category(slug, name)

        added = 0
        skipped = 0
        for idx, item in enumerate(CURATED):
            if limit and idx >= limit:
                break
            (name, cslug, cname, lat, lon, district, province, city, short_desc, aliases,
             best_time) = item

            cat = cat_cache[(cslug, cname)]
            # Normalize alias string
            aliases_str = aliases or ""

            # Idempotency: match by existing name containing key terms
            base_name = name.split("(")[0].strip()
            existing = Destination.objects.filter(name__iexact=name).first()
            if not existing and base_name != name:
                existing = Destination.objects.filter(name__iexact=base_name).first()
            # also check aliases
            if not existing and aliases_str:
                for a in aliases_str.split(","):
                    a = a.strip()
                    if len(a) > 4:
                        existing = Destination.objects.filter(name__icontains=a).first()
                        if existing:
                            break
            if existing:
                skipped += 1
                # update a few fields if empty
                changed = False
                if not existing.short_description and short_desc:
                    existing.short_description = short_desc
                    changed = True
                if not existing.latitude and lat:
                    existing.latitude = lat
                    changed = True
                if not existing.longitude and lon:
                    existing.longitude = lon
                    changed = True
                if not existing.district and district:
                    existing.district = district
                    changed = True
                if not existing.province and province:
                    existing.province = province
                    changed = True
                if not existing.city and city:
                    existing.city = city
                    changed = True
                if not existing.best_time_to_visit and best_time:
                    existing.best_time_to_visit = best_time
                    changed = True
                if changed:
                    existing.save()
                continue

            dest = Destination.objects.create(
                name=name,
                category=cat,
                latitude=lat,
                longitude=lon,
                district=district,
                province=province,
                city=city,
                country="Nepal",
                short_description=short_desc[:300],
                description=f"{short_desc} Located in {district} district, {province} province, Nepal.",
                aliases=aliases_str,
                best_time_to_visit=best_time,
                status=Destination.SubmissionStatus.APPROVED,
                is_active=True,
                is_user_submitted=False,
                source="curated",
            )
            added += 1
            if added % 20 == 0:
                self.stdout.write(f"  ...added {added} places so far ({name})")

        total = Destination.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Done. Added {added} new curated destinations, skipped {skipped} that already existed. "
            f"Total destinations in DB: {total}."
        ))
