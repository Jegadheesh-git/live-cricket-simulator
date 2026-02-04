from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.utils import timezone

from simulator.models import Match, Ball, InningsScore, Tournament
from simulator.services.generator import create_dummy_match, setup_match_squads, get_or_create_default_tournament
from simulator.services.engine import SimulationEngine


class LiveMatchFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass123")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_start_match_appears_in_live_list(self):
        match = create_dummy_match()
        setup_match_squads(match)

        start_resp = self.client.post(f"/api/v1/match/{match.id}/start/")
        self.assertEqual(start_resp.status_code, 200)

        live_resp = self.client.get("/api/v1/matches/live")
        self.assertEqual(live_resp.status_code, 200)

        data = live_resp.json().get("data", [])
        self.assertTrue(any(m["id"] == match.id for m in data))

    def test_pause_match_removed_from_live_list(self):
        match = create_dummy_match()
        setup_match_squads(match)
        match.is_live = True
        match.save()

        pause_resp = self.client.post(f"/api/v1/match/{match.id}/pause/")
        self.assertEqual(pause_resp.status_code, 200)

        live_resp = self.client.get("/api/v1/matches/live")
        data = live_resp.json().get("data", [])
        self.assertFalse(any(m["id"] == match.id for m in data))

    def test_reset_clears_scores_and_balls(self):
        match = create_dummy_match()
        setup_match_squads(match)
        match.is_live = True
        match.save()

        engine = SimulationEngine()
        engine.simulate_ball(match)
        engine.simulate_ball(match)

        self.assertGreater(Ball.objects.filter(match=match).count(), 0)

        reset_resp = self.client.post(f"/api/v1/match/{match.id}/reset/")
        self.assertEqual(reset_resp.status_code, 200)

        self.assertEqual(Ball.objects.filter(match=match).count(), 0)
        self.assertEqual(InningsScore.objects.filter(match=match).count(), 0)

    def test_speed_change(self):
        match = create_dummy_match()
        setup_match_squads(match)

        resp = self.client.post(
            f"/api/v1/match/{match.id}/speed/",
            {"seconds_per_ball": 0.5},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        match.refresh_from_db()
        self.assertEqual(match.seconds_per_ball, 0.5)


class SimulationEngineTests(TestCase):
    def test_simulation_creates_ball_and_score(self):
        match = create_dummy_match()
        setup_match_squads(match)
        match.is_live = True
        match.save()

        engine = SimulationEngine()
        engine.simulate_ball(match)

        self.assertEqual(Ball.objects.filter(match=match).count(), 1)
        score = InningsScore.objects.filter(match=match, innings=1).first()
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score.total_runs, 0)


class TournamentEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="tester", password="pass123")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_tournament_list_live_and_upcoming(self):
        tournament = get_or_create_default_tournament()
        live_match = create_dummy_match()
        setup_match_squads(live_match)
        live_match.tournament = tournament
        live_match.is_live = True
        live_match.save()

        upcoming_match = create_dummy_match()
        setup_match_squads(upcoming_match)
        upcoming_match.tournament = tournament
        upcoming_match.is_live = False
        upcoming_match.date = timezone.now() + timezone.timedelta(days=2)
        upcoming_match.save()

        resp = self.client.get("/api/v1/tournaments/")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn("live", payload)
        self.assertIn("upcoming", payload)
        self.assertTrue(any(t["code"] == tournament.code for t in payload["live"]))
