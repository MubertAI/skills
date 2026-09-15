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

Browse and search the Mubert pre-made royalty-free music library — filter by genres, moods, themes, activities, instruments, key, BPM, and duration. This skill covers the pre-made catalogue only. **Playlists are not here** — `playlist_index` values for generation or streaming come from `GET /public/playlists`, documented in **mubert-generate** and **mubert-streaming**.

> **Is the Mubert Music MCP server connected?** If tools named `get_capabilities`,
> `generate_track`, `search_library`, `get_library_filters` are available and the user wants
> *music* — a track, a loop, a stream, background audio — follow the **mubert-music-mcp**
> skill and call those tools instead of writing HTTP: they already know what the license
> allows and what quota is left. This skill is for the other case: **writing code** that calls
> the Mubert API from the user's own product. Even then, if the server is connected, call
> `get_capabilities` first and put its real bitrates, formats, modes and max duration into
> the snippet instead of guessing.

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

The `company-id` + `license-token` pair from the Mubert signup email is service-level and is **not** accepted by library endpoints. `MUBERT_CUSTOMER_ID` + `MUBERT_ACCESS_TOKEN` are a different pair, produced by creating a customer via `POST /service/customers` (see the mubert-manage or mubert-setup skill). A `.env` holding a working setup has all four variables.

## Quick Start

> **Verifying credentials:** do not use the music-library endpoints as a credentials check — they are CDN-cached with `Cache-Control: public`, so a warm URL can return `200` even with no credentials. Probe `GET /public/playlists` instead: it is uncached and returns `401 {"message": "Unauthenticated", "code": "Unauthenticated"}` for a bad pair.

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
    "genres": "Ambient",   # exact, case-sensitive value from /params
    "bpm": 120,
    "limit": 10,
}).json()
print("total matches:", tracks["meta"]["total"])
for t in tracks["data"]:
    # the audio URL lives on the generation, not on the track
    print(t["id"], t["bpm"], t["duration"], t["generations"][0]["url"])

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
  `${BASE}/public/music-library/tracks?genres=Ambient&bpm=120&limit=10`,
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
curl -X GET "https://music-api.mubert.com/api/v3/public/music-library/tracks?genres=Ambient&bpm=120&limit=10" \
  -H "customer-id: $MUBERT_CUSTOMER_ID" \
  -H "access-token: $MUBERT_ACCESS_TOKEN"

```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/public/music-library/params` | GET | Get available filter parameters and their values |
| `/public/music-library/tracks` | GET | Browse/filter library tracks |
| `/public/playlists` | GET | List playlists/channels and their `playlist_index` |

See [API Reference](references/api_reference.md) for full parameter details.

## Filtering Tracks

> **Trial licenses:** the API silently ignores every music-library filter for trial licenses and always returns the first 20 tracks (`offset=0, limit=20`). There is no error — if filters appear to have no effect, check the license type.

All filter parameters are optional and combined with AND logic. Values are **exact-match and case-sensitive**, **single-valued** (comma/pipe lists and repeated keys do not OR — a repeated key keeps only the last), and `bpm`/`duration` match an **exact** number rather than a range. Always copy values verbatim from `/public/music-library/params`; anything else returns `200` with `meta.total: 0`.

| Parameter | Description | Example |
|-----------|-------------|---------|
| `genres` | Music genre (exact, case-sensitive) | `Ambient`, `Hip-Hop`, `Techno` |
| `themes` | Theme/use context | `Cinematic`, `Corporate`, `Podcast` |
| `activities` | Activity preset | `Meditation`, `Yoga`, `Run 140` |
| `moods` | Mood (separate axis from `themes`) | `Uplifting`, `Dreamy`, `Epic` |
| `instruments` | Instrument present | `Drums`, `Bells`, `Piano` |
| `playlists` | Curated playlist name | `Autumn Vibes`, `Background Music` |
| `key` | Musical key | `Cm`, `A#` |
| `mode` | Track mode | `track`, `jingle`, `mix` |
| `bpm` | Beats per minute (exact value from `/params`) | `120` |
| `duration` | Track length in seconds (exact value from `/params`) | `120` |
| `order` | Sort direction (`asc`/`desc`) | `desc` |
| `order_by` | Sort field (`bpm`, `duration`, `created_at`) | `bpm` |
| `limit` | Page size (min 1, default 20, no maximum) | `10` |
| `offset` | Pagination offset (min 0, default 0) | `0` |

The values above are real taxonomy entries, but the taxonomy is owned by the API: always take the value you send from `GET /public/music-library/params`, never from memory. `order`/`order_by` are accepted by `/tracks` only — `/params` ignores them.

### Discovering Available Filters

Use `/public/music-library/params` to discover what values are available. Each parameter returns its possible values with track counts. Unfiltered the array has 10 groups (`activities`, `bpm`, `genres`, `instruments`, `key`, `moods`, `playlists`, `themes`, `duration`, `mode`); when you pass filters, groups with no remaining values are omitted, so look groups up by `param` name and never by array position:

```json
[
  {
    "param": "genres",
    "values": [
      { "value": "Ambient", "tracks_count": 1046 },
      { "value": "Hip-Hop", "tracks_count": 219 }
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

Every `value` is a **string**, including `bpm` and `duration`. Send it back verbatim — the filter matching is exact and case-sensitive.

You can pass existing filters to narrow down remaining options:

```python
# After selecting genres=Ambient, see what BPMs are available
params = requests.get(f"{BASE}/public/music-library/params", headers=HEADERS, params={
    "genres": "Ambient",
}).json()
bpm = next((p for p in params if p["param"] == "bpm"), None)  # look up by name, not index
```

```typescript
const filtered = await fetch(
  `${BASE}/public/music-library/params?genres=Ambient`,
  { headers: HEADERS },
);
```

## Related Skills

- **mubert-generate** — generate new tracks from a text prompt, image, or playlist
- **mubert-streaming** — stream real-time music from a playlist

`GET /public/playlists` is documented in the [API Reference](references/api_reference.md) because library tracks carry a `playlist_index`. Use that `playlist_index` with **mubert-generate** (track creation) or **mubert-streaming** (real-time streaming) — but re-validate it against `/public/playlists` first: some library tracks reference playlists that are no longer active.

A `playlist_index` must be one of the exact values returned by `GET /public/playlists` — a three-part `category.group.channel` string such as `0.0.0`. Partial values like `0` or `0.0` are rejected with `422`; there is no "broader level" that blends channels.

## Authentication

| Headers | Use case |
|---------|----------|
| `customer-id` + `access-token` | All library and playlist endpoints |

> **Known API defect:** library responses are returned with `Cache-Control: public`, so a URL another caller already requested can be served from the CDN edge without any credentials. Do not treat library results as private to your customer, and never use these endpoints as a credentials check — probe `GET /public/playlists` instead.

## Error Handling

> `order_by` is not allow-listed by the API: an unknown field name produces a **500** whose body echoes the internal upstream URL. Stick to `bpm`, `duration`, `created_at`.

- **401** - Invalid credentials (customer-id/access-token) or missing headers — body `{"message": "Unauthenticated", "code": "Unauthenticated"}`
- **403** - The license does not include the `music-library` feature (`LicenseForbiddenFeature`)
- **422** - Malformed parameter (wrong type or out of range: `bpm` 1-500, `duration` >= 5, `limit` >= 1, `offset` >= 0, invalid `key`/`mode`/`order`) — body `{"message": ..., "errors": {"<field>": [...]}}`, with **no** `code` key
- **200 with an empty `data` array** - a filter VALUE that does not exist in the taxonomy (e.g. `genres=electronic`). Unknown filter values never 422; always check `meta.total`.

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`. Validation failures return `422` with `message` + an `errors` object keyed by field, and **no** `code`. These endpoints take no path parameters, so a `404` never occurs.

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)
