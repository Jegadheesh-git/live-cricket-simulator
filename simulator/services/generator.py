import random
from faker import Faker
from simulator.models import Team, Player, Match, PlayingSquad
from django.utils import timezone

fake = Faker()

def generate_teams_and_players(count=2):
    teams = []
    for _ in range(count):
        city = fake.city()
        name = f"{city} {fake.color_name().capitalize()}s"
        short_name = "".join([w[0] for w in name.split()]).upper()[:3] + str(random.randint(10, 99))
        
        team, created = Team.objects.get_or_create(
            name=name,
            defaults={'short_name': short_name}
        )
        
        # Ensure players
        if team.matches.count() == 0:  # Only add players if new or unused essentially
             _generate_players_for_team(team)
        
        teams.append(team)
    return teams

def _generate_players_for_team(team):
    roles = ['BATSMAN'] * 5 + ['ALL_ROUNDER'] * 2 + ['WICKET_KEEPER'] * 1 + ['BOWLER'] * 4
    for role in roles:
        Player.objects.create(
            first_name=fake.first_name_male(),
            last_name=fake.last_name(),
            role=role,
            batting_hand=random.choice(['RIGHT', 'LEFT']),
            bowling_style=random.choice(['FAST', 'SPIN', 'MEDIUM']) if role != 'WICKET_KEEPER' else None
        )

def create_dummy_match():
    teams = generate_teams_and_players(2)
    match = Match.objects.create(
        date=timezone.now(),
        match_type='T20',
        is_live=False,
        current_innings=1
    )
    match.teams.set(teams)
    
    # Init squads (simple: pick first 11)
    for team in teams:
        players = Player.objects.filter(playingsquad__team=team).distinct()
        if not players.exists():
             _generate_players_for_team(team)
             players = Player.objects.filter(playingsquad__team=team).distinct() # Re-query? No, wait.
             # Actually Player creation doesn't link to team directly in many models, 
             # but here we don't have a Team-Player link in Model yet? 
             # Ah, Player model is standalone. PlayingSquad links them.
             # So we need to just pick ANY players or associate them loosely.
             # Let's just pick random players who are NOT in a squad for this match yet?
             # Or better: Create new players for every team generation to avoid conflicts.
             pass
        else:
             # reuse?
             pass

    # REVISION: Player model doesn't have a 'Team' foreign key in my design phase 1.
    # It seems Players are free agents in my model or I missed linking them.
    # Checking Phase 1 models... 
    # Team, Player, Match, PlayingSquad.
    # Player has no Team FK. So Players are global pool.
    # FIX: I will assign players to the squad from a global pool or create new ones tailored for the team name.
    
    return match

def setup_match_squads(match):
    # For each team, create 11 players and add to squad
    for team in match.teams.all():
        # Create 11 fresh players for this match/team specifically to avoid logic complexity
        roles = ['BATSMAN'] * 4 + ['ALL_ROUNDER'] * 2 + ['WICKET_KEEPER'] * 1 + ['BOWLER'] * 4
        for i, role in enumerate(roles):
            player = Player.objects.create(
                first_name=fake.first_name_male(),
                last_name=fake.last_name(),
                role=role,
                batting_hand=random.choice(['RIGHT', 'LEFT']),
                bowling_style=random.choice(['FAST', 'SPIN', 'MEDIUM']) if role != 'WICKET_KEEPER' else None
            )
            PlayingSquad.objects.create(
                match=match,
                team=team,
                player=player,
                is_captain=(i==0),
                is_wicket_keeper=(role=='WICKET_KEEPER')
            )
