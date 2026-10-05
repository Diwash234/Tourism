import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
os.environ['ML_SERVICE_URL'] = 'http://127.0.0.1:8001'
os.environ['ML_SERVICE_TIMEOUT'] = '30'
import django
django.setup()
print('Django setup complete')
from django.test import Client
client = Client()
print('Client created')

# Test itinerary endpoint
response = client.post('/api/v1/ml/itinerary/', {
    'days': 3,
    'travelers': 1,
    'budget_level': 'mid',
    'travel_style': 'leisure',
    'travel_type': 'solo',
    'interests': ['culture'],
    'start_city': 'Kathmandu'
}, content_type='application/json')
print('Itinerary endpoint status:', response.status_code)
if response.status_code != 200:
    print('Itinerary response content:', response.content[:500])
else:
    print('Itinerary response:', response.json())