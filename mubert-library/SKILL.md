---
name: mubert-library
description: Browse and search the Mubert pre-made royalty-free music library. Use when searching for tracks by genre, theme, activity, BPM, or duration, or listing available filter parameters. All library tracks are royalty-free and licensed for commercial use in apps, games, videos, and other projects.
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

# Mubert Music Library

Browse and search the Mubert pre-made royalty-free music library — filter by genres, themes, activities, BPM, and duration. Discover playlists and channels for use with track generation and streaming.

All library tracks are **royalty-free** and cleared for commercial use. Use them directly in your apps, games, videos, podcasts, and any other projects without copyright concerns.

## Use Cases

- **Music discovery** — find the right track by genre, mood, or tempo
- **Content creation** — search for background music for videos, podcasts, ads
- **App integration** — browse available playlists to offer users curated music categories
- **Playlist selection** — find the right `playlist_index` for use with **mubert-generate** or **mubert-streaming**

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

# Get available filter parameters
params = requests.get(f"{BASE}/public/music-library/params", headers=HEADERS).json()
for p in params:
    print(p["param"], [v["value"] for v in p["values"][:5]])

# Search tracks by genre and BPM
tracks = requests.get(f"{BASE}/public/music-library/tracks", headers=HEADERS, params={
    "genres": "electronic",
    "bpm": 120,
    "limit": 10,
}).json()
for t in tracks["data"]:
    print(t["id"], t["bpm"], t["duration"])

```

### TypeScript

```typescript
const BASE = "https://music-api.mubert.com/api/v3";
const HEADERS = {
  "customer-id": CUSTOMER_ID,
  "access-token": ACCESS_TOKEN,
  "Content-Type": "application/json",
};

// Get available filter parameters
const paramsRes = await fetch(`${BASE}/public/music-library/params`, {
  headers: HEADERS,
});
const params = await paramsRes.json();
console.log(params);

// Search tracks by genre and BPM
const tracksRes = await fetch(
  `${BASE}/public/music-library/tracks?genres=electronic&bpm=120&limit=10`,
  { headers: HEADERS },
);
const tracks = await tracksRes.json();
console.log(tracks.data);

```

### cURL

```bash
# Get filter parameters
curl -X GET "https://music-api.mubert.com/api/v3/public/music-library/params" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN"

# Search tracks
curl -X GET "https://music-api.mubert.com/api/v3/public/music-library/tracks?genres=electronic&bpm=120&limit=10" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN"

```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/public/music-library/params` | GET | Get available filter parameters and their values |
| `/public/music-library/tracks` | GET | Browse/filter library tracks |

See [API Reference](references/api_reference.md) for full parameter details.

## Filtering Tracks

All filter parameters are optional and combined with AND logic:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `genres` | Music genre | `electronic`, `hip-hop`, `ambient` |
| `themes` | Mood/theme | `chill`, `dark`, `uplifting` |
| `activities` | Use case | `workout`, `focus`, `relaxation` |
| `bpm` | Beats per minute | `120` |
| `duration` | Track length | `30` |
| `limit` | Page size | `10` |
| `offset` | Pagination offset | `0` |

### Discovering Available Filters

Use `/public/music-library/params` to discover what values are available. Each parameter returns its possible values with track counts:

```json
[
  {
    "param": "genres",
    "values": [
      { "value": "electronic", "tracks_count": 1500 },
      { "value": "hip-hop", "tracks_count": 800 }
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

You can pass existing filters to narrow down remaining options:

```python
# After selecting genre=electronic, see what BPMs are available
params = requests.get(f"{BASE}/public/music-library/params", headers=HEADERS, params={
    "genres": "electronic",
}).json()
```

```typescript
const filtered = await fetch(
  `${BASE}/public/music-library/params?genres=electronic`,
  { headers: HEADERS },
);
```

## Related Skills

- **mubert-generate** — generate new tracks from a text prompt, image, or playlist
- **mubert-streaming** — stream real-time music from a playlist

For playlists (used with generate/streaming, not library), see **mubert-generate** or **mubert-streaming** skills.

## Authentication

| Headers | Use case |
|---------|----------|
| `customer-id` + `access-token` | All library and playlist endpoints |

## Error Handling

- **401** - Invalid credentials (customer-id/access-token)
- **422** - Invalid parameters

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)
