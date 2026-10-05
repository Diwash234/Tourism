import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
os.environ['ML_SERVICE_URL'] = 'http://127.0.0.1:8001'
os.environ['ML_SERVICE_TIMEOUT'] = '1'
import django
django.setup()
print('Django setup complete')
from django.test import Client
client = Client()
print('Client created')

# Test just the destination query used by itinerary
from tourist.models import Destination, Hotel, Hospital, PoliceStation, OSMEssentialService
print('Counting hotels...')
print('Hotels:', Hotel.objects.filter(is_active=True).count())
print('Hospitals:', Hospital.objects.filter(is_archived=False).count())
print('Police:', PoliceStation.objects.filter(is_archived=False).count())
print('OSM:', OSMEssentialService.objects.count())
