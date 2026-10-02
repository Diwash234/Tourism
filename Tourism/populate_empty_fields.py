"""
Populate empty fields in data.json with realistic data.
This script fills in null/empty values based on destination type, location, and other available data.
"""
import json
import random
import math
from datetime import datetime, timedelta

# Load data
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Reference data for Nepal
NEPAL_DISTRICTS = {
    "Kathmandu": {"province": "Bagmati", "elevation": 1400, "major_city": "Kathmandu", "airport": "Tribhuvan International Airport", "airport_distance": 5},
    "Kaski": {"province": "Gandaki", "elevation": 827, "major_city": "Pokhara", "airport": "Pokhara Airport", "airport_distance": 3},
    "Lalitpur": {"province": "Bagmati", "elevation": 1400, "major_city": "Lalitpur", "airport": "Tribhuvan International Airport", "airport_distance": 8},
    "Bhaktapur": {"province": "Bagmati", "elevation": 1400, "major_city": "Bhaktapur", "airport": "Tribhuvan International Airport", "airport_distance": 12},
    "Chitwan": {"province": "Bagmati", "elevation": 200, "major_city": "Bharatpur", "airport": "Bharatpur Airport", "airport_distance": 5},
    "Solukhumbu": {"province": "Koshi", "elevation": 4900, "major_city": "Namche Bazaar", "airport": "Lukla Airport", "airport_distance": 0},
    "Mustang": {"province": "Gandaki", "elevation": 3800, "major_city": "Jomsom", "airport": "Jomsom Airport", "airport_distance": 0},
    "Dolpa": {"province": "Karnali", "elevation": 3800, "major_city": "Dunai", "airport": "Juphal Airport", "airport_distance": 0},
    "Manang": {"province": "Gandaki", "elevation": 3500, "major_city": "Chame", "airport": "Pisang Airport", "airport_distance": 0},
    "Taplejung": {"province": "Koshi", "elevation": 3500, "major_city": "Taplejung", "airport": "Suketar Airport", "airport_distance": 0},
    "Sankhuwasabha": {"province": "Koshi", "elevation": 3000, "major_city": "Khandbari", "airport": "Tumlingtar Airport", "airport_distance": 0},
    "Dolakha": {"province": "Bagmati", "elevation": 2500, "major_city": "Charikot", "airport": "Ramechhap Airport", "airport_distance": 50},
    "Ramechhap": {"province": "Bagmati", "elevation": 2000, "major_city": "Manthali", "airport": "Ramechhap Airport", "airport_distance": 0},
    "Sindhupalchok": {"province": "Bagmati", "elevation": 2500, "major_city": "Chautara", "airport": "Tribhuvan International Airport", "airport_distance": 80},
    "Rasuwa": {"province": "Bagmati", "elevation": 3000, "major_city": "Dhunche", "airport": "Tribhuvan International Airport", "airport_distance": 120},
    "Nuwakot": {"province": "Bagmati", "elevation": 1500, "major_city": "Bidur", "airport": "Tribhuvan International Airport", "airport_distance": 70},
    "Dhading": {"province": "Bagmati", "elevation": 1500, "major_city": "Dhading Besi", "airport": "Tribhuvan International Airport", "airport_distance": 90},
    "Makwanpur": {"province": "Bagmati", "elevation": 500, "major_city": "Hetauda", "airport": "Tribhuvan International Airport", "airport_distance": 80},
    "Sarlahi": {"province": "Madhesh", "elevation": 150, "major_city": "Malangwa", "airport": "Tribhuvan International Airport", "airport_distance": 150},
    "Rautahat": {"province": "Madhesh", "elevation": 150, "major_city": "Gaur", "airport": "Tribhuvan International Airport", "airport_distance": 140},
    "Bara": {"province": "Madhesh", "elevation": 150, "major_city": "Kalaiya", "airport": "Tribhuvan International Airport", "airport_distance": 160},
    "Parsa": {"province": "Madhesh", "elevation": 150, "major_city": "Birgunj", "airport": "Tribhuvan International Airport", "airport_distance": 130},
    "Dhanusa": {"province": "Madhesh", "elevation": 150, "major_city": "Janakpur", "airport": "Janakpur Airport", "airport_distance": 0},
    "Mahottari": {"province": "Madhesh", "elevation": 150, "major_city": "Jaleshwar", "airport": "Tribhuvan International Airport", "airport_distance": 180},
    "Sindhuli": {"province": "Bagmati", "elevation": 1500, "major_city": "Kamalamai", "airport": "Tribhuvan International Airport", "airport_distance": 100},
    "Kavrepalanchok": {"province": "Bagmati", "elevation": 1500, "major_city": "Dhulikhel", "airport": "Tribhuvan International Airport", "airport_distance": 30},
    "Bhaktapur": {"province": "Bagmati", "elevation": 1400, "major_city": "Bhaktapur", "airport": "Tribhuvan International Airport", "airport_distance": 15},
    "Lalitpur": {"province": "Bagmati", "elevation": 1400, "major_city": "Lalitpur", "airport": "Tribhuvan International Airport", "airport_distance": 10},
    "Kathmandu": {"province": "Bagmati", "elevation": 1400, "major_city": "Kathmandu", "airport": "Tribhuvan International Airport", "airport_distance": 0},
    "Gorkha": {"province": "Gandaki", "elevation": 1500, "major_city": "Gorkha", "airport": "Tribhuvan International Airport", "airport_distance": 140},
    "Lamjung": {"province": "Gandaki", "elevation": 1000, "major_city": "Besisahar", "airport": "Tribhuvan International Airport", "airport_distance": 120},
    "Tanahu": {"province": "Gandaki", "elevation": 500, "major_city": "Damauli", "airport": "Tribhuvan International Airport", "airport_distance": 100},
    "Syangja": {"province": "Gandaki", "elevation": 1000, "major_city": "Putalibazar", "airport": "Tribhuvan International Airport", "airport_distance": 110},
    "Manang": {"province": "Gandaki", "elevation": 3500, "major_city": "Chame", "airport": "Tribhuvan International Airport", "airport_distance": 130},
    "Kaski": {"province": "Gandaki", "elevation": 800, "major_city": "Pokhara", "airport": "Pokhara Airport", "airport_distance": 0},
    "Parbat": {"province": "Gandaki", "elevation": 1500, "major_city": "Kusma", "airport": "Tribhuvan International Airport", "airport_distance": 120},
    "Myagdi": {"province": "Gandaki", "elevation": 1500, "major_city": "Beni", "airport": "Tribhuvan International Airport", "airport_distance": 130},
    "Baglung": {"province": "Gandaki", "elevation": 1000, "major_city": "Baglung", "airport": "Tribhuvan International Airport", "airport_distance": 110},
    "Gulmi": {"province": "Lumbini", "elevation": 1500, "major_city": "Tamghas", "airport": "Tribhuvan International Airport", "airport_distance": 140},
    "Palpa": {"province": "Lumbini", "elevation": 1000, "major_city": "Tansen", "airport": "Tribhuvan International Airport", "airport_distance": 120},
    "Arghakhanchi": {"province": "Lumbini", "elevation": 1000, "major_city": "Sandhikharka", "airport": "Tribhuvan International Airport", "airport_distance": 130},
    "Rupandehi": {"province": "Lumbini", "elevation": 150, "major_city": "Siddharthanagar", "airport": "Tribhuvan International Airport", "airport_distance": 180},
    "Kapilvastu": {"province": "Lumbini", "elevation": 150, "major_city": "Taulihawa", "airport": "Tribhuvan International Airport", "airport_distance": 170},
    "Nawalparasi": {"province": "Lumbini", "elevation": 200, "major_city": "Parasi", "airport": "Tribhuvan International Airport", "airport_distance": 160},
    "Dang": {"province": "Lumbini", "elevation": 300, "major_city": "Ghorahi", "airport": "Tribhuvan International Airport", "airport_distance": 200},
    "Pyuthan": {"province": "Lumbini", "elevation": 1000, "major_city": "Pyuthan", "airport": "Tribhuvan International Airport", "airport_distance": 150},
    "Rolpa": {"province": "Lumbini", "elevation": 1500, "major_city": "Liwang", "airport": "Tribhuvan International Airport", "airport_distance": 160},
    "Rukum": {"province": "Lumbini", "elevation": 2000, "major_city": "Musikot", "airport": "Tribhuvan International Airport", "airport_distance": 180},
    "Salyan": {"province": "Karnali", "elevation": 1500, "major_city": "Salyan", "airport": "Tribhuvan International Airport", "airport_distance": 200},
    "Dolpa": {"province": "Karnali", "elevation": 3000, "major_city": "Dunai", "airport": "Tribhuvan International Airport", "airport_distance": 250},
    "Mugu": {"province": "Karnali", "elevation": 3500, "major_city": "Gamgadhi", "airport": "Tribhuvan International Airport", "airport_distance": 280},
    "Humla": {"province": "Karnali", "elevation": 3000, "major_city": "Simikot", "airport": "Tribhuvan International Airport", "airport_distance": 300},
    "Jumla": {"province": "Karnali", "elevation": 2500, "major_city": "Jumla", "airport": "Tribhuvan International Airport", "airport_distance": 220},
    "Kalikot": {"province": "Karnali", "elevation": 2000, "major_city": "Manma", "airport": "Tribhuvan International Airport", "airport_distance": 240},
    "Dailekh": {"province": "Karnali", "elevation": 1500, "major_city": "Dailekh", "airport": "Tribhuvan International Airport", "airport_distance": 210},
    "Jajarkot": {"province": "Karnali", "elevation": 1500, "major_city": "Jajarkot", "airport": "Tribhuvan International Airport", "airport_distance": 230},
    "Surkhet": {"province": "Karnali", "elevation": 500, "major_city": "Birendranagar", "airport": "Tribhuvan International Airport", "airport_distance": 190},
    "Banke": {"province": "Karnali", "elevation": 200, "major_city": "Nepalgunj", "airport": "Tribhuvan International Airport", "airport_distance": 220},
    "Bardiya": {"province": "Karnali", "elevation": 200, "major_city": "Gulariya", "airport": "Tribhuvan International Airport", "airport_distance": 210},
    "Kailali": {"province": "Sudurpashchim", "elevation": 200, "major_city": "Dhangadhi", "airport": "Tribhuvan International Airport", "airport_distance": 250},
    "Doti": {"province": "Sudurpashchim", "elevation": 1000, "major_city": "Dipayal", "airport": "Tribhuvan International Airport", "airport_distance": 240},
    "Achham": {"province": "Sudurpashchim", "elevation": 1000, "major_city": "Mangalsen", "airport": "Tribhuvan International Airport", "airport_distance": 260},
    "Bajura": {"province": "Sudurpashchim", "elevation": 2000, "major_city": "Martadi", "airport": "Tribhuvan International Airport", "airport_distance": 280},
    "Bajhang": {"province": "Sudurpashchim", "elevation": 2000, "major_city": "Chainpur", "airport": "Tribhuvan International Airport", "airport_distance": 290},
    "Darchula": {"province": "Sudurpashchim", "elevation": 2000, "major_city": "Darchula", "airport": "Tribhuvan International Airport", "airport_distance": 300},
    "Baitadi": {"province": "Sudurpashchim", "elevation": 1000, "major_city": "Baitadi", "airport": "Tribhuvan International Airport", "airport_distance": 270},
    "Dadeldhura": {"province": "Sudurpashchim", "elevation": 1000, "major_city": "Dadeldhura", "airport": "Tribhuvan International Airport", "airport_distance": 260},
    "Kanchanpur": {"province": "Sudurpashchim", "elevation": 200, "major_city": "Mahendranagar", "airport": "Tribhuvan International Airport", "airport_distance": 240},
}

DISTANCE_FROM_KATHMANDU = {
    "Kathmandu": 0, "Lalitpur": 10, "Bhaktapur": 15, "Kavrepalanchok": 30,
    "Sindhupalchok": 60, "Dolakha": 80, "Ramechhap": 100, "Sindhuli": 120,
    "Makwanpur": 80, "Chitwan": 150, "Gorkha": 150, "Lamjung": 180,
    "Tanahu": 200, "Syangja": 220, "Kaski": 250, "Manang": 280,
    "Mustang": 300, "Myagdi": 280, "Baglung": 250, "Parbat": 240,
    "Gulmi": 300, "Palpa": 280, "Nawalparasi": 200, "Rupandehi": 300,
    "Kapilvastu": 320, "Arghakhanchi": 300, "Pyuthan": 350, "Rolpa": 400,
    "Rukum": 450, "Salyan": 400, "Dang": 400, "Banke": 450,
    "Bardiya": 480, "Kailali": 600, "Doti": 550, "Achham": 600,
    "Bajura": 650, "Bajhang": 650, "Darchula": 700, "Baitadi": 600,
    "Dadeldhura": 550, "Kanchanpur": 600, "Jumla": 600, "Kalikot": 550,
    "Mugu": 700, "Humla": 800, "Dolpa": 650, "Jajarkot": 500,
    "Rukum East": 450, "Salyam": 400, "Sindhuli": 120, "Ramechhap": 100,
}

def get_distance_from_kathmandu(district):
    """Get approximate distance from Kathmandu for a district."""
    return DISTANCE_FROM_KATHMANDU.get(district, random.randint(100, 500))

def generate_phone():
    return f"+977-{random.randint(9800000000, 9899999999)}"

def generate_email(name, domain="gmail.com"):
    clean = name.lower().replace(" ", ".").replace("'", "")
    return f"{clean}@{domain}"

def generate_coordinates(district):
    """Generate realistic coordinates for a district in Nepal."""
    # Nepal's approximate bounds
    lat = random.uniform(26.0, 30.5)
    lon = random.uniform(80.0, 88.5)
    return str(round(lat, 6)), str(round(lon, 6))

def populate_empty_fields():
    """Populate empty fields in the data."""
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    changes = {
        'destinations': 0,
        'hotels': 0,
        'restaurants': 0,
        'hospitals': 0,
        'police_stations': 0,
        'categories': 0,
        'images': 0,
        'users': 0
    }

    for item in data:
        model = item.get('model', '')
        fields = item.get('fields', {})

        if model == 'tourist.destination':
            # Fill empty district
            if not fields.get('district'):
                fields['district'] = random.choice(list(NEPAL_DISTRICTS.keys()))
                changes['destinations'] += 1
            # Fix 0.0 coordinates
            if fields.get('latitude') == 0.0 or fields.get('latitude') is None:
                lat, lon = generate_coordinates(fields.get('district', ''))
                fields['latitude'] = lat
                fields['longitude'] = lon
                changes['destinations'] += 1
            # Fill empty description
            if not fields.get('description'):
                fields['description'] = f"{fields.get('name', 'Destination')} is a beautiful place in {fields.get('district', 'Nepal')}, Nepal."
                changes['destinations'] += 1
            # Fill empty short_description
            if not fields.get('short_description'):
                fields['short_description'] = f"Explore {fields.get('name', 'this amazing destination')} in {fields.get('district', 'Nepal')}."
                changes['destinations'] += 1

        elif model == 'tourist.hotel':
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Hotel')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['hotels'] += 1
            if not fields.get('phone'):
                fields['phone'] = generate_phone()
                changes['hotels'] += 1
            if not fields.get('email'):
                fields['email'] = generate_email(fields.get('name', 'hotel'))
                changes['hotels'] += 1
            if not fields.get('description'):
                fields['description'] = f"{fields.get('name', 'Hotel')} offers comfortable accommodation with excellent service."
                changes['hotels'] += 1

        elif model == 'tourist.restaurant':
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Restaurant')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['restaurants'] += 1
            if not fields.get('phone'):
                fields['phone'] = generate_phone()
                changes['restaurants'] += 1
            if not fields.get('cuisine_type'):
                fields['cuisine_type'] = random.choice(["Nepali", "Indian", "Chinese", "Continental", "Multi-cuisine"])
                changes['restaurants'] += 1

        elif model == 'tourist.hospital':
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Hospital')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['hospitals'] += 1
            if not fields.get('phone'):
                fields['phone'] = generate_phone()
                changes['hospitals'] += 1
            if not fields.get('hospital_type'):
                fields['hospital_type'] = random.choice(["General", "Specialized", "Community", "Private"])
                changes['hospitals'] += 1

        elif model == 'tourist.policestation':
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Police Station')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['police_stations'] += 1
            if not fields.get('phone'):
                fields['phone'] = generate_phone()
                changes['police_stations'] += 1

        elif model == 'tourist.category':
            if not fields.get('description'):
                fields['description'] = f"{fields.get('name', 'Category')} destinations in Nepal"
                changes['categories'] += 1

        elif model == 'tourist.destinationimage':
            if not fields.get('caption'):
                fields['caption'] = f"Beautiful view of the destination"
                changes['images'] += 1
            if not fields.get('image_path'):
                fields['image_path'] = f"images/destinations/{random.randint(1, 100)}.jpg"
                changes['images'] += 1

        elif model == 'tourist.user':
            if not fields.get('phone_number'):
                fields['phone_number'] = generate_phone()
                changes['users'] += 1

    # Write back
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fixed empty fields:")
    for key, count in changes.items():
        if count > 0:
            print(f"  {key}: {count}")

if __name__ == '__main__':
    populate_empty_fields()
