"""
Nepal Administrative Boundaries & Local Governance Dataset
Contains definitions for all 7 Provinces, 77 Districts, and Major Municipalities.
"""

NEPAL_PROVINCES = [
    "Koshi",
    "Madhesh",
    "Bagmati",
    "Gandaki",
    "Lumbini",
    "Karnali",
    "Sudurpashchim"
]

NEPAL_DISTRICTS = {
    "Koshi": ["Bhojpur", "Dhankuta", "Ilam", "Jhapa", "Khotang", "Morang", "Okhaldhunga", "Panchthar", "Sankhuwasabha", "Solukhumbu", "Sunsari", "Taplejung", "Terhathum", "Udayapur"],
    "Madhesh": ["Bara", "Dhanusha", "Mahottari", "Parsa", "Rautahat", "Saptari", "Sarlahi", "Siraha"],
    "Bagmati": ["Bhaktapur", "Chitwan", "Dhading", "Dolakha", "Kathmandu", "Kavrepalanchok", "Lalitpur", "Makwanpur", "Nuwakot", "Ramechhap", "Rasuwa", "Sindhuli", "Sindhupalchok"],
    "Gandaki": ["Baglung", "Gorkha", "Kaski", "Lamjung", "Manang", "Mustang", "Myagdi", "Nawalpur", "Parbat", "Syangja", "Tanahun"],
    "Lumbini": ["Arghakhanchi", "Banke", "Bardiya", "Dang", "Gulmi", "Kapilvastu", "Parasi", "Palpa", "Pyuthan", "Rolpa", "Rukum East", "Rupandehi"],
    "Karnali": ["Dailekh", "Dolpa", "Humla", "Jajarkot", "Jumla", "Kalikot", "Mugu", "Rukum West", "Salyan", "Surkhet"],
    "Sudurpashchim": ["Achham", "Baitadi", "Bajhang", "Bajura", "Dadeldhura", "Darchula", "Doti", "Kailali", "Kanchanpur"]
}

MUNICIPALITY_COORDINATES = {
    # Kathmandu Valley
    "kathmandu metropolitan city": {"lat": 27.7172, "lng": 85.3240, "alt": 1400, "district": "Kathmandu", "province": "Bagmati"},
    "lalitpur metropolitan city": {"lat": 27.6644, "lng": 85.3188, "alt": 1400, "district": "Lalitpur", "province": "Bagmati"},
    "bhaktapur municipality": {"lat": 27.6710, "lng": 85.4298, "alt": 1401, "district": "Bhaktapur", "province": "Bagmati"},
    "kirtipur municipality": {"lat": 27.6797, "lng": 85.2754, "alt": 1420, "district": "Kathmandu", "province": "Bagmati"},
    "budhanilkantha municipality": {"lat": 27.7788, "lng": 85.3606, "alt": 1480, "district": "Kathmandu", "province": "Bagmati"},
    "chandragiri municipality": {"lat": 27.6933, "lng": 85.2155, "alt": 1550, "district": "Kathmandu", "province": "Bagmati"},
    "changunarayan municipality": {"lat": 27.7126, "lng": 85.4282, "alt": 1540, "district": "Bhaktapur", "province": "Bagmati"},

    # Pokhara & Gandaki
    "pokhara metropolitan city": {"lat": 28.2096, "lng": 83.9856, "alt": 822, "district": "Kaski", "province": "Gandaki"},
    "annapurna rural municipality": {"lat": 28.3744, "lng": 83.8089, "alt": 2012, "district": "Kaski", "province": "Gandaki"},
    "bandipur rural municipality": {"lat": 27.9333, "lng": 84.4167, "alt": 1030, "district": "Tanahun", "province": "Gandaki"},
    "gharapjhong rural municipality": {"lat": 28.7833, "lng": 83.7333, "alt": 2743, "district": "Mustang", "province": "Gandaki"},
    "baragung muktikshetra": {"lat": 28.8167, "lng": 83.8667, "alt": 3800, "district": "Mustang", "province": "Gandaki"},
    "lo manthang rural municipality": {"lat": 29.1822, "lng": 83.9567, "alt": 3840, "district": "Mustang", "province": "Gandaki"},
    "manang disyang rural municipality": {"lat": 28.6667, "lng": 84.0167, "alt": 3519, "district": "Manang", "province": "Gandaki"},
    "gorkha municipality": {"lat": 28.0000, "lng": 84.6333, "alt": 1150, "district": "Gorkha", "province": "Gandaki"},

    # Chitwan & Lumbini
    "bharatpur metropolitan city": {"lat": 27.6833, "lng": 84.4333, "alt": 208, "district": "Chitwan", "province": "Bagmati"},
    "ratnanagar municipality": {"lat": 27.6167, "lng": 84.5167, "alt": 150, "district": "Chitwan", "province": "Bagmati"},
    "lumbini sanskritik municipality": {"lat": 27.4699, "lng": 83.2755, "alt": 105, "district": "Rupandehi", "province": "Lumbini"},
    "butwal sub-metropolitan city": {"lat": 27.7000, "lng": 83.4500, "alt": 210, "district": "Rupandehi", "province": "Lumbini"},
    "tansen municipality": {"lat": 27.8667, "lng": 83.5500, "alt": 1350, "district": "Palpa", "province": "Lumbini"},

    # Everest & Koshi
    "khumbu pasanglhamu rural municipality": {"lat": 27.8056, "lng": 86.7111, "alt": 3440, "district": "Solukhumbu", "province": "Koshi"},
    "solududhkunda municipality": {"lat": 27.5000, "lng": 86.5833, "alt": 2162, "district": "Solukhumbu", "province": "Koshi"},
    "ilam municipality": {"lat": 26.9117, "lng": 87.9261, "alt": 1208, "district": "Ilam", "province": "Koshi"},
    "suryodaya municipality": {"lat": 26.8833, "lng": 88.0667, "alt": 1600, "district": "Ilam", "province": "Koshi"},

    # Karnali & Far West
    "chhayanath rara municipality": {"lat": 29.5333, "lng": 82.0833, "alt": 2990, "district": "Mugu", "province": "Karnali"},
    "shey phoksundo rural municipality": {"lat": 29.2167, "lng": 82.9500, "alt": 3611, "district": "Dolpa", "province": "Karnali"},
    "birendranagar municipality": {"lat": 28.6000, "lng": 81.6333, "alt": 665, "district": "Surkhet", "province": "Karnali"},
    "dhangadhi sub-metropolitan city": {"lat": 28.6833, "lng": 80.6000, "alt": 182, "district": "Kailali", "province": "Sudurpashchim"},
    "bhimdatta municipality": {"lat": 28.9667, "lng": 80.1833, "alt": 198, "district": "Kanchanpur", "province": "Sudurpashchim"},

    # Madhesh
    "janakpurdham sub-metropolitan": {"lat": 26.7271, "lng": 85.9242, "alt": 74, "district": "Dhanusha", "province": "Madhesh"},
    "birgunj metropolitan city": {"lat": 27.0167, "lng": 84.8833, "alt": 91, "district": "Parsa", "province": "Madhesh"},
}
