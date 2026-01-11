from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import Match
from .serializers import MatchSerializer

class LiveMatchesView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter matches that are live
        matches = Match.objects.filter(is_live=True).order_by('-date')
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data)

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
