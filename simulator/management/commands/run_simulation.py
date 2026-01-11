import time
from django.core.management.base import BaseCommand
from simulator.models import Match
from simulator.services.engine import SimulationEngine

class Command(BaseCommand):
    help = 'Runs the cricket simulation loop for live matches'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Simulation Engine..."))
        engine = SimulationEngine()
        
        # Track last update time per match_id
        last_updates = {}
        
        while True:
            live_matches = Match.objects.filter(is_live=True, match_ended=False)
            
            if not live_matches.exists():
                # self.stdout.write("No live matches. Waiting...") # Too noisy
                time.sleep(1)
                continue
            
            now = time.time()
            
            for match in live_matches:
                last_update = last_updates.get(match.id, 0)
                
                if now - last_update >= match.seconds_per_ball:
                    # self.stdout.write(f"Simulating ball for Match {match.id}")
                    try:
                        engine.simulate_ball(match)
                        last_updates[match.id] = now
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error in Match {match.id}: {e}"))
            
            # Tick rate
            time.sleep(0.1)
