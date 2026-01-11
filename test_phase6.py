import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from simulator.models import Match, Ball
from simulator.views_admin import MatchActionView
from simulator.services.generator import create_dummy_match, setup_match_squads
from simulator.services.engine import SimulationEngine

def test_controls():
    print("Setting up match...")
    match = create_dummy_match()
    setup_match_squads(match)
    match.is_live = True
    match.save()
    
    # Simulate some balls
    engine = SimulationEngine()
    engine.simulate_ball(match)
    engine.simulate_ball(match)
    
    ball_count_before = Ball.objects.filter(match=match).count()
    print(f"Balls before reset: {ball_count_before}")
    if ball_count_before == 0:
        print("FAIL: No balls generated?")
        return

    # Test Speed Control
    print("Testing Speed Control...")
    factory = RequestFactory()
    request = factory.post(f'/simulator/match/{match.id}/speed/', {'seconds_per_ball': '0.5'})
    
    view = MatchActionView.as_view()
    response = view(request, match_id=match.id, action='speed')
    
    match.refresh_from_db()
    print(f"Match Speed: {match.seconds_per_ball}")
    if match.seconds_per_ball == 0.5:
        print("PASS: Speed updated")
    else:
        print("FAIL: Speed mismatch")

    # Test Reset
    print("Testing Reset...")
    request = factory.post(f'/simulator/match/{match.id}/reset/')
    response = view(request, match_id=match.id, action='reset')
    
    ball_count_after = Ball.objects.filter(match=match).count()
    match.refresh_from_db()
    
    print(f"Balls after reset: {ball_count_after}")
    print(f"Match Live: {match.is_live}")
    
    if ball_count_after == 0 and not match.is_live:
         print("PASS: Match reset successfully")
    else:
         print("FAIL: Reset failed")

if __name__ == "__main__":
    test_controls()
