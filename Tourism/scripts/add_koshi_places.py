"""Add 109 famous Koshi-province places (from the ward-level district data)
as real destinations with categories + coordinates. Skips existing."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")

import django  # noqa: E402

django.setup()

from tourist.models import Destination, Category  # noqa: E402

cats = {c.slug: c for c in Category.objects.all()}

# (name, category_slug, district, province, city, lat, lon, short)
PLACES = [
    # ---------- Taplejung ----------
    ("Khangpachen", "mountains", "Taplejung", "Koshi", "Khangpachen", 27.70, 87.90, "High settlement near Kumbhakarna on the Kanchenjunga trek."),
    ("Khambachen", "villages", "Taplejung", "Koshi", "Khambachen", 27.74, 87.98, "Trekking village on the Kanchenjunga Base Camp route."),
    ("Timbung Pokhari", "lakes", "Taplejung", "Koshi", "Timbung", 27.43, 87.85, "Sacred high-altitude lake (4,481 m) on the Taplejung-Panchthar border."),
    ("Dhangdhange Waterfall", "waterfalls", "Taplejung", "Koshi", "Sidingwa", 27.40, 87.78, "Tall waterfall of Sidingwa Rural Municipality, Taplejung."),
    ("Sidingwa Dham", "pilgrimage", "Taplejung", "Koshi", "Sidingwa", 27.39, 87.75, "Sacred religious site of Sidingwa Rural Municipality."),
    ("Diki Chhyoling Monastery", "buddhist-sites", "Taplejung", "Koshi", "Olangchung Gola", 27.62, 87.82, "600-year-old monastery near Olangchung Gola, Taplejung."),
    # ---------- Panchthar ----------
    ("Sadhutar Viewpoint", "viewpoints", "Panchthar", "Koshi", "Phidim", 27.13, 87.72, "Phidim Ward 8 viewpoint with Kanchenjunga and Kumbhakarna views."),
    ("Hilihang Palace", "heritage", "Panchthar", "Koshi", "Hilihang", 27.18, 87.70, "Historic palace of Hilihang Rural Municipality, Panchthar."),
    ("Jor Pokhari", "lakes", "Panchthar", "Koshi", "Jor Pokhari", 27.20, 87.66, "Twin sacred ponds of Hilihang, Panchthar."),
    ("Timbu Pokhari", "lakes", "Panchthar", "Koshi", "Timbu", 27.10, 87.85, "High-altitude lake of Yangwarak, Panchthar."),
    ("Chiwabhanjyang", "viewpoints", "Panchthar", "Koshi", "Chiwabhanjyang", 27.08, 87.90, "Border pass viewpoint of Yangwarak, Panchthar."),
    ("Phalot", "trekking", "Panchthar", "Koshi", "Phalelung", 27.20, 87.80, "Highland trekking area of Phalelung, Panchthar."),
    ("Phokte Danda", "viewpoints", "Panchthar", "Koshi", "Phokte", 27.22, 87.78, "Ridge viewpoint of Phalelung, Panchthar."),
    ("Aagejung Monastery", "buddhist-sites", "Panchthar", "Koshi", "Aagejung", 27.24, 87.76, "Old monastery of Phalelung Ward 1, Panchthar."),
    ("Labrekuti", "pilgrimage", "Panchthar", "Koshi", "Labrekuti", 27.16, 87.68, "Heritage area of the Silauti-Labrekuti route, Phalgunanda."),
    ("Silauti", "heritage", "Panchthar", "Koshi", "Silauti", 27.15, 87.67, "Historic settlement of Phalgunanda, Panchthar."),
    ("Mahaguru Phalgunanda Mausoleum", "pilgrimage", "Panchthar", "Koshi", "Silauti", 27.15, 87.67, "Mausoleum of Mahaguru Phalgunanda in the Silauti-Labrekuti area."),
    ("Kummayak Kussayak", "pilgrimage", "Panchthar", "Koshi", "Yasok", 27.12, 87.62, "Sacred Kirat/Limbu site of Kummayak, Panchthar."),
    ("Battise Waterfall", "waterfalls", "Panchthar", "Koshi", "Phalgunanda", 27.14, 87.70, "Thirty-two-step waterfall of Phalgunanda Ward 2."),
    ("Hile Pokhari Panchthar", "lakes", "Panchthar", "Koshi", "Miklajung", 27.24, 87.72, "Lake of Miklajung Rural Municipality, Panchthar."),
    ("Gumse Pathibhara", "temples", "Panchthar", "Koshi", "Yangwarak", 27.08, 87.88, "Pathibhara shrine of Yangwarak, Panchthar."),
    ("Pauwa Bhanjyang", "viewpoints", "Panchthar", "Koshi", "Pauwa", 27.12, 87.75, "Pass viewpoint of Phidim, Panchthar."),
    ("Loha Kil", "viewpoints", "Panchthar", "Koshi", "Phidim", 27.14, 87.72, "Sunrise viewpoint on the Phidim-Phalgunanda boundary."),
    ("Sumhatlung", "heritage", "Panchthar", "Koshi", "Hilihang", 27.19, 87.69, "Historic cultural site of Hilihang, Panchthar."),
    # ---------- Ilam ----------
    ("Antu Danda", "viewpoints", "Ilam", "Koshi", "Shree Antu", 26.93, 87.99, "Famous sunrise viewpoint of Shree Antu, Ilam."),
    ("Chhintapu", "villages", "Ilam", "Koshi", "Chhintapu", 26.98, 87.99, "Village of Sandakpur Rural Municipality, Ilam."),
    ("Gajur Mukhi", "temples", "Ilam", "Koshi", "Gajurmukhi", 26.93, 87.96, "Sacred stone-tunnel temple of goddess Gajur Mukhi, Ilam."),
    ("Sanu Pathibhara", "temples", "Ilam", "Koshi", "Sanu Pathibhara", 26.92, 87.95, "Small Pathibhara temple of Ilam district."),
    ("Mai Beni Dham", "pilgrimage", "Ilam", "Koshi", "Mai Beni", 26.85, 87.90, "Sacred confluence of the Mai and Jogmai rivers."),
    ("Siddhi Thumka", "temples", "Ilam", "Koshi", "Siddhithumka", 26.95, 87.97, "Hilltop temple of Ilam district."),
    ("Pashupatinagar", "cities", "Ilam", "Koshi", "Pashupatinagar", 26.96, 88.12, "Border town of Suryodaya Municipality, Ilam."),
    ("Panchakanya Temple Ilam", "temples", "Ilam", "Koshi", "Panchakanya", 26.90, 88.00, "Five-goddess temple of Suryodaya Ward 13, Ilam."),
    ("Panitar Tea Garden", "tea-coffee", "Ilam", "Koshi", "Panitar", 26.92, 87.95, "Tea estate and picnic area of Deumai, Ilam."),
    ("Mangmanglung", "pilgrimage", "Ilam", "Koshi", "Mangmanglung", 26.98, 87.93, "Kirat sacred site of Mangsebung, Ilam."),
    ("Larumba Mangsebung", "pilgrimage", "Ilam", "Koshi", "Mangsebung", 26.99, 87.92, "Kirat religious centre of Mangsebung, Ilam."),
    ("Meghma Gumba", "buddhist-sites", "Ilam", "Koshi", "Meghma", 26.95, 87.99, "Buddhist monastery of Maijogmai, Ilam."),
    ("Thumkerani Viewpoint", "viewpoints", "Ilam", "Koshi", "Naya Bazar", 26.90, 87.91, "New viewpoint near Naya Bazar with views to Darjeeling."),
    ("Singhdevi Temple", "temples", "Ilam", "Koshi", "Singhdevi", 26.88, 87.92, "Temple of goddess Singhdevi in Maijogmai, Ilam."),
    ("Tare Bhir", "viewpoints", "Ilam", "Koshi", "Tare Bhir", 26.87, 87.95, "Cliff viewpoint of Maijogmai, Ilam."),
    ("Deumai Pokhari", "lakes", "Ilam", "Koshi", "Deumai", 26.90, 87.93, "Lake of Deumai Municipality, Ilam."),
    ("Kuibhir", "forests", "Ilam", "Koshi", "Kuibhir", 26.91, 87.94, "Rhododendron cliff and rock-climbing area of Deumai, Ilam."),
    ("Ratna Tunnel", "heritage", "Ilam", "Koshi", "Ratna", 26.92, 87.94, "Historic tunnel of Deumai Municipality, Ilam."),
    ("Guphathumki", "caves", "Ilam", "Koshi", "Guphathumki", 26.93, 87.95, "Cave area of Deumai, Ilam."),
    ("Sohana Devi Temple", "temples", "Ilam", "Koshi", "Sohana", 26.93, 87.95, "Goddess temple of Deumai Ward 2, Ilam."),
    ("Todke Jharana", "waterfalls", "Ilam", "Koshi", "Todke", 26.99, 87.97, "Waterfall of Sandakpur Rural Municipality, Ilam."),
    # ---------- Jhapa ----------
    ("Satakshi Dham", "pilgrimage", "Jhapa", "Koshi", "Satakshi", 26.62, 87.90, "Major pilgrimage complex of Shivasatakshi with Devi and Mahadev temples."),
    ("Kankai Dham Kotihom", "pilgrimage", "Jhapa", "Koshi", "Kankai", 26.63, 87.87, "Sacred Kankai river ghat and temple site of Kankai Municipality."),
    ("Domukha", "pilgrimage", "Jhapa", "Koshi", "Domukha", 26.64, 87.88, "Kankai river confluence religious site of Shivasatakshi."),
    ("Chillagadh", "heritage", "Jhapa", "Koshi", "Chillagadh", 26.62, 87.91, "Historic cultural area of Shivasatakshi, Jhapa."),
    ("Dhanuskoti Dham", "pilgrimage", "Jhapa", "Koshi", "Dhanuskoti", 26.63, 87.86, "Religious site on the Kankai river, Jhapa."),
    ("Jamunkhadi Simsar", "lakes", "Jhapa", "Koshi", "Jamunkhadi", 26.63, 87.85, "Wetland reserve with boating and wildlife of Kankai, Jhapa."),
    ("Kechana Lake", "lakes", "Jhapa", "Koshi", "Kechana", 26.35, 88.05, "Lake at Nepal's southernmost point, Kachankawal, Jhapa."),
    ("Char Koshe Jhadi", "forests", "Jhapa", "Koshi", "Char Koshe", 26.40, 88.00, "Forest belt of Kachankawal, Jhapa."),
    ("Sukhani Martyrs' Park", "heritage", "Jhapa", "Koshi", "Sukhani", 26.65, 87.93, "Memorial park of the martyrs of Arjundhara, Jhapa."),
    ("Biratpokhar", "lakes", "Jhapa", "Koshi", "Birtamod", 26.62, 87.62, "Seven-pond historical landscape of Birtamod, Jhapa."),
    ("Timai Suspension Bridge", "heritage", "Jhapa", "Koshi", "Kolbung", 26.70, 87.75, "477 m suspension bridge over the Timai river, Buddhashanti."),
    ("Dharagola View Tower", "viewpoints", "Jhapa", "Koshi", "Dharagola", 26.69, 87.74, "View tower of Buddhashanti Ward 7, Jhapa."),
    ("Selfie Danda", "viewpoints", "Jhapa", "Koshi", "Kankai", 26.66, 87.84, "Hill viewpoint of Kankai Municipality, Jhapa."),
    # ---------- Morang ----------
    ("Raja Rani Lake", "lakes", "Morang", "Koshi", "Raja Rani", 26.78, 87.47, "Scenic forest lake of Pathari-Shanishchare, Morang."),
    ("Kane Pokhari", "lakes", "Morang", "Koshi", "Kanepokhari", 26.62, 87.52, "Historic highway-side wetland of Kanepokhari, Morang."),
    ("Kalikoshi Simsar", "lakes", "Morang", "Koshi", "Kalikoshi", 26.60, 87.55, "Wetland complex of Kanepokhari/Jahada, Morang."),
    ("Sunwarshi Pokhari", "lakes", "Morang", "Koshi", "Sunwarshi", 26.58, 87.50, "Sacred pond of Sunwarshi Maharaj Than, Morang."),
    ("Beteni Simsar", "lakes", "Morang", "Koshi", "Urlabari", 26.64, 87.55, "Wetland of Urlabari Municipality, Morang."),
    ("Lampate Simsar", "lakes", "Morang", "Koshi", "Urlabari", 26.65, 87.56, "Wetland of Urlabari Municipality, Morang."),
    ("Biratnagar Jute Mills", "heritage", "Morang", "Koshi", "Biratnagar", 26.47, 87.28, "Historic first large-scale industrial mill of Nepal."),
    ("Dhanpalgadhi", "heritage", "Morang", "Koshi", "Dhanpalthan", 26.58, 87.48, "Historic fort site of Dhanpalthan, Morang."),
    ("Letang Chure Forest", "forests", "Morang", "Koshi", "Letang", 26.85, 87.43, "Chure/Mahabharat foothill forest of Letang, Morang."),
    ("Budha Thakur", "temples", "Morang", "Koshi", "Urlabari", 26.66, 87.53, "Religious site of Urlabari Municipality, Morang."),
    ("Gidhaniya Park", "parks-gardens", "Morang", "Koshi", "Gramthan", 26.57, 87.46, "Park of Gramthan Ward 5, Morang."),
    ("Miklajung Danda", "viewpoints", "Morang", "Koshi", "Miklajung", 26.90, 87.45, "Peak viewpoint of Miklajung Rural Municipality, Morang."),
    ("Chuli Pokhari", "lakes", "Morang", "Koshi", "Chuli Pokhari", 26.92, 87.47, "Sacred lake of Miklajung, Morang."),
    ("Miklubeteni", "heritage", "Morang", "Koshi", "Miklajung", 26.91, 87.46, "Religious site of Miklajung Rural Municipality."),
    ("Neselung Danda", "viewpoints", "Morang", "Koshi", "Neselung", 26.93, 87.48, "Scenic ridge of Miklajung, Morang."),
    ("Devisthan Simsar", "lakes", "Morang", "Koshi", "Madhumalla", 26.90, 87.44, "Wetland of Miklajung Ward 7, Morang."),
    # ---------- Sunsari ----------
    ("Chhinnamasta Temple Barahakshetra", "temples", "Sunsari", "Koshi", "Barahakshetra", 26.87, 87.07, "Goddess temple at the Barahakshetra pilgrimage complex."),
    ("Vishnupaduka", "temples", "Sunsari", "Koshi", "Dharan", 26.81, 87.30, "Sacred Vishnu footprint temple near Dharan."),
    ("Panchakanya Natural Park", "parks-gardens", "Sunsari", "Koshi", "Dharan", 26.84, 87.31, "Forest park with Panchakanya, Pathibhara and Bindabasini temples, Dharan."),
    ("Taltalaiya", "lakes", "Sunsari", "Koshi", "Itahari", 26.68, 87.28, "Recreational ponds of Itahari Wards 2-3."),
    ("Kachana Mahadev Temple", "temples", "Sunsari", "Koshi", "Itahari", 26.67, 87.27, "Shiva temple of Itahari Ward 4 with the Siruwa festival."),
    ("Ramdhuni Temple", "temples", "Sunsari", "Koshi", "Ramdhuni", 26.63, 87.03, "Famous temple of Lord Ram in Ramdhuni Municipality."),
    ("Barju Tal", "lakes", "Sunsari", "Koshi", "Barju", 26.55, 87.05, "Large wetland lake of Barju Rural Municipality Ward 6."),
    ("Chimdi Wetland", "lakes", "Sunsari", "Koshi", "Chimdi", 26.55, 87.04, "Wetland section of the Barju lake complex."),
    ("Amaha Pokhari", "lakes", "Sunsari", "Koshi", "Barahakshetra", 26.60, 87.10, "Sacred pond of Barahakshetra Ward 5."),
    ("Tegne Pokhari", "lakes", "Sunsari", "Koshi", "Barahakshetra", 26.61, 87.09, "Pond of Barahakshetra Ward 3."),
    ("Kavyabatika", "parks-gardens", "Sunsari", "Koshi", "Itahari", 26.66, 87.28, "Artistic recreation park of Itahari Ward 5."),
    # ---------- Udayapur ----------
    ("Chaudandigadhi Fort", "heritage", "Udayapur", "Koshi", "Chaudandigadhi", 26.90, 86.75, "Historic 1773 fort and palace with panoramic Himalayan views."),
    ("Basaha Than Shivalaya", "temples", "Udayapur", "Koshi", "Basaha", 26.92, 86.72, "Shiva temple of Chaudandigadhi Ward 4."),
    ("Shivalaya Temple Belha", "temples", "Udayapur", "Koshi", "Belha", 26.91, 86.73, "Shiva temple of Chaudandigadhi Ward 5."),
    ("Pushpalal Chowk Park", "parks-gardens", "Udayapur", "Koshi", "Chaudandigadhi", 26.93, 86.74, "Recreation park of Chaudandigadhi Ward 6."),
    ("Lingeshwar Shivalaya", "temples", "Udayapur", "Koshi", "Chaudandigadhi", 26.93, 86.74, "Shiva shrine of Chaudandigadhi Ward 6."),
    ("Kanya Aulshree Gumba", "buddhist-sites", "Udayapur", "Koshi", "Chaudandigadhi", 26.94, 86.73, "Buddhist monastery of Chaudandigadhi Ward 7."),
    ("Dwardani Devi Sthan", "temples", "Udayapur", "Koshi", "Chaudandigadhi", 26.94, 86.73, "Goddess site of Chaudandigadhi Ward 7."),
    ("Mini Apraha Waterfall", "waterfalls", "Udayapur", "Koshi", "Chaudandigadhi", 26.95, 86.72, "Waterfall of Chaudandigadhi Ward 8."),
    ("Thanpokhari Than", "temples", "Udayapur", "Koshi", "Chaudandigadhi", 26.93, 86.75, "Sacred pond-temple of Chaudandigadhi Ward 9."),
    ("Katari Bazaar", "cities", "Udayapur", "Koshi", "Katari", 26.99, 86.32, "Historic market town of Katari Municipality on the Tawa river."),
    ("Tawa River", "rivers", "Udayapur", "Koshi", "Katari", 26.95, 86.35, "River of Katari valley, Udayapur."),
    ("Triyuga River", "rivers", "Udayapur", "Koshi", "Triyuga", 26.79, 86.70, "River flowing through Gaighat and Triyuga Municipality."),
    # ---------- Dhankuta / Terhathum ----------
    ("Namaste Jharna", "waterfalls", "Dhankuta", "Koshi", "Namaste", 26.98, 87.34, "Famous waterfall 8 km from Bhedetar, Dhankuta."),
    ("Dhwaje Danda", "viewpoints", "Dhankuta", "Koshi", "Dhwaje", 26.95, 87.40, "Sunrise viewpoint with Tamor river views, Dhankuta."),
    ("Hile Bazaar", "cities", "Dhankuta", "Koshi", "Hile", 26.98, 87.32, "Hill bazaar of Dhankuta Municipality Ward 1."),
    ("Mulghat", "pilgrimage", "Dhankuta", "Koshi", "Mulghat", 26.90, 87.35, "Sacred ghat on the Arun river near Dhankuta."),
    ("Marg Pokhari", "lakes", "Terhathum", "Koshi", "Marg Pokhari", 27.08, 87.58, "Lake of Laligurans Ward 3, Terhathum."),
    ("Panchakanya Pokhari", "lakes", "Terhathum", "Koshi", "Panchakanya", 27.06, 87.55, "Sacred pond cluster of Chhathar/Terhathum."),
    ("Myanglung Bazaar", "cities", "Terhathum", "Koshi", "Myanglung", 27.10, 87.53, "District headquarters bazaar of Terhathum."),
    ("Singha Bahini Temple", "temples", "Terhathum", "Koshi", "Myanglung", 27.10, 87.52, "Temple near Myanglung, Terhathum."),
    ("Sankranti Bazaar", "cities", "Terhathum", "Koshi", "Sankranti", 27.05, 87.55, "Market centre of Aathrai Rural Municipality Ward 1."),
    ("Khamlalung", "villages", "Terhathum", "Koshi", "Khamlalung", 27.08, 87.57, "Limbu village of Aathrai, Terhathum."),
    ("Pattek Danda", "viewpoints", "Terhathum", "Koshi", "Pattek", 27.14, 87.62, "Ridge viewpoint of Laligurans, Terhathum."),
    ("Hyatrung Jharana", "waterfalls", "Terhathum", "Koshi", "Hyatrung", 27.12, 87.60, "Waterfall of the Tinjure-Milke-Jaljale area."),
]

created = 0
skipped = 0
for name, cslug, dist, prov, city, lat, lon, short in PLACES:
    slug = name.lower().replace(" ", "-").replace("(", "").replace(")", "").replace(",", "").replace("'", "").replace("&", "and").replace("--", "-")
    if Destination.objects.filter(slug=slug).exists():
        skipped += 1
        continue
    cat = cats.get(cslug) or cats.get("attraction")
    Destination.objects.create(
        name=name, slug=slug, category=cat, district=dist, province=prov,
        city=city, city_english=city, latitude=lat, longitude=lon,
        short_description=short, description=short, country="Nepal",
        status="approved", is_active=True, source="koshi-province-round", views_count=0,
    )
    created += 1

print(f"created: {created} | skipped (already exist): {skipped}")
