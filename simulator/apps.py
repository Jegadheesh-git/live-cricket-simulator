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
        import sys
        import os
        import threading
        
        # Robust check: Are we running a server? (Runserver or Daphne)
        is_server = 'daphne' in sys.argv[0] or 'runserver' in sys.argv or os.environ.get('RUN_MAIN') == 'true'
        
        if not is_server:
            # We are likely running migration or collectstatic, do not start simulation/init
            return

        from django.core.management import call_command
        import time
        
        def run_startup_tasks():
            # Wait a bit for DB to be configured
            time.sleep(5)
            try:
                print("Running startup tasks (Admin Init + Simulation)...")
                call_command('init_admin')
                start_simulation_loop()
            except Exception as e:
                print(f"Startup Error: {e}")

        # Ensure we don't start multiple threads if ready() is called twice
        if not any(t.name == "StartupThread" for t in threading.enumerate()):
             thread = threading.Thread(target=run_startup_tasks, name="StartupThread", daemon=True)
             thread.start()
