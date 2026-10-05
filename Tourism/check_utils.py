import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
os.environ['ML_SERVICE_URL'] = 'http://127.0.0.1:8001'
os.environ['ML_SERVICE_TIMEOUT'] = '1'
import django
django.setup()
from tourist.utils import get_ml_budget_prediction

print("Testing get_ml_budget_prediction...")
result = get_ml_budget_prediction(
    city="Kathmandu",
    country="Nepal",
    days=3,
    travelers=1,
    budget_level="mid"
)
print("Result:", result)