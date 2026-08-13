# API Reference — Track Generation

Base URL: `https://music-api.mubert.com/api/v3`

Successful JSON responses are wrapped in a top-level `data` key — read `resp.json()["data"]`, not the body itself. The models described below are the contents of `data`. Paginated list endpoints (`GET /public/tracks`) add a sibling `meta` block with `offset`, `limit` and `total`; `GET /public/playlists` is not paginated and returns `data` only, with no `meta`.

Defaults come from your licence (`GET /service/licenses` → `default_bitrate`,
`default_intensity`, `default_format`, `default_mode`); the values below are the common case.

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`.
Validation failures return `422` with `message` + an `errors` object keyed by field, and
**no** `code`. A `404` from a UUID route carries only `message`.

```json
{ "message": "It is not possible to generate a track of this duration", "max_track_duration": 1800, "code": "LicenseForbiddenDuration" }
```

| Condition | Status | Body |
|---|---|---|
| bad/missing/mismatched credentials, deleted customer | **401** | `{"message": "Unauthenticated", "code": "Unauthenticated"}` |
| licence feature / bitrate / intensity / format / mode / duration refusal, limit exceeded | **403** | `{"message": ..., "code": "LicenseForbidden…", ...extras}` |
| unknown track id on a UUID route | **404** | `{"message": "No query results for model [App\\Models\\Track] <id>"}` — **no `code`** |
| image upload above ~1 MiB | **413** | an nginx **HTML** page, not JSON — `resp.json()` throws |
| invalid enum value, missing required field, invalid `playlist_index`, over-long `prompt` | **422** | `{"message": ..., "errors": {"<field>": [...]}}` — **no `code`**, array elements keyed by index (`replace_instruments.0`) |

Common 403 codes: `LicenseForbiddenFeature` (the feature is not enabled on the licence — check `features` via `GET /service/licenses`), `LicenseForbiddenDuration`. Never branch on `code` without checking that it exists, and never claim a `description` field — the API does not emit one.

---

## Track Generation

### `POST /public/tracks` - Generate from playlist

Generate a track using a specific playlist/channel.

**Headers:** `customer-id`, `access-token`, `Content-Type: application/json`

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `playlist_index` | string | Yes | One of the exact values returned by `GET /public/playlists` — a three-part `category.group.channel` string such as `0.0.0`. Partial values like `0` or `0.0` are rejected with `422`; there is no "broader level" that blends channels |
| `duration` | integer | Yes | Seconds. Minimum **5** (`422` below that); the maximum is the licence's `max_track_duration` (1800 on the common licence) and exceeding it is a **403** `LicenseForbiddenDuration`, not a 422 |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: the licence's `default_bitrate` (128) |
| `format` | string | No | `mp3` or `wav`. Default: the licence's `default_format` (`mp3`). With `wav` the requested `bitrate` is silently discarded and the generation reports `1411` |
| `intensity` | string | No | `low`, `medium`, `high`. Default: the licence's `default_intensity` (`high`) |
| `mode` | string | No | `track`, `loop`, `jingle`, `mix`. Default: the licence's `default_mode` (`track`) |
| `bpm` | integer | No | 1–500, and expected to fall inside one of this playlist's `params[].bpm` windows from `GET /public/playlists`. **Prohibited** unless `playlist_index` is set |
| `key` | string | No | `TrackKeyScaleEnum` value — `Am`-style, not `"A minor"`. Expected to be in the playlist's `params[].keys`. **Prohibited** unless `playlist_index` is set |

A `bpm`/`key` outside the playlist's advertised window is refused with a `422` whose body has `message`/`errors` but no `code`. That check runs only after every field rule has passed, so it never shows up in a probe that fails an earlier rule — the global bounds (`bpm` 1–500) are what a malformed request reports.

**Response:** `200 OK` - Track model.

---

### `POST /public/tracks` - Generate from text prompt

`bpm` and `key` are **rejected** in this mode (`422 The bpm field is prohibited when playlist index is empty.`) — they exist only for playlist mode.

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes* | Text description, max **255** characters — 256+ is rejected with `422 The prompt field must not be greater than 255 characters` (no truncation). *Exactly one of `prompt` / `playlist_index` / `image` is expected; the API only enforces "at least one" and silently accepts several with undefined precedence |
| `duration` | integer | Yes | Seconds, minimum 5; the maximum is the licence's `max_track_duration` (403 `LicenseForbiddenDuration` above it) |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: the licence's `default_bitrate` (128) |
| `format` | string | No | `mp3` or `wav`. Default: the licence's `default_format` (`mp3`); `wav` discards `bitrate` and reports `1411` |
| `intensity` | string | No | `low`, `medium`, `high`. Default: the licence's `default_intensity` (`high`) |
| `mode` | string | No | `track` or `loop`. Default: the licence's `default_mode` (`track`). `jingle`/`mix` are documented for playlist mode only but are **accepted** here without error |

---

### `POST /public/tracks` - Generate from image

**Content-Type:** `multipart/form-data` (send `duration` and the other options as form fields — there is no JSON body on this path). The response records nothing about the image: `prompt` and `playlist_index` are both `null`, so image-sourced tracks cannot be identified later.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | file | Yes | PNG, JPG/JPEG, WEBP or BMP. Minimum **50 KB** (`422` below that). The documented 10 MB app limit is unreachable: uploads over ~1 MiB are cut off by nginx with an **HTML** `413 Request Entity Too Large` and no JSON body — keep images under 1 MB |
| `duration` | integer | Yes | Seconds, minimum 5. Multipart has no types, so it travels as a string; the API casts it |
| `bitrate` | integer | No | 32, 96, 128, 192, 256, 320. Default: the licence's `default_bitrate` (128). Also cast from a string on this path |
| `format` | string | No | `mp3` or `wav`. Default: the licence's `default_format` (`mp3`) |
| `intensity` | string | No | `low`, `medium`, `high`. Default: the licence's `default_intensity` (`high`) |
| `mode` | string | No | `track` or `loop`. Default: the licence's `default_mode` (`track`) |

`bpm` and `key` are prohibited here too — they require `playlist_index`.

---

### `GET /public/tracks/{track_id}` - Get track

`{track_id}` is the track's `id` (UUID), not its `session_id`.

**Response:** `200 OK` - Track model, or `404` for an unknown id — the body is Laravel's raw `{"message": "No query results for model [App\\Models\\Track] <id>"}` with **no** `code` key, so do not match on `code: TrackNotFound`.

---

### `GET /public/tracks/session/{session_id}` - Get track by session id

**Response:** `200 OK` - Track model.

---

### `GET /public/tracks` - List tracks

**Query Parameters:** `limit` (optional, min 1, defaults to 100), `offset` (optional, min 0), `order` (`asc`/`desc`), `order_by`. Default ordering is newest first.

**Response:** `200 OK` - Array of track models in `data` (newest first), plus a `meta` block: `{ "offset": 0, "limit": 100, "total": 1 }`. `total` counts every generated track, including the tracks produced by `/edit` and `/similar`.

---

### `POST /public/tracks/{track_id}/similar` - Generate similar

**Body:** `duration` (**required**, min 5), plus optional `bitrate`, `format`, `intensity`, `mode`. Omitting `duration` is a `422`.

**Response:** `200 OK` — a **new** track (new `id` and `session_id`). It does not inherit the parent's `playlist_index` or `prompt` and carries no pointer back to the parent; the parent is not modified. This is a fresh billable generation.

---

## Track Editing

Every `/edit` call **forks**: it returns a brand-new track with its own `id`, `session_id` and `processing` generation, leaves the parent untouched, costs another generation, and adds another row to `GET /public/tracks`. Poll the id from the edit response, never the parent's.

### `POST /public/tracks/{track_id}/edit` - Edit parameters

**Body:** `duration`, `bitrate`, `format`, `intensity` (all optional). `mode` and `prompt` are **silently ignored** here — there is no way to change them by editing, and no error tells you so.

---

### `POST /public/tracks/{track_id}/edit` - Replace instruments

```json
{ "replace_instruments": ["DRUMS", "BASS", "LEADS"] }
```

Available (UPPERCASE only — `drums` is rejected): `DRUMS`, `PERCS`, `HATS`, `CLAPS`, `BASS`, `MIDS`, `LEADS`, `FX`, `VOCALS`, `PADS`, `RISER`, `IMPACT`. An invalid element returns `422` keyed by index (`replace_instruments.0`); the message never lists the permitted values.

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

Stem names are UPPERCASE and validated per element (`replace_stems.0`). The membership mapping above comes from Mubert's own docs only — the API never returns it and never validates against it.

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

**Response:** `200 OK` — `data` holds an array of 139 playlist objects with `playlist_index`, `category`, `group`, `channel`, and `params`. There is **no** `meta` block on this endpoint. `params` is an **array** of `{ "bpm": { "gt": N, "lt": N }, "keys": [...] }` objects, not a single object; a `bpm`/`key` you send with a create must fall inside one of these windows.

Every `playlist_index` returned here is three-part (`category.group.channel`). These strings are the only accepted values — the API validates `playlist_index` by existence, not by prefix.

---

## Track Model

```json
{
  "id": "track-id",
  "session_id": "session-id",
  "playlist_index": "0.0.0",
  "prompt": "text prompt if used",
  "duration": 30,
  "intensity": "high",
  "mode": "track",
  "key": "Cm",
  "bpm": 120,
  "generations": [
    {
      "session_id": "gen-session-id",
      "format": "mp3",
      "bitrate": 128,
      "status": "done",
      "generated_at": "2024-01-01T00:00:00Z",
      "expired_at": "2024-01-01T00:15:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "url": "https://..."
    }
  ]
}
```

That is the **complete** field list. There is no track-level `bitrate` and no track-level `created_at`, `status` or `url`: `bitrate` and `format` live on each entry of `generations[]`, and so do `status` and `url`. `bpm` and `key` are `null` in the create response for prompt and image mode and are back-filled once generation finishes. `expired_at` is `generated_at` + the licence's `track_expiration_time` (900 s on the common licence).

### Generation status

Generation is asynchronous. `POST /public/tracks` returns immediately with a track whose generations are still rendering; poll `GET /public/tracks/{track_id}` until the status is terminal.

| Status | Meaning |
|--------|---------|
| `processing` | Rendering — keep polling |
| `done` | Ready — `url` is populated |
| `failed` | Generation failed — stop polling |

`url` is present as `null` from the first response and is filled in once the status is `done`; every endpoint that returns the track (create, show, list) follows this rule. Gate on the status, not on the presence of the key.

`{track_id}` is the track's `id` (UUID). Passing `session_id` here returns `404` — use `GET /public/tracks/session/{session_id}` for that identifier.