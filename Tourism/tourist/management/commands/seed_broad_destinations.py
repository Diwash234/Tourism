"""
Seed a broad set of real Nepal destinations across all 36 taxonomy categories.

Curated list organized by category; covers all 7 provinces.
Run with: python manage.py seed_broad_destinations [--clear]
Idempotent: uses get_or_create on (slug,) so re-runs are safe.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from tourist.models import Category, Destination


# (name, district, province, lat, lon, short_description)
# slug will be auto-derived from name by model save(); but we set it explicitly.

DESTINATIONS = [
    # =============== TEMPLES ===============
    ("temples", [
        ("Pashupatinath Temple", "Kathmandu", "Bagmati", 27.7106, 85.3485, "Sacred Hindu temple on the Bagmati River; UNESCO World Heritage Site."),
        ("Janaki Mandir", "Dhanusha", "Madhesh", 26.7306, 85.9258, "Hindu temple dedicated to Goddess Sita in Janakpur."),
        ("Manakamana Temple", "Gorkha", "Gandaki", 27.9036, 84.5833, "Sacred Bhagwati temple atop a ridge, reached by cable car."),
        ("Muktinath Temple", "Mustang", "Gandaki", 28.8158, 83.8733, "Sacred Vishnu temple at 3,710 m; one of the Char Dham of Nepal."),
        ("Bindhyabasini Temple", "Kaski", "Gandaki", 28.2333, 83.9833, "Popular hilltop goddess temple in Pokhara."),
        ("Dakshinkali Temple", "Kathmandu", "Bagmati", 27.6083, 85.2500, "Famous Kali temple in a forested valley south of Kathmandu."),
        ("Guhyeshwari Temple", "Kathmandu", "Bagmati", 27.7126, 85.3508, "Shakti Peeth near Pashupatinath."),
        ("Krishna Mandir Patan", "Lalitpur", "Bagmati", 27.6728, 85.3248, "17th-century stone Krishna temple in Patan Durbar Square."),
        ("Nyatapola Temple", "Bhaktapur", "Bagmati", 27.6722, 85.4298, "Five-tiered pagoda, tallest in Nepal, in Taumadhi Square."),
        ("Changunarayan Temple", "Bhaktapur", "Bagmati", 27.7210, 85.4290, "Ancient Vishnu temple; UNESCO World Heritage Site."),
        ("Doleshwor Mahadev", "Bhaktapur", "Bagmati", 27.6625, 85.4400, "Believed to be the head part of Kedarnath."),
        ("Siddhikali Temple", "Bhaktapur", "Bagmati", 27.6760, 85.4280, "Shakti Peeth in Thimi, Bhaktapur."),
        ("Bajrayogini Temple", "Kathmandu", "Bagmati", 27.7522, 85.4583, "Tantric goddess temple in Sankhu."),
        ("Sheshnarayan Temple", "Kathmandu", "Bagmati", 27.6500, 85.2700, "One of the four Narayan temples of the Kathmandu Valley."),
        ("Ichangu Narayan", "Kathmandu", "Bagmati", 27.7200, 85.2600, "Ancient Vishnu temple in the western valley."),
        ("Chandeshwori Temple", "Kavrepalanchok", "Bagmati", 27.5800, 85.5400, "Ancient Durga temple near Banepa."),
        ("Palanchowk Bhagwati", "Kavrepalanchok", "Bagmati", 27.6200, 85.6100, "Famous three-armed Bhagwati statue."),
        ("Kailashnath Mahadev", "Kavrepalanchok", "Bagmati", 27.6260, 85.5900, "World's tallest Shiva statue (144 ft)."),
        ("Bhaleshwor Mahadev", "Kathmandu", "Bagmati", 27.7830, 85.2060, "Shiva temple atop Chandragiri hill."),
        ("Gokarna Mahadev", "Kathmandu", "Bagmati", 27.7600, 85.4000, "Holy riverside Shiva temple."),
        ("Santaneshwor Temple", "Lalitpur", "Bagmati", 27.6300, 85.3300, "Sacred Mahadev temple in Harisiddhi."),
        ("Balkumari Temple", "Lalitpur", "Bagmati", 27.6700, 85.3200, "Ancient goddess temple in Lalitpur."),
        ("Kumbheshwar Temple", "Lalitpur", "Bagmati", 27.6757, 85.3250, "Five-storied Shiva temple in Patan."),
        ("Bangalamukhi Temple", "Lalitpur", "Bagmati", 27.6740, 85.3180, "Famous Shakti Peeth in Patan."),
        ("Taleju Temple", "Kathmandu", "Bagmati", 27.7041, 85.3058, "Royal goddess temple in Hanuman Dhoka."),
        ("Taleju Bhaktapur", "Bhaktapur", "Bagmati", 27.6720, 85.4290, "Royal Taleju temple in Bhaktapur Durbar Square."),
        ("Tal Barahi Temple", "Kaski", "Gandaki", 28.2150, 83.9550, "Two-storied pagoda on an island in Phewa Lake."),
        ("Bhadrakali Temple", "Kaski", "Gandaki", 28.2200, 83.9850, "Goddess temple on a small hill near Pokhara."),
        ("Vindhyavasini Temple", "Kaski", "Gandaki", 28.2350, 83.9850, "Popular Shakti shrine in central Pokhara."),
        ("Akala Devi Temple", "Lamjung", "Gandaki", 28.2800, 84.3500, "Sacred goddess temple in central Nepal."),
        ("Manakamana Gorkha Temple", "Gorkha", "Gandaki", 27.9040, 84.5830, "The wish-fulfilling goddess temple of Gorkha."),
        ("Gorkha Kalika Temple", "Gorkha", "Gandaki", 27.9900, 84.6300, "Royal goddess of the former Gorkha kingdom."),
        ("Akala Devi Pokhara", "Kaski", "Gandaki", 28.2400, 83.9900, "Cultural hilltop shrine in Pokhara."),
        ("Jal Binayak", "Kathmandu", "Bagmati", 27.6700, 85.3000, "One of the four original Vinayak shrines of the valley."),
        ("Surya Binayak", "Bhaktapur", "Bagmati", 27.6700, 85.4400, "Ganesh temple on a forested hill."),
        ("Karya Binayak", "Lalitpur", "Bagmati", 27.6400, 85.3000, "Ganesh shrine in Bungamati."),
        ("Ashok Binayak", "Kathmandu", "Bagmati", 27.7040, 85.3080, "Maru Ganesh at Durbar Square."),
        ("Dantakali Temple", "Dharan", "Koshi", 26.8100, 87.2900, "Sacred tooth-shrine of Sati in Bijayapur."),
        ("Budha Subba Temple", "Dharan", "Koshi", 26.8000, 87.2800, "Famous Rai/Limbu sacred shrine."),
        ("Barahachhetra", "Sunsari", "Koshi", 26.5000, 87.0700, "Sacred Vishnu/Baraha temple on the Koshi River."),
        ("Chandannath Temple", "Jumla", "Karnali", 29.2750, 82.1830, "Ancient Shiva/Chandannath temple in Jumla."
         ),
        ("Bageshwori Temple", "Nepalgunj", "Lumbini", 28.0500, 81.6200, "Famous Durga temple in Banke."),
        ("Ambikeswari Temple", "Dang", "Lumbini", 28.0000, 82.3000, "Cultural goddess shrine in Dang valley."),
        ("Swargadwari Temple", "Pyuthan", "Lumbini", 28.1700, 82.7400, "Hilltop Hindu pilgrimage site."),
        ("Thakurbaba Temple", "Bardiya", "Lumbini", 28.3000, 81.3500, "Sacred Krishna/Bishnu temple in Bardiya."),
        ("Devghat Dham", "Chitwan", "Bagmati", 27.7800, 84.4200, "Sacred confluence of Kali Gandaki and Trishuli."),
        ("Triveni Dham", "Nawalparasi", "Lumbini", 27.5000, 83.8000, "Confluence pilgrimage site."),
        ("Ridi Kedareshwor", "Gulmi", "Lumbini", 27.9300, 83.4300, "Sacred Shiva shrine at Ridi confluence."),
        ("Resunga Yagyashala", "Gulmi", "Lumbini", 27.9400, 83.3500, "Hindu pilgrimage site with Vedic fire ceremonies."),
        ("Bhairabsthan Temple", "Palpa", "Lumbini", 27.8500, 83.5500, "Fearsome Bhairava shrine above Tansen."),
        ("Siddha Baba Temple", "Palpa", "Lumbini", 27.8700, 83.4800, "Highly revered Shiva shrine near Butwal."),
        ("Manakamana Palpa", "Palpa", "Lumbini", 27.8200, 83.5800, "Local wish-fulfilling goddess shrine."),
        ("Gadhimai Temple", "Bara", "Madhesh", 27.0000, 85.1200, "Famous Gadhimai goddess shrine."),
        ("Kankalini Temple", "Saptari", "Madhesh", 26.6300, 86.8200, "Famous Durga shrine in eastern Terai."),
        ("Chhintang Devi", "Dhankuta", "Koshi", 26.9500, 87.3500, "Ancient goddess temple in Dhankuta."),
        ("Pathibhara Devi", "Taplejung", "Koshi", 27.4300, 87.7500, "High-altitude sacred goddess shrine (3,794 m)."),
        ("Bishnupaduka", "Dharan", "Koshi", 26.8200, 87.2800, "Sacred Vishnu footprint site."),
        ("Halesi Mahadev", "Khotang", "Koshi", 27.1800, 86.6200, "Maratika cave temple sacred to Hindus and Buddhists."),
        ("Salinadi Temple", "Sindhupalchok", "Bagmati", 27.8500, 85.8000, "Sacred river temple near Barhabise."),
        ("Kalinchowk Bhagwati", "Dolakha", "Bagmati", 27.7600, 86.0500, "High-altitude Bhagwati shrine and snow viewpoint."),
        ("Dolakha Bhimsen", "Dolakha", "Bagmati", 27.6800, 86.0700, "Ancient Bhimsen temple in Dolakha."),
        ("Chandrabhoga Khaptad", "Doti", "Sudurpashchim", 29.3000, 80.9000, "Sacred Khaptad Baba ashram and Shiva temple."),
        ("Badimalika", "Bajura", "Sudurpashchim", 29.4500, 81.4500, "Sacred Malika Devi high-altitude pilgrimage."),
        ("Surma Sarovar", "Bajhang", "Sudurpashchim", 29.8000, 81.1000, "High-altitude sacred lake and Surma Devi shrine."),
        ("RaRa Mahadev", "Mugu", "Karnali", 29.5300, 82.0900, "Shiva temple near Rara Lake."),
        ("Panchpokhari", "Sindhupalchok", "Bagmati", 28.0300, 85.7000, "Five sacred glacial lakes and Shiva shrine."),
        ("Gosaikunda", "Rasuwa", "Bagmati", 28.0833, 85.4167, "Sacred glacial lake Shiva pilgrimage."),
        ("Kunda Daha", "Achham", "Sudurpashchim", 29.0700, 81.3000, "Sacred lake pilgrimage."),
        ("Baidyanath Dham", "Achham", "Sudurpashchim", 29.0000, 81.2500, "Hindu pilgrimage site in Achham."),
    ]),

    # =============== BUDDHIST SITES / MONASTERIES ===============
    ("buddhist-sites", [
        ("Boudhanath Stupa", "Kathmandu", "Bagmati", 27.7214, 85.3620, "One of the largest spherical stupas in the world; UNESCO site."),
        ("Swayambhunath Stupa", "Kathmandu", "Bagmati", 27.7149, 85.2904, "Ancient hilltop stupa, the Monkey Temple."),
        ("Lumbini Sacred Garden", "Rupandehi", "Lumbini", 27.4695, 83.2750, "Birthplace of Gautama Buddha; UNESCO World Heritage Site."),
        ("Maya Devi Temple", "Rupandehi", "Lumbini", 27.4695, 83.2753, "Sacred temple marking Buddha's birth spot in Lumbini."),
        ("Kopan Monastery", "Kathmandu", "Bagmati", 27.7420, 85.3680, "Tibetan Buddhist monastery north of Bodhnath."),
        ("Thrangu Tashi Yangtse Monastery", "Kavrepalanchok", "Bagmati", 27.6100, 85.5900, "Prominent Karma Kagyu monastery in Namo Buddha."),
        ("Namo Buddha", "Kavrepalanchok", "Bagmati", 27.6100, 85.5900, "Sacred site of the Buddha's self-sacrifice to a tigress."),
        ("Pharping Monastery & Yangleshö Cave", "Kathmandu", "Bagmati", 27.5800, 85.2700, "Sacred Padmasambhava cave and monastery."),
        ("Asura Cave", "Kathmandu", "Bagmati", 27.5800, 85.2700, "Guru Rinpoche meditation cave in Pharping."),
        ("Swayambhu Puran Stupa", "Kathmandu", "Bagmati", 27.7149, 85.2904, "Ancient Swayambhunath complex."),
        ("Shanti Stupa Pokhara", "Kaski", "Gandaki", 28.2050, 83.9500, "World Peace Pagoda on Ananda Hill above Phewa Lake."),
        ("Tengboche Monastery", "Solukhumbu", "Koshi", 27.8360, 86.7650, "Famous Sherpa monastery on the Everest Base Camp trek."),
        ("Khumjung Gompa", "Solukhumbu", "Koshi", 27.8250, 86.7200, "Sherpa village monastery with Yeti scalp relic."),
        ("Thame Monastery", "Solukhumbu", "Koshi", 27.8400, 86.6500, "Ancient Sherpa monastery near the Nangpa La."),
        ("Chiwang Gompa", "Solukhumbu", "Koshi", 27.7000, 86.7300, "Historic Nyingma monastery."),
        ("Maratika Monastery", "Khotang", "Koshi", 27.1800, 86.6200, "Sacred Padmasambhava site near Halesi Mahadev."),
        ("Lo Manthang Monasteries", "Mustang", "Gandaki", 29.1830, 83.9500, "Wall city with Jampa, Thubchen and Chodey gompas."),
        ("Chhoser Jhong Cave Gompa", "Mustang", "Gandaki", 29.1900, 83.9300, "Sky-caves and monasteries of Upper Mustang."),
        ("Muktinath Gompa", "Mustang", "Gandaki", 28.8158, 83.8733, "Buddhist gompa adjacent to Muktinath temple."),
        ("Braga Gompa", "Manang", "Gandaki", 28.6380, 84.0100, "Ancient Nyingma monastery on the Annapurna Circuit."),
        ("Shree Muktinath Gumba", "Mustang", "Gandaki", 28.8150, 83.8700, "Tibetan Buddhist shrine at Muktinath."),
        ("Tashi Palkhel Tibetan Camp", "Kaski", "Gandaki", 28.2400, 83.9600, "Tashi Ling refugee camp and monastery."),
        ("Pema Namding Monastery", "Solukhumbu", "Koshi", 27.7500, 86.7300, "Nyingma nunnery in the Khumbu."),
        ("Rinchenling Gompa", "Dolpa", "Karnali", 29.0400, 82.9200, "Ancient Bonpo/Buddhist monastery in upper Dolpo."),
        ("Shey Gompa", "Dolpa", "Karnali", 29.1400, 82.8000, "Crystal Mountain monastery in Shey Phoksundo."),
        ("Namche Monastery", "Solukhumbu", "Koshi", 27.8050, 86.7120, "Sherpa monastery overlooking Namche Bazaar."),
        ("Ridi Monastery", "Gulmi", "Lumbini", 27.9300, 83.4300, "Buddhist site at the Kali Gandaki confluence."),
        ("Lumbini Monastic Zone", "Rupandehi", "Lumbini", 27.4800, 83.2800, "International monasteries representing Buddhist nations."),
    ]),

    # =============== HERITAGE / DURBAR / PALACES ===============
    ("heritage", [
        ("Kathmandu Durbar Square", "Kathmandu", "Bagmati", 27.7041, 85.3058, "Royal palace complex with Hanuman Dhoka; UNESCO site."),
        ("Bhaktapur Durbar Square", "Bhaktapur", "Bagmati", 27.6722, 85.4298, "Royal square with 55-window palace and Golden Gate."),
        ("Patan Durbar Square", "Lalitpur", "Bagmati", 27.6728, 85.3248, "Ancient city of fine arts with Krishna Mandir and Sundari Chowk."),
        ("Bhaktapur Taumadhi Square", "Bhaktapur", "Bagmati", 27.6720, 85.4280, "Square containing Nyatapola, Bhairavnath and Tilmadhab Narayan."),
        ("Hanuman Dhoka Palace", "Kathmandu", "Bagmati", 27.7040, 85.3070, "Royal Malla and Shah palace complex in Kathmandu."),
        ("Patan Museum", "Lalitpur", "Bagmati", 27.6750, 85.3250, "World-class bronze and sacred art museum in Sundari Chowk."),
        ("Narayanhiti Palace Museum", "Kathmandu", "Bagmati", 27.7180, 85.3210, "Former royal palace now a public museum."),
        ("Gorkha Durbar", "Gorkha", "Gandaki", 27.9950, 84.6300, "Historic hilltop palace of Prithvi Narayan Shah."),
        ("Nuwakot Durbar", "Nuwakot", "Bagmati", 27.9200, 85.1800, "Seven-story historic palace, Prithvi Narayan's western fort."),
        ("Rani Mahal Palpa", "Palpa", "Lumbini", 27.8700, 83.4900, "Palpa's Taj Mahal on the banks of the Kali Gandaki."),
        ("Tansen Durbar", "Palpa", "Lumbini", 27.8680, 83.5460, "Rana-era palace in Tansen, now a museum."),
        ("Bagh Durbar", "Kathmandu", "Bagmati", 27.7000, 85.3100, "Historic Rana palace complex."),
        ("Singha Durbar", "Kathmandu", "Bagmati", 27.6970, 85.3250, "Iconic Rana palace housing government offices."),
        ("Keshar Mahal", "Kathmandu", "Bagmati", 27.7130, 85.3180, "Garden of Dreams palace in Kaiser Mahal."),
        ("Garden of Dreams", "Kathmandu", "Bagmati", 27.7140, 85.3150, "Restored Edwardian neo-classical garden in Thamel."),
        ("Bhimsen Tower (Dharahara)", "Kathmandu", "Bagmati", 27.6990, 85.3100, "Reconstructed 19th-century watchtower after the 2015 earthquake."),
        ("Sankhu Vajrayogini", "Kathmandu", "Bagmati", 27.7520, 85.4580, "Ancient Newar town with 8th-century goddess temple."),
        ("Bungamati", "Lalitpur", "Bagmati", 27.6250, 85.3000, "Medieval Newar village and Rato Machhindranath shrine."),
        ("Khokana", "Lalitpur", "Bagmati", 27.6300, 85.3000, "Traditional Newar oil-pressing village."),
        ("Bandipur Bazaar Heritage", "Tanahun", "Gandaki", 27.9400, 84.4100, "Preserved Newar hilltop trading town."),
        ("Tansen Old Bazaar", "Palpa", "Lumbini", 27.8670, 83.5450, "Traditional cobbled bazaar with Newari houses."),
        ("Dhulikhel Heritage Town", "Kavrepalanchok", "Bagmati", 27.6200, 85.5600, "Historic Newari trade post with Himalayan views."),
        ("Panauti Old Town", "Kavrepalanchok", "Bagmati", 27.5850, 85.5100, "Medieval Newari town at sacred river confluence."),
        ("Kirtipur Medieval Town", "Kathmandu", "Bagmati", 27.6700, 85.2800, "Hilltop Newar town with Chilancho Stupa."),
    ]),

    # =============== MOUNTAINS / PEAKS ===============
    ("mountains", [
        ("Mount Everest (Sagarmatha)", "Solukhumbu", "Koshi", 27.9881, 86.9250, "World's highest peak at 8,848 m."),
        ("Kanchenjunga", "Taplejung", "Koshi", 27.7025, 88.1483, "World's third-highest peak at 8,586 m."),
        ("Lhotse", "Solukhumbu", "Koshi", 27.9619, 86.9335, "Fourth-highest mountain at 8,516 m."),
        ("Makalu", "Sankhuwasabha", "Koshi", 27.8890, 87.0888, "Fifth-highest peak at 8,485 m."),
        ("Cho Oyu", "Solukhumbu", "Koshi", 28.0940, 86.6608, "Sixth-highest peak at 8,188 m."),
        ("Dhaulagiri I", "Myagdi", "Gandaki", 28.6966, 83.4894, "Seventh-highest peak at 8,167 m."),
        ("Manaslu", "Gorkha", "Gandaki", 28.5500, 84.5597, "Eighth-highest peak at 8,163 m."),
        ("Annapurna I", "Myagdi", "Gandaki", 28.5961, 83.8203, "Tenth-highest peak at 8,091 m."),
        ("Machhapuchhre (Fishtail)", "Kaski", "Gandaki", 28.4950, 83.9450, "Sacred unclimbed peak above Pokhara."),
        ("Annapurna South", "Myagdi", "Gandaki", 28.5180, 83.8060, "7,219 m peak in the Annapurna Sanctuary."),
        ("Hiunchuli", "Kaski", "Gandaki", 28.4600, 83.9000, "6,441 m peak guarding the Annapurna Sanctuary."),
        ("Gangkhar Puensum", "Gasa (Bhutan border)", "Koshi", 28.0480, 90.4500, "Highest unclimbed peak in the world; shared with Bhutan."),
        ("Api Himal", "Darchula", "Sudurpashchim", 30.0100, 80.9300, "7,132 m far-western peak."),
        ("Saipal", "Bajhang", "Sudurpashchim", 29.8500, 81.3200, "7,031 m far-western mountain."),
        ("Kanjirowa Himal", "Dolpa", "Karnali", 29.2200, 82.7000, "6,883 m peak in the Kanjirowa range."),
    ]),

    # =============== TREKKING ===============
    ("trekking", [
        ("Everest Base Camp Trek", "Solukhumbu", "Koshi", 27.9900, 86.8500, "Classic trek to the foot of Everest."),
        ("Annapurna Base Camp Trek", "Kaski", "Gandaki", 28.5000, 83.8700, "Trek to the Annapurna Sanctuary."),
        ("Annapurna Circuit Trek", "Manang/Mustang/Myagdi", "Gandaki", 28.6200, 84.0000, "Classic circumnavigation of the Annapurna massif via Thorong La."),
        ("Poon Hill Trek (Ghorepani)", "Myagdi", "Gandaki", 28.4000, 83.7100, "Popular short trek with a famous sunrise viewpoint."),
        ("Langtang Valley Trek", "Rasuwa", "Bagmati", 28.2200, 85.5200, "Valley of glaciers and Tamang heritage close to Kathmandu."),
        ("Gosaikunda Trek", "Rasuwa", "Bagmati", 28.0833, 85.4167, "Sacred alpine lake trek."),
        ("Helambu Trek", "Sindhupalchok", "Bagmati", 28.0500, 85.5500, "Tamang heritage trek north of Kathmandu."),
        ("Manaslu Circuit Trek", "Gorkha", "Gandaki", 28.5500, 84.5600, "Restricted-area trek around Mount Manaslu."),
        ("Upper Mustang Trek", "Mustang", "Gandaki", 29.1830, 83.9500, "Trans-Himalayan restricted trek to the walled kingdom of Lo."),
        ("Upper Dolpo Trek", "Dolpa", "Karnali", 29.1000, 82.8500, "Remote high-altitude trek to Shey Phoksundo and beyond."),
        ("Kanchenjunga Base Camp Trek", "Taplejung", "Koshi", 27.7000, 88.0500, "Trek to the base of the third-highest mountain."),
        ("Makalu Base Camp Trek", "Sankhuwasabha", "Koshi", 27.8500, 87.1000, "Remote trek to the base of Makalu."),
        ("Mardi Himal Trek", "Kaski", "Gandaki", 28.3800, 83.9200, "Shorter ridge trek beneath Machhapuchhre."),
        ("Khopra Danda Trek", "Myagdi", "Gandaki", 28.3900, 83.7200, "Ridge trek with Annapurna and Dhaulagiri views."),
        ("Tsum Valley Trek", "Gorkha", "Gandaki", 28.4800, 84.8500, "Sacred hidden valley near Manaslu."),
        ("Rara Lake Trek", "Mugu", "Karnali", 29.5300, 82.0900, "Trek to Nepal's largest alpine lake."),
        ("Jomsom Muktinath Trek", "Mustang", "Gandaki", 28.8100, 83.7400, "Kali Gandaki gorge trek to Muktinath."),
    ]),

    # =============== LAKES ===============
    ("lakes", [
        ("Phewa Lake", "Kaski", "Gandaki", 28.2140, 83.9470, "Iconic 4.43 km2 freshwater lake in Pokhara."),
        ("Begnas Lake", "Kaski", "Gandaki", 28.1800, 84.0700, "Second-largest lake in Pokhara valley."),
        ("Rupa Lake", "Kaski", "Gandaki", 28.1600, 84.0900, "Freshwater wetland lake near Begnas."),
        ("Rara Lake", "Mugu", "Karnali", 29.5280, 82.0900, "Nepal's largest alpine lake at 2,990 m."),
        ("Tilicho Lake", "Manang", "Gandaki", 28.6830, 83.8600, "Glacial lake at 4,919 m in the Annapurna massif."),
        ("Phoksundo Lake", "Dolpa", "Karnali", 29.2200, 82.9000, "Turquoise alpine lake in Shey Phoksundo National Park."),
        ("Gokyo Lakes", "Solukhumbu", "Koshi", 27.9600, 86.7000, "Series of sacred glacial lakes in the Khumbu."),
        ("Gosaikunda Lake", "Rasuwa", "Bagmati", 28.0833, 85.4167, "Sacred alpine lake at 4,380 m."),
        ("Panch Pokhari", "Sindhupalchok", "Bagmati", 28.0300, 85.7000, "Five sacred glacial lakes at ~4,100 m."),
        ("Indra Sarovar", "Makwanpur", "Bagmati", 27.5700, 85.0800, "Man-made reservoir on the Kulekhani River."),
        ("Kulekhani Lake", "Makwanpur", "Bagmati", 27.5700, 85.0800, "Reservoir popular for boating."),
        ("Sat Pokhari", "Kathmandu", "Bagmati", 27.7300, 85.3800, "Historic seven-pond tank in Kathmandu."),
        ("Rani Pokhari", "Kathmandu", "Bagmati", 27.7070, 85.3180, "Historic 17th-century artificial pond in central Kathmandu."),
        ("Siddha Pokhari (Ta Pukhu)", "Bhaktapur", "Bagmati", 27.6750, 85.4240, "Ancient rectangular pond in Bhaktapur."),
        ("Nagdaha", "Lalitpur", "Bagmati", 27.6400, 85.3300, "Snake-shaped sacred pond in Dhapakhel."),
        ("Phulchowki Lake", "Lalitpur", "Bagmati", 27.5700, 85.4000, "High-altitude pond below Phulchowki hill."),
        ("Surma Sarovar Lake", "Bajhang", "Sudurpashchim", 29.8000, 81.1000, "Sacred high-altitude lake in far-west Nepal."),
    ]),

    # =============== RIVERS ===============
    ("rivers", [
        ("Koshi River (Sapta Kosi)", "Sunsari", "Koshi", 26.5300, 86.9200, "Largest river in Nepal, known as the sorrow of Bihar."),
        ("Gandaki River (Narayani)", "Chitwan", "Bagmati", 27.5200, 84.0200, "Seven tributaries form the Narayani; famous for rafting."),
        ("Karnali River", "Kailali", "Sudurpashchim", 28.6000, 81.2500, "Nepal's longest river; famous for remote rafting."),
        ("Trishuli River", "Dhading", "Bagmati", 27.8300, 85.0800, "Most popular rafting river near Kathmandu."),
        ("Bhote Koshi", "Sindhupalchok", "Bagmati", 27.8800, 85.9000, "Steep upper-Bhote Kosi rafting and bungee."),
        ("Sun Koshi", "Sindhuli", "Bagmati", 27.3000, 85.9000, "'River of Gold'; long multi-day rafting."),
        ("Kali Gandaki Gorge", "Mustang", "Gandaki", 28.7300, 83.7200, "Deepest gorge in the world between Annapurna and Dhaulagiri."),
        ("Seti Gandaki Gorge", "Kaski", "Gandaki", 28.2300, 83.9700, "Deep narrow gorge running through Pokhara."),
        ("Arun River", "Sankhuwasabha", "Koshi", 27.6000, 87.2500, "Major trans-Himalayan tributary of the Sapta Kosi."),
        ("Tamur River", "Taplejung", "Koshi", 27.0000, 87.6000, "Eastern tributary of the Kosi."),
        ("Marshyangdi River", "Manang", "Gandaki", 28.4000, 84.4000, "White-water river along the Annapurna Circuit."),
        ("Bheri River", "Surkhet", "Karnali", 28.5000, 81.5000, "Mid-western rafting and fishing river."),
        ("West Rapti River", "Dang", "Lumbini", 28.0000, 82.4000, "Major Lumbini-zone river."),
        ("Bagmati River", "Kathmandu", "Bagmati", 27.6800, 85.3700, "Sacred Kathmandu Valley river passing Pashupatinath."),
        ("Tinau River", "Palpa/Rupandehi", "Lumbini", 27.7500, 83.5000, "River below Tansen."),
    ]),

    # =============== WATERFALLS ===============
    ("waterfalls", [
        ("Davis Falls (Patale Chhango)", "Kaski", "Gandaki", 28.1900, 83.9500, "Waterfall from Phewa Lake plunging into an underground tunnel."),
        ("Pachaljharana Waterfall", "Kalikot", "Karnali", 29.2500, 81.7000, "One of the tallest waterfalls in Nepal at 381 m."),
        ("Hyatung Falls", "Terhathum", "Koshi", 27.1500, 87.5500, "365 m waterfall in eastern Nepal."),
        ("Rupse Falls", "Myagdi", "Gandaki", 28.5500, 83.6500, "Roadside 300m falls en route to Jomsom."),
        ("Tindhare Waterfall", "Kavrepalanchok", "Bagmati", 27.6000, 85.5200, "300 m waterfall near Roshi."),
        ("Sundarijal Waterfall", "Kathmandu", "Bagmati", 27.7600, 85.4200, "Popular waterfall and hiking spot."),
        ("Jhor Waterfall", "Kathmandu", "Bagmati", 27.7800, 85.3300, "Seasonal falls north of Kathmandu."),
        ("Chhange Waterfall", "Lalitpur", "Bagmati", 27.5600, 85.3600, "Waterfall near Lele."),
        ("Pokali Waterfall", "Okhaldhunga", "Koshi", 27.3500, 86.5000, "130 m waterfall in eastern Nepal."),
        ("Todke Waterfall", "Ilam", "Koshi", 26.9500, 87.8500, "85 m waterfall in eastern Ilam."),
        ("Simba Falls", "Dhading", "Bagmati", 27.9000, 84.8500, "Waterfall on the Pasang Lhamu highway."),
        ("Bhalamphokhari Falls", "Nuwakot", "Bagmati", 27.9500, 85.2000, "Scenic waterfall near Nuwakot."),
    ]),

    # =============== CAVES ===============
    ("caves", [
        ("Mahendra Cave", "Kaski", "Gandaki", 28.2500, 83.9700, "Limestone cave with stalactites near Pokhara."),
        ("Gupteshwor Mahadev Cave", "Kaski", "Gandaki", 28.1900, 83.9550, "Sacred Shiva cave across from Davis Falls."),
        ("Bat Cave (Chamere Gufa)", "Kaski", "Gandaki", 28.2500, 83.9750, "Cave inhabited by thousands of bats."),
        ("Mahadev Cave Pokhara", "Kaski", "Gandaki", 28.2500, 83.9730, "Shiva cave near Mahendra Cave."),
        ("Halesi Mahadev Cave", "Khotang", "Koshi", 27.1800, 86.6200, "Sacred natural cave venerated by Hindus and Buddhists."),
        ("Siddha Gufa", "Tanahun", "Gandaki", 27.9400, 84.4000, "437 m-long cave near Bimalnagar/Bandipur."),
        ("Chobhar Gorge Caves", "Kathmandu", "Bagmati", 27.6550, 85.2900, "Limestone gorge and caves on the Bagmati."),
        ("Maratika Caves (Halesi)", "Khotang", "Koshi", 27.1800, 86.6200, "Padmasambhava meditation cave complex."),
        ("Sky Caves of Mustang", "Mustang", "Gandaki", 29.2000, 83.9000, "Ancient cliffside man-made caves in Upper Mustang."),
        ("Chhoser Jhong Cave", "Mustang", "Gandaki", 29.1900, 83.9300, "Multi-story cave system in Lo Manthang."),
    ]),

    # =============== WILDLIFE / NATIONAL PARKS ===============
    ("wildlife", [
        ("Chitwan National Park", "Chitwan", "Bagmati", 27.5400, 84.4800, "UNESCO park with one-horned rhino and Bengal tiger."),
        ("Bardiya National Park", "Bardiya", "Lumbini", 28.4000, 81.5000, "Remote Terai park famous for tigers and wild elephants."),
        ("Shuklaphanta National Park", "Kanchanpur", "Sudurpashchim", 28.8500, 80.2000, "Grassland park with swamp deer and tigers."),
        ("Parsa National Park", "Parsa", "Madhesh", 27.3500, 84.8500, "Wildlife reserve east of Chitwan."),
        ("Banke National Park", "Banke", "Lumbini", 28.1000, 81.8500, "Tiger conservation park in the mid-west."),
        ("Khaptad National Park", "Doti", "Sudurpashchim", 29.3500, 80.9500, "Mid-mountain national park with Khaptad Baba ashram."),
        ("Shivapuri Nagarjun National Park", "Kathmandu", "Bagmati", 27.8000, 85.4000, "Protected watershed north of Kathmandu."),
        ("Langtang National Park", "Rasuwa", "Bagmati", 28.2200, 85.5300, "Himalayan national park near the Tibetan border."),
        ("Makalu Barun National Park", "Sankhuwasabha", "Koshi", 27.7800, 87.1000, "Remote eastern Himalayan national park."),
        ("Shey Phoksundo National Park", "Dolpa", "Karnali", 29.2500, 82.9000, "Trans-Himalayan park with turquoise Phoksundo Lake."),
        ("Rara National Park", "Mugu", "Karnali", 29.5000, 82.1000, "Smallest Himalayan national park containing Rara Lake."),
        ("Sagarmatha National Park", "Solukhumbu", "Koshi", 27.9500, 86.8000, "UNESCO park containing Mount Everest."),
        ("Annapurna Conservation Area", "Kaski/Manang/Mustang", "Gandaki", 28.6000, 83.9000, "Largest protected area in Nepal; Annapurna region."),
        ("Manaslu Conservation Area", "Gorkha", "Gandaki", 28.5500, 84.6000, "Conservation area around Mount Manaslu."),
        ("Kanchenjunga Conservation Area", "Taplejung", "Koshi", 27.6500, 88.0000, "High-altitude protected area around Kanchenjunga."),
        ("Gaurishankar Conservation Area", "Dolakha", "Bagmati", 27.8500, 86.1000, "Conservation area near the Tibetan border."),
        ("Dhorpatan Hunting Reserve", "Rukum", "Lumbini", 28.5000, 83.0000, "Only hunting reserve in Nepal."),
    ]),

    # =============== VIEWPOINTS ===============
    ("viewpoints", [
        ("Sarangkot Viewpoint", "Kaski", "Gandaki", 28.2400, 83.9400, "Popular sunrise viewpoint over Pokhara and the Annapurnas."),
        ("Poon Hill", "Myagdi", "Gandaki", 28.4000, 83.7000, "Famous Ghorepani sunrise viewpoint (3,210 m)."),
        ("Nagarkot View Tower", "Bhaktapur", "Bagmati", 27.7200, 85.5200, "Popular sunrise/sunset viewpoint over the Himalayas."),
        ("Chandragiri Hill", "Kathmandu", "Bagmati", 27.7830, 85.2060, "Hill station with cable car and Bhaleshwor temple."),
        ("Phulchowki Hill", "Lalitpur", "Bagmati", 27.5800, 85.4000, "Highest hill around the Kathmandu Valley (2,782 m)."),
        ("Shree Antu Viewpoint", "Ilam", "Koshi", 26.8800, 88.0800, "Easternmost sunrise viewpoint with Kanchenjunga views."),
        ("Kakani Viewpoint", "Nuwakot", "Bagmati", 27.8200, 85.2700, "Ridge viewpoint north of Kathmandu."),
        ("Daman View Tower", "Makwanpur", "Bagmati", 27.6200, 85.1000, "Mid-hill viewpoint with the widest Himalayan panorama."),
        ("Kala Patthar", "Solukhumbu", "Koshi", 27.9950, 86.8250, "Iconic 5,644 m viewpoint above Everest Base Camp."),
        ("Gokyo Ri", "Solukhumbu", "Koshi", 27.9600, 86.6800, "5,357 m viewpoint above Gokyo Lakes."),
        ("Pikey Peak", "Solukhumbu", "Koshi", 27.5000, 86.7500, "4,065 m viewpoint with stunning Everest views."),
        ("Sarangkot Paragliding Takeoff", "Kaski", "Gandaki", 28.2450, 83.9350, "World's 2nd-best paragliding launch site."),
    ]),

    # =============== HILLS ===============
    ("hills", [
        ("Bandipur Hill Station", "Tanahun", "Gandaki", 27.9400, 84.4100, "Restored Newar trading post on a ridgetop."),
        ("Tansen Hill Station", "Palpa", "Lumbini", 27.8700, 83.5400, "Historic Newar trading town at 1,350 m."),
        ("Dhulikhel Hill", "Kavrepalanchok", "Bagmati", 27.6200, 85.5600, "Ridgetop town with Himalayan panorama."),
        ("Nagarkot Hill", "Bhaktapur", "Bagmati", 27.7200, 85.5200, "Hill station at 2,175 m popular for sunrises."),
        ("Godawari Botanical Hill", "Lalitpur", "Bagmati", 27.5900, 85.3800, "Botanical gardens at the base of Phulchowki."),
    ]),

    # =============== VILLAGES ===============
    ("villages", [
        ("Ghandruk", "Kaski", "Gandaki", 28.3800, 83.8200, "Iconic Gurung village with Annapurna South views."),
        ("Ghorepani", "Myagdi", "Gandaki", 28.4000, 83.7100, "Gurung village on the Poon Hill trek."),
        ("Manang Braga", "Manang", "Gandaki", 28.6400, 84.0100, "Traditional Tibetan-Buddhist village."),
        ("Kagbeni", "Mustang", "Gandaki", 28.8600, 83.7400, "Medieval walled village at the entrance to Upper Mustang."),
        ("Marpha", "Mustang", "Gandaki", 28.7700, 83.6900, "Apple capital of Nepal on the Jomsom trek."),
        ("Tukuche", "Mustang", "Gandaki", 28.7300, 83.6500, "Thakali trading village along the Kali Gandaki."),
        ("Ghandruk Gurung Village", "Kaski", "Gandaki", 28.3700, 83.8100, "Stone-roofed Gurung settlement."),
        ("Syangja Village Homestays", "Syangja", "Gandaki", 28.0000, 83.8500, "Community homestay villages."),
        ("Sirubari Village", "Syangja", "Gandaki", 27.9900, 83.7500, "Pioneer Gurung homestay village."),
        ("Ghale Gaun", "Lamjung", "Gandaki", 28.3300, 84.4300, "Model Gurung homestay village."),
        ("Ghalegaun", "Lamjung", "Gandaki", 28.3400, 84.4200, "Popular Gurung hill village."),
        ("Barpak", "Gorkha", "Gandaki", 28.2500, 84.7500, "Epicenter of the 2015 quake; scenic Gurung village."),
        ("Chitlang", "Makwanpur", "Bagmati", 27.6300, 85.1700, "Newar and Tamang village near Kathmandu."),
        ("Namche Bazaar", "Solukhumbu", "Koshi", 27.8050, 86.7120, "Sherpa trading hub and gateway to Everest."),
        ("Khumjung", "Solukhumbu", "Koshi", 27.8250, 86.7200, "Sherpa village above Namche."),
        ("Phakding", "Solukhumbu", "Koshi", 27.7500, 86.7100, "Sherpa/Lama village on the EBC trail."),
        ("Jhong", "Mustang", "Gandaki", 28.8400, 83.7700, "Traditional Mustang village above Kagbeni."),
        ("Lo Manthang", "Mustang", "Gandaki", 29.1830, 83.9500, "Walled medieval capital of Upper Mustang."),
        ("Dhampus", "Kaski", "Gandaki", 28.3000, 83.8700, "Gurung village near Pokhara."),
        ("Sarangkot Village", "Kaski", "Gandaki", 28.2400, 83.9400, "Hilltop village above Pokhara."),
        ("Bandipur Newar Bazaar", "Tanahun", "Gandaki", 27.9400, 84.4100, "Preserved Newar hill bazaar."),
    ]),

    # =============== HOT SPRINGS ===============
    ("hot-springs", [
        ("Tatopani Hot Spring (Myagdi)", "Myagdi", "Gandaki", 28.4800, 83.6800, "Natural hot spring on the Annapurna Circuit."),
        ("Jomsom Tatopani", "Mustang", "Gandaki", 28.8800, 83.7500, "Hot spring above Kagbeni."),
        ("Chhumchaur Hot Spring", "Jumla", "Karnali", 29.2000, 82.2500, "Mid-western hot spring."),
        ("Ruru Kshetra (Ridi) Hot Spring", "Gulmi", "Lumbini", 27.9300, 83.4300, "Sacred hot spring at Ridi."),
    ]),

    # =============== MUSEUMS ===============
    ("museums", [
        ("Patan Museum", "Lalitpur", "Bagmati", 27.6750, 85.3250, "Houses one of the finest collections of traditional Nepali art."),
        ("National Museum of Nepal", "Kathmandu", "Bagmati", 27.7070, 85.2890, "Military and cultural museum at Chhauni."),
        ("Narayanhiti Palace Museum", "Kathmandu", "Bagmati", 27.7180, 85.3210, "Former royal palace."),
        ("Tansen Durbar Museum", "Palpa", "Lumbini", 27.8680, 83.5460, "Restored Rana palace museum."),
        ("Gorkha Museum", "Gorkha", "Gandaki", 27.9950, 84.6300, "Historic artifacts of the Shah dynasty."),
        ("Tharu Cultural Museum", "Chitwan", "Bagmati", 27.5600, 84.5000, "Tharu cultural museum in Sauraha."),
        ("Annapurna Butterfly Museum", "Kaski", "Gandaki", 28.2200, 83.9700, "Butterfly and insect collection in Pokhara."),
        ("International Mountain Museum", "Kaski", "Gandaki", 28.1900, 83.9800, "Comprehensive museum of mountaineering."),
    ]),

    # =============== CITIES ===============
    ("cities", [
        ("Kathmandu Metropolis", "Kathmandu", "Bagmati", 27.7172, 85.3240, "Capital and largest city of Nepal."),
        ("Pokhara", "Kaski", "Gandaki", 28.2096, 83.9856, "Tourism capital and gateway to the Annapurnas."),
        ("Lalitpur (Patan)", "Lalitpur", "Bagmati", 27.6667, 85.3167, "City of fine arts and Patan Durbar Square."),
        ("Bhaktapur", "Bhaktapur", "Bagmati", 27.6722, 85.4298, "Medieval city of temples and woodcarving."),
        ("Biratnagar", "Morang", "Koshi", 26.4524, 87.2718, "Industrial hub of eastern Nepal."),
        ("Birgunj", "Parsa", "Madhesh", 27.0000, 84.8800, "Southern trade gateway to India."),
        ("Bharatpur", "Chitwan", "Bagmati", 27.6800, 84.4300, "Commercial hub of Chitwan."),
        ("Nepalgunj", "Banke", "Lumbini", 28.0500, 81.6200, "Mid-western industrial and transit hub."),
        ("Dharan", "Sunsari", "Koshi", 26.8126, 87.2837, "Eastern hillstation town and British Gurkha camp."),
        ("Butwal", "Rupandehi", "Lumbini", 27.7000, 83.4500, "Siddhartha Highway junction city."),
        ("Bhairahawa (Siddharthanagar)", "Rupandehi", "Lumbini", 27.5000, 83.4500, "Gateway to Lumbini; regional airport."),
        ("Janakpur", "Dhanusha", "Madhesh", 26.7306, 85.9258, "Historic Mithila city of Janaki Mandir."),
        ("Hetauda", "Makwanpur", "Bagmati", 27.4200, 85.0300, "Industrial city on the Tribhuvan Rajpath."),
        ("Tansen", "Palpa", "Lumbini", 27.8670, 83.5460, "Historic Newar hill town."),
        ("Dhangadhi", "Kailali", "Sudurpashchim", 28.7000, 80.6000, "Far-western commercial hub."),
    ]),

    # =============== FESTIVALS ===============
    ("festivals", [
        ("Dashain Ghatasthapana", "Kathmandu", "Bagmati", 27.7100, 85.3200, "Nepal's longest and most auspicious Hindu festival."),
        ("Tihar (Deepawali)", "Kathmandu", "Bagmati", 27.7100, 85.3200, "Festival of lights honouring Laxmi and animals."),
        ("Holi (Fagu Purnima)", "Kathmandu", "Bagmati", 27.7100, 85.3200, "Festival of colours."),
        ("Indra Jatra", "Kathmandu", "Bagmati", 27.7040, 85.3060, "Kathmandu's iconic masked-dance festival with Kumari."),
        ("Bisket Jatra Bhaktapur", "Bhaktapur", "Bagmati", 27.6720, 85.4290, "Nepali New Year chariot festival in Bhaktapur."),
        ("Rato Machhindranath Jatra", "Lalitpur", "Bagmati", 27.6700, 85.3200, "Month-long chariot festival of Patan."),
        ("Mani Rimdu", "Solukhumbu", "Koshi", 27.8360, 86.7650, "Sherpa masked dance festival at Tengboche."),
        ("Tiji Festival", "Mustang", "Gandaki", 29.1830, 83.9500, "Three-day Mustang festival for world peace."),
        ("Janaki Vivah Panchami", "Dhanusha", "Madhesh", 26.7300, 85.9200, "Celebrating the marriage of Ram and Sita."),
        ("Buddha Jayanti (Lumbini)", "Rupandehi", "Lumbini", 27.4700, 83.2800, "Celebration of Buddha's birth in Lumbini."),
        ("Gai Jatra", "Kathmandu", "Bagmati", 27.7000, 85.3100, "Cow procession festival honouring departed souls."),
        ("Ghode Jatra", "Kathmandu", "Bagmati", 27.6950, 85.3150, "Horse racing festival at Tundikhel."),
    ]),

    # =============== TEA / COFFEE ===============
    ("tea-coffee", [
        ("Kanyam Tea Gardens", "Ilam", "Koshi", 26.9200, 88.0500, "Queen of Ilam tea gardens; popular tourist spot."),
        ("Ilam Tea Estates", "Ilam", "Koshi", 26.9100, 87.9300, "Rolling green tea plantations in eastern Nepal."),
        ("Shree Antu Tea Gardens", "Ilam", "Koshi", 26.8800, 88.1000, "Tea gardens at the sunrise viewpoint."),
        ("Sankhuwasabha Organic Coffee", "Sankhuwasabha", "Koshi", 27.5000, 87.3000, "High-altitude organic Arabica coffee."),
        ("Gulmi Coffee Farms", "Gulmi", "Lumbini", 27.9500, 83.3000, "Famous mid-hill organic coffee district."),
        ("Laliguras Tea Garden", "Dhankuta", "Koshi", 26.9800, 87.3500, "Eastern hill tea estate."),
    ]),

    # =============== BIRD WATCHING ===============
    ("bird-watching", [
        ("Koshi Tappu Wildlife Reserve", "Sunsari", "Koshi", 26.6300, 87.0000, "Ramsar wetland with over 485 bird species."),
        ("Chitwan Jungle Birding", "Chitwan", "Bagmati", 27.5500, 84.5000, "Over 500 bird species in sal and riverine forest."),
        ("Godawari Botanical Garden Birds", "Lalitpur", "Bagmati", 27.5900, 85.3800, "Valley birding hotspot with 200+ species."),
        ("Phulchowki Birding", "Lalitpur", "Bagmati", 27.5800, 85.4000, "Highest Kathmandu hill; Himalayan bird species."),
        ("Shivapuri Birding Trail", "Kathmandu", "Bagmati", 27.8000, 85.4000, "Ridge trail with over 300 species."),
        ("Bishazari Tal Bird Area", "Chitwan", "Bagmati", 27.6000, 84.4500, "Ramsar 20,000-lake wetland for migratory birds."),
    ]),

    # =============== ADVENTURE / AIR / WATER / CAMP / CYCLE ===============
    ("adventure", [
        ("The Last Resort Bungee", "Sindhupalchok", "Bagmati", 27.8900, 85.9000, "160 m bungee jump over the Bhote Koshi."),
        ("HighGround Adventures Bungee", "Kaski", "Gandaki", 28.2500, 83.9900, "Bungee and swing in Pokhara."),
        ("Cliff Kushma Bungee", "Parbat", "Gandaki", 28.0500, 83.7000, "World's second-highest bungee (228 m)."),
        ("Hattiban Rock Climbing", "Kathmandu", "Bagmati", 27.6400, 85.2900, "Rock climbing cliff south of Kathmandu."),
        ("Nagarjun Cliff Climbing", "Kathmandu", "Bagmati", 27.7500, 85.2700, "Rock climbing in Nagarjun forest."),
    ]),
    ("air-sports", [
        ("Sarangkot Paragliding", "Kaski", "Gandaki", 28.2400, 83.9400, "Tandem paragliding over Phewa Lake."),
        ("Pokhara Ultralight Flights", "Kaski", "Gandaki", 28.2000, 84.0000, "Ultralight flights over the Annapurnas."),
        ("Everest Mountain Flight", "Kathmandu", "Bagmati", 27.7000, 85.3500, "Early-morning scenic flight past Everest."),
        ("Zipflyer Pokhara", "Kaski", "Gandaki", 28.2600, 83.9800, "Steep 1.8 km zip-line in Sarangkot."),
        ("Skydiving Everest", "Solukhumbu", "Koshi", 27.9800, 86.7500, "Seasonal skydiving over the Khumbu."),
    ]),
    ("water-sports", [
        ("Trishuli Rafting", "Chitwan/Nuwakot", "Bagmati", 27.8000, 85.1000, "Grade III–IV rafting two hours from Kathmandu."),
        ("Bhote Koshi Rafting", "Sindhupalchok", "Bagmati", 27.8900, 85.9200, "Steep continuous Grade IV–V rafting."),
        ("Seti River Rafting", "Kaski", "Gandaki", 28.2000, 84.0000, "Short half-day rafting near Pokhara."),
        ("Karnali River Rafting", "Surkhet", "Karnali", 28.6000, 81.2500, "Multi-day remote wilderness rafting."),
        ("Phewa Lake Boating", "Kaski", "Gandaki", 28.2140, 83.9470, "Paddle and sail boating on Phewa Lake."),
    ]),
    ("camping", [
        ("Balthali Camping", "Kavrepalanchok", "Bagmati", 27.5800, 85.5300, "Village-ridge camping near Panauti."),
        ("Chandragiri Camping", "Kathmandu", "Bagmati", 27.7800, 85.2000, "Camping on the Kathmandu ridge."),
        ("Kulekhani Camping", "Makwanpur", "Bagmati", 27.5700, 85.0800, "Lakeside camping near the reservoir."),
        ("Sarangkot Camping", "Kaski", "Gandaki", 28.2400, 83.9400, "Hilltop camping with Himalayan views."),
    ]),
    ("cycling", [
        ("Kathmandu Valley Rim Cycling", "Kathmandu", "Bagmati", 27.7200, 85.3200, "Classic loop around the valley."),
        ("Pokhara Lakeside Cycling", "Kaski", "Gandaki", 28.2100, 83.9700, "Flat cycling around Phewa Lake."),
        ("Shivapuri Mountain Biking", "Kathmandu", "Bagmati", 27.8000, 85.4000, "Popular MTB trails on the valley rim."),
    ]),
    ("winter", [
        ("Kalinchowk Snow View", "Dolakha", "Bagmati", 27.7600, 86.0500, "Closest heavy-snow destination to Kathmandu."),
        ("Chandragiri Winter Snow", "Kathmandu", "Bagmati", 27.7800, 85.2000, "Occasional snow in winter."),
        ("Phulchowki Winter Snow", "Lalitpur", "Bagmati", 27.5800, 85.4000, "First snowfall viewpoint from Kathmandu."),
        ("Daman Snow", "Makwanpur", "Bagmati", 27.6200, 85.1000, "Mid-hill winter snow viewpoint."),
    ]),
    ("agriculture", [
        ("Kavrepalanchok Organic Farms", "Kavrepalanchok", "Bagmati", 27.6000, 85.5500, "Community-based organic farming."),
        ("Mustang Apple Orchards", "Mustang", "Gandaki", 28.8000, 83.7500, "High-altitude apple, buckwheat and barley farms."),
        ("Rasuwa Potato Farms", "Rasuwa", "Bagmati", 28.1500, 85.4000, "Traditional Himalayan potato cultivation."),
    ]),
    ("scenic-routes", [
        ("Prithvi Highway (Mugling Road)", "Chitwan", "Bagmati", 27.7800, 84.5000, "Scenic Kathmandu-Pokhara highway."),
        ("Siddhartha Highway", "Palpa/Rupandehi", "Lumbini", 27.8000, 83.5500, "Butwal to Pokhara road with Tansen views."),
        ("Araniko Highway", "Kavrepalanchok", "Bagmati", 27.7500, 85.7500, "Kathmandu to Kodari border; Himalayan scenery."),
        ("Karnali Highway", "Surkhet/Jumla", "Karnali", 29.0000, 81.9000, "Mid-west highway to Jumla and Rara."),
        ("Pasang Lhamu Highway", "Rasuwa/Dhading", "Bagmati", 28.0500, 85.2500, "Road to Syabrubesi and Langtang."),
    ]),
    ("forests", [
        ("Chitwan Sal Forests", "Chitwan", "Bagmati", 27.5500, 84.4800, "Dense sal and riverine forest."),
        ("Shivapuri Oak Forests", "Kathmandu", "Bagmati", 27.8000, 85.4000, "Oak, rhododendron and pine forest."),
        ("Phulchowki Rhododendron Forest", "Lalitpur", "Bagmati", 27.5800, 85.4000, "Subtropical to temperate forest."),
        ("Bardia Sal & Grasslands", "Bardiya", "Lumbini", 28.4000, 81.5000, "Sal forest and tall grasslands."),
        ("Khaptad Grass & Oak", "Doti", "Sudurpashchim", 29.3500, 80.9500, "Temperate mixed forest with meadows."),
    ]),
    ("parks-gardens", [
        ("Godawari Botanical Gardens", "Lalitpur", "Bagmati", 27.5900, 85.3800, "National botanical garden."),
        ("Garden of Dreams", "Kathmandu", "Bagmati", 27.7140, 85.3150, "Restored neo-classical garden."),
        ("Ratna Park", "Kathmandu", "Bagmati", 27.7060, 85.3150, "Central public park in Kathmandu."),
        ("Sahid Smarak Park", "Hetauda", "Bagmati", 27.4100, 85.0300, "Martyr's memorial park in Hetauda."),
        ("Nagarkot Nature Walks", "Bhaktapur", "Bagmati", 27.7200, 85.5200, "Pine-forest walks and viewpoints."),
    ]),
    ("eco-tourism", [
        ("Ghalegaun Eco-Village", "Lamjung", "Gandaki", 28.3400, 84.4200, "Model community eco-tourism village."),
        ("Sirubari Eco-Homestays", "Syangja", "Gandaki", 27.9900, 83.7500, "Award-winning community homestay."),
        ("Chepang Hills Trail", "Chitwan", "Bagmati", 27.7500, 84.7000, "Indigenous Chepang community eco-trail."),
        ("Amaltari Homestay", "Chitwan", "Bagmati", 27.6000, 84.2500, "Buffer-zone community eco-stay."),
    ]),
    ("spiritual-wellness", [
        ("Osho Tapoban", "Kathmandu", "Bagmati", 27.7600, 85.3600, "Meditation retreat in Nagarjun forest."),
        ("Kopan Meditation Courses", "Kathmandu", "Bagmati", 27.7420, 85.3680, "Popular Tibetan Buddhist meditation retreats."),
        ("Pullahari Monastery Retreat", "Kathmandu", "Bagmati", 27.7500, 85.3700, "Tibetan Buddhist retreat centre."),
        ("Lumbini Meditation Retreats", "Rupandehi", "Lumbini", 27.4700, 83.2800, "Monastic zone with international retreat centres."),
    ]),
    ("pilgrimage", [
        ("Muktinath Dham", "Mustang", "Gandaki", 28.8158, 83.8733, "Sacred Char Dham site for Hindus and Buddhists."),
        ("Pashupatinath Dham", "Kathmandu", "Bagmati", 27.7106, 85.3485, "Most sacred Hindu temple in Nepal."),
        ("Janakpur Dham", "Dhanusha", "Madhesh", 26.7306, 85.9258, "Birthplace of Sita and Ram-Sita marriage site."),
        ("Barahachhetra Dham", "Sunsari", "Koshi", 26.5000, 87.0700, "One of Nepal's four Char Dham."),
        ("Devghat Dham", "Chitwan/Tanahun", "Gandaki", 27.7800, 84.4200, "Sacred river confluence."),
        ("Swargadwari Dham", "Pyuthan", "Lumbini", 28.1700, 82.7400, "Hilltop pilgrimage site."),
        ("Halesi Mahadev Dham", "Khotang", "Koshi", 27.1800, 86.6200, "Pashupati of the east."),
        ("Pathibhara Devi Dham", "Taplejung", "Koshi", 27.4300, 87.7500, "High-altitude goddess shrine."),
        ("Badimalika Dham", "Bajura", "Sudurpashchim", 29.4500, 81.4500, "Far-western pilgrimage."),
    ]),
    ("food-culinary", [
        ("Bhojan Griha Newari Cuisine", "Kathmandu", "Bagmati", 27.7100, 85.3250, "Traditional Newari feast restaurant in a restored Rana house."),
        ("Thamel Street Food", "Kathmandu", "Bagmati", 27.7150, 85.3120, "Tourist hub serving momo, thukpa and Newari snacks."),
        ("Pokhara Lakeside Cafes", "Kaski", "Gandaki", 28.2100, 83.9600, "Lakeside dining with Himalayan views."),
        ("Thakali Kitchens Tukuche", "Mustang", "Gandaki", 28.7300, 83.6500, "Authentic Thakali bhat along the Kali Gandaki."),
        ("Bhojpur Momo Trail", "Bhojpur", "Koshi", 27.1700, 87.0500, "Eastern hill region famous for buff momo."),
    ]),
    ("shopping", [
        ("Asan Bazaar", "Kathmandu", "Bagmati", 27.7080, 85.3130, "Historic six-street market junction."),
        ("Indrachowk Bazaar", "Kathmandu", "Bagmati", 27.7060, 85.3100, "Wholesale and retail traditional market."),
        ("Thamel Tourist Market", "Kathmandu", "Bagmati", 27.7150, 85.3120, "Handicrafts, trekking gear and souvenir shopping."),
        ("Patan Mangal Bazaar", "Lalitpur", "Bagmati", 27.6730, 85.3240, "Metal crafts, woodcarving and thangka shops."),
        ("Bhaktapur Potter's Square", "Bhaktapur", "Bagmati", 27.6700, 85.4280, "Traditional pottery market."),
        ("Pokhara Lakeside Market", "Kaski", "Gandaki", 28.2100, 83.9600, "Souvenir and trekking-gear shops."),
    ]),
    ("natural-wonders", [
        ("Kali Gandaki Gorge", "Mustang", "Gandaki", 28.7300, 83.7200, "World's deepest gorge between Annapurna and Dhaulagiri."),
        ("Seti Gandaki Gorge", "Kaski", "Gandaki", 28.2300, 83.9700, "Narrow 60 m-deep gorge through Pokhara."),
        ("Sindhupalchok Jugal Himal", "Sindhupalchok", "Bagmati", 28.0000, 85.8000, "Jagged glacial formations."),
        ("Dudh Kunda", "Solukhumbu", "Koshi", 27.6000, 86.7000, "Sacred glacial lake at 4,600 m."),
    ]),
]


def _slugify(text):
    import re
    s = (text or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


class Command(BaseCommand):
    help = "Seed curated real Nepal destinations across all 36 taxonomy categories."

    @transaction.atomic
    def handle(self, *args, **options):
        created = 0
        updated = 0
        for category_slug, items in DESTINATIONS:
            cat = Category.objects.filter(slug=category_slug).first()
            if not cat:
                cat = Category.objects.filter(name__icontains=category_slug).first()
            if not cat:
                self.stderr.write(self.style.ERROR(f"Category {category_slug} not found — run seed_taxonomy first."))
                continue
            for (name, district, province, lat, lon, desc) in items:
                slug = _slugify(name)
                existing = Destination.objects.filter(slug=slug).first()
                if existing:
                    # Ensure it has the correct category, lat, lon, description
                    changed = False
                    if existing.category_id != cat.id:
                        existing.category = cat; changed = True
                    if (not existing.latitude) and lat:
                        existing.latitude = lat; changed = True
                    if (not existing.longitude) and lon:
                        existing.longitude = lon; changed = True
                    if (not existing.short_description) and desc:
                        existing.short_description = desc; changed = True
                    if not existing.district:
                        existing.district = district; changed = True
                    if not existing.city:
                        existing.city = district; changed = True
                    if not existing.province:
                        existing.province = province; changed = True
                    if not existing.is_active:
                        existing.is_active = True; changed = True
                    if existing.status != Destination.SubmissionStatus.APPROVED:
                        existing.status = Destination.SubmissionStatus.APPROVED; changed = True
                    if changed:
                        existing.save()
                        updated += 1
                    continue
                Destination.objects.create(
                    name=name,
                    slug=slug,
                    category=cat,
                    district=district,
                    city=district,
                    province=province,
                    latitude=lat,
                    longitude=lon,
                    short_description=desc,
                    description=desc,
                    is_active=True,
                    status=Destination.SubmissionStatus.APPROVED,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created} new destinations; updated {updated} existing ones."
        ))
