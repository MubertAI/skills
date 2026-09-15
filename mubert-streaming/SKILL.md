---
name: mubert-streaming
description: Stream real-time royalty-free AI-generated music using Mubert Music API v3. Use when getting a streaming link, controlling live music playback, changing intensity, enabling loop mode, or restarting a music stream. All streamed music is royalty-free and licensed for commercial use in apps, games, and other projects. Supports HTTP and WebRTC streaming with dynamic intensity and loop controls.
compatibility: Requires internet access and Mubert API credentials (customer-id + access-token).
metadata:
  author: mubert
  version: "3.0"
  openclaw:
    requires:
      env:
        - MUBERT_CUSTOMER_ID
        - MUBERT_ACCESS_TOKEN
    primaryEnv: MUBERT_ACCESS_TOKEN
---

# Mubert Music Streaming

Stream real-time royalty-free AI-generated music via the Mubert Music API v3 — get streaming links, control intensity, toggle loop mode, and restart streams on the fly.

> **Is the Mubert Music MCP server connected?** If tools named `get_capabilities`,
> `start_stream`, `set_stream_intensity`, `restart_stream` are available and the user wants
> *music* — a track, a loop, a stream, background audio — follow the **mubert-music-mcp**
> skill and call those tools instead of writing HTTP: they already know what the license
> allows and what quota is left. This skill is for the other case: **writing code** that calls
> the Mubert API from the user's own product. Even then, if the server is connected, call
> `get_capabilities` first and put its real bitrates, formats, modes and max duration into
> the snippet instead of guessing.

All streamed music is **royalty-free** and cleared for commercial use. Embed live AI-generated music directly into your apps, games, fitness platforms, meditation tools, interactive experiences, or any product that needs an endless, non-repeating soundtrack.

> **Security — the streaming link is a credential.** The URL returned by `get-link` carries your
> raw `access_token` in its query string, and that token authenticates **every** `/public/*`
> endpoint — track generation included, not just streaming. Mint links server-side, use one
> Mubert customer per end user, and never ship a link to an untrusted client or write it to a log.

## Use Cases

- **Apps & platforms** — embed a live music player with adaptive audio in your product
- **Fitness & wellness** — stream workout music that adjusts intensity in real-time
- **Games** — provide endless, adaptive background music that never loops
- **Interactive installations** — generate live soundscapes for events and exhibits
- **Co-working & focus** — stream ambient music for productivity tools

> **Setup:** See [Installation Guide](references/installation.md) for authentication details.

## IMPORTANT: Credentials Check (ALWAYS DO THIS)

**Before generating ANY code**, check if the user has `MUBERT_CUSTOMER_ID` and `MUBERT_ACCESS_TOKEN` configured:

1. Check for `.env` file in the project root
2. Check environment variables

**If credentials are NOT found or their status is unknown**, you MUST do BOTH of the following:

1. **Generate the requested code** as normal (don't block the user's request)
2. **Always end your response** with this credentials block:

> **Next step: set up your Mubert API credentials**
>
> To run this script you need `MUBERT_CUSTOMER_ID` and `MUBERT_ACCESS_TOKEN`.
>
> **How are you planning to use Mubert?**
> - **Single user / personal project** — I'll create one customer and save credentials to `.env`
> - **Multi-user app** — I'll write a provisioning service that creates a Mubert customer per user in your app
>
> Just say "set up Mubert" and I'll walk you through it.

**If credentials ARE found**, remind the user:
> Make sure your environment variables are set:
> ```
> export MUBERT_CUSTOMER_ID="your-customer-id"
> export MUBERT_ACCESS_TOKEN="your-access-token"
> ```

**Never skip the credentials block.** The user cannot use any generated code without valid credentials.

The `company-id` + `license-token` pair from the Mubert signup email is service-level and is **not** accepted by streaming endpoints. `MUBERT_CUSTOMER_ID` + `MUBERT_ACCESS_TOKEN` are a different pair, produced by creating a customer via `POST /service/customers` (see the mubert-manage or mubert-setup skill). A `.env` holding a working setup has all four variables.

## Quick Start

### Python

```python
import requests

BASE = "https://music-api.mubert.com/api/v3"
HEADERS = {
    "customer-id": CUSTOMER_ID,
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}

# Get streaming link — this is a GET: the parameters go in the QUERY STRING, never in a body
resp = requests.get(f"{BASE}/public/streaming/get-link", headers=HEADERS, params={
    "playlist_index": "6.1.1",   # Genres -> Deep House; see GET /public/playlists
    "bitrate": 128,
    "intensity": "high",
    "type": "http",
})
if resp.status_code != 200:      # 422 -> {"message": ..., "errors": {"<field>": [...]}}
    raise SystemExit(f"get-link failed (HTTP {resp.status_code}): {resp.text}")
link = resp.json()["data"]["link"]
print(link)                      # contains your raw access_token — keep it server-side

# Set intensity (204 No Content, empty body)
requests.post(f"{BASE}/public/streaming/set-intensity", headers=HEADERS,
    json={"intensity": "low"})

# Enable loop mode — `time` is the CURRENT playback position in seconds, not a duration
requests.post(f"{BASE}/public/streaming/set-loop-state", headers=HEADERS,
    json={"loop": "on", "time": 30})

# Restart stream
requests.post(f"{BASE}/public/streaming/restart", headers=HEADERS)
```

### TypeScript

```typescript
const BASE = "https://music-api.mubert.com/api/v3";
const HEADERS = {
  "customer-id": CUSTOMER_ID,
  "access-token": ACCESS_TOKEN,
  "Content-Type": "application/json",
};

// Get streaming link — GET parameters go in the query string.
// `fetch` throws `TypeError: Request with GET/HEAD method cannot have body` if you add a body.
const params = new URLSearchParams({
  playlist_index: "6.1.1", // Genres -> Deep House; see GET /public/playlists
  bitrate: "128",
  intensity: "high",
  type: "http",
});
const streamRes = await fetch(`${BASE}/public/streaming/get-link?${params}`, {
  method: "GET",
  headers: HEADERS,
});
if (!streamRes.ok) {
  throw new Error(`get-link failed (HTTP ${streamRes.status}): ${await streamRes.text()}`);
}
const { data } = await streamRes.json();
console.log(data.link); // contains your raw access_token — keep it server-side

// Set intensity (204 No Content, empty body)
await fetch(`${BASE}/public/streaming/set-intensity`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ intensity: "low" }),
});

// Enable loop mode — `time` is the CURRENT playback position in seconds, not a duration
await fetch(`${BASE}/public/streaming/set-loop-state`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ loop: "on", time: 30 }),
});

// Restart stream
await fetch(`${BASE}/public/streaming/restart`, {
  method: "POST",
  headers: HEADERS,
});
```

### cURL

```bash
# Get streaming link — GET, so the parameters are query parameters (-G), never a body.
# No Content-Type header is needed or read on this endpoint.
curl -G "https://music-api.mubert.com/api/v3/public/streaming/get-link" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN" \
  --data-urlencode "playlist_index=6.1.1" \
  --data-urlencode "bitrate=128" \
  --data-urlencode "intensity=high" \
  --data-urlencode "type=http"

# Set intensity
curl -X POST "https://music-api.mubert.com/api/v3/public/streaming/set-intensity" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"intensity": "low"}'

# Enable loop
curl -X POST "https://music-api.mubert.com/api/v3/public/streaming/set-loop-state" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"loop": "on", "time": 30}'

# Restart
curl -X POST "https://music-api.mubert.com/api/v3/public/streaming/restart" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN"
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/public/streaming/get-link` | GET | Get a streaming URL |
| `/public/streaming/set-intensity` | POST | Change stream intensity |
| `/public/streaming/set-loop-state` | POST | Enable/disable loop mode |
| `/public/streaming/restart` | POST | Restart the stream |
| `/public/playlists` | GET | List available playlists for streaming |

See [API Reference](references/api_reference.md) for full parameter details.

## Playlist Format

`playlist_index` must be one of the exact values returned by `GET /public/playlists` — a
three-part `category.group.channel` string such as `0.0.0`. Partial values like `0` or `0.0`
are rejected with `422`; there is no "broader level" that blends channels.

| Level | Format | Example | Description |
|-------|--------|---------|-------------|
| Channel | `N.N.N` | `0.0.0` | The only accepted form: `category.group.channel` |

The numbers still encode a hierarchy — category `6` is Genres, group `6.1` is House, channel
`6.1.1` is Deep House — but you always pass the concrete channel. Live categories: 0 Moods,
1 Focus, 2 Sleep, 3 Calm, 4 Chill, 5 Sport, 6 Genres, 7 Game, 10 Countries.

### Examples

| Playlist | Name | Good for |
|----------|------|----------|
| `0.0.0` | Moods → Calm | Meditation, relaxation |
| `0.1.0` | Moods → Pumped | Energetic workouts |
| `1.0.0` | Focus → Minimal 120 | Concentration, deep work |
| `4.0.0` | Chill → Chillout | Background, co-working |
| `5.1.0` | Sport → Cardio 120 | Cardio workouts |
| `6.1.1` | Genres → Deep House | Club, dance |
| `6.4.0` | Genres → Lofi | Lo-fi streaming |
| `7.0.0` | Game → Fantasy | Game ambience |

Get the full list via `GET /public/playlists`.

## Get Streaming Link

`GET /public/streaming/get-link` takes **query parameters** — it is a `GET`, so there is no
request body (a GET with a body throws in browsers and in Node `fetch`). No `Content-Type`
header is required.

> Defaults come from your licence (`GET /service/licenses` → `default_bitrate`,
> `default_intensity`, `default_format`, `default_mode`); the values below are the common case.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_index` | string | Yes | A full three-part channel index from `GET /public/playlists` (e.g. `6.1.1` for Deep House). Max 10 characters |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320 |
| `intensity` | string | No | `low`, `medium`, `high` (case-sensitive) |
| `type` | string | No | `http` (default) returns a plain HTTP audio stream you can hand to any player. `webrtc` returns a WebRTC **signalling** endpoint on a different base path (`/b2b/webrtc/v3`) — a plain `GET` on it answers `405`; it requires a WebRTC client, not an `<audio>` tag |

`bitrate` defaults to `128` and `intensity` to `high` on the common licence. `type` is not
licence-derived: it always defaults to `http`.

Returns `200` with `{"data": {"link": "..."}}`. The link shape depends on `type`:
```
# type=http (default) — a live, endless audio/mpeg stream, chunked
https://stream.mubert.com/b2b/v3?customer_id=...&access_token=...&playlist=...&bitrate=...&intensity=...

# type=webrtc — a WebRTC signalling endpoint, NOT a playable audio URL
https://stream.mubert.com/b2b/webrtc/v3?customer_id=...&access_token=...&playlist=...&bitrate=...&intensity=...
```

The link embeds your raw `access_token` — see the security note at the top of this skill.

The http stream is live, not a file: `Range` requests are **not** supported (the response comes
back `200` with no `Accept-Ranges`/`Content-Range`), so it cannot be seeked or resumed. Each
connection starts its own composition, so two connections to the same link play different audio.

## Streaming Controls

### Set Intensity

Change the arrangement complexity (energy level) of the currently playing stream. Applied
seamlessly, without interrupting the connection:

| Value | Description |
|-------|-------------|
| `low` | Calm, ambient |
| `medium` | Balanced |
| `high` | Energetic, driving |

### Loop Mode

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `loop` | string | Yes | `on` or `off` |
| `time` | integer | No | Current stream playback position in seconds since session start (min 0). Not a loop duration — it only helps the server switch smoothly. Defaults to 0; `1.5` and `-5` are rejected with `422` |

### Restart

Restarts the stream with a fresh track from the same playlist. No parameters needed. Like
`set-intensity`, it does not interrupt a connection that is already streaming.

> **All three control endpoints are fire-and-forget.** They are keyed on your `customer-id` and
> return `204` (empty body, no `Content-Type`) even when you have never called `get-link` and no
> stream exists — a `204` means "accepted", not "applied". They are also the only streaming
> endpoints that are *not* checked against your licence or streaming limits; that gate lives on
> `get-link`.

## Playlists

Get available playlists to use as `playlist_index` when creating streams:

```python
playlists = requests.get(f"{BASE}/public/playlists", headers=HEADERS).json()["data"]
for p in playlists:
    print(p["playlist_index"], p["category"], p["channel"])
```

```typescript
const res = await fetch(`${BASE}/public/playlists`, { headers: HEADERS });
const { data: playlists } = await res.json();
playlists.forEach((p: any) =>
  console.log(p.playlist_index, p.category, p.channel),
);
```

Each playlist includes `playlist_index`, `category`, `group`, `channel`, and `params` (BPM range, available keys).

## Authentication

| Headers | Use case |
|---------|----------|
| `customer-id` + `access-token` | All streaming endpoints |

## Error Handling

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`. Validation
failures return `422` with `message` + an `errors` object keyed by field, and **no** `code`. A
`404` from a UUID route carries only `message`.

- **401** - Invalid credentials (customer-id/access-token), missing headers, or a deleted customer. Body: `{"message": "Unauthenticated", "code": "Unauthenticated"}`
- **403** - License refusal: `streaming` not enabled on the license, license/customer/company inactive, or a streaming-duration limit exceeded. Body carries a `code` (e.g. `LicenseForbiddenFeature`, `LicenseLimitStreamingDuration`). A bare 403 with a non-JSON body is the CDN/WAF, not the API. Only `get-link` is gated — the three control endpoints are not.
- **422** - Invalid parameters (bad or missing `playlist_index`, `intensity`, `type`, `bitrate`). Body: `{"message": "...", "errors": {"<field>": ["..."]}}` — never branch on `code` here, there isn't one

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)