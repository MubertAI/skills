# API Reference — Streaming

Base URL: `https://music-api.mubert.com/api/v3`

`GET /public/streaming/get-link` and `GET /public/playlists` wrap their payload in a top-level
`data` key — read `resp.json()["data"]`, not the body itself. Neither adds a `meta` block:
neither is paginated. `set-intensity`, `set-loop-state` and `restart` return `204 No Content`
with an empty body — check the status code, do not parse JSON.

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`. Validation
failures return `422` with `message` + an `errors` object keyed by field, and **no** `code`. A
`404` from a UUID route carries only `message`.

---

## Get Streaming Link

### `GET /public/streaming/get-link`

Get a streaming URL for real-time AI music.

**Headers:** `customer-id`, `access-token`

**Query parameters** (this is a `GET` — the parameters go in the query string, not a body; a GET with a body throws in browsers and Node `fetch`):

> Defaults come from your licence (`GET /service/licenses` → `default_bitrate`,
> `default_intensity`, `default_format`, `default_mode`); the values below are the common case.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_index` | string | Yes | A full three-part `category.group.channel` index from `GET /public/playlists`, e.g. `6.1.1`. Max 10 characters; partial values (`0`, `0.0`) and any invented opaque id are rejected with `422` |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Defaults to your licence's `default_bitrate` (128 on most licences) |
| `intensity` | string | No | `low`, `medium`, `high` (case-sensitive). Defaults to your licence's `default_intensity` (`high` on most licences) |
| `type` | string | No | `http` (default, not licence-derived) or `webrtc` |

**Response:** `200 OK`

```json
{
  "data": {
    "link": "https://stream.mubert.com/b2b/v3?customer_id=...&access_token=...&playlist=...&bitrate=...&intensity=..."
  }
}
```

`type=webrtc` returns a different URL shape — base path `https://stream.mubert.com/b2b/webrtc/v3`
with the same query parameters. That is a WebRTC **signalling** endpoint, not a playable media
URL: a plain `GET` on it answers `405`. The single link format documented above is `http`-only.

The `http` link is a live, endless `audio/mpeg` stream: chunked, no `Range` support (a `Range`
request comes back `200` with no `Accept-Ranges`/`Content-Range`), and every connection starts
its own composition, so two connections to the same link deliver different audio.

**Security:** the link embeds your raw `access_token`, which authenticates every `/public/*`
endpoint including track generation. Never hand it to an untrusted client and never log it.

**Errors:** `422` when `playlist_index` is missing, longer than 10 characters or not an existing
active playlist, and for any invalid `bitrate`/`intensity`/`type`. `POST` on this route returns
`405` with an HTML body, not JSON.

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

**Response:** `204 No Content` — empty body, no `Content-Type`.

---

## Loop Mode

### `POST /public/streaming/set-loop-state`

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `loop` | string | Yes | `on` or `off` |
| `time` | integer | No | Current stream playback position in seconds since session start (min 0). Not a loop duration — it only helps the server switch smoothly. Defaults to 0; `1.5` (not an integer) and `-5` (below 0) are rejected with `422` |

**Response:** `204 No Content` — empty body, no `Content-Type`.

---

## Restart Stream

### `POST /public/streaming/restart`

Restarts the stream with a fresh track from the same playlist. No body required, and an
unrelated body is ignored. It does not interrupt a connection that is already streaming.

**Response:** `204 No Content` — empty body, no `Content-Type`.

---

All three control endpoints are **fire-and-forget**: they are keyed on `customer-id` only, and
answer `204` even for a customer that has never called `get-link` and has no stream at all. A
`204` means "accepted", not "applied". They are also the only streaming endpoints that are not
checked against the licence or its streaming limits — that gate lives on `get-link`.

---

## Playlists

### `GET /public/playlists`

Get all available playlists/channels to use as `playlist_index`. Every `playlist_index` returned
is a three-part `category.group.channel` string; these exact values are the only ones `get-link`
accepts. The response has `data` and **no** `meta` — it is not paginated.

**Response:** `200 OK` — `data` holds the array of playlist objects:

```json
{
  "data": [
    {
      "playlist_index": "6.1.1",
      "category": "Genres",
      "group": "House",
      "channel": "Deep House",
      "params": [
        {
          "bpm": { "gt": 110, "lt": 130 },
          "keys": ["Cm", "C", "C#m", "C#"]
        }
      ]
    }
  ]
}
```
