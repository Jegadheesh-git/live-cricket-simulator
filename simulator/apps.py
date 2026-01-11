import threading
import time
import os
from django.apps import AppConfig

global_debug_logs = []

def log_debug(msg):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    global_debug_logs.append(entry)
    if len(global_debug_logs) > 100:
        global_debug_logs.pop(0)

def start_simulation_loop():
    # Deferred import to avoid registry not ready issues
    from simulator.models import Match
    from simulator.services.engine import SimulationEngine

    # Wait for DB to be potentially ready
    time.sleep(2)
    
    engine = SimulationEngine()
    last_updates = {}
    engine = SimulationEngine()
    last_updates = {}
    log_debug("Background Simulation Loop Started")

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
                # log_debug(f"Checking Match {match.id}")
                last_update = last_updates.get(match.id, 0)
                if now - last_update >= match.seconds_per_ball:
                    log_debug(f"Simulating ball for Match {match.id}")
                    engine.simulate_ball(match)
                    last_updates[match.id] = now
            
            time.sleep(0.1)
        except Exception as e:
            log_debug(f"Simulation Loop Error: {e}")
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
        
        # Robust check: Used defined Environment Variable
        should_run_jobs = str(os.environ.get('RUN_JOBS', '')).lower() == 'true'
        
        log_debug(f"App Ready. RUN_JOBS={should_run_jobs} (Raw: {os.environ.get('RUN_JOBS')})")
        
        if not should_run_jobs:
            # We are likely running migration or collectstatic, or not the main node
            return

        from django.core.management import call_command
        import time
        
        def run_startup_tasks():
            # Wait a bit for DB to be configured
            time.sleep(5)
            try:
                log_debug("Running startup tasks (Admin Init + Simulation)...")
                call_command('init_admin')
                start_simulation_loop()
            except Exception as e:
                log_debug(f"Startup Error: {e}")

        # Ensure we don't start multiple threads if ready() is called twice
        if not any(t.name == "StartupThread" for t in threading.enumerate()):
             thread = threading.Thread(target=run_startup_tasks, name="StartupThread", daemon=True)
             thread.start()
