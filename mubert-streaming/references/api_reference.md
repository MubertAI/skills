# API Reference — Streaming

Base URL: `https://music-api.mubert.com/api/v3`

---

## Get Streaming Link

### `GET /public/streaming/get-link`

Get a streaming URL for real-time AI music.

**Headers:** `customer-id`, `access-token`, `Content-Type: application/json`

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_index` | string | Yes | Playlist identifier |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: 128 |
| `intensity` | string | No | `low`, `medium`, `high`. Default: `high` |
| `type` | string | No | `http` or `webrtc`. Default: `http` |

**Response:** `200 OK`

```json
{
  "data": {
    "link": "https://stream.mubert.com/b2b/v3?customer_id=...&access_token=...&playlist=...&bitrate=...&intensity=..."
  }
}
```

---

## Set Intensity

### `POST /public/streaming/set-intensity`

Change the energy level of the currently playing stream.

**Body:**

```json
{ "intensity": "low|medium|high" }
```

| Value | Description |
|-------|-------------|
| `low` | Calm, ambient |
| `medium` | Balanced |
| `high` | Energetic, driving |

**Response:** `204 No Content`

---

## Loop Mode

### `POST /public/streaming/set-loop-state`

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `loop` | string | Yes | `on` or `off` |
| `time` | number | No | Loop duration in seconds |

**Response:** `204 No Content`

---

## Restart Stream

### `POST /public/streaming/restart`

Restarts the stream with a fresh track from the same playlist. No body required.

**Response:** `204 No Content`

---

## Playlists

### `GET /public/playlists`

Get all available playlists/channels to use as `playlist_index`.

**Response:** `200 OK` - Array of playlist objects:

```json
{
  "playlist_index": "P001",
  "category": "Electronic",
  "group": "Dance",
  "channel": "Deep House",
  "params": {
    "bpm": { "gt": 110, "lt": 130 },
    "keys": ["C", "D", "E"]
  }
}
```
