import os, json, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourism.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1'
import django
django.setup()
from django.test import Client

client = Client()
email = f"test_{uuid.uuid4().hex[:8]}@example.com"
password = "TestPass123!"
print("email:", email)

# 1. Register
r = client.post('/api/v1/auth/register/', data=json.dumps({
    "email": email, "password": password, "password_confirm": password,
    "first_name": "Test", "last_name": "User",
    "username": email.split('@')[0]
}), content_type='application/json')
print("REGISTER:", r.status_code, r.content[:300])

# 2. Login
r = client.post('/api/v1/auth/login/', data=json.dumps({
    "email": email, "password": password
}), content_type='application/json')
print("LOGIN:", r.status_code, r.content[:300])
if r.status_code == 200:
    tokens = r.json()
    access = tokens.get('access')
    refresh = tokens.get('refresh')
    # 3. Authenticated request
    r2 = client.get('/api/v1/auth/profile/', HTTP_AUTHORIZATION=f'Bearer {access}')
    print("PROFILE:", r2.status_code, r2.content[:300])
    # 4. Refresh
    r3 = client.post('/api/v1/auth/token/refresh/', data=json.dumps({"refresh": refresh}), content_type='application/json')
    print("REFRESH:", r3.status_code, r3.content[:200])
    # 5. Bad login
    r5 = client.post('/api/v1/auth/login/', data=json.dumps({"email": email, "password": "wrong"}), content_type='application/json')
    print("BAD LOGIN (expect 401/400):", r5.status_code)
    # 6. Logout (authenticated)
    r4 = client.post('/api/v1/auth/logout/', data=json.dumps({"refresh": refresh}), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {access}')
    print("LOGOUT:", r4.status_code, r4.content[:200])
    # 7. Reuse refresh after logout (expect 401)
    r6 = client.post('/api/v1/auth/token/refresh/', data=json.dumps({"refresh": refresh}), content_type='application/json')
    print("REFRESH AFTER LOGOUT (expect 401):", r6.status_code)
