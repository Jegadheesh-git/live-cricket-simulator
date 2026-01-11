import threading
import time
import os
from django.apps import AppConfig

def start_simulation_loop():
    # Deferred import to avoid registry not ready issues
    from simulator.models import Match
    from simulator.services.engine import SimulationEngine

    # Wait for DB to be potentially ready
    time.sleep(2)
    
    engine = SimulationEngine()
    last_updates = {}
    print("Background Simulation Loop Started")

    while True:
        try:
            # Check for generic stop signal if needed (e.g. file existence)
            # For now, infinite loop daemon
            
            # We must wrap DB access in try/except or ensure connection validity
            # but Django usually handles persistent connection in threads okay-ish
            # if we close old ones.
            from django.db import connection
            connection.close_if_unusable_or_obsolete()
            
            live_matches = Match.objects.filter(is_live=True, match_ended=False)
            
            if not live_matches.exists():
                # print("No live matches...")
                time.sleep(1)
                continue
            
            now = time.time()
            for match in live_matches:
                # print(f"Checking Match {match.id}")
                last_update = last_updates.get(match.id, 0)
                if now - last_update >= match.seconds_per_ball:
                    print(f"Simulating ball for Match {match.id}")
                    engine.simulate_ball(match)
                    last_updates[match.id] = now
            
            time.sleep(0.1)
        except Exception as e:
            print(f"Simulation Loop Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)

class SimulatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simulator'

    def ready(self):
        # Only start if runserver or daphne is running (prevent during migrate/collectstatic)
        # However, checking 'runserver' in argv is unreliable.
        # But for 'daphne', we can check process name or env?
        # Let's just check if we are in the main process.
        
        if os.environ.get('RUN_MAIN') or os.environ.get('DAPHNE_SERVER'):
            # Only run in the reloader process or if specifically flagged
            # Actually, standard runserver uses RUN_MAIN=true for the child process.
            # Daphne doesn't set RUN_MAIN standardly unless using --noreload maybe?
            # Let's just try starting it. Thread is daemon, so it dies with main.
            pass
        
        # Avoid double start
        if not any(t.name == "SimulationThread" for t in threading.enumerate()):
            t = threading.Thread(target=start_simulation_loop, name="SimulationThread", daemon=True)
            t.start()
