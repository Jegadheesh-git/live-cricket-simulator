from django.urls import path
from .views import LiveMatchesView, MatchDetailView, DebugLogView, TournamentListView
from .views_admin import DashboardView, CreateMatchView, MatchActionView

urlpatterns = [
    # Admin / Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('match/create/', CreateMatchView.as_view(), name='create-match'),
    path('match/<int:match_id>/<str:action>/', MatchActionView.as_view(), name='match-action'),

    # Public APIs
    path('matches/live', LiveMatchesView.as_view(), name='live-matches'),
    path('matches/<int:match_id>', MatchDetailView.as_view(), name='match-detail'),
    path('tournaments/', TournamentListView.as_view(), name='tournament-list'),
    path('debug-logs/', DebugLogView.as_view(), name='debug-logs'),
]
