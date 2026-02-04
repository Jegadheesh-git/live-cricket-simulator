from rest_framework import serializers
from .models import Match, Team, Player, PlayingSquad, Nationality, Tournament

class NationalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Nationality
        fields = ['id', 'name', 'code']

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ['id', 'code', 'name']

class PlayerSerializer(serializers.ModelSerializer):
    nationality = NationalitySerializer(read_only=True)
    
    class Meta:
        model = Player
        fields = [
            'id', 'first_name', 'middle_name', 'last_name', 'nick_name',
            'nationality', 'dob', 'gender',
            'height', 'weight', 'height_type',
            'role', 'batting_hand', 'bowling_hand', 'bowling_style',
            'batting_style', 'fielding_skill', 'wicket_keeping_skill',
            'batting_type', 'bowling_type'
        ]

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'logo_url']

class SquadPlayerSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    
    class Meta:
        model = PlayingSquad
        fields = ['player', 'is_captain', 'is_wicket_keeper']

class TeamSquadSerializer(serializers.ModelSerializer):
    squad = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'logo_url', 'squad']
        
    def get_squad(self, team_obj):
        # We need the match context to filter the squad correctly
        match = self.context.get('match')
        if match:
            squad_entries = PlayingSquad.objects.filter(team=team_obj, match=match)
            return SquadPlayerSerializer(squad_entries, many=True).data
        return []

class MatchSerializer(serializers.ModelSerializer):
    # We use a serializer method field or custom init to pass context to TeamSerializer if we want nested squad
    teams = serializers.SerializerMethodField()
    tournament = TournamentSerializer(read_only=True)
    toss_won_by = TeamSerializer(read_only=True)
    score = serializers.SerializerMethodField()
    matchId = serializers.IntegerField(source='id', read_only=True)
    matchName = serializers.SerializerMethodField()
    tournamentId = serializers.SerializerMethodField()
    tournamentName = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = [
            'id', 'matchId', 'matchName', 'tournament', 'tournamentId', 'tournamentName',
            'teams', 'date', 'venue', 'match_type', 'is_live', 'match_ended',
            'toss_won_by', 'opt_to', 'current_innings', 'score'
        ]

    def get_teams(self, obj):
        # Pass the match object in context so TeamSquadSerializer can find the specific squad
        return TeamSquadSerializer(obj.teams.all(), many=True, context={'match': obj}).data

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

    def get_matchName(self, obj):
        return f"Match {obj.id}"

    def get_tournamentId(self, obj):
        if obj.tournament:
            return obj.tournament.code
        return None

    def get_tournamentName(self, obj):
        if obj.tournament:
            return obj.tournament.name
        return None

class PlayingSquadSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    
    class Meta:
        model = PlayingSquad
        fields = ['match', 'team', 'player', 'is_captain', 'is_wicket_keeper']
