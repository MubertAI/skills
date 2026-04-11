---
name: mubert-generate
description: Generate royalty-free AI music tracks using Mubert Music API v3. Use when creating tracks from text prompts, images, or playlists, editing tracks (replacing/deleting instruments and stems), or generating similar tracks. All generated music is royalty-free and licensed for commercial use in apps, games, videos, and other projects. Supports modes like track, loop, jingle, and mix.
compatibility: Requires internet access and Mubert API credentials (customer-id + access-token for public endpoints, company-id + license-token for service endpoints).
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

# Mubert Track Generation

Generate royalty-free AI music tracks via the Mubert Music API v3 — from text prompts, images, or playlists. Edit tracks by replacing/deleting instruments and stems.

All music generated through the Mubert API is **royalty-free** and cleared for commercial use. You can integrate it directly into your apps, games, videos, podcasts, social media content, and any other projects without worrying about copyright claims or additional licensing fees.

## Use Cases

- **App development** — add background music to your mobile or web app
- **Game development** — generate dynamic soundtracks and adaptive audio
- **Video production** — create unique background music for YouTube, TikTok, ads
- **Podcasts & broadcasts** — generate intros, outros, jingles, and background music
- **In-app AI features** — let your users generate their own music within your product
- **Prototyping** — quickly add placeholder or final audio to demos and MVPs

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

# Generate track from text prompt
resp = requests.post(f"{BASE}/public/tracks", headers=HEADERS, json={
    "prompt": "Energetic electronic music for a workout video",
    "duration": 30,
    "format": "mp3",
    "bitrate": 320,
    "intensity": "high",
    "mode": "track",
})
track = resp.json()
print(track)

# Generate track from playlist
resp = requests.post(f"{BASE}/public/tracks", headers=HEADERS, json={
    "playlist_index": "PLAYLIST_INDEX",
    "duration": 60,
    "bitrate": 256,
    "intensity": "medium",
    "mode": "loop",
})
```

### TypeScript

```typescript
const BASE = "https://music-api.mubert.com/api/v3";
const HEADERS = {
  "customer-id": CUSTOMER_ID,
  "access-token": ACCESS_TOKEN,
  "Content-Type": "application/json",
};

// Generate track from text prompt
const trackRes = await fetch(`${BASE}/public/tracks`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({
    prompt: "Energetic electronic music for a workout video",
    duration: 30,
    format: "mp3",
    bitrate: 320,
    intensity: "high",
    mode: "track",
  }),
});
const track = await trackRes.json();
console.log(track);

// Generate track from playlist
const loopRes = await fetch(`${BASE}/public/tracks`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({
    playlist_index: "PLAYLIST_INDEX",
    duration: 60,
    bitrate: 256,
    intensity: "medium",
    mode: "loop",
  }),
});
```

### cURL

```bash
curl -X POST "https://music-api.mubert.com/api/v3/public/tracks" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Chill lo-fi beat", "duration": 30}'
```

## Endpoints Overview

| Endpoint | Description |
|----------|-------------|
| `POST /public/tracks` | Generate track from prompt, playlist, or image |
| `GET /public/tracks/{id}` | Get track by ID |
| `GET /public/tracks` | List all tracks (paginated) |
| `POST /public/tracks/{id}/similar` | Generate a similar track |
| `POST /public/tracks/{id}/edit` | Edit track (params, instruments, stems) |
| `GET /public/playlists` | List available playlists |

See [API Reference](references/api_reference.md) for full parameter details.

## Playlist Format

Playlists use a hierarchical `category.group.channel` numbering format:

| Level | Format | Example | Description |
|-------|--------|---------|-------------|
| Category | `N` | `0` | All channels in the category (e.g. all Moods) |
| Group | `N.N` | `0.0` | All channels in the group (e.g. all Calm moods) |
| Channel | `N.N.N` | `0.0.0` | Specific channel (e.g. Calm) |

You can pass any level as `playlist_index` — broader levels mix more variety.

### Available Playlists (examples)

| Playlist | Category | Group | Channel |
|----------|----------|-------|---------|
| `0` | Moods | — | — |
| `0.0` | Moods | Calm | — |
| `0.0.0` | Moods | Calm | Calm |
| `0.0.1` | Moods | Calm | Acoustic |
| `0.1.0` | Moods | Energizing | Pumped |
| `0.8.1` | Moods | Heroic | Cinematic |
| `1.0.0` | Focus | Minimal | Minimal 120 |
| `2.0.0` | Sleep | Ambient | Ambient |
| `3.0.0` | Calm | Ambient | Meditation |
| `4.0.0` | Chill | Chillout | Chillout |
| `5.0.1` | Sport | Fitness | Fitness 90 |
| `5.1.0` | Sport | Cardio | Cardio 120 |
| `5.2.0` | Sport | Running | Run 130 |
| `6.1.1` | Genres | House | Deep House |
| `6.2.0` | Genres | Techno | Techno |
| `6.4.0` | Genres | Hiphop | Lofi |
| `6.4.1` | Genres | Hiphop | Hiphop |
| `6.5.1` | Genres | Ambient | Ambient |
| `6.12.0` | Genres | Jazz & Funk | Acid Jazz |
| `6.15.0` | Genres | Pop | Pop |
| `7.0.0` | Game | Setting | Fantasy |
| `7.0.1` | Game | Setting | Sci-fi |

Get the full list via `GET /public/playlists` endpoint.

## Track Generation Modes

| Mode | Description |
|------|-------------|
| `track` | Standard music track (default) |
| `loop` | Seamlessly looping track |
| `jingle` | Short musical jingle (playlist-based only) |
| `mix` | DJ-style mix (playlist-based only) |

## Common Parameters

| Parameter | Values | Default |
|-----------|--------|---------|
| `bitrate` | 32, 96, 128, 192, 256, 320 | 128 |
| `format` | mp3, wav | mp3 |
| `intensity` | low, medium, high | high |
| `mode` | track, loop, jingle, mix | track |

## Track Editing

After generating a track, you can edit it in several ways:

### Replace or delete instruments

Available instruments: `DRUMS`, `PERCS`, `HATS`, `CLAPS`, `BASS`, `MIDS`, `LEADS`, `FX`, `VOCALS`, `PADS`, `RISER`, `IMPACT`

```python
# Replace specific instruments with new ones
requests.post(f"{BASE}/public/tracks/{track_id}/edit", headers=HEADERS, json={
    "replace_instruments": ["DRUMS", "BASS"]
})

# Delete instruments from the track
requests.post(f"{BASE}/public/tracks/{track_id}/edit", headers=HEADERS, json={
    "delete_instruments": ["VOCALS", "FX"]
})
```

```typescript
// Replace specific instruments with new ones
await fetch(`${BASE}/public/tracks/${trackId}/edit`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ replace_instruments: ["DRUMS", "BASS"] }),
});

// Delete instruments from the track
await fetch(`${BASE}/public/tracks/${trackId}/edit`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ delete_instruments: ["VOCALS", "FX"] }),
});
```

### Replace or delete stems

Available stems: `DRUMS` (includes DRUMS, PERCS, HATS, CLAPS), `BASS`, `LEADS` (includes MIDS, LEADS, PADS), `VOCALS`, `FX` (includes FX, RISER, IMPACT)

```python
requests.post(f"{BASE}/public/tracks/{track_id}/edit", headers=HEADERS, json={
    "replace_stems": ["DRUMS", "LEADS"]
})
```

```typescript
await fetch(`${BASE}/public/tracks/${trackId}/edit`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ replace_stems: ["DRUMS", "LEADS"] }),
});
```

## Authentication

| Headers | Use case |
|---------|----------|
| `customer-id` + `access-token` | All track generation and library endpoints |

## Error Handling

- **401** - Invalid credentials (customer-id/access-token)
- **422** - Invalid parameters

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)