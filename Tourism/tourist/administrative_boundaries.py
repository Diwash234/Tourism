"""
administrative_boundaries.py

Comprehensive administrative dataset for Nepal:
- 7 Provinces (Koshi, Madhesh, Bagmati, Gandaki, Lumbini, Karnali, Sudurpashchim)
- 77 Districts
- Key Municipalities, Metropolises, Sub-Metropolises, and Rural Municipalities (Gaunpalika)
- Center coordinates (Latitude, Longitude) and average elevations
"""

NEPAL_PROVINCES = [
    {"id": 1, "name": "Koshi", "capital": "Biratnagar", "districts_count": 14},
    {"id": 2, "name": "Madhesh", "capital": "Janakpur", "districts_count": 8},
    {"id": 3, "name": "Bagmati", "capital": "Hetauda", "districts_count": 13},
    {"id": 4, "name": "Gandaki", "capital": "Pokhara", "districts_count": 11},
    {"id": 5, "name": "Lumbini", "capital": "Deukhuri (Dang)", "districts_count": 12},
    {"id": 6, "name": "Karnali", "capital": "Birendranagar (Surkhet)", "districts_count": 10},
    {"id": 7, "name": "Sudurpashchim", "capital": "Godawari (Kailali)", "districts_count": 9},
]

NEPAL_DISTRICTS_DATA = {
    # Bagmati Province
    "Kathmandu": {"province": "Bagmati", "lat": 27.7172, "lng": 85.3240, "altitude": 1400, "type": "Metropolitan"},
    "Bhaktapur": {"province": "Bagmati", "lat": 27.6710, "lng": 85.4298, "altitude": 1401, "type": "Municipality"},
    "Lalitpur": {"province": "Bagmati", "lat": 27.6644, "lng": 85.3188, "altitude": 1400, "type": "Metropolitan"},
    "Chitwan": {"province": "Bagmati", "lat": 27.5341, "lng": 84.4530, "altitude": 208, "type": "Metropolitan/Sub-tropical"},
    "Rasuwa": {"province": "Bagmati", "lat": 28.1167, "lng": 85.3000, "altitude": 2000, "type": "Himalayan/Langtang"},
    "Kavrepalanchok": {"province": "Bagmati", "lat": 27.5333, "lng": 85.5500, "altitude": 1500, "type": "Hill/Dhulikhel"},
    "Sindhupalchok": {"province": "Bagmati", "lat": 27.9500, "lng": 85.6833, "altitude": 1800, "type": "Himalayan/Helambu"},
    "Makwanpur": {"province": "Bagmati", "lat": 27.4167, "lng": 85.0333, "altitude": 450, "type": "Hill/Hetauda"},
    "Nuwakot": {"province": "Bagmati", "lat": 27.9167, "lng": 85.1667, "altitude": 1000, "type": "Historical/Durbar"},
    "Dhading": {"province": "Bagmati", "lat": 27.8667, "lng": 84.9000, "altitude": 1200, "type": "Hill/Prithvi Highway"},

    # Gandaki Province
    "Kaski": {"province": "Gandaki", "lat": 28.2096, "lng": 83.9856, "altitude": 822, "type": "Metropolitan/Annapurna Hub"},
    "Mustang": {"province": "Gandaki", "lat": 28.9833, "lng": 83.8667, "altitude": 3800, "type": "Trans-Himalayan/Lo Manthang"},
    "Manang": {"province": "Gandaki", "lat": 28.6667, "lng": 84.0167, "altitude": 3519, "type": "High Altitude/Tilicho"},
    "Tanahun": {"province": "Gandaki", "lat": 27.9333, "lng": 84.4167, "altitude": 1030, "type": "Heritage/Bandipur"},
    "Gorkha": {"province": "Gandaki", "lat": 28.0000, "lng": 84.6333, "altitude": 1100, "type": "Historic/Manaslu"},
    "Lamjung": {"province": "Gandaki", "lat": 28.2333, "lng": 84.3833, "altitude": 1300, "type": "Gurung Heritage/Besisahar"},
    "Myagdi": {"province": "Gandaki", "lat": 28.3500, "lng": 83.5667, "altitude": 1750, "type": "Trekking/Poon Hill/Beni"},
    "Parbat": {"province": "Gandaki", "lat": 28.2167, "lng": 83.6833, "altitude": 1200, "type": "Kusma Bungee & Bridge"},
    "Syangja": {"province": "Gandaki", "lat": 28.1000, "lng": 83.8667, "altitude": 1080, "type": "Hill/Sirkot Paragliding"},
    "Baglung": {"province": "Gandaki", "lat": 28.2667, "lng": 83.6000, "altitude": 1020, "type": "Dhorpatan/Suspension Bridge"},

    # Koshi Province
    "Solukhumbu": {"province": "Koshi", "lat": 27.8056, "lng": 86.7111, "altitude": 3440, "type": "Everest Region/Khumbu"},
    "Ilam": {"province": "Koshi", "lat": 26.9117, "lng": 87.9261, "altitude": 1208, "type": "Tea Gardens/Kanyam"},
    "Jhapa": {"province": "Koshi", "lat": 26.6333, "lng": 87.9833, "altitude": 120, "type": "Eastern Plains/Kakarbhitta"},
    "Morang": {"province": "Koshi", "lat": 26.4525, "lng": 87.2718, "altitude": 80, "type": "Industrial/Biratnagar"},
    "Sunsari": {"province": "Koshi", "lat": 26.8167, "lng": 87.2833, "altitude": 150, "type": "Dharan/Bhedetar/Koshi Tappu"},
    "Taplejung": {"province": "Koshi", "lat": 27.3500, "lng": 87.6667, "altitude": 1820, "type": "Kanchenjunga/Pathibhara"},
    "Sankhuwasabha": {"province": "Koshi", "lat": 27.6000, "lng": 87.2000, "altitude": 1500, "type": "Makalu Barun Valley"},

    # Lumbini Province
    "Rupandehi": {"province": "Lumbini", "lat": 27.4699, "lng": 83.2755, "altitude": 105, "type": "Lumbini Birthplace/Butwal"},
    "Palpa": {"province": "Lumbini", "lat": 27.8667, "lng": 83.5500, "altitude": 1350, "type": "Tansen Hill Station/Rani Mahal"},
    "Kapilvastu": {"province": "Lumbini", "lat": 27.5500, "lng": 83.0500, "altitude": 100, "type": "Ancient Kingdom of Shakya"},
    "Banke": {"province": "Lumbini", "lat": 28.0500, "lng": 81.6167, "altitude": 150, "type": "Nepalgunj Gateway"},
    "Bardiya": {"province": "Lumbini", "lat": 28.3000, "lng": 81.3500, "altitude": 150, "type": "Bardiya National Park"},

    # Karnali Province
    "Mugu": {"province": "Karnali", "lat": 29.5333, "lng": 82.0833, "altitude": 2990, "type": "Rara Lake"},
    "Dolpa": {"province": "Karnali", "lat": 29.2167, "lng": 82.9500, "altitude": 3611, "type": "Shey Phoksundo Lake"},
    "Jumla": {"province": "Karnali", "lat": 29.2747, "lng": 82.1838, "altitude": 2370, "type": "Apple Capital/Jumla Rice"},
    "Surkhet": {"province": "Karnali", "lat": 28.6000, "lng": 81.6333, "altitude": 720, "type": "Birendranagar/Kakrebihar"},

    # Madhesh Province
    "Dhanusha": {"province": "Madhesh", "lat": 26.7271, "lng": 85.9242, "altitude": 74, "type": "Janakpurdham/Mithila"},
    "Parsa": {"province": "Madhesh", "lat": 27.0167, "lng": 84.8667, "altitude": 90, "type": "Birgunj Border/Parsa Wildlife"},

    # Sudurpashchim Province
    "Kanchanpur": {"province": "Sudurpashchim", "lat": 28.9667, "lng": 80.1833, "altitude": 198, "type": "Shuklaphanta National Park"},
    "Kailali": {"province": "Sudurpashchim", "lat": 28.7167, "lng": 80.6000, "altitude": 180, "type": "Dhangadhi/Tikapur"},
    "Doti": {"province": "Sudurpashchim", "lat": 29.2667, "lng": 80.9833, "altitude": 1300, "type": "Khaptad National Park"},
}


def get_district_info(district_name: str) -> dict:
    for name, data in NEPAL_DISTRICTS_DATA.items():
        if name.lower() == district_name.lower() or name.lower() in district_name.lower():
            return {"district": name, **data}
    return None
