# API Reference — Track Generation

Base URL: `https://music-api.mubert.com/api/v3`

---

## Track Generation

### `POST /public/tracks` - Generate from playlist

Generate a track using a specific playlist/channel.

**Headers:** `customer-id`, `access-token`, `Content-Type: application/json`

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_index` | string | Yes | Playlist identifier |
| `duration` | integer | Yes | Duration in seconds |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: 128 |
| `format` | string | No | `mp3` or `wav`. Default: `mp3` |
| `intensity` | string | No | `low`, `medium`, `high`. Default: `high` |
| `mode` | string | No | `track`, `loop`, `jingle`, `mix`. Default: `track` |
| `bpm` | integer | No | Beats per minute |
| `key` | string | No | Musical key |

**Response:** `200 OK` - Track model.

---

### `POST /public/tracks` - Generate from text prompt

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Text description, max 200 characters |
| `duration` | integer | Yes | Duration in seconds |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: 128 |
| `format` | string | No | `mp3` or `wav`. Default: `mp3` |
| `intensity` | string | No | `low`, `medium`, `high`. Default: `high` |
| `mode` | string | No | `track` or `loop`. Default: `track` |

---

### `POST /public/tracks` - Generate from image

**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | file | Yes | JPEG or PNG, max 10 MB |
| `duration` | string | Yes | Duration in seconds |
| `bitrate` | string | No | Default: 128 |
| `format` | string | No | `mp3` or `wav`. Default: `mp3` |
| `intensity` | string | No | `low`, `medium`, `high`. Default: `high` |
| `mode` | string | No | `track` or `loop`. Default: `track` |

---

### `GET /public/tracks/{track_id}` - Get track

**Response:** `200 OK` - Track model.

---

### `GET /public/tracks` - List tracks

**Query Parameters:** `limit` (optional), `offset` (optional)

**Response:** `200 OK` - Array of track models.

---

### `POST /public/tracks/{track_id}/similar` - Generate similar

**Body:** `duration`, `bitrate`, `format`, `intensity`, `mode` (all optional)

**Response:** `200 OK` - Track model.

---

## Track Editing

### `POST /public/tracks/{track_id}/edit` - Edit parameters

**Body:** `duration`, `bitrate`, `format`, `intensity` (all optional)

---

### `POST /public/tracks/{track_id}/edit` - Replace instruments

```json
{ "replace_instruments": ["DRUMS", "BASS", "LEADS"] }
```

Available: `DRUMS`, `PERCS`, `HATS`, `CLAPS`, `BASS`, `MIDS`, `LEADS`, `FX`, `VOCALS`, `PADS`, `RISER`, `IMPACT`

---

### `POST /public/tracks/{track_id}/edit` - Replace stems

```json
{ "replace_stems": ["DRUMS", "LEADS"] }
```

| Stem | Includes |
|------|----------|
| `DRUMS` | DRUMS, PERCS, HATS, CLAPS |
| `BASS` | BASS |
| `LEADS` | MIDS, LEADS, PADS |
| `VOCALS` | VOCALS |
| `FX` | FX, RISER, IMPACT |

---

### `POST /public/tracks/{track_id}/edit` - Delete instruments

```json
{ "delete_instruments": ["VOCALS", "FX"] }
```

---

### `POST /public/tracks/{track_id}/edit` - Delete stems

```json
{ "delete_stems": ["VOCALS", "FX"] }
```

---

## Playlists

### `GET /public/playlists` - List playlists

**Response:** `200 OK` - Array of playlist objects with `playlist_index`, `category`, `group`, `channel`, and `params` (BPM range, available keys).

---

## Track Model

```json
{
  "id": "track-id",
  "session_id": "session-id",
  "playlist_index": "playlist-index",
  "prompt": "text prompt if used",
  "bitrate": 128,
  "duration": 30,
  "intensity": "high",
  "mode": "track",
  "key": "C",
  "bpm": 120,
  "generations": [
    {
      "session_id": "gen-session-id",
      "format": "mp3",
      "bitrate": 128,
      "status": "completed",
      "generated_at": "2024-01-01T00:00:00Z",
      "expired_at": "2024-02-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "url": "https://..."
    }
  ]
}
```