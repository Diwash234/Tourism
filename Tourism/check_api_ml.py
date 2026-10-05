import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
os.environ['ML_SERVICE_URL'] = 'http://127.0.0.1:8001'
os.environ['ML_SERVICE_TIMEOUT'] = '30'
import django
django.setup()
from django.test import Client
client = Client()

# Test budget endpoint
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
    data = response.json()
    print('Budget total:', data.get('total_budget_usd'))
