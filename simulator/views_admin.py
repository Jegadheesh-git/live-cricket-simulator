from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect, get_object_or_404
from .models import Match, Team, Ball, InningsScore, BattingScore, BowlingScore, PlayingSquad
from .services.generator import create_dummy_match, setup_match_squads

class DashboardView(TemplateView):
    template_name = "simulator/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['matches'] = Match.objects.all().order_by('-date')
        return context

class CreateMatchView(View):
    def post(self, request):
        match = create_dummy_match()
        setup_match_squads(match)
        return redirect('dashboard')

from .models import Match, Team, Ball, InningsScore, BattingScore, BowlingScore, PlayingSquad

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class MatchActionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, match_id, action):
        match = get_object_or_404(Match, id=match_id)
        
        if action == 'start':
            match.is_live = True
            match.match_ended = False
            match.save()
            msg = "Match Started"
        elif action == 'pause':
            match.is_live = False
            match.save()
            msg = "Match Paused"
        elif action == 'reset':
            match.is_live = False
            match.match_ended = False
            match.current_innings = 1
            match.toss_won_by = None
            match.opt_to = None
            
            # Delete Related Data
            Ball.objects.filter(match=match).delete()
            InningsScore.objects.filter(match=match).delete()
            BattingScore.objects.filter(match=match).delete()
            BowlingScore.objects.filter(match=match).delete()
            
            match.save()
            msg = "Match Reset"
        elif action == 'speed':
            try:
                speed = float(request.data.get('seconds_per_ball', 1.0))
                match.seconds_per_ball = speed
                match.save()
                msg = f"Speed set to {speed}"
            except ValueError:
                msg = "Invalid speed"
            
        return Response({"status": "success", "message": msg})
