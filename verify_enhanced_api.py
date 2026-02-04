import requests
import json
import time

BASE_URL = "https://live-cricket-simulator.onrender.com/api/v1"
TOKEN = "b71b5cf35520a80447d2fe98e666d1c7ff47112c" # Using existing token, assumes it's valid for now, or we test locally.
# Actually faster to test locally usually, but user asked for Postman testing on prod url.
# I should probably test LOCAL URL first to be safe.
LOCAL_URL = "http://127.0.0.1:8000/api/v1"
TOKEN_LOCAL = "NOT_SET_YET" # Need to get this

# Let's use the local test harness logic instead of requests if we are running locally?
# Or just run `python test_phase1.py` style test which uses Django Test Client.
# I will use Django Test Client to verify LOCALLY first.

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from django.conf import settings
from simulator.models import Match
from simulator.services.generator import create_dummy_match, setup_match_squads

def test_enhanced_api():
    print("🚀 Setting up test data...")
    match = create_dummy_match()
    setup_match_squads(match)
    match.is_live = True
    match.save()
    
    print(f"Match created: {match} with venue: {match.venue}")
    
    client = APIClient()
    # We need a user/token.
    # For test client we can force auth maybe? Or use existing token.
    # Let's creaate a user if needed or just force auth.
    from rest_framework.authtoken.models import Token
    from django.contrib.auth.models import User
    
    user, _ = User.objects.get_or_create(username='tester')
    token, _ = Token.objects.get_or_create(user=user)
    
    client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    
    print("📡 Calling API...")
    response = client.get('/api/v1/matches/live')
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        print(f"✅ Status 200 OK")
        
        # Verify Venue
        if len(data) > 0:
            m = data[0]
            print(f"   Venue: {m.get('venue')}")
            if not m.get('venue'):
                print("   ❌ Venue Missing!")
            
            # Verify Players in Squad
            teams = m.get('teams', [])
            if len(teams) > 0:
                squad = teams[0].get('squad', [])
                print(f"   Squad Size: {len(squad)}")
                if len(squad) > 0:
                    p = squad[0]['player']
                    print(f"   Player Example: {p.get('first_name')} {p.get('last_name')}")
                    print(f"   Nationality: {p.get('nationality')}")
                    print(f"   Role: {p.get('role')}")
                    print(f"   DOB: {p.get('dob')}")
        else:
             print("   ⚠️ No live matches found in response (unexpected)")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.data)

if __name__ == "__main__":
    test_enhanced_api()
