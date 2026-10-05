import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
os.environ['ML_SERVICE_URL'] = 'http://127.0.0.1:8001'
os.environ['ML_SERVICE_TIMEOUT'] = '1'
import django
django.setup()

# Test the destination lookup
from tourist.models import Destination
print("Looking for Kathmandu destination...")
dest = Destination.publicly_visible().filter(name__iexact="Kathmandu").first()
if dest:
    print(f"Found destination: {dest.name} (id={dest.id})")
else:
    print("Not found, trying prefix match...")
    dest = Destination.publicly_visible().filter(name__istartswith="Kathmandu").order_by("name").first()
    if dest:
        print(f"Found destination: {dest.name} (id={dest.id})")
    else:
        print("Still not found, trying icontains...")
        dest = Destination.publicly_visible().filter(name__icontains="Kathmandu").order_by("name").first()
        if dest:
            print(f"Found destination: {dest.name} (id={dest.id})")
        else:
            print("No destination found")

# Now test the view
from django.test import Client
client = Client()

print("\nTesting budget endpoint...")
response = client.post('/api/v1/ml/budget/', {
    'city': 'Kathmandu',
    'country': 'Nepal',
    'days': 3,
    'travelers': 1,
    'budget_level': 'mid'
}, content_type='application/json')
print('Budget endpoint status:', response.status_code)
if response.status_code != 200:
    print('Budget response content:', response.content[:500])
else:
    print('Budget response:', response.json())