import asyncio
import websockets
import json
import sys

TOKEN = "b71b5cf35520a80447d2fe98e666d1c7ff47112c"
BASE_URL = "live-cricket-simulator.onrender.com"

async def test_live_feed(match_id):
    uri = f"wss://{BASE_URL}/ws/matches/{match_id}/?token={TOKEN}"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for 10 balls...")
            count = 0
            while count < 10:
                message = await websocket.recv()
                data = json.loads(message)
                
                # Filter for BALL_UPDATE to be specific, or just print everything
                if data.get('type') == 'BALL_UPDATE':
                    count += 1
                    ball = data['ball']
                    score = data['score']
                    print(f"[{count}/10] {ball['over']}.{ball['ball']} - Runs: {ball['runs']} | Score: {score['runs']}/{score['wickets']} ({score['overs']})")
                else:
                    print(f"Received Event: {data.get('type')}")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_remote_ws.py <match_id>")
        sys.exit(1)
    
    match_id = sys.argv[1]
    asyncio.run(test_live_feed(match_id))
