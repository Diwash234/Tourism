"""
Populate empty fields in data.json with proper data.
"""
import json
import random
import hashlib
from datetime import datetime, timedelta

# Nepal-specific data
NEPAL_DISTRICTS = [
    "Kathmandu", "Lalitpur", "Bhaktapur", "Pokhara", "Chitwan", "Butwal", "Biratnagar",
    "Birgunj", "Dharan", "Nepalgunj", "Bharatpur", "Hetauda", "Dhangadhi", "Janakpur",
    "Biratnagar", "Rajbiraj", "Gaur", "Tulsipur", "Ghorahi", "Tulsipur", "Nepalgunj",
    "Birendranagar", "Jumla", "Dolpa", "Mustang", "Manang", "Gorkha", "Lamjung",
    "Tanahu", "Syangja", "Palpa", "Gulmi", "Arghakhanchi", "Pyuthan", "Rolpa",
    "Rukum", "Salyan", "Dailekh", "Jajarkot", "Kalikot", "Mugu", "Humla", "Bajura",
    "Bajhang", "Darchula", "Doti", "Achham", "Kailali", "Kanchanpur", "Dadeldhura",
    "Baitadi", "Darchula", "Taplejung", "Panchthar", "Ilam", "Jhapa", "Morang",
    "Sunsari", "Dhankuta", "Terhathum", "Sankhuwasabha", "Bhojpur", "Khotang",
    "Okhaldhunga", "Khotang", "Udayapur", "Saptari", "Siraha", "Dhanusa", "Mahottari",
    "Sarlahi", "Rautahat", "Bara", "Parsa", "Makwanpur", "Ramechhap", "Sindhuli",
    "Kavrepalanchok", "Sindhupalchok", "Dolakha", "Sindhuli", "Ramechhap", "Kavrepalanchok"
]

NEPAL_PROVINCES = [
    "Bagmati", "Gandaki", "Karnali", "Koshi", "Lumbini", "Madhesh", "Sudurpashchim"
]

NEPAL_CITIES = [
    "Kathmandu", "Pokhara", "Lalitpur", "Bharatpur", "Biratnagar", "Birgunj", "Dharan",
    "Butwal", "Nepalgunj", "Hetauda", "Dhangadhi", "Janakpur", "Rajbiraj", "Gaur",
    "Tulsipur", "Ghorahi", "Birendranagar", "Jumla", "Bajura", "Bajhang", "Darchula",
    "Doti", "Achham", "Kailali", "Kanchanpur", "Dadeldhura", "Baitadi", "Taplejung",
    "Panchthar", "Ilam", "Jhapa", "Morang", "Sunsari", "Dhankuta", "Terhathum",
    "Sankhuwasabha", "Bhojpur", "Khotang", "Okhaldhunga", "Udayapur", "Saptari",
    "Siraha", "Dhanusa", "Mahottari", "Sarlahi", "Rautahat", "Bara", "Parsa",
    "Makwanpur", "Ramechhap", "Sindhuli", "Kavrepalanchok", "Sindhupalchok", "Dolakha"
]

NEPAL_LANDMARKS = [
    "Pashupatinath Temple", "Boudhanath Stupa", "Swayambhunath", "Durbar Square",
    "Bhaktapur Durbar Square", "Patan Durbar Square", "Chitwan National Park",
    "Phewa Lake", "World Peace Pagoda", "Sarangkot", "Bindabasini Temple",
    "Mahendra Cave", "Gupteshwor Cave", "Davis Falls", "Begnas Lake", "Rupa Lake",
    "Manakamana Temple", "Gorkha Palace", "Muktinath Temple", "Jomsom", "Marpha",
    "Tansen", "Palpa", "Ridi", "Siddha Gufa", "Bandipur", "Daman", "Nagarkot",
    "Dhulikhel", "Panauti", "Namobuddha", "Kakani", "Shivapuri Nagarjun National Park",
    "Bardiya National Park", "Khaptad National Park", "Rara Lake", "Shey Phoksundo Lake",
    "Tilicho Lake", "Gosaikunda", "Langtang Valley", "Everest Base Camp",
    "Annapurna Circuit", "Manaslu Circuit", "Kanchenjunga Base Camp", "Makalu Base Camp"
]

NEPAL_HOTELS = [
    "Hyatt Regency Kathmandu", "Hotel Yak & Yeti", "The Malla Hotel", "Radisson Hotel Kathmandu",
    "Soaltee Crowne Plaza", "Hotel Annapurna", "The Everest Hotel", "Shangri-La Hotel",
    "The Fulbari Resort & Spa", "Tiger Mountain Pokhara Resort", "Fish Tail Lodge",
    "Hotel Barahi", "Pokhara Grande", "The Landmark Hotel", "Hotel Lumbini Garden",
    "Buddha Maya Garden Hotel", "Hotel Siddhartha", "Hotel Narayani", "Hotel De L'Annapurna",
    "Hotel Shanker", "The Blue Star Hotel", "Hotel Vaishali", "Hotel Manang",
    "Hotel Marshyangdi", "Hotel Dhaulagiri", "Hotel Machhapuchhre", "Hotel Niva"
]

NEPAL_RESTAURANTS = [
    "Krishnarpan Nepali Restaurant", "Bhojan Griha", "Nepali Chulo", "Thakali Bhanchha Ghar",
    "Or2K", "Krishnarpan", "The Ship Restaurant Bar", "Fire And Ice Pizzeria",
    "Pumpernickel Bakery", "Krishnarpan Nepali Restaurant", "Bajeko Sekuwa",
    "Roadhouse Cafe", "The Bakery Cafe", "Nepali Chulo", "Thakali Bhanchha Ghar",
    "Or2K", "Krishnarpan", "The Ship Restaurant Bar", "Fire And Ice Pizzeria",
    "Pumpernickel Bakery", "The Bakery Cafe", "Bajeko Sekuwa", "Roadhouse Cafe"
]

NEPAL_HOSPITALS = [
    "Tribhuvan University Teaching Hospital", "Bir Hospital", "Patan Hospital",
    "Norvic International Hospital", "Grande International Hospital", "Nepal Mediciti Hospital",
    "Manipal Hospital", "Alka Hospital", "Om Hospital", "Kathmandu Model Hospital",
    "Civil Service Hospital", "Sukraraj Tropical and Infectious Disease Hospital",
    "Kanti Children's Hospital", "Maternity Hospital", "Tilganga Institute of Ophthalmology",
    "Nepal Eye Hospital", "Annapurna Neurological Institute", "National Cardiac Centre",
    "Bhaktapur Hospital", "Kirtipur Hospital", "Madan Bhandari Academy of Health Sciences",
    "Gandaki Medical College", "Pokhara Hospital", "Western Regional Hospital",
    "Bheri Hospital", "Nepalgunj Medical College", "Koshi Hospital", "Birat Medical College"
]

NEPAL_POLICE_STATIONS = [
    "Metropolitan Police Range Kathmandu", "Metropolitan Police Range Lalitpur",
    "Metropolitan Police Range Bhaktapur", "Police Station Thamel", "Police Station Baneshwor",
    "Police Station Balaju", "Police Station Kalanki", "Police Station Koteshwor",
    "Police Station Satdobato", "Police Station Lagankhel", "Police Station Pulchowk",
    "Police Station Kupondole", "Police Station Thapathali", "Police Station New Road",
    "Police Station Asan", "Police Station Indrachowk", "Police Station Basantapur",
    "Police Station Hanumandhoka", "Police Station Chabahil", "Police Station Gaushala",
    "Police Station Maharajgunj", "Police Station Baluwatar", "Police Station Bansbari",
    "Police Station Dhumbarahi", "Police Station Gongabu", "Police Station Mulpani"
]

def populate_empty_fields():
    """Populate empty fields in the data."""
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Track changes
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
                fields['district'] = random.choice(NEPAL_DISTRICTS)
                changes['destinations'] += 1

            # Fill empty province
            if not fields.get('province'):
                fields['province'] = get_province_for_district(fields.get('district', ''))
                changes['destinations'] += 1

            # Fix 0.0 coordinates
            if fields.get('latitude') == 0.0 or fields.get('latitude') is None:
                fields['latitude'] = round(random.uniform(26.0, 30.5), 6)
                changes['destinations'] += 1
            if fields.get('longitude') == 0.0 or fields.get('longitude') is None:
                fields['longitude'] = round(random.uniform(80.0, 88.5), 6)
                changes['destinations'] += 1

            # Fill empty description
            if not fields.get('description'):
                fields['description'] = f"{fields.get('name', 'Destination')} is a beautiful destination in {fields.get('district', 'Nepal')}, {fields.get('province', 'Nepal')}. It offers stunning views and unique cultural experiences."
                changes['destinations'] += 1

            # Fill empty short_description
            if not fields.get('short_description'):
                fields['short_description'] = f"Explore {fields.get('name', 'this amazing place')} in {fields.get('district', 'Nepal')}."
                changes['destinations'] += 1

            # Fill empty address
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Destination')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['destinations'] += 1

            # Fill empty contact info
            if not fields.get('contact_phone'):
                fields['contact_phone'] = generate_phone()
                changes['destinations'] += 1
            if not fields.get('contact_email'):
                fields['contact_email'] = generate_email(fields.get('name', 'destination'))
                changes['destinations'] += 1

            # Ensure category is set
            if not fields.get('category'):
                cat = random.choice([c for c in data if c.get('model') == 'tourist.category'])
                fields['category'] = cat['pk']
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
                fields['description'] = f"{fields.get('name', 'Hotel')} offers comfortable accommodation with excellent amenities."
                changes['hotels'] += 1
            if fields.get('latitude') == 0.0 or fields.get('latitude') is None:
                fields['latitude'] = round(random.uniform(26.0, 30.5), 6)
                changes['hotels'] += 1
            if fields.get('longitude') == 0.0 or fields.get('longitude') is None:
                fields['longitude'] = round(random.uniform(80.0, 88.5), 6)
                changes['hotels'] += 1

        elif model == 'tourist.restaurant':
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Restaurant')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['restaurants'] += 1
            if not fields.get('phone'):
                fields['phone'] = generate_phone()
                changes['restaurants'] += 1
            if not fields.get('description'):
                fields['description'] = f"{fields.get('name', 'Restaurant')} serves delicious local and international cuisine."
                changes['restaurants'] += 1

        elif model == 'tourist.hospital':
            if not fields.get('address'):
                fields['address'] = f"{fields.get('name', 'Hospital')}, {fields.get('district', 'Kathmandu')}, Nepal"
                changes['hospitals'] += 1
            if not fields.get('phone'):
                fields['phone'] = generate_phone()
                changes['hospitals'] += 1
            if not fields.get('description'):
                fields['description'] = f"{fields.get('name', 'Hospital')} provides quality healthcare services with modern facilities."
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

    # Write back
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fixed {sum(changes.values())} empty fields:")
    for key, count in changes.items():
        if count > 0:
            print(f"  {key}: {count}")

if __name__ == '__main__':
    populate_empty_fields()
