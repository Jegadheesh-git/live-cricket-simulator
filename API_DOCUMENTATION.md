# Live Cricket Simulator - API Documentation

## Overview
This API allows broadcast solutions to fetch live cricket match data, control simulations, and subscribe to real-time ball-by-ball updates via WebSockets.

Base URL: `https://live-cricket-simulator.onrender.com/api/v1`
WebSocket URL: `wss://live-cricket-simulator.onrender.com/ws/matches/<match_id>/`

---

## Authentication
All API requests require a token (TokenAuth).

HTTP header:
```http
Authorization: Token <YOUR_TOKEN>
```

WebSocket query parameter:
```
wss://.../ws/matches/<match_id>/?token=<YOUR_TOKEN>
```

---

## Data Models (Response Shape)

### Tournament
```json
{
  "id": 1,
  "code": "tour123",
  "name": "IPL"
}
```

### Match (Live List Item)
```json
{
  "tournamentId": "tour123",
  "tournamentName": "IPL",
  "matchId": 2,
  "matchName": "Match 2",
  "id": 2,
  "teams": [
    {
      "id": 3,
      "name": "Jessicabury Wheats",
      "short_name": "JW71",
      "logo_url": null,
      "squad": [
        {
          "player": {
            "id": 119,
            "first_name": "Mike",
            "middle_name": null,
            "last_name": "Ferguson",
            "nick_name": null,
            "nationality": null,
            "dob": null,
            "gender": "M",
            "height": null,
            "weight": null,
            "height_type": null,
            "role": "BATSMAN",
            "batting_hand": "LEFT",
            "bowling_hand": "RIGHT",
            "bowling_style": "FAST",
            "batting_style": null,
            "fielding_skill": null,
            "wicket_keeping_skill": null,
            "batting_type": null,
            "bowling_type": null
          },
          "is_captain": true,
          "is_wicket_keeper": false
        }
      ]
    }
  ],
  "status": "LIVE",
  "score": {
    "runs": 24,
    "wickets": 1,
    "overs": 4,
    "team_id": 3
  },
  "venue": null,
  "date": "2026-01-11T17:01:40.743499Z",
  "match_type": "T20",
  "is_live": true,
  "match_ended": false,
  "toss_won_by": null,
  "opt_to": null,
  "current_innings": 1
}
```

---

## Endpoints (HTTP)

### 1. Get Live Matches
Returns all currently live matches.

Endpoint: `/matches/live`
Method: `GET`

Response:
```json
{
  "data": [
    {
      "tournamentId": "tour123",
      "tournamentName": "IPL",
      "matchId": 2,
      "matchName": "Match 2",
      "id": 2,
      "teams": [
        {"id": 3, "name": "Team A", "short_name": "TMA", "logo_url": null, "squad": []},
        {"id": 4, "name": "Team B", "short_name": "TMB", "logo_url": null, "squad": []}
      ],
      "score": {"runs": 24, "wickets": 1, "overs": 4, "team_id": 3},
      "is_live": true,
      "match_ended": false,
      "current_innings": 1
    }
  ]
}
```

---

### 2. Get Match Details
Returns full details for a specific match.

Endpoint: `/matches/<match_id>`
Method: `GET`

Response:
```json
{
  "tournamentId": "tour123",
  "tournamentName": "IPL",
  "matchId": 2,
  "matchName": "Match 2",
  "id": 2,
  "teams": [...],
  "score": {...},
  "date": "2026-01-11T17:01:40.743499Z",
  "match_type": "T20",
  "is_live": true,
  "match_ended": false,
  "current_innings": 1
}
```

---

### 3. Match Control APIs
Control simulation state.

Endpoint: `/match/<id>/start/`
Method: `POST`
Body: none

Endpoint: `/match/<id>/pause/`
Method: `POST`
Body: none

Endpoint: `/match/<id>/reset/`
Method: `POST`
Body: none
Note: Destructive, clears balls and scores.

Endpoint: `/match/<id>/speed/`
Method: `POST`
Body:
```json
{"seconds_per_ball": 1.0}
```

Response (for all control calls):
```json
{"status": "success", "message": "Match Started"}
```

---

### 4. Tournaments (Live + Upcoming)
Useful for tournament pass feature.

Endpoint: `/tournaments/`
Method: `GET`

Response:
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

---

### 5. Debug Logs
Returns recent simulation logs.

Endpoint: `/debug-logs/`
Method: `GET`

Response:
```json
[
  "[12:30:01] Background Simulation Loop Started",
  "[12:30:04] Simulating ball for Match 2"
]
```

---

## WebSocket (Real-Time)

Connect to receive ball-by-ball events for a match.

URL:
```
wss://live-cricket-simulator.onrender.com/ws/matches/<match_id>/?token=<YOUR_TOKEN>
```

Event: `BALL_UPDATE`
```json
{
  "type": "BALL_UPDATE",
  "matchId": 1,
  "matchInfo": {
    "matchId": 1,
    "matchName": "New Meredith Reds vs East Amy Limegreens",
    "tournament": {"id": "1", "name": "IPL", "code": "tour123"},
    "venue": "Eden Gardens",
    "startTime": "2026-02-10T07:56:33.264Z",
    "status": "LIVE",
    "overs_per_innings": 50
  },
  "teams": [
    {
      "id": 1,
      "name": "New Meredith Reds",
      "short_name": "NMR",
      "logo_url": "https://example.com/team1.png",
      "squad": [
        {
          "player_id": 49,
          "name": "John Greer",
          "role": "BATSMAN",
          "batting_hand": "LEFT",
          "bowling_style": "MEDIUM",
          "is_captain": true,
          "is_wicket_keeper": false
        }
      ]
    }
  ],
  "score": {
    "team_id": 1,
    "runs": 270,
    "wickets": 7,
    "overs": 41.1,
    "run_rate": 6.56,
    "required_run_rate": 7.2
  },
  "currentInnings": {
    "batting_team_id": 1,
    "bowling_team_id": 2,
    "partnership": {
      "runs": 11,
      "balls": 15,
      "batsmen": [
        {"player_id": 57, "name": "Player A"},
        {"player_id": 51, "name": "Player B"}
      ]
    },
    "last_ball": {
      "over": 41,
      "ball": 1,
      "runs": 0,
      "extras": 0,
      "extra_type": null,
      "is_wicket": false,
      "striker": {"player_id": 57, "name": "Player A"},
      "non_striker": {"player_id": 51, "name": "Player B"},
      "bowler": {"player_id": 64, "name": "Player C"},
      "dismissal": null
    },
    "batsmen": [
      {
        "player_id": 57,
        "name": "Player A",
        "runs": 7,
        "balls": 11,
        "fours": 0,
        "sixes": 0,
        "strike_rate": 63.64,
        "on_strike": true
      }
    ],
    "bowler": {
      "player_id": 64,
      "name": "Player C",
      "overs": 6.3,
      "maidens": 0,
      "runs_conceded": 53,
      "wickets": 0,
      "economy": 8.15
    },
    "fall_of_wickets": [
      {"score": 1, "wicket": 1, "player_id": 50, "name": "Player X", "over": 0.2}
    ],
    "last_6_balls": [
      {"over": 40.2, "runs": 1},
      {"over": 40.3, "runs": 1},
      {"over": 40.4, "runs": 0},
      {"over": 40.5, "runs": 0},
      {"over": 40.6, "runs": 1},
      {"over": 41.1, "runs": 0}
    ]
  },
  "extras": {
    "wides": 2,
    "no_balls": 1,
    "byes": 0,
    "leg_byes": 0
  },
  "events": [
    {"type": "commentary", "text": "Player A hits a four!", "over": 40.4},
    {"type": "wicket", "player_id": 49, "name": "John Greer", "over": 2.3}
  ]
}
```

---

## How To Use (Quick Start)

1. Get your token (admin init prints it on server startup).
2. Create a match from the dashboard: `/api/v1/dashboard/` (web UI).
3. Start the match with the control endpoint.
4. Consume `/matches/live` and WebSocket events.

---

## Postman Testing Guide

### 1. Set Environment
Create a Postman environment with:
```
base_url = https://live-cricket-simulator.onrender.com/api/v1
token = <YOUR_TOKEN>
```

### 2. Authorization
For all HTTP requests:
Header:
```
Authorization: Token {{token}}
```

### 3. Test Live Matches
Method: `GET`
URL: `{{base_url}}/matches/live`

Expected: `200` with `data` array.

### 4. Test Match Control (Start)
Method: `POST`
URL: `{{base_url}}/match/<match_id>/start/`

Expected: `200` with status success.

### 5. Test Match Control (Speed)
Method: `POST`
URL: `{{base_url}}/match/<match_id>/speed/`
Body (JSON):
```json
{"seconds_per_ball": 0.5}
```

### 6. Test Match Details
Method: `GET`
URL: `{{base_url}}/matches/<match_id>`

### 7. Test Tournaments
Method: `GET`
URL: `{{base_url}}/tournaments/`

### 8. WebSocket Test
Postman supports WebSocket testing:
1. New -> WebSocket Request
2. URL:
   ```
   wss://live-cricket-simulator.onrender.com/ws/matches/<match_id>/?token={{token}}
   ```
3. Click Connect and observe `BALL_UPDATE` messages.
