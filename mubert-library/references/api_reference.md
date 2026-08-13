# API Reference — Music Library

Base URL: `https://music-api.mubert.com/api/v3`

**Headers:** `customer-id`, `access-token`

Envelopes are per-endpoint here, not blanket:

- `GET /public/music-library/params` → a **bare array**, no `data` wrapper.
- `GET /public/music-library/tracks` → `data` + `meta` (`offset`, `limit`, `total`).
- `GET /public/playlists` → `data`, **no `meta`**.

Both music-library endpoints are cached server-side (`/params` 24 h, `/tracks` 1 h) and carry an `ETag`. Repeating a query returns a byte-identical body. Append the undocumented `flush=1` to force a refresh. They are also sent with `Cache-Control: public`, so the CDN edge may answer a repeat request — including one with no credentials at all. Never use them as a credentials check; probe `GET /public/playlists`, which is not cacheable.

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`. Validation failures return `422` with `message` + an `errors` object keyed by field, and **no** `code`. These endpoints take no path parameters, so a `404` never occurs.

A filter value that does not exist in the taxonomy is **not** an error: the API returns `200` with an empty `data` array and `meta.total: 0`. Filter values are exact-match and case-sensitive Title-Case strings taken from `GET /public/music-library/params` (`Ambient` matches 1046 tracks, `ambient` matches none), single-valued (`Ambient,Techno` matches nothing, `genres[]=Ambient` is a `422`), and `bpm`/`duration` match an exact number rather than a range.

---

## Filter Parameters

### `GET /public/music-library/params`

Get available filter values. Pass existing filters to narrow down remaining options.

**Query Parameters:** `bpm`, `genres`, `themes`, `activities`, `moods`, `instruments`, `playlists`, `key`, `mode`, `duration` (all optional, combined with AND). `limit`/`offset`/`order`/`order_by` are not supported here — they are accepted with `200` and silently ignored. Values are exact-match and case-sensitive (`Ambient`, not `ambient`).

**Response:** `200 OK`

Unfiltered the array has 10 groups — `activities`, `bpm`, `genres`, `instruments`, `key`, `moods`, `playlists`, `themes`, `duration`, `mode`. Groups whose values are all excluded by your filters are omitted (a nonexistent `genres` value leaves only `duration` and `mode`), so look a group up by its `param` name and never by array position. Every `value` is a string, `bpm` and `duration` included.

```json
[
  {
    "param": "genres",
    "values": [
      { "value": "Ambient", "tracks_count": 1046 },
      { "value": "Hip-Hop", "tracks_count": 219 },
      { "value": "Techno", "tracks_count": 150 }
    ]
  },
  {
    "param": "themes",
    "values": [
      { "value": "Cinematic", "tracks_count": 600 },
      { "value": "Corporate", "tracks_count": 300 }
    ]
  },
  {
    "param": "bpm",
    "values": [
      { "value": "100", "tracks_count": 684 },
      { "value": "120", "tracks_count": 2050 }
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
| `genres` | string | No | Filter by genre (`Ambient`, `Hip-Hop`, `Techno`) |
| `themes` | string | No | Filter by theme/use context (`Cinematic`, `Corporate`) |
| `activities` | string | No | Filter by activity preset (`Meditation`, `Run 140`) |
| `moods` | string | No | Filter by mood — a separate axis from `themes` (`Uplifting`, `Dreamy`) |
| `instruments` | string | No | Filter by instrument present (`Drums`, `Bells`) |
| `playlists` | string | No | Filter by curated playlist name (`Autumn Vibes`) |
| `key` | string | No | Musical key (`Cm`, `A#`); an unknown key is a `422` |
| `mode` | string | No | Track mode (`track`, `jingle`, `mix`); an unknown mode is a `422`, and the accepted `loop` currently matches no library tracks |
| `bpm` | integer | No | Exact BPM, 1-500. `bpm=120` matches; `bpm=121` returns 0 results |
| `duration` | integer | No | Exact duration in seconds, min 5. Not a range |
| `order` | string | No | Sort direction, `asc` or `desc`; anything else is a `422` |
| `order_by` | string | No | Sort field. Only `bpm`, `duration`, `created_at` work — the API does not allow-list this, so any other value returns a **500** whose body echoes the internal upstream URL |
| `limit` | integer | No | Page size. Minimum 1, **default 20**, no server-side maximum. |
| `offset` | integer | No | Pagination offset. Minimum 0, **default 0**. An offset past `meta.total` returns an empty `data` array, not an error. |

All filters are combined with AND logic. A malformed value (wrong type, out of range, unknown `key`/`mode`/`order`) is a `422`; a well-formed value that is simply absent from the taxonomy is a `200` with `meta.total: 0`.

> **Trial licenses:** the API silently discards every filter for a trial license and returns the first 20 tracks (`offset=0, limit=20`) with no error.

**Response:** `200 OK`

```json
{
  "data": [
    {
      "id": "a24df0da-5ef5-416c-a450-4c1f7e907d00",
      "session_id": "842e3b219ba144a5a4e815e2ef0362d9",
      "playlist_index": "6.5.1",
      "prompt": null,
      "duration": 120,
      "intensity": "medium",
      "mode": "track",
      "bpm": 130,
      "key": "C#m",
      "generations": [
        {
          "session_id": "ad12cf9d3cb842d3bccfcd79583270b5",
          "format": "mp3",
          "bitrate": 320,
          "status": "done",
          "generated_at": "2026-07-20T14:06:27.000000Z",
          "created_at": "2026-07-20T14:06:10.000000Z",
          "url": "https://static-eu.gcp.mubert.com/.../ad12cf9d3cb842d3bccfcd79583270b5.mp3"
        }
      ]
    }
  ],
  "meta": {
    "offset": 0,
    "limit": 10,
    "total": 350
  }
}
```

Track element keys are exactly `id`, `session_id`, `playlist_index`, `prompt`, `duration`, `intensity`, `mode`, `bpm`, `key`, `generations`. There is **no** top-level `url`, **no** `genres` and **no** `themes` — the audio URL is at `generations[0].url`, and the genre/theme you filtered by is not echoed back. Generation objects carry `session_id`, `format`, `bitrate`, `status`, `generated_at`, `created_at`, `url`; unlike `/public/tracks`, they have no `expired_at`. These payloads are a raw pass-through of an upstream render API, so they are not shaped by this API's resource layer.

---

## Playlists

### `GET /public/playlists`

Get all available playlists/channels.

**Response:** `200 OK`

```json
{
  "data": [
    {
      "playlist_index": "3.0.0",
      "category": "Calm",
      "group": "Ambient",
      "channel": "Meditation",
      "params": [
        {
          "bpm": { "gt": 45, "lt": 83 },
          "keys": ["Cm", "C", "C#m", "C#", "…all 24 keys for this BPM range"]
        }
      ]
    }
  ]
}
```

The response has a `data` key and **no** `meta` — it is not paginated. `params` is only present when the playlist has one.

`playlist_index` must be one of the exact values returned by `GET /public/playlists` — a three-part `category.group.channel` string such as `0.0.0`. Partial values like `0` or `0.0` are rejected with `422`; there is no "broader level" that blends channels.

Use `playlist_index` with **mubert-generate** (track creation) or **mubert-streaming** (real-time streaming). Only indexes returned by this endpoint are guaranteed to be accepted — library tracks may carry a `playlist_index` whose playlist is no longer active, and those are rejected with `422` downstream, so validate against this list first.
