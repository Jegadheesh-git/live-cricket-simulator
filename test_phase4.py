import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from simulator.models import Match, Ball, BattingScore, InningsScore
from simulator.services.engine import SimulationEngine
from simulator.services.generator import create_dummy_match, setup_match_squads

def test_engine():
    print("Setting up match...")
    match = create_dummy_match()
    setup_match_squads(match)
    match.is_live = True
    match.save()
    
    engine = SimulationEngine()
    
    print("Simulating 1 over (6 balls)...")
    for i in range(6):
        engine.simulate_ball(match)
        # Check latest ball
        ball = Ball.objects.filter(match=match).last()
        if ball:
             print(f"Ball {ball.over_number}.{ball.ball_number}: {ball.total_runs} runs (Batter: {ball.runs_batter}, Extras: {ball.extras}) - {ball.striker.last_name} on strike")
             if ball.is_wicket:
                 print(f"!!! WICKET: {ball.dismissal_type} !!!")
        else:
             print("No ball created?")

    # Check Innings Score
    score = InningsScore.objects.get(match=match, innings=1)
    print(f"Innings Score: {score.total_runs}/{score.total_wickets} in {score.total_overs} overs")
    
    # Check Batters
    batters = BattingScore.objects.filter(match=match, innings=1)
    for b in batters:
        on_strike = "*" if b.is_on_strike else ""
        status = "OUT" if b.is_out else "NOT OUT"
        print(f"{b.player.last_name} {on_strike}: {b.runs} ({b.balls_faced}) - {status}")

if __name__ == "__main__":
    test_engine()
