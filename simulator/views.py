from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.utils import timezone
from .models import Match, Tournament
from .serializers import MatchSerializer, TournamentSerializer

class LiveMatchesView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter matches that are live
        matches = Match.objects.filter(is_live=True).order_by('-date')
        serializer = MatchSerializer(matches, many=True)
        return Response({"data": serializer.data})

class MatchDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, match_id):
        try:
            match = Match.objects.get(id=match_id)
            serializer = MatchSerializer(match)
            return Response(serializer.data)
        except Match.DoesNotExist:
            return Response({"error": "Match not found"}, status=status.HTTP_404_NOT_FOUND)

class DebugLogView(APIView):
    def get(self, request):
        from .apps import global_debug_logs
        return Response(global_debug_logs)

class TournamentListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()

        live_tournaments = Tournament.objects.filter(matches__is_live=True, matches__match_ended=False).distinct()
        upcoming_tournaments = Tournament.objects.filter(
            matches__date__gt=now,
            matches__is_live=False,
            matches__match_ended=False
        ).distinct()

        return Response({
            "live": TournamentSerializer(live_tournaments, many=True).data,
            "upcoming": TournamentSerializer(upcoming_tournaments, many=True).data,
        })
