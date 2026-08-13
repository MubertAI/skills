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

The `company-id` + `license-token` pair from the Mubert signup email is service-level and is **not** accepted by track endpoints. `MUBERT_CUSTOMER_ID` + `MUBERT_ACCESS_TOKEN` are a different pair, produced by creating a customer via `POST /service/customers` (see the mubert-manage or mubert-setup skill). A `.env` holding a working setup has all four variables.

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
    "prompt": "Energetic electronic music for a workout video",  # max 255 characters
    "duration": 30,
    "format": "mp3",
    "bitrate": 320,
    "intensity": "high",
    "mode": "track",
})
# Check the status BEFORE reading the body: 401/403/422 bodies have no "data" key,
# so resp.json()["data"] would raise KeyError instead of telling you what went wrong.
if resp.status_code != 200:
    raise RuntimeError(f"Mubert {resp.status_code}: {resp.text}")
track = resp.json()["data"]
print(track)

# Generate track from playlist
resp = requests.post(f"{BASE}/public/tracks", headers=HEADERS, json={
    # An exact value from GET /public/playlists — always three parts.
    "playlist_index": "0.0.0",
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
    prompt: "Energetic electronic music for a workout video", // max 255 characters
    duration: 30,
    format: "mp3",
    bitrate: 320,
    intensity: "high",
    mode: "track",
  }),
});
// Check the status BEFORE destructuring: error bodies have no `data`, so
// `const { data }` would silently yield undefined and blow up later.
if (!trackRes.ok) throw new Error(`Mubert ${trackRes.status}: ${await trackRes.text()}`);
const { data: track } = await trackRes.json();
console.log(track);

// Generate track from playlist
const loopRes = await fetch(`${BASE}/public/tracks`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({
    // An exact value from GET /public/playlists — always three parts.
    playlist_index: "0.0.0",
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

## Waiting for the Audio URL (required)

Generation is asynchronous. `POST /public/tracks` returns a track model right away whose `generations[0]` carries `status: "processing"` and `url: null` — both fields live **inside** `generations[]`, never at track level. Poll `GET /public/tracks/{id}` until every generation reaches a terminal status.

The create response is also not the final state of the track: `bpm` and `key` come back `null` in prompt and image mode and are only filled in once generation completes, so re-read the track after polling if you need them.

| Status | Meaning |
|--------|---------|
| `processing` | Rendering — keep polling |
| `done` | Ready — `url` is populated |
| `failed` | Generation failed — stop polling |

The `url` key is present from the first response but stays `null` until the status is `done` — wait for the status, don't test the key's existence. Both `GET /public/tracks/{id}` and the list endpoint return the populated link.

Poll by the track's `id` (a UUID). `session_id` is a different identifier and 404s on this route; it has its own endpoint, `GET /public/tracks/session/{session_id}`. That 404 is Laravel's raw route-model-binding error — `{"message": "No query results for model [App\\Models\\Track] ..."}` with **no** `code` key — so do not match on `code: TrackNotFound`.

### Python

```python
import time

def wait_for_track(track_id, timeout=300, interval=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(f"{BASE}/public/tracks/{track_id}", headers=HEADERS)
        payload = resp.json()
        # Status first: a 401/403/404/422 body has no "data" key, so indexing it
        # blind raises KeyError instead of showing what the API objected to.
        if resp.status_code != 200:
            raise RuntimeError(
                f"Mubert {resp.status_code}: {payload.get('message')} "
                f"{payload.get('errors', '')}".strip()
            )
        track = payload["data"]
        for gen in track.get("generations") or []:
            if gen.get("status") == "failed":
                raise RuntimeError(f"Generation failed for track {track_id}")
            if gen.get("status") == "done" and gen.get("url"):
                return gen["url"]
        time.sleep(interval)
    raise TimeoutError(f"Track {track_id} not ready after {timeout}s")

url = wait_for_track(track["id"])
```

### TypeScript

```typescript
async function waitForTrack(trackId: string, timeoutMs = 300_000, intervalMs = 5_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const res = await fetch(`${BASE}/public/tracks/${trackId}`, { headers: HEADERS });
    const payload = await res.json();
    // Status first: error bodies carry no `data`, so destructuring one yields
    // undefined and the next line dies with an unhelpful TypeError.
    if (!res.ok) {
      throw new Error(
        `Mubert ${res.status}: ${payload.message ?? ""} ${JSON.stringify(payload.errors ?? {})}`,
      );
    }
    const track = payload.data;
    for (const gen of track.generations ?? []) {
      if (gen.status === "failed") throw new Error(`Generation failed for track ${trackId}`);
      if (gen.status === "done" && gen.url) return gen.url as string;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Track ${trackId} not ready after ${timeoutMs}ms`);
}

const url = await waitForTrack(track.id);
```

Poll every ~5 s with a timeout of a few minutes. Download links expire at `generations[].expired_at` — the window is your licence's `track_expiration_time` (900 s = 15 min on the common licence; check `GET /service/licenses`), so download the file instead of storing the URL.

## Endpoints Overview

| Endpoint | Description |
|----------|-------------|
| `POST /public/tracks` | Generate track from prompt, playlist, or image |
| `GET /public/tracks/{id}` | Get track by ID |
| `GET /public/tracks` | List all tracks (paginated) |
| `POST /public/tracks/{id}/similar` | **Fork** the track: generate a similar NEW track (`duration` required; the parent is untouched) |
| `POST /public/tracks/{id}/edit` | **Fork** the track into a NEW track with edited params/instruments/stems (the original is never modified) |
| `GET /public/playlists` | List available playlists |

(The API also exposes `POST /public/tracks/record` and `POST /public/tracks/stored`; they are out of scope for this skill.)

See [API Reference](references/api_reference.md) for full parameter details.

## Playlist Format

`playlist_index` must be one of the exact values returned by `GET /public/playlists` — a
three-part `category.group.channel` string such as `0.0.0`. Partial values like `0` or `0.0`
are rejected with `422`; there is no "broader level" that blends channels.

The three components name a category, a group and a channel, but only the whole string is a queryable value — the API checks `playlist_index` for existence in the playlist list, not by prefix.

| Level | Format | Example | Description |
|-------|--------|---------|-------------|
| Channel | `N.N.N` | `0.0.0` | The only form accepted as `playlist_index` (here: Moods / Calm / Calm) |

Live category numbering: 0 Moods, 1 Focus, 2 Sleep, 3 Calm, 4 Chill, 5 Sport, 6 Genres, 7 Game, 10 Countries. There are 139 channels; fetch the current list with `GET /public/playlists`.

### Available Playlists (examples)

| Playlist | Category | Group | Channel |
|----------|----------|-------|---------|
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

Only `track` returns exactly the requested duration; `loop` and `jingle` come back slightly short (measured 4.96 s and 4.93 s for a 5 s request) because they are trimmed to a musical boundary. Do not assert exact lengths for those modes.

| Mode | Description |
|------|-------------|
| `track` | Standard music track (default) |
| `loop` | Seamlessly looping track |
| `jingle` | Short musical jingle. Mubert documents jingle/mix for playlist mode only, but the API **accepts** them with `prompt`/`image` without any error — treat prompt+jingle as unsupported-but-silent, not rejected |
| `mix` | DJ-style mix. Same caveat as `jingle` |

## Common Parameters

Defaults come from your licence (`GET /service/licenses` → `default_bitrate`,
`default_intensity`, `default_format`, `default_mode`); the values below are the common case.

| Parameter | Values | Default |
|-----------|--------|---------|
| `duration` | 5 … licence `max_track_duration` (1800), seconds | required |
| `prompt` | ≤ 255 characters | one of `prompt` / `playlist_index` / `image` required |
| `playlist_index` | exact three-part index from `GET /public/playlists`, e.g. `0.0.0` | — |
| `image` | png/jpg/jpeg/webp/bmp, 50 KB … ~1 MB | — |
| `bpm` / `key` | 1–500 / `Am`-style; playlist mode only | — |
| `bitrate` | 32, 96, 128, 192, 256, 320 | 128. **Ignored when `format` is `wav`** — wav generations always report 1411 |
| `format` | mp3, wav | mp3. With `wav` the API silently discards a requested `bitrate` and reports `1411` (16-bit/44.1 kHz stereo PCM) |
| `intensity` | low, medium, high | high |
| `mode` | track, loop, jingle, mix | track |

## Track Editing

> Every `/edit` and `/similar` call is a **new billable generation** and adds another row to `GET /public/tracks`. There is no in-place, free edit.

Editing **forks**. `POST /public/tracks/{id}/edit` leaves the original untouched and returns a **brand-new track** with its own `id` and `session_id`, its own `processing` generation, and its own billing. Always read `data.id` out of the edit response and poll *that* id — polling the parent will never show the edit, because the parent keeps exactly the generations it already had. The same is true of `POST /public/tracks/{id}/similar`.

The edit parameters are not echoed anywhere in the response, and `mode` and `prompt` are **silently ignored** on `/edit` — there is no way to change them by editing and no error tells you so.

### Replace or delete instruments

Available instruments (UPPERCASE — `drums` is rejected): `DRUMS`, `PERCS`, `HATS`, `CLAPS`, `BASS`, `MIDS`, `LEADS`, `FX`, `VOCALS`, `PADS`, `RISER`, `IMPACT`. An invalid value returns `422` keyed by index (`replace_instruments.0`) with a message that does not list the valid options.

```python
# Replace specific instruments — returns a NEW track that must be polled
resp = requests.post(f"{BASE}/public/tracks/{track_id}/edit", headers=HEADERS, json={
    "replace_instruments": ["DRUMS", "BASS"]
})
if resp.status_code != 200:
    raise RuntimeError(f"Mubert {resp.status_code}: {resp.text}")
edited = resp.json()["data"]
url = wait_for_track(edited["id"])   # the fork's id, NOT track_id

# Delete instruments — also a fork, also a fresh generation
resp = requests.post(f"{BASE}/public/tracks/{track_id}/edit", headers=HEADERS, json={
    "delete_instruments": ["VOCALS", "FX"]
})
if resp.status_code != 200:
    raise RuntimeError(f"Mubert {resp.status_code}: {resp.text}")
stripped = resp.json()["data"]
print(stripped["id"], "!=", track_id)
```

```typescript
// Replace specific instruments — returns a NEW track that must be polled
const editRes = await fetch(`${BASE}/public/tracks/${trackId}/edit`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ replace_instruments: ["DRUMS", "BASS"] }),
});
if (!editRes.ok) throw new Error(`Mubert ${editRes.status}: ${await editRes.text()}`);
const { data: edited } = await editRes.json();
const editedUrl = await waitForTrack(edited.id); // the fork's id, NOT trackId

// Delete instruments — also a fork, also a fresh generation
const stripRes = await fetch(`${BASE}/public/tracks/${trackId}/edit`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ delete_instruments: ["VOCALS", "FX"] }),
});
if (!stripRes.ok) throw new Error(`Mubert ${stripRes.status}: ${await stripRes.text()}`);
const { data: stripped } = await stripRes.json();
console.log(stripped.id !== trackId);
```

### Replace or delete stems

Available stems (UPPERCASE): `DRUMS` (includes DRUMS, PERCS, HATS, CLAPS), `BASS`, `LEADS` (includes MIDS, LEADS, PADS), `VOCALS`, `FX` (includes FX, RISER, IMPACT). The membership mapping is documented by Mubert only — the API never returns it and never validates against it.

```python
resp = requests.post(f"{BASE}/public/tracks/{track_id}/edit", headers=HEADERS, json={
    "replace_stems": ["DRUMS", "LEADS"]
})
if resp.status_code != 200:
    raise RuntimeError(f"Mubert {resp.status_code}: {resp.text}")
restemmed = resp.json()["data"]
url = wait_for_track(restemmed["id"])   # again, the fork's id
```

```typescript
const stemRes = await fetch(`${BASE}/public/tracks/${trackId}/edit`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ replace_stems: ["DRUMS", "LEADS"] }),
});
if (!stemRes.ok) throw new Error(`Mubert ${stemRes.status}: ${await stemRes.text()}`);
const { data: restemmed } = await stemRes.json();
const restemmedUrl = await waitForTrack(restemmed.id); // again, the fork's id
```

### Generate a similar track

`POST /public/tracks/{id}/similar` requires `duration` (min 5); `bitrate`, `format`, `intensity` and `mode` are optional. Like `/edit` it forks: the response is a new track with a new `id` and `session_id`, it does not inherit the parent's `playlist_index` or `prompt`, and it carries no pointer back to the parent.

```python
resp = requests.post(f"{BASE}/public/tracks/{track_id}/similar", headers=HEADERS, json={
    "duration": 45,       # required — omitting it is a 422
    "mode": "loop",
})
if resp.status_code != 200:
    raise RuntimeError(f"Mubert {resp.status_code}: {resp.text}")
similar = resp.json()["data"]
url = wait_for_track(similar["id"])   # the new track, not track_id
```

## Authentication

| Headers | Use case |
|---------|----------|
| `customer-id` + `access-token` | All track generation and library endpoints |

## Error Handling

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`.
Validation failures return `422` with `message` + an `errors` object keyed by field, and
**no** `code`. A `404` from a UUID route carries only `message`.

- **401** — invalid or missing `customer-id` / `access-token`, or a deleted customer. Body: `{"message": "Unauthenticated", "code": "Unauthenticated"}`
- **403** — licence/limit refusal: `LicenseForbiddenDuration` (with `max_track_duration`), `LicenseForbiddenFeature` / `Bitrate` / `Intensity` / `Format` / `Mode`, and the track-count/duration/concurrency limits. `LicenseNotFound` is a 403 too, not a 404
- **404** — unknown track id, or a `session_id` on the UUID route. Body is Laravel's raw `{"message": "No query results for model [App\\Models\\Track] <id>"}` with **no** `code` — do not match on `code: TrackNotFound`
- **413** — image upload above ~1 MiB. nginx returns an **HTML** page, so `resp.json()` throws — check the status and `Content-Type` before parsing
- **422** — invalid parameters (bad enum, missing required field, unknown `playlist_index`, over-long `prompt`). Body: `{"message": ..., "errors": {"<field>": [...]}}`, array elements keyed by index (`replace_instruments.0`)

Never branch on `code` without checking that it exists.

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)