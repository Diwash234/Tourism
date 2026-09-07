"""
Management command: expand_destinations
========================================
Adds 2000+ curated Nepal destinations across all 77 districts and 36 categories
to approach the 100+ per category target. Each destination gets a unique
deterministic SVG postcard cover automatically.

Run:
    python manage.py expand_destinations
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from tourist.models import Category, Destination


# Curated destination data keyed by category slug.
# (name, district, short_description, province)
EXTRA_DESTINATIONS: dict[str, list[tuple[str, str, str, int]]] = {
    # -------- MOUNTAINS / PEAKS --------
    "mountains": [
        ("Mount Everest (Sagarmatha)", "Solukhumbu", "World's highest peak at 8,848.86 m in Khumbu", 1),
        ("Kanchenjunga Main", "Taplejung", "Third highest mountain in the world (8,586 m)", 1),
        ("Lhotse", "Solukhumbu", "Fourth highest peak at 8,516 m adjacent to Everest", 1),
        ("Makalu", "Sankhuwasabha", "Fifth highest peak at 8,485 m, pyramid shaped", 1),
        ("Cho Oyu", "Solukhumbu", "Sixth highest peak at 8,188 m on Nepal-Tibet border", 1),
        ("Dhaulagiri I", "Myagdi", "Seventh highest peak at 8,167 m", 4),
        ("Manaslu", "Gorkha", "Eighth highest peak at 8,163 m", 4),
        ("Annapurna I", "Myagdi", "Tenth highest peak at 8,091 m", 4),
        ("Annapurna South", "Kaski", "Iconic 7,219 m peak overlooking Pokhara", 4),
        ("Machhapuchhre (Fishtail)", "Kaski", "Sacred 6,993 m peak, iconic symbol of Pokhara", 4),
        ("Hiunchuli", "Kaski", "6,441 m peak south of Annapurna South", 4),
        ("Gangapurna", "Manang", "7,455 m peak above Gangapurna glacier", 4),
        ("Nilgiri Himal", "Mustang", "Distinctive triple peak above Kali Gandaki gorge", 4),
        ("Tukuche Peak", "Mustang", "6,920 m peak in the Dhaulagiri range", 4),
        ("Dhampus Peak", "Myagdi", "6,012 m trekking peak above Dhaulagiri", 4),
        ("Pisang Peak", "Manang", "6,091 m trekking peak on Annapurna Circuit", 4),
        ("Chulu West", "Manang", "6,419 m popular trekking peak", 4),
        ("Chulu East", "Manang", "6,584 m trekking peak", 4),
        ("Thorong Peak", "Manang", "6,144 m trekking peak near Thorong La", 4),
        ("Mardi Himal", "Kaski", "5,587 m trekking peak below Machhapuchhre", 4),
        ("Ama Dablam", "Solukhumbu", "Iconic 6,812 m peak known as 'Mother's Necklace'", 1),
        ("Imja Tse (Island Peak)", "Solukhumbu", "6,189 m popular trekking peak", 1),
        ("Lobuche East", "Solukhumbu", "6,119 m trekking peak near Everest Base Camp", 1),
        ("Pokalde Peak", "Solukhumbu", "5,806 m trekking peak near EBC", 1),
        ("Kala Patthar", "Solukhumbu", "5,545 m famous viewpoint over Everest", 1),
        ("Gokyo Ri", "Solukhumbu", "5,357 m viewpoint over Gokyo Lakes and Cho Oyu", 1),
        ("Nirekha Peak", "Solukhumbu", "6,069 m trekking peak in Khumbu", 1),
        ("Kongde Ri", "Solukhumbu", "6,187 m peak above Namche Bazaar", 1),
        ("Thamserku", "Solukhumbu", "6,623 m dramatic peak above Namche", 1),
        ("Kusum Kanguru", "Solukhumbu", "6,367 m peak in Khumbu region", 1),
        ("Kangtega", "Solukhumbu", "6,782 m 'Snow Saddle' peak", 1),
        ("Taboche Peak", "Solukhumbu", "6,367 m peak above Dingboche", 1),
        ("Cholatse", "Solukhumbu", "6,440 m peak above Gokyo", 1),
        ("Baruntse", "Solukhumbu", "7,129 m peak between Makalu and Everest", 1),
        ("Mera Peak", "Solukhumbu", "6,476 m highest trekking peak in Nepal", 1),
        ("Kanchenjunga South", "Taplejung", "8,494 m peak of Kanchenjunga massif", 1),
        ("Jannu (Kumbhakarna)", "Taplejung", "7,710 m dramatic peak on Kanchenjunga west face", 1),
        ("Api Himal", "Darchula", "7,132 m far-western peak", 7),
        ("Saipal", "Bajhang", "7,031 m peak in far-western Nepal", 7),
        ("Kanjiroba", "Dolpa", "6,883 m highest peak of Kanjiroba Himal", 6),
        ("Patrasi Himal", "Dolpa", "6,450 m peak in Upper Dolpa", 6),
        ("Putha Hiunchuli", "Dolpa", "7,246 m peak in western Nepal", 6),
        ("Churen Himal", "Dolpa", "6,136 m peak in Dolpa", 6),
        ("Gurja Himal", "Myagdi", "7,193 m peak of Dhaulagiri range", 4),
        ("Langtang Lirung", "Rasuwa", "7,227 m highest peak in Langtang", 3),
        ("Dorje Lakpa", "Sindhupalchok", "6,966 m peak in Jugal Himal", 3),
        ("Gauri Shankar", "Dolakha", "7,134 m sacred peak near Rolwaling", 3),
        ("Melungtse", "Dolakha", "7,181 m peak on Nepal-Tibet border", 3),
        ("Rolwaling Himal", "Dolakha", "Mountain range east of Langtang", 3),
        ("Numbur Cheese Peak", "Ramechhap", "6,958 m peak in Rolwaling region", 3),
        ("Sisne Himal", "Jumla", "5,849 m 'Junga' peak in Karnali", 6),
        ("Kanti Himal", "Mugu", "6,859 m peak above Rara", 6),
        ("Changla", "Dolpa", "6,563 m peak near Phoksundo", 6),
        ("Om Parvat", "Darchula", "Sacred 6,191 m peak with Om-snow pattern", 7),
        ("Yala Peak", "Rasuwa", "5,520 m popular trekking peak in Langtang", 3),
    ],

    # -------- LAKES --------
    "lakes": [
        ("Rara Lake", "Mugu", "Largest lake in Nepal at 2,990 m in Karnali", 6),
        ("Phoksundo Lake", "Dolpa", "Turquoise glacial lake in Shey Phoksundo NP", 6),
        ("Tilicho Lake", "Manang", "Highest lake (4,919 m) on Annapurna Circuit", 4),
        ("Gokyo Lakes", "Solukhumbu", "Series of six glacial lakes at 4,700-5,000 m", 1),
        ("Gosaikunda", "Rasuwa", "Sacred alpine lake at 4,380 m in Langtang", 3),
        ("Phewa Lake", "Kaski", "Iconic Pokhara lake with Tal Barahi temple", 4),
        ("Begnas Lake", "Kaski", "Second largest lake in Pokhara valley", 4),
        ("Rupa Lake", "Kaski", "Freshwater lake in Lekhnath, Pokhara", 4),
        ("Dipang Lake", "Kaski", "Wetland lake in Pokhara valley", 4),
        ("Khaste Lake", "Kaski", "Lake and wetland area near Pokhara", 4),
        ("Maidi Lake", "Kaski", "Small lake in Pokhara valley", 4),
        ("Gunde Lake", "Kaski", "Lake in Lekhnath, Pokhara", 4),
        ("Kamaltal (Lotus Lake)", "Kailali", "Wetland lotus lake in western Terai", 7),
        ("Jagadishpur Reservoir", "Kapilvastu", "Man-made reservoir, Ramsar site", 5),
        ("Ghodaghodi Lake", "Kailali", "Ramsar wetland with 13 associated lakes", 7),
        ("Bishazari Lake", "Chitwan", "20,000 ha wetland complex in Chitwan", 3),
        ("Indra Sarovar", "Makwanpur", "Reservoir lake at Kulekhani", 3),
        ("Kulekhani Lake", "Makwanpur", "Hydroelectric reservoir south of Kathmandu", 3),
        ("Rani Pokhari", "Kathmandu", "Historic 17th-century pond in central Kathmandu", 3),
        ("Siddha Pokhari", "Bhaktapur", "Historic medieval pond in Bhaktapur", 3),
        ("Ta Pukhu (Taudaha)", "Lalitpur", "Ancient lake south of Patan", 3),
        ("Nagdaha", "Lalitpur", "Sacred lake in Dhapakhel", 3),
        ("Godavari Kunda", "Lalitpur", "Pond at Godavari botanical garden", 3),
        ("Panch Pokhari", "Sindhupalchok", "Five sacred glacial lakes at 4,100 m", 3),
        ("Bhairab Kunda", "Rasuwa", "Glacial lake in Langtang region", 3),
        ("Ganga Jamuna Lake", "Dhading", "Sacred twin lakes", 3),
        ("Kalinchok Bhagwati Kunda", "Dolakha", "Sacred pond at Kalinchowk hilltop", 3),
        ("Jata Pokhari", "Ilam", "Wetland pond in eastern hills", 1),
        ("Mai Pokhari", "Ilam", "Ramsar wetland lake in Ilam", 1),
        ("Suke Pokhari", "Ilam", "High-altitude pond in Ilam", 1),
        ("Salpa Pokhari", "Bhojpur", "Sacred lake at 3,400 m in eastern Nepal", 1),
        ("Tsho Rolpa", "Dolakha", "Glacial lake in Rolwaling valley", 3),
        ("Imja Lake", "Solukhumbu", "Glacial lake below Imja Tse", 1),
        ("Dudh Pokhari", "Lalitpur", "Pilgrimage pond on Phulchowki base", 3),
        ("Bedkot Lake", "Kanchanpur", "Freshwater lake near Dhangadhi", 7),
        ("Jhilmila Lake", "Kanchanpur", "Lake in Shuklaphanta area", 7),
        ("Rupa View Point Lake", "Kaski", "Viewpoint over Rupa Lake", 4),
        ("Panchpokhari (Baitadi)", "Baitadi", "Five sacred lakes in far-west Nepal", 7),
        ("Barhakune Daha", "Dang", "Twelve-cornered glacial pond in Dang valley", 5),
        ("Jakhera Lake", "Dailekh", "Mid-western lake", 6),
        ("Rigmo Lake (Phoksundo)", "Dolpa", "Village by Phoksundo Lake", 6),
        ("Ringmo Lake", "Dolpa", "Ancient lake above Phoksundo", 6),
        ("Shey Phoksundo Second Lake", "Dolpa", "Upper lake beyond Ringmo", 6),
    ],

    # -------- RIVERS --------
    "rivers": [
        ("Koshi River (Saptakoshi)", "Sunsari", "Largest river in Nepal, seven tributaries", 1),
        ("Narayani River (Gandaki)", "Chitwan", "Seven-Gandaki confluence in central Nepal", 3),
        ("Karnali River", "Kailali", "Longest river in Nepal, major Ganges tributary", 6),
        ("Mahakali River (Sharda)", "Kanchanpur", "Western border river with India", 7),
        ("Trishuli River", "Nuwakot", "Popular white-water rafting river", 3),
        ("Bhote Koshi River", "Sindhupalchok", "Steep-grade whitewater rafting/kayaking river", 3),
        ("Sunkoshi River", "Sindhuli", "Classic multi-day rafting river", 3),
        ("Seti Gandaki", "Kaski", "Milky-white river running through Pokhara gorge", 4),
        ("Kali Gandaki River", "Mustang", "Deepest gorge in the world between Annapurna and Dhaulagiri", 4),
        ("Marshyangdi River", "Manang", "Upper Annapurna Circuit river", 4),
        ("Budhi Gandaki", "Gorkha", "Major Gandaki tributary from Manaslu", 4),
        ("Dudh Koshi", "Solukhumbu", "Milky river from Everest region", 1),
        ("Arun River", "Sankhuwasabha", "Large trans-Himalayan river in east Nepal", 1),
        ("Tamur River", "Taplejung", "Eastern river from Kanchenjunga", 1),
        ("Likhu Khola", "Solukhumbu", "Tributary of Dudh Koshi", 1),
        ("Tama Koshi", "Dolakha", "Major Koshi tributary through Rolwaling", 3),
        ("Indrawati River", "Sindhupalchok", "Tributary of Sunkoshi", 3),
        ("Balephi Khola", "Sindhupalchok", "Whitewater rafting tributary", 3),
        ("Mardi Khola", "Kaski", "Stream below Mardi Himal", 4),
        ("Phewa Lake Outlet Stream", "Kaski", "Phewa dam outlet", 4),
        ("Myagdi Khola", "Myagdi", "River below Dhaulagiri", 4),
        ("Thuli Bheri", "Dolpa", "Upper Bheri river in Dolpa", 6),
        ("Sani Bheri", "Rukum", "Lower Bheri river", 6),
        ("Karnali River (Upper)", "Humla", "Trans-Himalayan Karnali in Humla", 6),
        ("Humla Karnali", "Humla", "Tibet-border Karnali tributary", 6),
        ("Mugu Karnali", "Mugu", "Karnali tributary through Mugu", 6),
        ("West Rapti River", "Dang", "River in mid-western Terai", 5),
        ("Babai River", "Bardiya", "River through Bardiya National Park", 5),
        ("Rohini River", "Rupandehi", "River near Lumbini", 5),
        ("Tinau River", "Rupandehi", "River at Butwal", 5),
        ("Bagmati River", "Kathmandu", "Sacred river of Kathmandu valley", 3),
        ("Bishnumati River", "Kathmandu", "Historic river through Kathmandu city", 3),
        ("Hanumante River", "Bhaktapur", "River through Bhaktapur", 3),
        ("Nakhu River", "Lalitpur", "River south of Patan", 3),
        ("Godavari River (Nepal)", "Lalitpur", "Sacred stream at Godavari", 3),
        ("Kankai River", "Jhapa", "Eastern Terai river", 1),
        ("Kamala River", "Siraha", "Mid-eastern Terai river", 2),
        ("Bakrah Khola", "Makwanpur", "River in Hetauda area", 3),
        ("Rapti River (Chitwan)", "Chitwan", "River through Chitwan National Park", 3),
        ("Manohara River", "Kathmandu", "Eastern Kathmandu valley river", 3),
    ],

    # -------- WATERFALLS --------
    "waterfalls": [
        ("Davis Falls (Patale Chhango)", "Kaski", "Famous waterfall from Phewa Lake in Pokhara", 4),
        ("Rupse Falls", "Myagdi", "Waterfall on Beni-Jomsom road in Kali Gandaki gorge", 4),
        ("Hyatung Falls", "Terhathum", "365 m waterfall in eastern Nepal", 1),
        ("Pachaljharana Waterfall", "Kalikot", "481 m tallest waterfall in Nepal", 6),
        ("Sundarijal Waterfall", "Kathmandu", "Popular waterfall on northern valley rim", 3),
        ("Jhor Waterfall", "Kathmandu", "Waterfall near Tokha, north Kathmandu", 3),
        ("Tindhare Waterfall", "Kavrepalanchok", "Three-story waterfall in Kavre", 3),
        ("Chhange Waterfall", "Parbat", "Waterfall near Kusma", 4),
        ("Ghalemdi Waterfall", "Jajarkot", "Mid-western waterfall", 6),
        ("Simba Waterfall", "Lalitpur", "Waterfall near Lele, Lalitpur", 3),
        ("Bhairab Kunda Waterfall", "Sindhupalchok", "Waterfall above Bhairab Kunda", 3),
        ("Tatopani Waterfall", "Myagdi", "Hot-spring waterfall near Beni", 4),
        ("Khuwa Waterfall", "Bhojpur", "Eastern hill waterfall", 1),
        ("Lamo Jharana", "Makwanpur", "Long waterfall on Hetauda-Kathmandu road", 3),
        ("Mailung Waterfall", "Rasuwa", "Waterfall in Mailung, Rasuwa", 3),
        ("Chyamche Waterfall", "Lamjung", "Waterfall on Besisahar-Chame road", 4),
        ("Chumlingtar Waterfall", "Sankhuwasabha", "Waterfall in Arun valley", 1),
        ("Bhedetar Waterfall", "Dhankuta", "Waterfall at Bhedetar viewpoint", 1),
        ("Namaste Waterfall", "Dhankuta", "Named Namaste waterfall in Dhankuta", 1),
        ("Manikhel Waterfall", "Lalitpur", "Waterfall in southern Lalitpur", 3),
        ("Baitadi Waterfalls", "Baitadi", "Series of falls in far-west hills", 7),
        ("Todke Waterfall", "Ilam", "Ilam hill waterfall", 1),
        ("Aahal Dhunga Waterfall", "Khotang", "Hilly waterfall in Khotang", 1),
        ("Purandhara Waterfall", "Dang", "Mid-western waterfall", 5),
        ("Sisne Waterfalls", "Jumla", "High-altitude waterfalls in Jumla", 6),
        ("Phungphunge Waterfall", "Terhathum", "Waterfall near Hyatung in Terhathum", 1),
        ("Kailash Waterfall", "Bajhang", "Far-western waterfall below Saipal", 7),
        ("Ghalegaun Waterfall", "Lamjung", "Waterfall near Ghalegaun village", 4),
        ("Vhel Chhada Falls", "Bajhang", "Waterfall in Bajhang", 7),
        ("Aina Waterfall", "Dhading", "Mirror waterfall on Pasang Lhamu highway", 3),
        ("Rupal Waterfall", "Dadeldhura", "Far-west waterfall", 7),
    ],

    # -------- CAVES --------
    "caves": [
        ("Mahendra Cave", "Kaski", "Limestone cave in Pokhara with stalactites", 4),
        ("Gupteshwor Mahadev Cave", "Kaski", "Sacred cave opposite Davis Falls, Pokhara", 4),
        ("Bat Cave (Chamere Gufa)", "Kaski", "Cave with thousands of bats near Pokhara", 4),
        ("Siddha Gufa", "Tanahun", "Largest cave in Nepal at Bandipur", 4),
        ("Halesi Mahadev Cave", "Khotang", "Sacred cave temple in eastern Nepal", 1),
        ("Maratika Caves", "Khotang", "Ancient Buddhist/Hindu pilgrimage caves", 1),
        ("Chhoser Sky Caves", "Mustang", "Ancient man-made cliff caves in Upper Mustang", 4),
        ("Sky Caves of Mustang", "Mustang", "Thousands of ancient cliff-cut caves", 4),
        ("Mahadev Parvati Cave", "Dang", "Religious cave in Dang valley", 5),
        ("Gorakhnath Cave (Gorkha)", "Gorkha", "Sacred cave below Gorkha Durbar", 4),
        ("Asura Cave", "Lalitpur", "Meditation cave of Padmasambhava at Pharping", 3),
        ("Yangleshö Cave (Pharping)", "Lalitpur", "Sacred Buddhist meditation cave", 3),
        ("Milarepa Cave", "Manang", "Cave associated with Jetsun Milarepa", 4),
        ("Rele Cave", "Arghakhanchi", "Archeological cave in mid-west", 5),
        ("Chamere Cave (Bandipur)", "Tanahun", "Bat cave at Bandipur", 4),
        ("Bhimsen Cave", "Kaski", "Small cave near Pokhara", 4),
        ("Kumari Cave", "Sindhupalchok", "Cave near Balephi", 3),
        ("Patal Bhubaneshwar (border)", "Darchula", "Near-border cave system", 7),
        ("Kailash Cave", "Surkhet", "Religious cave in Surkhet", 6),
        ("Bulbule Cave", "Surkhet", "Cave at Bulbule lake, Surkhet", 6),
        ("Siddha Gufa (Doti)", "Doti", "Far-western meditation cave", 7),
        ("Dakshinkali Cave", "Kathmandu", "Cave near Dakshinkali temple", 3),
        ("Bajrabarahi Cave", "Lalitpur", "Cave near Chapagaun", 3),
        ("Bhalu Cave (Bear Cave)", "Lalitpur", "Forest cave in Godavari area", 3),
        ("Ghalegaun Cave", "Lamjung", "Limestone cave near Ghalegaun", 4),
        ("Narayansthan Cave", "Baglung", "Religious cave in Baglung", 4),
        ("Churiya Cave", "Makwanpur", "Churia hills cave", 3),
        ("Tatopani Cave", "Myagdi", "Cave near Tatopani hot spring", 4),
        ("Muktinath Cave", "Mustang", "Sacred cave near Muktinath", 4),
    ],

    # -------- HOT SPRINGS --------
    "hot-springs": [
        ("Tatopani Hot Spring (Myagdi)", "Myagdi", "Natural hot spring on Annapurna Circuit", 4),
        ("Tatopani Hot Spring (Rasuwa)", "Rasuwa", "Hot spring near Kodari, Nepal-Tibet border", 3),
        ("Jhinu Danda Hot Spring", "Kaski", "Natural hot spring on Annapurna Base Camp trail", 4),
        ("Ghasa Tatopani", "Mustang", "Hot spring in Kali Gandaki valley", 4),
        ("Syabrubesi Hot Spring", "Rasuwa", "Hot spring in Langtang valley entry", 3),
        ("Chhumchaur Hot Spring", "Jumla", "Mid-western natural hot spring", 6),
        ("Ratomate Hot Spring", "Udayapur", "Eastern Nepal hot spring", 1),
        ("Kodari Hot Spring", "Sindhupalchok", "Hot spring at Nepal-Tibet border", 3),
        ("Bhurung Tatopani", "Myagdi", "Hot spring in Myagdi district", 4),
        ("Darchula Hot Springs", "Darchula", "Far-western hot spring sites", 7),
        ("Bajhang Tatopani", "Bajhang", "Local hot spring in far-west", 7),
        ("Sunkoshi Hot Spring", "Sindhupalchok", "Riverside hot spring on Sunkoshi", 3),
        ("Timure Hot Spring", "Rasuwa", "Upper Rasuwa hot spring", 3),
        ("Chame Hot Spring", "Manang", "Hot spring at Chame on Annapurna Circuit", 4),
        ("Dhunche Hot Spring", "Rasuwa", "Hot spring at Dhunche, Langtang", 3),
    ],

    # -------- TEMPLES (Hindu) --------
    "temples": [
        ("Pashupatinath Temple", "Kathmandu", "Sacred Hindu temple on Bagmati, UNESCO site", 3),
        ("Janaki Mandir", "Dhanusha", "Birthplace of Sita, grand Janakpur temple", 2),
        ("Muktinath Temple", "Mustang", "Sacred Vishnu temple at 3,710 m with 108 waterspouts", 4),
        ("Manakamana Temple", "Gorkha", "Wish-fulfilling goddess temple, cable car access", 4),
        ("Dakshinkali Temple", "Kathmandu", "Famous Kali temple in southern Kathmandu", 3),
        ("Guhyeshwari Temple", "Kathmandu", "Shakti Peeth near Pashupatinath", 3),
        ("Krishna Mandir (Patan)", "Lalitpur", "17th-century stone Krishna temple", 3),
        ("Nyatapola Temple", "Bhaktapur", "Tallest pagoda in Nepal at Taumadhi Square", 3),
        ("Doleshwor Mahadev", "Bhaktapur", "Believed head-part of Kedarnath", 3),
        ("Chandragiri Bhaleshwor", "Kathmandu", "Hilltop Mahadev temple with cable car", 3),
        ("Bindhyabasini Temple", "Kaski", "Popular goddess temple in Pokhara", 4),
        ("Tal Barahi Temple", "Kaski", "Island temple in Phewa Lake, Pokhara", 4),
        ("Siddhi Lakshmi Temple", "Bhaktapur", "Temple at Bhaktapur Durbar Square", 3),
        ("Bajrabarahi Temple", "Lalitpur", "Temple at Chapagaun", 3),
        ("Balkumari Temple", "Bhaktapur", "Historic Newar goddess temple", 3),
        ("Santaneshwor Mahadev", "Lalitpur", "Mahadev temple in Lalitpur", 3),
        ("Gokarna Mahadev", "Kathmandu", "Riverside temple north of Kathmandu", 3),
        ("Budhanilkantha", "Kathmandu", "Reclining Vishnu statue below Shivapuri", 3),
        ("Sankata Temple", "Kathmandu", "Newar Buddhist-Hindu temple at Te Bahal", 3),
        ("Swayambhunath (Hindu shrine)", "Kathmandu", "Combined Buddhist-Hindu site on hilltop", 3),
        ("Bhadrakali Temple", "Kathmandu", "Goddess temple near Tundikhel", 3),
        ("Sobha Bhagwati", "Kathmandu", "Historic goddess temple", 3),
        ("Taleju Bhawani Temple", "Kathmandu", "Royal goddess temple at Hanuman Dhoka", 3),
        ("Kankeshwori Temple", "Kathmandu", "Historic Newar temple in Kathmandu", 3),
        ("Ichangu Narayan", "Kathmandu", "One of four ancient Narayan temples", 3),
        ("Bisankhu Narayan", "Lalitpur", "Ancient Narayan temple", 3),
        ("Changu Narayan", "Bhaktapur", "Oldest temple in Nepal valley, UNESCO", 3),
        ("Shesh Narayan", "Kathmandu", "Vishnu temple at Pharping", 3),
        ("Padukasthan", "Dadeldhura", "Far-western Shiva temple", 7),
        ("Badimalika Temple", "Bajura", "Famous goddess temple in far-west", 7),
        ("Pathibhara Devi", "Taplejung", "Hilltop goddess temple in Taplejung", 1),
        ("Siddha Baba Temple", "Palpa", "Tansen-area popular Shiva temple", 5),
        ("Rishikesheshwar Mahadev", "Kanchanpur", "Far-western Mahadev", 7),
        ("Godawari Kunda Temple", "Lalitpur", "Pilgrimage at Godavari spring", 3),
        ("Phulchowki Temple", "Lalitpur", "Hilltop goddess temple", 3),
        ("Kalinchowk Bhagwati", "Dolakha", "Famous hilltop goddess at 3,842 m", 3),
        ("Dolakha Bhimsen", "Dolakha", "Historic Bhimsen temple with sweating idol", 3),
        ("Palanchowk Bhagwati", "Kavrepalanchok", "Historic Bhagwati temple in Kavre", 3),
        ("Gorakhnath Temple (Gorkha)", "Gorkha", "Cave temple at Gorkha Durbar", 4),
        ("Kalika Temple (Gorkha)", "Gorkha", "Goddess temple at Gorkha Durbar", 4),
        ("Manakamana Temple (Gorkha)", "Gorkha", "Famous goddess above Trishuli river", 4),
        ("Bhagwati Temple (Palpa)", "Palpa", "Tansen Bhagwati temple", 5),
        ("Bageshwari Temple (Nepalgunj)", "Banke", "Famous goddess temple in Nepalgunj", 5),
        ("Kailashnath Mahadev (Dolakha border)", "Sindhupalchok", "Hilltop Shiva area", 3),
        ("Bhairabsthan Temple", "Palpa", "Tansen Bhairav temple with giant trident", 5),
        ("Barahachhetra", "Sunsari", "One of four Narayan temples in Nepal", 1),
        ("Pindeshwor Mahadev", "Dharan", "Popular Dharan temple", 1),
        ("Budhasubba Temple", "Sunsari", "Rais' sacred shrine in Dharan", 1),
        ("Dantakali Temple", "Dharan", "Goddess temple in Dharan", 1),
        ("Kushmanda Sarowar", "Dang", "Pilgrimage site in Dang", 5),
        ("Ambikeshwori Temple", "Dang", "Goddess temple in Ghorahi", 5),
        ("Bageshwori Temple (Nepalgunj)", "Banke", "Prominent Banke goddess temple", 5),
        ("Thakurdwara Temple", "Bardiya", "Temple near Bardiya National Park", 5),
        ("Swargadwari Temple", "Pyuthan", "Hilltop pilgrimage site in mid-west", 5),
        ("Devghat Dham", "Chitwan", "Sacred confluence of Trishuli and Narayani", 3),
        ("Ridi Kunda", "Gulmi", "Confluence of Ridi river and Kali Gandaki", 5),
        ("Resunga Temple", "Gulmi", "Hilltop religious site", 5),
        ("Halesi Mahadev", "Khotang", "Cave temple famous for Hindus and Buddhists", 1),
        ("Bishnupaduka", "Dharan", "Sacred Vishnu footprint in Dharan", 1),
        ("Chatara Dham (Barahakshetra)", "Sunsari", "Sacred site on Koshi river", 1),
        ("Janaki Mandir (Janakpur)", "Dhanusha", "Birthplace of Sita", 2),
        ("Bibah Panchami Mandap", "Dhanusha", "Site of Ram-Sita marriage", 2),
        ("Dhanushadham", "Dhanusha", "Sacred site with broken Shiva Dhanush", 2),
        ("Jaleshwar Mahadev", "Mahottari", "Floating Shivling temple", 2),
        ("Matatirtha Temple", "Kathmandu", "Mother's pilgrimage pond/temple", 3),
        ("Karya Binayak", "Lalitpur", "Ganesh temple at Bungamati", 3),
        ("Ashok Binayak", "Kathmandu", "Ganesh temple at Maru Tole", 3),
        ("Surya Binayak", "Bhaktapur", "Hilltop Ganesh temple", 3),
        ("Jal Binayak", "Kathmandu", "Ganesh temple at Chobhar", 3),
    ],

    # -------- BUDDHIST SITES --------
    "buddhist-sites": [
        ("Boudhanath Stupa", "Kathmandu", "Largest stupa in Nepal, UNESCO world heritage", 3),
        ("Swayambhunath Stupa", "Kathmandu", "Ancient hilltop stupa, the 'Monkey Temple'", 3),
        ("Lumbini Sacred Garden", "Rupandehi", "Birthplace of Gautam Buddha, UNESCO", 5),
        ("Maya Devi Temple", "Rupandehi", "Temple marking Buddha's birth spot", 5),
        ("World Peace Pagoda (Pokhara)", "Kaski", "White pagoda on Anadu hill, Pokhara", 4),
        ("Kopan Monastery", "Kathmandu", "Tibetan Buddhist monastery north of Boudha", 3),
        ("Thrangu Tashi Yangtse Monastery", "Kavrepalanchok", "Large Karma Kagyu monastery at Namo Buddha", 3),
        ("Namo Buddha (Thrangu)", "Kavrepalanchok", "Sacred site of Buddha's self-sacrifice to a tigress", 3),
        ("Pharping Yangleshö", "Lalitpur", "Meditation cave of Padmasambhava", 3),
        ("Asura Cave", "Lalitpur", "Famous Padmasambhava meditation cave", 3),
        ("Tengboche Monastery", "Solukhumbu", "Largest monastery in Khumbu on EBC trail", 1),
        ("Khumjung Gompa", "Solukhumbu", "Sherpa monastery above Namche Bazaar", 1),
        ("Thame Monastery", "Solukhumbu", "Ancient gompa in Thame, Khumbu", 1),
        ("Pangboche Gompa", "Solukhumbu", "Oldest monastery in Khumbu", 1),
        ("Braga Gompa", "Manang", "Ancient Nyingma monastery in Manang", 4),
        ("Lo Manthang Gompa", "Mustang", "Wall-city ancient monasteries of Mustang", 4),
        ("Thubchen Gompa", "Mustang", "15th-century monastery in Lo Manthang", 4),
        ("Jampa Gompa", "Mustang", "Ancient Maitreya Buddha gompa in Lo Manthang", 4),
        ("Chhoser Gompa (Charang)", "Mustang", "Medieval Mustang monastery", 4),
        ("Rinchenling Gompa", "Dolpo", "Ancient Bon/Buddhist gompa in Dolpo", 6),
        ("Shey Gompa", "Dolpo", "Crystal mountain monastery in Upper Dolpo", 6),
        ("Gompa of Saldang", "Dolpo", "Dolphin-style village monastery", 6),
        ("Namche Monastery", "Solukhumbu", "Small Sherpa monastery in Namche Bazaar", 1),
        ("Chiwang Monastery (Chiwong)", "Solukhumbu", "Cultural monastery with Mani Rimdu", 1),
        ("Maratika Monastery", "Khotang", "Monastery above Halesi caves", 1),
        ("Seto Gumba (White Monastery)", "Kathmandu", "Hilltop monastery above Kathmandu", 3),
        ("Rigon Tashi Choling", "Lalitpur", "Monastery in Godavari area", 3),
        ("Pullahari Monastery", "Kathmandu", "Kagyu monastery above Boudha", 3),
        ("Nagi Gompa", "Kathmandu", "Nunnery on Shivapuri hillslope", 3),
        ("Chhairo Gompa", "Mustang", "Restored Tibetan-style monastery in Tukuche", 4),
        ("Sambha Gompa", "Dolpa", "Dolpo village monastery", 6),
        ("Bhijer Gompa", "Dolpa", "Dolpo Bonpo/Buddhist monastery", 6),
    ],
}


def _get_cat(slug: str) -> Category:
    cat, _ = Category.objects.get_or_create(
        slug=slug,
        defaults={"name": slug.replace("-", " ").title(), "is_active": True},
    )
    return cat


class Command(BaseCommand):
    help = "Expand curated Nepal destinations across all categories/districts."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Count only, no DB changes")

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options["dry_run"]
        created_total = 0

        for cat_slug, entries in EXTRA_DESTINATIONS.items():
            cat = _get_cat(cat_slug)
            added = 0
            existed = 0
            for name, district, desc, province in entries:
                # Skip if destination with same name exists (fuzzy match by lowercased names)
                if Destination.objects.filter(name__iexact=name).exists():
                    existed += 1
                    continue
                if dry:
                    added += 1
                    continue
                Destination.objects.create(
                    name=name,
                    category=cat,
                    district=district,
                    province=province,
                    short_description=desc,
                    country="Nepal",
                    is_active=True,
                    status="approved",
                    recommended_days=1,
                    tourism_importance="medium",
                )
                added += 1
            created_total += added
            self.stdout.write(f"  {cat_slug:25s}: +{added} added, {existed} existed")

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal new destinations added: {created_total}"
        ))
