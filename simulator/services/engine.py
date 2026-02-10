import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction, models
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from simulator.models import Match, Team, Player, Ball, InningsScore, BattingScore, BowlingScore, PlayingSquad

class SimulationEngine:
    def __init__(self):
        pass

    def simulate_ball(self, match):
        """
        Main entry point to simulate a single ball for a match.
        """
        if match.match_ended or not match.is_live:
            return

        with transaction.atomic():
            # Reload match to lock it or ensure fresh data? 
            # For now, just trust the object passed or re-fetch if needed.
            # match.refresh_from_db() 
            
            innings_score, created = InningsScore.objects.get_or_create(
                match=match, 
                team=self._get_batting_team(match),
                innings=match.current_innings
            )

            # Check if innings over
            if innings_score.is_completed:
                self._handle_innings_break(match, innings_score)
                return

            # Calculate current over/ball before outcome
            legal_balls = Ball.objects.filter(match=match, innings=match.current_innings, is_wide=False, is_no_ball=False).count()
            over_number = legal_balls // 6
            ball_number = (legal_balls % 6) + 1

            # Determine Outcome
            outcome = self._determine_outcome(match, innings_score, over_number, ball_number)

            # Get Context (Striker, Bowler, etc.)
            striker, non_striker = self._get_current_batters(match, innings_score)
            bowler = self._get_current_bowler(match, innings_score)

            if not striker or not bowler:
                print(f"Match {match.id}: Not enough players to continue.")
                # Maybe stop simulation?
                match.is_live = False
                match.save()
                return

            # Calculate Runs/Extras
            runs_batter = outcome['runs']
            extras = outcome['extras']
            total_runs = runs_batter + extras
            is_wicket = outcome['is_wicket']
            
            # Create Ball
            ball = Ball.objects.create(
                match=match,
                innings=match.current_innings,
                over_number=over_number,
                ball_number=ball_number,
                striker=striker,
                non_striker=non_striker,
                bowler=bowler,
                runs_batter=runs_batter,
                extras=extras,
                total_runs=total_runs,
                is_wide=outcome['is_wide'],
                is_no_ball=outcome['is_no_ball'],
                is_wicket=is_wicket,
                dismissal_type=outcome['dismissal_type'] if is_wicket else None,
                dismissed_player=striker if is_wicket else None # Simple: striker always out
            )

            # Update Scores
            self._update_innings_score(innings_score, total_runs, is_wicket, outcome)
            self._update_batting_score(match, striker, runs_batter, is_wicket)
            self._update_bowling_score(match, bowler, total_runs, is_wicket, outcome)
            
            # Handle Wicket (Swap striker/new bat) - Implicitly handled by _get_current_batters next time?
            # No, we need to mark the batter as out in BattingScore so _get_current_batters picks a NEW one.
            
            # Handle Over End (Swap Ends?) - Logic for finding striker needs to know who is on strike.
            # Complex. For MVP:
            # - We need to track who is on strike. 
            # - Simpler: Just randomise who faces next if it's an odd run? 
            # - Better: Store 'on_strike_player' in a cache or deduce it.
            # - Let's deduce:
            #   If runs are odd -> Swap.
            #   If over ends -> Swap.
            #   We need to persist this state. 
            #   Phase 4 MVP: Randomly pick one of the two active batters to be striker? 
            #   No, that's too chaotic.
            #   Let's rely on LAST ball.
            
            self._handle_strike_rotation(match, ball, striker, non_striker)

            # Check for Innings/Match End conditions
            if innings_score.total_wickets >= 10:
                innings_score.is_completed = True
                innings_score.save()
                self._handle_innings_break(match, innings_score)

            # Ensure new batter is created after wicket for payload completeness
            self._get_current_batters(match, innings_score)

            # Broadcast Event
            channel_layer = get_channel_layer()
            extra_type = None
            if ball.is_wide:
                extra_type = "WIDE"
            elif ball.is_no_ball:
                extra_type = "NO_BALL"
            elif ball.is_bye:
                extra_type = "BYE"
            elif ball.is_leg_bye:
                extra_type = "LEG_BYE"

            batsmen_payload = self._build_batsmen_payload(match)
            bowler_payload = self._build_bowler_payload(match, bowler)
            partnership_payload = self._build_partnership_payload(match)
            fall_of_wickets_payload = self._build_fall_of_wickets(match)
            last_6_balls_payload = self._build_last_6_balls(match)

            legal_balls_after = Ball.objects.filter(match=match, innings=match.current_innings, is_wide=False, is_no_ball=False).count()
            overs_float = legal_balls_after / 6 if legal_balls_after > 0 else 0
            run_rate = (innings_score.total_runs / overs_float) if overs_float > 0 else 0

            payload = {
                'type': 'BALL_UPDATE',
                'matchId': match.id,
                'ball': {
                    'over': ball.over_number,
                    'ball': ball.ball_number,
                    'runs': ball.runs_batter,
                    'extras': ball.extras,
                    'extra_type': extra_type,
                    'is_wicket': ball.is_wicket,
                    'dismissal': ball.dismissal_type,
                    'striker_id': striker.id,
                    'non_striker_id': non_striker.id,
                    'bowler_id': bowler.id,
                },
                'score': {
                    'team_id': innings_score.team.id,
                    'runs': innings_score.total_runs,
                    'wickets': innings_score.total_wickets,
                    'overs': innings_score.total_overs,
                    'run_rate': round(run_rate, 2),
                    'required_run_rate': None,
                }
                ,
                'batsmen': batsmen_payload,
                'bowler': bowler_payload,
                'partnership': partnership_payload,
                'fall_of_wickets': fall_of_wickets_payload,
                'last_6_balls': last_6_balls_payload,
            }
            async_to_sync(channel_layer.group_send)(
                f'match_{match.id}',
                {
                    'type': 'match_update',
                    'payload': payload
                }
            )

    def _determine_outcome(self, match, innings_score, over_number, ball_number):
        # Weighted Random
        choices = [
            {'runs': 0, 'extras': 0, 'is_wicket': False, 'is_wide': False, 'is_no_ball': False}, # Dot
            {'runs': 1, 'extras': 0, 'is_wicket': False, 'is_wide': False, 'is_no_ball': False}, # Single
            {'runs': 2, 'extras': 0, 'is_wicket': False, 'is_wide': False, 'is_no_ball': False}, # Double
            {'runs': 4, 'extras': 0, 'is_wicket': False, 'is_wide': False, 'is_no_ball': False}, # Four
            {'runs': 6, 'extras': 0, 'is_wicket': False, 'is_wide': False, 'is_no_ball': False}, # Six
            {'runs': 0, 'extras': 0, 'is_wicket': True,  'is_wide': False, 'is_no_ball': False, 'dismissal_type': 'CAUGHT'}, # Wicket
            {'runs': 0, 'extras': 1, 'is_wicket': False, 'is_wide': True,  'is_no_ball': False}, # Wide
        ]
        weights = [40, 30, 5, 8, 4, 3, 2] # Probabilities

        # Encourage wickets between overs 3-5 (inclusive)
        if 3 <= over_number <= 5:
            weights = [38, 29, 5, 8, 4, 8, 2]
        return random.choices(choices, weights=weights, k=1)[0]

    def _get_batting_team(self, match):
        # T20: Innings 1 -> Toss Winner (if Bat) or Loser (if Bowl)
        # Simplified: Just grab teams[0] for inn 1, teams[1] for inn 2
        teams = list(match.teams.all())
        if match.current_innings == 1:
            return teams[0]
        else:
            return teams[1]

    def _get_bowling_team(self, match):
        teams = list(match.teams.all())
        if match.current_innings == 1:
            return teams[1]
        else:
            return teams[0]

    def _get_current_batters(self, match, innings_score):
        # Find 2 batters who are NOT out and have BattingScores or need new ones.
        # Get existing scores
        scores = BattingScore.objects.filter(match=match, innings=match.current_innings)
        active_scores = scores.filter(is_out=False)
        
        active_batters = [s.player for s in active_scores]
        
        # If less than 2, pick new ones
        needed = 2 - len(active_batters)
        if needed > 0:
            team = innings_score.team
            squad = PlayingSquad.objects.filter(match=match, team=team).select_related('player')
            existing_ids = [s.player.id for s in scores]
            candidates = [sq.player for sq in squad if sq.player.id not in existing_ids] # Order by squad id implicitly or random?
            
            # Simple Sort: Captain/WK or just ID
            new_batters = candidates[:needed]
            
            for player in new_batters:
                # If this is the FIRST/Opening pair, set first one as strike?
                is_strike = (len(active_batters) == 0) and (active_scores.count() == 0) # Very first batter
                # Or if we just got out, and we need a replacement, does he take strike?
                # Check logic in _handle_strike_rotation: w/ Wicket Striker, we clear flags.
                # So if no one is on strike, the NEW guy takes strike?
                # If we have 1 active (NonStriker) who is NOT on strike, new guy MUST be on strike.
                
                check_strike = False
                if not active_scores.filter(is_on_strike=True).exists():
                     # No one currently on strike.
                     # If there is another batter, is he off strike?
                     other = active_scores.first()
                     if other and not other.is_on_strike:
                         check_strike = True
                     elif not other:
                         # Opening pair: First guy strike
                         if len(active_batters) == 0: 
                             check_strike = True
                             
                s = BattingScore.objects.create(match=match, player=player, innings=match.current_innings, is_on_strike=check_strike)
                active_batters.append(player)
        
        if len(active_batters) < 2:
            return None, None
            
        # Determine Striker vs Non-Striker
        # We need the objects again to check flags
        p1 = active_batters[0]
        p2 = active_batters[1]
        
        s1 = BattingScore.objects.get(match=match, player=p1, innings=match.current_innings)
        s2 = BattingScore.objects.get(match=match, player=p2, innings=match.current_innings)
        
        if s1.is_on_strike:
            return p1, p2
        elif s2.is_on_strike:
            return p2, p1
        else:
            # Fallback: Default p1 strike
            s1.is_on_strike = True
            s1.save()
            return p1, p2

    def _get_current_bowler(self, match, innings_score):
        # Bowling team
        team = self._get_bowling_team(match)
        squad = PlayingSquad.objects.filter(match=match, team=team).select_related('player')
        
        # Logic: Pick a bowler. Simplified: Random from BOWLERS/ALL_ROUNDERS
        bowlers = [sq.player for sq in squad if sq.player.role in ['BOWLER', 'ALL_ROUNDER']]
        if not bowlers:
             bowlers = [sq.player for sq in squad] # fallback
        
        return random.choice(bowlers)

    def _update_innings_score(self, score, runs, is_wicket, outcome):
        score.total_runs += runs
        score.extra_runs += outcome['extras']
        if is_wicket:
            score.total_wickets += 1
        
        # Overs update logic: 
        # Float is tricky (0.5 + 0.1 = 0.6 -> 1.0). 
        # Re-calc from DB is safer.
        legal_balls = Ball.objects.filter(match=score.match, innings=score.innings, is_wide=False, is_no_ball=False).count()
        overs = legal_balls // 6
        balls = legal_balls % 6
        score.total_overs = float(f"{overs}.{balls}")
        score.save()

    def _update_batting_score(self, match, player, runs, is_out):
        score, _ = BattingScore.objects.get_or_create(match=match, player=player, innings=match.current_innings)
        score.runs += runs
        score.balls_faced += 1
        if runs == 4:
            score.fours += 1
        elif runs == 6:
            score.sixes += 1
        
        if is_out:
            score.is_out = True
            score.dismissal_text = "Caught" # Stub
        
        if score.balls_faced > 0:
            score.strike_rate = (score.runs / score.balls_faced) * 100
        score.save()

    def _update_bowling_score(self, match, player, runs_conceded, is_wicket, outcome):
        score, _ = BowlingScore.objects.get_or_create(match=match, player=player, innings=match.current_innings)
        score.runs_conceded += runs_conceded
        if is_wicket:
            score.wickets += 1
        
        # Update overs bowled by THIS bowler
        legal_balls = Ball.objects.filter(match=match, innings=match.current_innings, bowler=player, is_wide=False, is_no_ball=False).count()
        overs = legal_balls // 6
        balls = legal_balls % 6
        score.overs = float(f"{overs}.{balls}")
        
        if score.overs > 0:
             # Economy = Runs / Overs (Roughly)
             # Exact: Runs / (LegalBalls/6)
             total_overs = legal_balls / 6
             score.economy = score.runs_conceded / total_overs if total_overs > 0 else 0
        
        score.save()

    def _handle_strike_rotation(self, match, ball, striker, non_striker):
        # Determine who should be on strike next
        # If runs are odd (1, 3, 5), they swap.
        # If over ends (6 legal balls), they swap (after the runs swap).
        
        swap_ends = (ball.runs_batter % 2 != 0)
        
        # Check Over End
        legal_balls = Ball.objects.filter(match=match, innings=match.current_innings, is_wide=False, is_no_ball=False).count()
        over_complete = (legal_balls % 6 == 0) and (legal_balls > 0)
        
        if over_complete:
            swap_ends = not swap_ends
            
        # If swap_ends is True, the NON-STRIKER becomes the striker for next ball.
        # If False, the STRIKER remains.
        
        # Update is_on_strike flags
        # Reset all active batters to False first (safer)
        BattingScore.objects.filter(match=match, innings=match.current_innings, is_out=False).update(is_on_strike=False)
        
        if swap_ends:
            # Non-striker becomes striker
            # We need to find the non-striker's BattingScore
            new_striker = non_striker
        else:
            # Striker remains striker (unless out?)
            # If striker is OUT, then the NEW batter will be on strike?
            # Or does the new batter take the specific end?
            # Standard rule: 
            # If Caught: New batter comes to the end of the dismissed batter.
            # If crossed: (Not implementing cross logic on catch yet).
            # If Bowled/LBW: Striker's end.
            
            # If Wicket: 
            # The dismissed player is already marked Out.
            # The new player will be created/fetched in next _get_current_batters.
            # Who is on strike? 
            # If it was a wicket, the rule depends. 
            # Simplified: New batter is always on strike if it was strike's wicket.
            # If runout at non-striker end: Striker remains on strike (if no run taken).
            
            # Let's simplify: 
            # If Wicket (Striker): New batter is On Strike.
            # If Wicket (Non-Striker): Striker remains On Strike.
            
            if ball.is_wicket and ball.dismissed_player == striker:
                # Striker is out. New batter (not yet assigned) will be On Strike.
                # We can't set is_on_strike for a player who doesn't exist yet.
                # But existing non-striker should NOT be on strike.
                BattingScore.objects.filter(match=match, player=non_striker, innings=match.current_innings).update(is_on_strike=False)
                return # Next loop will pick new batter and set valid flags? No, we need to enforce on-strike for the new one.
                # Actually, if we set non-striker=False, the logic in _get_current_batters needs to default the NEW guy to True.
                pass
            else:
                 new_striker = striker

        # Set new striker to True
        if not (ball.is_wicket and ball.dismissed_player == striker):
             BattingScore.objects.filter(match=match, player=new_striker, innings=match.current_innings).update(is_on_strike=True)

    def _handle_innings_break(self, match, innings_score):
        if match.current_innings == 1:
            match.current_innings = 2
            match.save()
            print(f"Match {match.id}: Innings 1 Complete. Starting Innings 2.")
        else:
            match.match_ended = True
            match.is_live = False
            match.save()
            print(f"Match {match.id}: Match Completed.")

    def _build_batsmen_payload(self, match):
        scores = BattingScore.objects.filter(match=match, innings=match.current_innings, is_out=False)
        payload = []
        for s in scores:
            payload.append({
                'player_id': s.player.id,
                'runs': s.runs,
                'balls': s.balls_faced,
                'fours': s.fours,
                'sixes': s.sixes,
                'strike_rate': round(s.strike_rate, 2),
                'on_strike': s.is_on_strike,
            })
        return payload

    def _build_bowler_payload(self, match, bowler):
        score = BowlingScore.objects.filter(match=match, innings=match.current_innings, player=bowler).first()
        if not score:
            return {
                'player_id': bowler.id,
                'overs': 0.0,
                'maidens': 0,
                'runs_conceded': 0,
                'wickets': 0,
                'economy': 0.0,
            }
        return {
            'player_id': bowler.id,
            'overs': score.overs,
            'maidens': score.maidens,
            'runs_conceded': score.runs_conceded,
            'wickets': score.wickets,
            'economy': round(score.economy, 2),
        }

    def _build_partnership_payload(self, match):
        last_wicket_ball = Ball.objects.filter(
            match=match, innings=match.current_innings, is_wicket=True
        ).order_by('-id').first()

        balls_qs = Ball.objects.filter(match=match, innings=match.current_innings)
        if last_wicket_ball:
            balls_qs = balls_qs.filter(id__gt=last_wicket_ball.id)

        runs = balls_qs.aggregate(total=models.Sum('total_runs')).get('total') or 0
        balls = balls_qs.filter(is_wide=False, is_no_ball=False).count()

        return {'runs': runs, 'balls': balls}

    def _build_fall_of_wickets(self, match):
        balls = Ball.objects.filter(match=match, innings=match.current_innings).order_by('id')
        fall = []
        total = 0
        wickets = 0
        for b in balls:
            total += b.total_runs
            if b.is_wicket:
                wickets += 1
                fall.append({
                    'score': total,
                    'wicket': wickets,
                    'player_id': b.dismissed_player.id if b.dismissed_player else None,
                    'over': float(f"{b.over_number}.{b.ball_number}"),
                })
        return fall

    def _build_last_6_balls(self, match):
        balls = Ball.objects.filter(match=match, innings=match.current_innings).order_by('-id')[:6]
        payload = []
        for b in reversed(list(balls)):
            payload.append({
                'over': float(f"{b.over_number}.{b.ball_number}"),
                'runs': b.total_runs,
            })
        return payload
