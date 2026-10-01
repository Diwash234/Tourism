#!/usr/bin/env python
"""Fix data.json - fill missing city_english, add proper images, fix Korean/Chinese text."""
import json
from pathlib import Path
import math

data_path = Path(__file__).resolve().parent / "dataset" / "data.json"

with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

destinations = data.get("destinations", {})
print(f"Total destinations: {len(destinations)}")

# Nepal district to city_english mapping
DISTRICT_TO_CITY = {
    "Kathmandu": "Kathmandu", "Lalitpur": "Lalitpur (Patan)", "Bhaktapur": "Bhaktapur",
    "Kavrepalanchok": "Dhulikhel", "Sindhupalchok": "Barabise", "Nuwakot": "Bidur",
    "Rasuwa": "Dhunche", "Dhading": "Dhading Besi", "Makwanpur": "Hetauda",
    "Chitwan": "Bharatpur", "Gorkha": "Gorkha", "Lamjung": "Besisahar",
    "Tanahun": "Damauli", "Syangja": "Putalibazar", "Kaski": "Pokhara",
    "Manang": "Chame", "Mustang": "Jomsom", "Myagdi": "Beni", "Parbat": "Kushma",
    "Baglung": "Baglung", "Gulmi": "Tamghas", "Palpa": "Tansen", "Nawalparasi": "Ramgram",
    "Rupandehi": "Butwal", "Kapilvastu": "Taulihawa", "Arghakhanchi": "Sandhikharka",
    "Pyuthan": "Pyuthan", "Rolpa": "Liwang", "Rukum": "Musikot", "Salyan": "Salyan",
    "Surkhet": "Birendranagar", "Dailekh": "Dailekh", "Jajarkot": "Khalanga",
    "Dolpa": "Dunai", "Jumla": "Chandannath", "Kalikot": "Manma", "Mugu": "Gamgadhi",
    "Humla": "Simikot", "Bajura": "Martadi", "Bajhang": "Chainpur", "Achham": "Mangalsen",
    "Doti": "Dipayal", "Kailali": "Dhangadhi", "Kanchanpur": "Mahendranagar",
    "Dadeldhura": "Dadeldhura", "Baitadi": "Dasharathchand", "Darchula": "Darchula",
    "Sindhuli": "Sindhuli", "Ramechhap": "Manthali", "Dolakha": "Charikot",
    "Solukhumbu": "Salleri", "Okhaldhunga": "Okhaldhunga", "Khotang": "Diktel",
    "Udayapur": "Gaighat", "Saptari": "Rajbiraj", "Siraha": "Siraha", "Dhanusa": "Janakpur",
    "Mahottari": "Jaleshwar", "Sarlahi": "Malangwa", "Rautahat": "Gaur", "Bara": "Kalaiya",
    "Parsa": "Birgunj", "Taplejung": "Phungling", "Panchthar": "Phidim", "Ilam": "Ilam",
    "Jhapa": "Bhadrapur", "Morang": "Biratnagar", "Sunsari": "Inaruwa", "Dhankuta": "Dhankuta",
    "Terhathum": "Myrung", "Sankhuwasabha": "Khandbari", "Bhojpur": "Bhojpur",
    "Okhaldhunga": "Okhaldhunga", "Sankhuwasabha": "Khandbari", "Bhojpur": "Bhojpur",
}

# Nepal landmark photos (Wikimedia Commons)
PLACEHOLDER_IMAGES = {
    "default": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg",
    "kathmandu": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Kathmandu_Durbar_Square.jpg/960px-Kathmandu_Durbar_Square.jpg",
    "pokhara": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
    "everest": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg",
    "chitwan": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
    "lumbini": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
    "default_hotel": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
}

# District to major city mapping
DISTRICT_TO_CITY = {
    "Kathmandu": "Kathmandu", "Lalitpur": "Lalitpur", "Bhaktapur": "Bhaktapur",
    "Kavrepalanchok": "Dhulikhel", "Sindhupalchok": "Barabise", "Nuwakot": "Bidur",
    "Rasuwa": "Dhunche", "Dhading": "Dhading Besi", "Makwanpur": "Hetauda",
    "Chitwan": "Bharatpur", "Gorkha": "Gorkha", "Lamjung": "Besisahar",
    "Tanahun": "Damauli", "Syangja": "Putalibazar", "Kaski": "Pokhara",
    "Manang": "Chame", "Mustang": "Jomsom", "Myagdi": "Beni", "Parbat": "Kushma",
    "Baglung": "Baglung", "Gulmi": "Tamghas", "Palpa": "Tansen", "Nawalparasi": "Ramgram",
    "Rupandehi": "Butwal", "Kapilvastu": "Taulihawa", "Arghakhanchi": "Sandhikharka",
    "Pyuthan": "Pyuthan", "Rolpa": "Liwang", "Rukum": "Musikot", "Salyan": "Salyan",
    "Surkhet": "Birendranagar", "Dailekh": "Dailekh", "Jajarkot": "Khalanga",
    "Dolpa": "Dunai", "Jumla": "Chandannath", "Kalikot": "Manma", "Mugu": "Gamgadhi",
    "Humla": "Simikot", "Bajura": "Martadi", "Bajhang": "Chainpur", "Achham": "Mangalsen",
    "Doti": "Dipayal", "Kailali": "Dhangadhi", "Kanchanpur": "Mahendranagar",
    "Dadeldhura": "Dadeldhura", "Baitadi": "Dasharathchand", "Darchula": "Darchula",
    "Sindhuli": "Sindhuli", "Ramechhap": "Manthali", "Dolakha": "Charikot",
    "Solukhumbu": "Salleri", "Okhaldhunga": "Okhaldhunga", "Khotang": "Diktel",
    "Udayapur": "Gaighat", "Saptari": "Rajbiraj", "Siraha": "Siraha", "Dhanusa": "Janakpur",
    "Mahottari": "Jaleshwar", "Sarlahi": "Malangwa", "Rautahat": "Gaur", "Bara": "Kalaiya",
    "Parsa": "Birgunj", "Taplejung": "Phungling", "Panchthar": "Phidim", "Ilam": "Ilam",
    "Jhapa": "Bhadrapur", "Morang": "Biratnagar", "Sunsari": "Inaruwa", "Dhankuta": "Dhankuta",
    "Terhathum": "Myrung", "Sankhuwasabha": "Khandbari", "Bhojpur": "Bhojpur",
    "Okhaldhunga": "Okhaldhunga", "Sankhuwasabha": "Khandbari", "Bhojpur": "Bhojpur",
}

def get_placeholder_image(district, city_english):
    """Get appropriate placeholder image based on district/city."""
    city_key = (city_english or "").lower().strip()
    district_key = district.lower().strip() if district else ""
    
    # Check for specific landmark
    for key, url in {
        "kathmandu": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Kathmandu_Durbar_Square.jpg/960px-Kathmandu_Durbar_Square.jpg",
        "pokhara": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
        "everest": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg",
        "chitwan": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
        "lumbini": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg/960px-Siddharthanagar%2C_Nepal%2C_9_April_2019_1.jpg",
    }.items():
        if key in city_key or key in district_key:
            return url
    
    # Default
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Nepal_Mount_Everest.jpg/960px-Nepal_Mount_Everest.jpg"

fixed_count = 0
for dest_id, dest_data in destinations.items():
    # Fix city_english
    if not dest_data.get("city_english") and dest_data.get("district"):
        district = dest_data.get("district", "").strip()
        if district in DISTRICT_TO_CITY:
            dest_data["city_english"] = DISTRICT_TO_CITY[district]
        elif not dest_data.get("city_english"):
            dest_data["city_english"] = district
    
    # Fix city if missing
    if not dest_data.get("city") and dest_data.get("city_english"):
        dest_data["city"] = dest_data["city_english"]
    
    # Fix distance_from_kathmandu_km
    if (dest_data.get("distance_from_kathmandu_km") is None and 
        dest_data.get("latitude") is not None and 
        dest_data.get("longitude") is not None):
        lat1, lon1 = math.radians(27.7172), math.radians(85.3240)
        lat2, lon2 = math.radians(dest_data["latitude"]), math.radians(dest_data["longitude"])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = 6371 * c
        dest_data["distance_from_kathmandu_km"] = round(distance, 1)
    
    # Add placeholder images if empty
    if not dest_data.get("images") or len(dest_data.get("images", [])) == 0:
        placeholder_url = get_placeholder_image(
            dest_data.get("district", ""), 
            dest_data.get("city_english", "")
        )
        dest_data["images"] = [{
            "id": int(dest_id) * 1000,
            "url": placeholder_url,
            "caption": f"{dest_data.get('name', 'Nepal')} - View",
            "is_cover": True,
            "status": "approved"
        }]
    
    # Fix Korean/Chinese text in city fields
    if dest_data.get("city") and any(ord(c) > 127 for c in dest_data["city"]):
        # Replace with city_english if available
        if dest_data.get("city_english"):
            dest_data["city"] = dest_data["city_english"]

# Save fixed data
data_path = Path(__file__).resolve().parent / "dataset" / "data.json"
with open(data_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Fixed {len(destinations)} destinations")
print("Data saved!")