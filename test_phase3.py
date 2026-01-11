import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from simulator.models import Match, Team, Player, Ball, InningsScore, BattingScore, BowlingScore
from simulator.services.generator import create_dummy_match, setup_match_squads

def test_models():
    print("Creating Match...")
    match = create_dummy_match()
    setup_match_squads(match)
    
    team_batting = match.teams.first()
    team_bowling = match.teams.last()
    
    batter = Player.objects.filter(playingsquad__match=match, playingsquad__team=team_batting).first()
    bowler = Player.objects.filter(playingsquad__match=match, playingsquad__team=team_bowling).first()
    
    print("Creating InningsScore...")
    innings_score = InningsScore.objects.create(
        match=match,
        team=team_batting,
        innings=1,
        total_runs=0,
        total_wickets=0,
        total_overs=0.0
    )
    print(f"PASS: InningsScore created: {innings_score}")
    
    print("Creating BattingScore...")
    bat_score = BattingScore.objects.create(
        match=match,
        player=batter,
        innings=1,
        runs=0,
        balls_faced=0
    )
    print(f"PASS: BattingScore created: {bat_score.player}")

    print("Creating BowlingScore...")
    bowl_score = BowlingScore.objects.create(
        match=match,
        player=bowler,
        innings=1,
        overs=0.0,
        runs_conceded=0
    )
    print(f"PASS: BowlingScore created: {bowl_score.player}")
    
    print("Creating Ball...")
    ball = Ball.objects.create(
        match=match,
        innings=1,
        over_number=0,
        ball_number=1,
        striker=batter,
        non_striker=batter, # Just for test (should be diff player)
        bowler=bowler,
        runs_batter=4,
        total_runs=4
    )
    print(f"PASS: Ball created: {ball}")

if __name__ == "__main__":
    test_models()
