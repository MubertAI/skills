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

All streamed music is **royalty-free** and cleared for commercial use. Embed live AI-generated music directly into your apps, games, fitness platforms, meditation tools, interactive experiences, or any product that needs an endless, non-repeating soundtrack.

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

# Get streaming link
resp = requests.get(f"{BASE}/public/streaming/get-link", headers=HEADERS, json={
    "playlist_index": "PLAYLIST_INDEX",
    "bitrate": 128,
    "intensity": "high",
    "type": "http",
})
link = resp.json()["data"]["link"]
print(link)

# Set intensity
requests.post(f"{BASE}/public/streaming/set-intensity", headers=HEADERS,
    json={"intensity": "low"})

# Enable loop mode
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

// Get streaming link
const streamRes = await fetch(`${BASE}/public/streaming/get-link`, {
  method: "GET",
  headers: HEADERS,
  body: JSON.stringify({
    playlist_index: "PLAYLIST_INDEX",
    bitrate: 128,
    intensity: "high",
    type: "http",
  }),
});
const { data } = await streamRes.json();
console.log(data.link);

// Set intensity
await fetch(`${BASE}/public/streaming/set-intensity`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ intensity: "low" }),
});

// Enable loop mode
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
# Get streaming link
curl -X GET "https://music-api.mubert.com/api/v3/public/streaming/get-link" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"playlist_index": "PLAYLIST_INDEX", "bitrate": 128}'

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

Playlists use a hierarchical `category.group.channel` numbering format:

| Level | Format | Example | Description |
|-------|--------|---------|-------------|
| Category | `N` | `0` | All channels in the category (e.g. all Moods) |
| Group | `N.N` | `0.0` | All channels in the group (e.g. all Calm moods) |
| Channel | `N.N.N` | `0.0.0` | Specific channel (e.g. Calm) |

You can pass any level as `playlist_index` — broader levels mix more variety.

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

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_index` | string | Yes | Playlist identifier (e.g. `6.1.1` for Deep House) |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: 128 |
| `intensity` | string | No | `low`, `medium`, `high`. Default: `high` |
| `type` | string | No | `http` or `webrtc`. Default: `http` |

Returns a URL like:
```
https://stream.mubert.com/b2b/v3?customer_id=...&access_token=...&playlist=...&bitrate=...&intensity=...
```

## Streaming Controls

### Set Intensity

Change the energy level of the currently playing stream:

| Value | Description |
|-------|-------------|
| `low` | Calm, ambient |
| `medium` | Balanced |
| `high` | Energetic, driving |

### Loop Mode

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `loop` | string | Yes | `on` or `off` |
| `time` | number | No | Loop duration in seconds |

### Restart

Restarts the stream with a fresh track from the same playlist. No parameters needed.

## Playlists

Get available playlists to use as `playlist_index` when creating streams:

```python
playlists = requests.get(f"{BASE}/public/playlists", headers=HEADERS).json()
for p in playlists:
    print(p["playlist_index"], p["category"], p["channel"])
```

```typescript
const res = await fetch(`${BASE}/public/playlists`, { headers: HEADERS });
const playlists = await res.json();
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

- **401** - Invalid credentials (customer-id/access-token)
- **403** - Streaming limit exceeded (daily/monthly/total duration)
- **422** - Invalid parameters

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)