import os, json, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
import django
django.setup()
from django.test import Client

client = Client()
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
password = "TestPass123!"

client.post('/api/v1/auth/register/', data=json.dumps({
    "email": email, "password": password, "password_confirm": password,
    "first_name": "Test", "last_name": "User", "username": email.split('@')[0]
}), content_type='application/json')

r = client.post('/api/v1/auth/login/', data=json.dumps({"email": email, "password": password}), content_type='application/json')
tok = r.json()
access, refresh = tok['access'], tok['refresh']
print("LOGIN:", r.status_code)

# Rotate refresh (frontend persists data.refresh)
r = client.post('/api/v1/auth/token/refresh/', data=json.dumps({"refresh": refresh}), content_type='application/json')
print("REFRESH:", r.status_code, "has refresh in response:", 'refresh' in r.json())
new_refresh = r.json().get('refresh', refresh)
new_access = r.json().get('access', access)

# Logout with the rotated token + current access
r = client.post('/api/v1/auth/logout/', data=json.dumps({"refresh": new_refresh}), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {new_access}')
print("LOGOUT:", r.status_code, r.content[:200])

# Verify the rotated refresh is now unusable
r = client.post('/api/v1/auth/token/refresh/', data=json.dumps({"refresh": new_refresh}), content_type='application/json')
print("REFRESH AFTER LOGOUT (expect 401):", r.status_code)
