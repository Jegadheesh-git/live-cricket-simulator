import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from simulator.models import Match, Team, Player, PlayingSquad

def test_dashboard_flow():
    c = Client()
    
    # 1. Check Dashboard Load
    response = c.get('/api/v1/dashboard/')  # Ah, I nested it under api/v1/ in urls.py? 
    # Let me check urls.py. config/urls.py includes simulator.urls at 'api/v1/'. 
    # So dashboard is at /api/v1/dashboard/. This is a bit odd for an HTML page but fine for now.
    
    if response.status_code == 200:
        print("PASS: Dashboard loaded")
    else:
        print(f"FAIL: Dashboard status {response.status_code}")
        return

    # 2. Create Match
    initial_count = Match.objects.count()
    print(f"Matches before: {initial_count}")
    
    response = c.post('/api/v1/match/create/')
    if response.status_code == 302: # Redirect
        print("PASS: Match creation redirect")
    else:
        print(f"FAIL: Match creation status {response.status_code}")
        
    final_count = Match.objects.count()
    print(f"Matches after: {final_count}")
    
    if final_count == initial_count + 1:
        print("PASS: Match created in DB")
    else:
        print("FAIL: Match not created")
        
    # Check details
    latest_match = Match.objects.last()
    print(f"Match Teams: {latest_match.teams.count()}")
    if latest_match.teams.count() == 2:
        print("PASS: 2 Teams assigned")
    else:
        print(f"FAIL: {latest_match.teams.count()} teams assigned")
        
    # Check Squads
    squad_count = PlayingSquad.objects.filter(match=latest_match).count()
    print(f"Squad Size: {squad_count}")
    if squad_count >= 22:
        print("PASS: Squads populated")
    else:
        print("FAIL: Squads incomplete")

if __name__ == "__main__":
    test_dashboard_flow()
