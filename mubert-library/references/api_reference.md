# API Reference — Music Library

Base URL: `https://music-api.mubert.com/api/v3`

**Headers:** `customer-id`, `access-token`

---

## Filter Parameters

### `GET /public/music-library/params`

Get available filter values. Pass existing filters to narrow down remaining options.

**Query Parameters:** `bpm`, `genres`, `themes`, `activities`, `duration` (all optional, combined with AND)

**Response:** `200 OK`

```json
[
  {
    "param": "genres",
    "values": [
      { "value": "electronic", "tracks_count": 1500 },
      { "value": "hip-hop", "tracks_count": 800 },
      { "value": "ambient", "tracks_count": 450 }
    ]
  },
  {
    "param": "themes",
    "values": [
      { "value": "chill", "tracks_count": 600 },
      { "value": "dark", "tracks_count": 300 }
    ]
  },
  {
    "param": "bpm",
    "values": [
      { "value": "100", "tracks_count": 200 },
      { "value": "120", "tracks_count": 350 }
    ]
  }
]
```

---

## Browse Tracks

### `GET /public/music-library/tracks`

Get pre-made tracks with optional filtering.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `genres` | string | No | Filter by genre |
| `themes` | string | No | Filter by theme/mood |
| `activities` | string | No | Filter by activity/use case |
| `bpm` | integer | No | Filter by BPM |
| `duration` | integer | No | Filter by duration |
| `limit` | integer | No | Page size |
| `offset` | integer | No | Pagination offset |

All filters are combined with AND logic.

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "track-id",
      "bpm": 120,
      "duration": 30,
      "genres": ["electronic"],
      "themes": ["chill"],
      "url": "https://..."
    }
  ],
  "meta": {
    "offset": 0,
    "limit": 10,
    "total": 350
  }
}
```

---

## Playlists

### `GET /public/playlists`

Get all available playlists/channels.

**Response:** `200 OK`

```json
[
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
]
```

Use `playlist_index` with **mubert-generate** (track creation) or **mubert-streaming** (real-time streaming).
