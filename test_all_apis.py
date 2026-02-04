import requests
import json
import time

BASE_URL = "https://live-cricket-simulator.onrender.com/api/v1"
TOKEN = "b71b5cf35520a80447d2fe98e666d1c7ff47112c"
HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Content-Type": "application/json"
}
MATCH_ID = 1

def log(name, status, response):
    icon = "✅" if status else "❌"
    print(f"{icon} {name}")
    print(f"   Status: {response.status_code}")
    try:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"   Response: {response.text}")
    print("-" * 40)

def test_apis():
    print(f"🚀 Starting API Tests on {BASE_URL}...\n")

    # 1. List Live Matches
    print("1. Testing List Live Matches...")
    resp = requests.get(f"{BASE_URL}/matches/live", headers=HEADERS)
    log("List Live Matches", resp.status_code == 200, resp)

    # 2. Get Match Detail
    print("2. Testing Get Match Detail...")
    resp = requests.get(f"{BASE_URL}/matches/{MATCH_ID}", headers=HEADERS)
    log("Get Match Detail", resp.status_code == 200, resp)

    # 3. Create/Reset (To ensure clean state)
    print("3. Testing Reset Match...")
    resp = requests.post(f"{BASE_URL}/match/{MATCH_ID}/reset/", headers=HEADERS)
    log("Reset Match", resp.status_code == 200, resp)

    # 4. Set Speed
    print("4. Testing Set Speed (to 0.5s)...")
    payload = {"seconds_per_ball": 0.5}
    resp = requests.post(f"{BASE_URL}/match/{MATCH_ID}/speed/", headers=HEADERS, json=payload)
    log("Set Speed", resp.status_code == 200, resp)

    # 5. Start Match
    print("5. Testing Start Match...")
    resp = requests.post(f"{BASE_URL}/match/{MATCH_ID}/start/", headers=HEADERS)
    log("Start Match", resp.status_code == 200, resp)

    # 6. Pause Match
    print("6. Testing Pause Match...")
    resp = requests.post(f"{BASE_URL}/match/{MATCH_ID}/pause/", headers=HEADERS)
    log("Pause Match", resp.status_code == 200, resp)
    
    # 7. Start Again (to leave it running)
    print("7. Restarting Match...")
    resp = requests.post(f"{BASE_URL}/match/{MATCH_ID}/start/", headers=HEADERS)
    log("Restart Match", resp.status_code == 200, resp)

    # 8. Filter by Live again
    print("8. Verifying Live Status...")
    resp = requests.get(f"{BASE_URL}/matches/live", headers=HEADERS)
    data = resp.json().get("data", [])
    is_present = any(m['id'] == MATCH_ID for m in data)
    print(f"   Match {MATCH_ID} in Live List: {is_present}")
    log("Verify Live List", is_present, resp)

    # 9. Debug Logs
    print("9. Fetching Debug Logs...")
    resp = requests.get(f"{BASE_URL}/debug-logs/", headers=HEADERS)
    log("Debug Logs", resp.status_code == 200, resp)

if __name__ == "__main__":
    test_apis()
