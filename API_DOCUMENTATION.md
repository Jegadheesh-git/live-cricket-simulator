# Live Cricket Simulator - API Documentation

## Overview
This API allows broadcast solutions to fetch live cricket match data and subscribe to real-time ball-by-ball updates via WebSockets.

**Base URL**: `https://live-cricket-simulator.onrender.com/api/v1`
**WebSocket URL**: `wss://live-cricket-simulator.onrender.com/ws/matches/<match_id>/`

---

## Authentication
All API requests require a **Token**.

### HTTP Headers
Include the `Authorization` header in all HTTP requests:
```http
Authorization: Token <YOUR_TOKEN>
```

### WebSocket Query Parameter
Include the `token` query parameter in the WebSocket URL:
```text
wss://.../ws/matches/1/?token=<YOUR_TOKEN>
```

---

## 1. Live Data APIs (HTTP)

### Get Live Matches
Returns a list of all currently active matches.

- **Endpoint**: `/matches/live`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "data": [
      {
        "tournamentId": "tour123",
        "tournamentName": "IPL",
        "matchId": 1,
        "matchName": "Match 1",
        "id": 1,
        "teams": [
          {"id": 1, "name": "Team A", "short_name": "TMA"},
          {"id": 2, "name": "Team B", "short_name": "TMB"}
        ],
        "is_live": true,
        "score": {
          "runs": 45,
          "wickets": 2,
          "overs": 5.4
        }
      }
    ]
  }
  ```

### Get Match Details
Returns full details for a specific match.

- **Endpoint**: `/matches/<match_id>`
- **Method**: `GET`
- **Response**: Returns match object (similar to above but with more detail if applicable).

---

## 2. Real-Time Streaming (WebSocket)

Connect to the WebSocket to receive instant updates whenever a ball is simulated.

- **URL**: `wss://live-cricket-simulator.onrender.com/ws/matches/<match_id>/?token=<YOUR_TOKEN>`

### Events
The server sends JSON messages. The primary event is `BALL_UPDATE`.

**Payload Example:**
```json
{
  "type": "BALL_UPDATE",
  "ball": {
    "ball": 4,          // Ball number in over (1-6)
    "over": 5,          // Current over number
    "bowler": "Bowler Name",
    "batsman": "Batsman Name",
    "runs": 4,          // Runs scored on this ball
    "is_wicket": false,
    "commentary": "Four runs!"
  },
  "score": {
    "runs": 49,
    "wickets": 2,
    "overs": 5.4,
    "team_id": 1
  }
}
```

---

## 3. Remote Control APIs
These endpoints allow you to control the simulation programmatically.

| Action | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Start** | `/match/<id>/start/` | `POST` | Starts the simulation loop. |
| **Pause** | `/match/<id>/pause/` | `POST` | Pauses the simulation. |
| **Reset** | `/match/<id>/reset/` | `POST` | **Destructive**. Clears all score data & resets match to 0-0. |
| **Speed** | `/match/<id>/speed/` | `POST` | Set simulation speed. Body: `{"seconds_per_ball": 1.0}` |

### Control Example (Restart Match)
```bash
curl -X POST https://live-cricket-simulator.onrender.com/api/v1/match/1/reset/ \
  -H "Authorization: Token <YOUR_TOKEN>"

curl -X POST https://live-cricket-simulator.onrender.com/api/v1/match/1/start/ \
  -H "Authorization: Token <YOUR_TOKEN>"
```

---

## 4. Debugging
If you suspect the server is inactive, you can check the logs.

- **Endpoint**: `/debug-logs/`
- **Method**: `GET`
- **Response**: List of recent server logs (Simulation Loop activity).

---

## 5. Tournaments
Fetch live and upcoming tournaments for tournament pass features.

- **Endpoint**: `/tournaments/`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "live": [
      {"id": 1, "code": "tour123", "name": "IPL"}
    ],
    "upcoming": [
      {"id": 2, "code": "tour124", "name": "BBL"}
    ]
  }
  ```
