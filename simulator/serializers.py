from rest_framework import serializers
from .models import Match, Team, Player, PlayingSquad

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'logo_url']

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'first_name', 'last_name', 'role', 'batting_hand', 'bowling_style']

class MatchSerializer(serializers.ModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)
    toss_won_by = TeamSerializer(read_only=True)
    score = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = [
            'id', 'teams', 'date', 'match_type', 'is_live', 'match_ended', 
            'toss_won_by', 'opt_to', 'current_innings', 'score'
        ]

    def get_score(self, obj):
        from .models import InningsScore
        score = InningsScore.objects.filter(match=obj, innings=obj.current_innings).first()
        if score:
            return {
                'runs': score.total_runs,
                'wickets': score.total_wickets,
                'overs': score.total_overs,
                'team_id': score.team.id
            }
        return {}

class PlayingSquadSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    
    class Meta:
        model = PlayingSquad
        fields = ['match', 'team', 'player', 'is_captain', 'is_wicket_keeper']
