import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from simulator.views import LiveMatchesView
from rest_framework.test import APIClient
from django.conf import settings

def test_api():
    client = APIClient()
    
    print("Testing without token...")
    response = client.get('/api/v1/matches/live')
    if response.status_code == 403:
        print("PASS: 403 Forbidden as expected")
    else:
        print(f"FAIL: Expected 403, got {response.status_code}")

    print("Testing with invalid token...")
    client.credentials(HTTP_AUTHORIZATION='Bearer INVALID')
    response = client.get('/api/v1/matches/live')
    if response.status_code == 403:
        print("PASS: 403 Forbidden as expected")
    else:
        print(f"FAIL: Expected 403, got {response.status_code}")

    print("Testing with valid token...")
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {settings.SIMULATOR_AUTH_TOKEN}')
    response = client.get('/api/v1/matches/live')
    if response.status_code == 200:
        print("PASS: 200 OK")
        print("Data:", response.data)
    else:
        print(f"FAIL: Expected 200, got {response.status_code}")
        print(response.data)

if __name__ == "__main__":
    test_api()
