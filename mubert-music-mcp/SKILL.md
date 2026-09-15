---
name: mubert-music-mcp
description: Use this skill whenever the user wants MUSIC — generating a track, scoring a video, finding background music, adding a soundtrack, a jingle, a loop, or a live stream — AND the Mubert Music MCP server is connected (tools named `get_capabilities`, `generate_track`, `search_library`, `start_stream`, `list_plans`). Triggers on any of {music, soundtrack, background music, score, jingle, loop, ambient, BGM, royalty-free music, stream music, lo-fi, generate a track}. PREFER THIS OVER `mubert-generate`, `mubert-library`, `mubert-streaming`, `mubert-manage`, `mubert-setup` whenever those tools are connected and the user wants music, not code: the tools already know the license's limits, so calling them beats generating HTTP snippets that may hit a 403. The siblings stay the right choice when the user is WRITING CODE that calls the Mubert API from their own product — a client library, a backend, webhooks — because that code runs without this server.
metadata:
  author: mubert
  version: "1.1"
---

# Mubert Music via MCP

The Mubert Music MCP server (`mcp.mubert.com/mcp`) generates royalty-free music, streams
it, and searches a pre-made catalogue. Everything it returns is cleared for commercial use.

Read this before the first tool call. The rules here exist because the alternative behaviours
cost the user real quota.

> **Music, or code?** This skill is for getting music *through the tools*. If the user is
> building their own integration — "write a Python client", "add Mubert to our backend",
> "set up the webhook" — that code will run without this server, so switch to the raw-API
> skills (`mubert-generate`, `mubert-library`, `mubert-streaming`, `mubert-manage`,
> `mubert-setup`). Even then, `get_capabilities` is the fastest way to learn what *this*
> license allows, and those real values belong in the snippet instead of guesses.

---

## 0. Connecting

The hosted server is streamable HTTP at `https://mcp.mubert.com/mcp`. Add the URL and nothing
else — `claude mcp add --transport http mubert-music https://mcp.mubert.com/mcp`, or the same
URL in a JSON config. On first use the client opens a browser page on the server where the
user either pastes the `company-id` and `license-token` from their Mubert confirmation email,
or picks a plan and pays first; the credentials then arrive by email and go into the same
page. The client keeps its own token; the license never enters the client config.

A backend, CI, or a client that cannot open a browser sends the credentials as headers instead:

```
Authorization: Bearer <license-token>
X-Mubert-Company-Id: <company-id>
X-Mubert-Client-Key: <stable id for this installation>   # optional
```

Either way the server provisions and caches its own Mubert customer, so there is no
`customer-id` or `access-token` to obtain — the `mubert-setup` skill's customer steps do not
apply here. Under OAuth the customer is keyed on the client's registration; with headers,
`X-Mubert-Client-Key` should stay stable across restarts, because each new value provisions a
new customer and consumes a seat.

If a tool answers `code=Unauthenticated` with `retryable=false`, the client is not connected:
tell the user to reconnect the server (which opens the browser page again) or to fix the
headers. Do not retry, and do not ask the user to paste a license token into the chat.

---

## 1. Mental model

A **license** decides what the user may ask for and how much of it they get. It is not a flat
API key: it carries an allowlist of bitrates, formats, modes and intensities, a maximum track
duration, and counters that reset daily, monthly, or never.

Everything expensive is metered:

| Action | Costs |
|---|---|
| `search_library` | nothing |
| `list_playlists`, `get_capabilities`, `get_track`, `wait_for_track` | nothing |
| `generate_track`, `generate_track_instant` | one track + its seconds |
| `regenerate_similar`, `edit_track` | **another** full track — these are not free tweaks |
| `start_stream` | streaming seconds while it plays |

---

## 2. The order of operations

**1. `get_capabilities` first.** Always, before the first generation of a session. It returns
the allowed values, the defaults, the max duration, and the remaining quota. Everything below
depends on it. It is free and cached.

**2. Try free before paid.** If the user needs background music and does not need it to be
unique, `search_library` may already have it. Only generate when the catalogue does not fit or
the user asked for something generated.

**3. Prefer a playlist over a prompt.** `list_playlists` gives a `category.group.channel`
taxonomy. Generating from a `playlist_index` is the only path that can be served instantly from
the pre-rendered store, and it is the only one that accepts `bpm` and `key`. Use a text `prompt`
when the brief is genuinely specific ("music box lullaby that turns menacing"), not when it maps
onto a genre the taxonomy already has.

**4. Round the duration to a stocked value when you can.** 5, 6, 8, 10, 15, 20, 30, 40, 60,
180, 240, 300. A 30-second request can return a finished track in one round trip; a 31-second
request always costs a full render. If the user said "about half a minute", use 30.

**5. Generate once.** Do not produce three options for the user to choose from unless they asked
for options. Each one is a track off their quota.

**6. Hand over the URL and say when it expires.** Generated audio is deleted — `get_capabilities`
reports the window, often 24 hours. If the user is building something, tell them to download it
now.

---

## 3. Choosing parameters

Omit anything the user did not specify. Omitted parameters take the license default; guessing
one that the license forbids wastes a call.

| Parameter | Say nothing unless |
|---|---|
| `bitrate` | the user cares about quality or file size |
| `format` | they need WAV for editing |
| `intensity` | the brief implies energy — `low` for ambient, `high` for driving |
| `mode` | they want a `loop` (games, apps), a `jingle`, or a `mix` |
| `bpm`, `key` | they gave a tempo or key **and** you are using a `playlist_index` |

`mode="loop"` is the right default for anything that plays under an app or game indefinitely.
`mode="track"` is right for video, where the music has an ending.

---

## 4. Refining a track step by step

This is the common shape of a session: generate something, then work on it —
*"now swap the bass"*, *"different lead"*, *"lose the vocals"*. `edit_track` does each step.

**Carry the id forward.** Every edit returns a **new** track and leaves the previous one
untouched. The next edit takes the id from the last result, not the original.

```
generate_track            -> v1
edit_track(v1, BASS)      -> v2      # "swap the bass"
edit_track(v2, LEADS)     -> v3      # "different lead"   <- v2, not v1
edit_track(v3, …VOCALS)   -> v4
```

Passing `v1` at the third step throws away the bass swap and returns success anyway. The
result's `important` field names the id to use next; `edited_from` shows where each track
came from.

**Budget the chain before starting it.** Every step is a full track off the quota. Five
refinements cost five tracks. If the user wants a long back-and-forth and the daily counter
is tight, say so before the first edit rather than stopping halfway.

**One part per step.** It keeps each change reviewable and avoids spending a track on a
combination nobody asked for. `replace_instruments` for a single part, `replace_stems` when
the user means a whole section.

**Translate what the user says into the vocabulary.**

| They say | Use |
|---|---|
| melody, lead, riff, "that horn/synth/дудка" | `LEADS` |
| pad, strings, chords, the bed underneath | `PADS` |
| a line under the lead, a stab | `MIDS` |
| bass, low end, 808 | `BASS` |
| beat, drums, kick, snare | `DRUMS` stem, or `PERCS`/`HATS`/`CLAPS` for one element |
| voice, vocal, singing | `VOCALS` |
| sweep into the drop | `RISER`; the hit itself is `IMPACT` |

**Never assert an edit landed.** Replacement is best-effort: with no alternative available at
that tempo and key, replacing a part **removes** it instead — and still returns success. Give
the user the new URL and let them listen. If they say it disappeared, that is what happened;
offer to regenerate rather than editing again.

There is no way to ask what a track contains. Work from what the user hears.

**When editing stops helping**, regenerate. Edits cannot change `mode`, and after several
rounds a fresh `generate_track` — or `regenerate_similar` for a variation on the same
material — is often closer than another swap.

## 5. Streaming vs generating

Generate a track when the music has a fixed length: a video, an ad, an intro.

`start_stream` when it should never stop and never repeat: a workout app, a game, a focus tool,
a venue. Then steer it live with `set_stream_intensity` (follow the workout's phases),
`set_stream_loop` (hold a mood over a menu screen), and `restart_stream` (fresh material, same
channel).

Two things to tell the user, once:

- **The stream URL is a credential.** It carries their access token in the query string. It
  goes to the audio player and nowhere else — not into a log, a document, or a page URL.
- **There is one stream at a time.** Calling `start_stream` again replaces the running one.

---

## 6. When something fails

Every error comes back with a `what_to_do` field. Follow it. In particular:

- **`retryable: false` means stop.** Do not retry the same call, do not vary a parameter and try
  again, do not fall back to another tool. Tell the user what happened.
- **Quota errors are not a reason to try smaller.** If the daily track count is spent, a shorter
  track does not help. If a *duration* quota is short, the message says how many seconds are
  left — offering that is fine.
- **`status: pending`** means the render outlived the wait budget. The track is not lost and the
  quota is already spent: call `wait_for_track` with the id you were given. Never start a second
  generation for the same brief.
- **Trial licenses cap `search_library`.** The result carries a `trial_cap` note when this
  happens; the tracks returned are the first 20 of the whole catalogue and do **not** match the
  requested filters. Say so rather than presenting them as matches, and do not paginate.

---

## 7. Money

`list_plans` needs no credentials — use it whenever the user asks what Mubert costs or hits a
limit that a bigger plan would solve. Note that a limit of `0` in a plan means unlimited.

`create_checkout_link` returns a Stripe URL. It charges nothing by itself. Before calling it:
name the plan, its price, and what changes. Ask for the billing email — never invent one. After
they pay, `get_capabilities` shows the new limits.

For an existing subscription — changing plan, updating a card, invoices, cancelling — use
`open_billing_portal`. There is deliberately no cancel tool.

---

## 8. Multi-user products

If the user is building something where **their** users each need music, `provision_customer`
mints per-user credentials with their own quota slice and their own stream. Seats are limited;
`list_customers` shows how many are left.

Nothing else needs this. The server already has a customer of its own for ordinary generation.

---

## 9. Anti-patterns

- Generating before calling `get_capabilities`.
- Generating several variations "so the user can pick" without being asked.
- Treating `edit_track` or `regenerate_similar` as a cheap tweak — both are full-price tracks.
- Editing the **original** id after the first edit — it silently discards every step since.
- Telling the user an instrument was replaced without them hearing it. Replacement that
  finds no candidate deletes the part instead, and still reports success.
- Retrying a `403`. It is an entitlement decision; it will not start succeeding.
- Passing `duration: 45` when the user said "about 40 seconds" — 40 is stocked, 45 is not.
- Pasting a stream URL into the chat, a file, or a commit.
- Presenting trial-capped library results as if they matched the filters.
- Reaching for `mubert-generate` / `mubert-library` / `mubert-streaming` to write raw HTTP when
  the user only wanted a track and these tools are connected. (Writing an integration is the
  opposite case — see "Music, or code?" at the top.)
