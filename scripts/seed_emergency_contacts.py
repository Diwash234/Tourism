import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/home/user/Tourism/Tourism')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
django.setup()

from tourist.models import EmergencyContact

EMERGENCY_CONTACTS = [
    # --- National Emergency & Police ---
    {
        "contact_type": "police",
        "name": "Nepal Police Central Emergency Control Room (100)",
        "phone_number": "100",
        "alternate_phone": "+977-1-4228435",
        "address": "Nepal Police Headquarters, Naxal",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7150,
        "longitude": 85.3260,
        "is_24_hours": True,
        "designation": "National Police Emergency Headquarters"
    },
    {
        "contact_type": "police",
        "name": "Kathmandu Tourist Police Headquarters",
        "phone_number": "+977-1-4247041",
        "alternate_phone": "1144",
        "address": "Bhrikutimandip, Tourist Service Center",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7025,
        "longitude": 85.3172,
        "is_24_hours": True,
        "designation": "Central Tourist Police Unit"
    },
    {
        "contact_type": "police",
        "name": "Pokhara Tourist Police Station",
        "phone_number": "+977-61-461080",
        "alternate_phone": "+977-61-462761",
        "address": "Lakeside, Damside Road",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2096,
        "longitude": 83.9580,
        "is_24_hours": True,
        "designation": "Pokhara Tourist Safety & Police Desk"
    },
    {
        "contact_type": "police",
        "name": "Chitwan Tourist Police & Security Post",
        "phone_number": "+977-56-580008",
        "alternate_phone": "+977-56-580120",
        "address": "Sauraha Tourist Hub",
        "city": "Chitwan",
        "country": "Nepal",
        "latitude": 27.5833,
        "longitude": 84.4833,
        "is_24_hours": True,
        "designation": "Sauraha Wildlife & Tourist Police Unit"
    },
    {
        "contact_type": "police",
        "name": "Lumbini Tourist Police Post",
        "phone_number": "+977-71-580012",
        "alternate_phone": "+977-71-580045",
        "address": "Sacred Garden Outer Gate",
        "city": "Lumbini",
        "country": "Nepal",
        "latitude": 27.4833,
        "longitude": 83.2760,
        "is_24_hours": True,
        "designation": "Lumbini Sacred Garden Police Post"
    },
    {
        "contact_type": "police",
        "name": "Namche Bazaar Mountain Police & Rescue Post",
        "phone_number": "+977-38-540020",
        "alternate_phone": "+977-38-540002",
        "address": "Namche Plateau",
        "city": "Solukhumbu",
        "country": "Nepal",
        "latitude": 27.8069,
        "longitude": 86.7142,
        "is_24_hours": True,
        "designation": "Everest Region Alpine Trekker Police Post"
    },
    {
        "contact_type": "police",
        "name": "Jomsom Mountain Police Checkpost",
        "phone_number": "+977-69-440012",
        "alternate_phone": "+977-69-440022",
        "address": "Jomsom Airport Runway Gate",
        "city": "Mustang",
        "country": "Nepal",
        "latitude": 28.7820,
        "longitude": 83.7225,
        "is_24_hours": True,
        "designation": "Mustang Trail & Pilgrim Security Desk"
    },

    # --- National Fire & Ambulance Services ---
    {
        "contact_type": "fire_station",
        "name": "Juddha Barun Yantra Central Fire Station (101)",
        "phone_number": "101",
        "alternate_phone": "+977-1-4221177",
        "address": "New Road, Basantapur",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7042,
        "longitude": 85.3114,
        "is_24_hours": True,
        "designation": "Central Fire Brigade Headquarters"
    },
    {
        "contact_type": "ambulance",
        "name": "Nepal Red Cross Central Ambulance Service (102)",
        "phone_number": "102",
        "alternate_phone": "+977-1-4228094",
        "address": "Red Cross Marg, Kalimati",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.6975,
        "longitude": 85.2980,
        "is_24_hours": True,
        "designation": "National Ambulance Dispatch Center"
    },
    {
        "contact_type": "ambulance",
        "name": "Nepal Ambulance Service (NAS) Emergency Dispatch",
        "phone_number": "102",
        "alternate_phone": "+977-1-4240805",
        "address": "Tripureshwor",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.6938,
        "longitude": 85.3160,
        "is_24_hours": True,
        "designation": "Emergency Medical Response Unit"
    },

    # --- Major Referral Hospitals & Rescue Clinics ---
    {
        "contact_type": "hospital",
        "name": "Tribhuvan University Teaching Hospital (TUTH) Emergency",
        "phone_number": "+977-1-4412303",
        "alternate_phone": "+977-1-4412404",
        "address": "Maharajgunj",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7360,
        "longitude": 85.3300,
        "is_24_hours": True,
        "designation": "24/7 Level-1 Emergency Trauma Center"
    },
    {
        "contact_type": "hospital",
        "name": "Bir Hospital National Trauma Center",
        "phone_number": "+977-1-4221988",
        "alternate_phone": "+977-1-4221119",
        "address": "Kanti Path, Mahabouddha",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7047,
        "longitude": 85.3148,
        "is_24_hours": True,
        "designation": "Central Public Hospital & Trauma Center"
    },
    {
        "contact_type": "hospital",
        "name": "Patan Hospital ER",
        "phone_number": "+977-1-5522295",
        "alternate_phone": "+977-1-5522266",
        "address": "Lagankhel",
        "city": "Lalitpur",
        "country": "Nepal",
        "latitude": 27.6675,
        "longitude": 85.3215,
        "is_24_hours": True,
        "designation": "24/7 Emergency & ICU Center"
    },
    {
        "contact_type": "hospital",
        "name": "Gandaki Medical College & Teaching Hospital",
        "phone_number": "+977-61-538595",
        "alternate_phone": "+977-61-538596",
        "address": "Prithvi Chowk",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2120,
        "longitude": 83.9870,
        "is_24_hours": True,
        "designation": "Pokhara Primary Emergency Hospital"
    },
    {
        "contact_type": "hospital",
        "name": "Himalayan Rescue Association (HRA) Altitude Medical Center",
        "phone_number": "+977-1-4440292",
        "alternate_phone": "+977-1-4440293",
        "address": "Dhobighat / Manang / Pheriche Aid Posts",
        "city": "Solukhumbu & Manang",
        "country": "Nepal",
        "latitude": 28.6650,
        "longitude": 84.0200,
        "is_24_hours": True,
        "designation": "High Altitude Sickness & Heli Rescue Coordination"
    },
    {
        "contact_type": "hospital",
        "name": "BP Koirala Institute of Health Sciences (BPKIHS)",
        "phone_number": "+977-25-525555",
        "alternate_phone": "+977-25-520200",
        "address": "Ghodepani Road",
        "city": "Dharan",
        "country": "Nepal",
        "latitude": 26.8125,
        "longitude": 87.2833,
        "is_24_hours": True,
        "designation": "Koshi Province Super Speciality Emergency Hospital"
    },
    {
        "contact_type": "hospital",
        "name": "Bharatpur Hospital Trauma Center",
        "phone_number": "+977-56-520111",
        "alternate_phone": "+977-56-520112",
        "address": "Hospital Road",
        "city": "Bharatpur",
        "country": "Nepal",
        "latitude": 27.6833,
        "longitude": 84.4333,
        "is_24_hours": True,
        "designation": "Central Highway Trauma & Emergency Hospital"
    },

    # --- Tourism Offices & Official Information Desks ---
    {
        "contact_type": "tourism_office",
        "name": "Nepal Tourism Board (NTB) Head Office & Information Center",
        "phone_number": "+977-1-4256909",
        "alternate_phone": "+977-1-4256910",
        "address": "Bhrikutimandap",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7022,
        "longitude": 85.3175,
        "is_24_hours": False,
        "designation": "National Tourism Board Information Desk"
    },
    {
        "contact_type": "tourism_office",
        "name": "Nepal Tourism Board Pokhara Regional Office",
        "phone_number": "+977-61-465292",
        "alternate_phone": "+977-61-465293",
        "address": "Damside",
        "city": "Pokhara",
        "country": "Nepal",
        "latitude": 28.2010,
        "longitude": 83.9630,
        "is_24_hours": False,
        "designation": "Gandaki Tourism Information Desk"
    },
    {
        "contact_type": "tourism_office",
        "name": "Department of Tourism Trekking Permit Desk",
        "phone_number": "+977-1-4225709",
        "alternate_phone": "+977-1-4222091",
        "address": "Tripureshwor",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.6930,
        "longitude": 85.3155,
        "is_24_hours": False,
        "designation": "Trekking Permits & TIMS Service Counter"
    },

    # --- Foreign Diplomatic Missions / Tourist Support ---
    {
        "contact_type": "embassy",
        "name": "Embassy of the United States Consular Emergency Section",
        "phone_number": "+977-1-4234000",
        "alternate_phone": "+977-1-4234250",
        "address": "Maharajgunj",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7385,
        "longitude": 85.3340,
        "is_24_hours": True,
        "designation": "U.S. Citizen Consular Emergency Response"
    },
    {
        "contact_type": "embassy",
        "name": "Embassy of India Consular Emergency Desk",
        "phone_number": "+977-1-4410900",
        "alternate_phone": "+977-1-4414200",
        "address": "Lainchaur",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7180,
        "longitude": 85.3185,
        "is_24_hours": True,
        "designation": "Indian Citizen Emergency Helpline"
    },
    {
        "contact_type": "embassy",
        "name": "Embassy of the People's Republic of China Consular Helpline",
        "phone_number": "+977-1-4411740",
        "alternate_phone": "+977-1-4413229",
        "address": "Baluwatar",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7280,
        "longitude": 85.3310,
        "is_24_hours": True,
        "designation": "Chinese Tourist Consular Desk"
    },
    {
        "contact_type": "embassy",
        "name": "British Embassy Emergency Consular Services",
        "phone_number": "+977-1-4237100",
        "alternate_phone": "+977-1-4237101",
        "address": "Lainchaur",
        "city": "Kathmandu",
        "country": "Nepal",
        "latitude": 27.7190,
        "longitude": 85.3190,
        "is_24_hours": True,
        "designation": "UK Citizen Emergency Assistance"
    }
]

def run():
    print("--- Seeding Authentic Emergency Contacts Across Nepal ---")
    created_count = 0
    updated_count = 0

    for item in EMERGENCY_CONTACTS:
        contact, created = EmergencyContact.objects.update_or_create(
            name=item["name"],
            defaults=item
        )
        if created:
            created_count += 1
            print(f"[CREATED] {contact.name} ({contact.contact_type}, {contact.phone_number})")
        else:
            updated_count += 1
            print(f"[UPDATED] {contact.name} ({contact.contact_type}, {contact.phone_number})")

    print(f"\nResult: {created_count} created, {updated_count} updated.")
    print(f"Total Emergency Contacts in Database: {EmergencyContact.objects.count()}")

if __name__ == "__main__":
    run()
