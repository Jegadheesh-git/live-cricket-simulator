import random
from faker import Faker
from simulator.models import Team, Player, Match, PlayingSquad, Nationality, Tournament
from django.utils import timezone

fake = Faker()

def get_or_create_nationalities():
    nationalities = [
        ('India', 'IND'), ('Australia', 'AUS'), ('England', 'ENG'), 
        ('South Africa', 'RSA'), ('New Zealand', 'NZ'), ('Pakistan', 'PAK'),
        ('West Indies', 'WI'), ('Sri Lanka', 'SL'), ('Bangladesh', 'BAN'), ('Afghanistan', 'AFG')
    ]
    objs = []
    for name, code in nationalities:
        obj, _ = Nationality.objects.get_or_create(name=name, code=code)
        objs.append(obj)
    return objs

def get_or_create_default_tournament():
    tournament, _ = Tournament.objects.get_or_create(
        code="tour123",
        defaults={"name": "IPL"}
    )
    return tournament

def generate_teams_and_players(count=2):
    nationalities = get_or_create_nationalities()
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
             _generate_players_for_team(team, nationalities)
        
        teams.append(team)
    return teams

def _generate_players_for_team(team, nationalities):
    roles = ['BATSMAN'] * 5 + ['ALL_ROUNDER'] * 2 + ['WICKET_KEEPER'] * 1 + ['BOWLER'] * 4
    for role in roles:
        Player.objects.create(
            first_name=fake.first_name_male(),
            middle_name=fake.first_name_male() if random.random() > 0.7 else "",
            last_name=fake.last_name(),
            nick_name=fake.first_name() if random.random() > 0.5 else "",
            nationality=random.choice(nationalities),
            dob=fake.date_of_birth(minimum_age=18, maximum_age=38),
            gender='M',
            height=random.uniform(165, 195),
            weight=random.uniform(60, 95),
            role=role,
            batting_hand=random.choice(['RIGHT', 'LEFT']),
            bowling_hand=random.choice(['RIGHT', 'LEFT']),
            bowling_style=random.choice(['FAST', 'SPIN', 'MEDIUM']) if role != 'WICKET_KEEPER' else None,
            batting_style="Accumulator" if role == 'BATSMAN' else "Slogger",
            fielding_skill=random.choice(['Elite', 'Good', 'Average']),
            wicket_keeping_skill='Elite' if role == 'WICKET_KEEPER' else 'None',
            height_type=random.choice(['Short', 'Medium', 'Tall']),
            bowling_type=random.choice(['Express Pace', 'Leg Spin', 'Off Spin']) if role == 'BOWLER' else None,
            batting_type="Technical"
        )

def create_dummy_match():
    teams = generate_teams_and_players(2)
    tournament = get_or_create_default_tournament()
    match = Match.objects.create(
        tournament=tournament,
        date=timezone.now(),
        venue=f"{fake.city()} International Cricket Stadium",
        match_type='T20',
        is_live=False,
        current_innings=1
    )
    match.teams.set(teams)
    
    # Init squads (simple: pick first 11)
    # Note: Phase 1 implementation didn't link players to teams, so we just pick random available players 
    # or create new ones in setup_match_squads.
    # We will rely on setup_match_squads to do the heavy lifting of squad creation
    
    return match

def setup_match_squads(match):
    nationalities = get_or_create_nationalities()
    # For each team, create 11 players and add to squad
    for team in match.teams.all():
        # Create 11 fresh players for this match/team specifically to avoid logic complexity
        roles = ['BATSMAN'] * 4 + ['ALL_ROUNDER'] * 2 + ['WICKET_KEEPER'] * 1 + ['BOWLER'] * 4
        for i, role in enumerate(roles):
            player = Player.objects.create(
                first_name=fake.first_name_male(),
                middle_name=fake.first_name_male() if random.random() > 0.7 else "",
                last_name=fake.last_name(),
                nationality=random.choice(nationalities),
                dob=fake.date_of_birth(minimum_age=18, maximum_age=38),
                gender='M',
                height=random.uniform(165, 195),
                weight=random.uniform(60, 95),
                role=role,
                batting_hand=random.choice(['RIGHT', 'LEFT']),
                bowling_style=random.choice(['FAST', 'SPIN', 'MEDIUM']) if role != 'WICKET_KEEPER' else None,
                height_type=random.choice(['Short', 'Medium', 'Tall'])
            )
            PlayingSquad.objects.create(
                match=match,
                team=team,
                player=player,
                is_captain=(i==0),
                is_wicket_keeper=(role=='WICKET_KEEPER')
            )
