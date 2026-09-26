---
name: cast-mcp
description: Use this skill whenever the user wants to EDIT or FINISH spoken audio — a podcast episode, interview, lecture, voice memo — and the Mubert Cast MCP server is connected (tools named `cast_get_account`, `cast_import_audio`, `cast_first_pass`, `cast_build_project`, `cast_export`). Triggers on {podcast, episode, raw recording, remove ums, filler words, cut pauses, clean up audio, enhance voice, add intro music, ducking, chapters, loudness, export for Spotify, finish my episode}. For music alone — a track, a jingle, a stream — with no recording to edit, the `mubert-music-mcp` skill is the right one.
metadata:
  author: mubert
  version: '1.0'
---

# Mubert Cast via MCP

The Cast MCP server (`https://cast-mcp.mubert.com/mcp`) turns a raw recording into a finished
episode: transcript, filler and pause removal, voice enhancement, licensed Mubert music with
automatic ducking, chapters, and a loudness-normalised export with a license PDF. Everything
lands in the user's Cast account, so they can open the result in the Cast editor and keep going.

Read this before the first tool call. Most of it is about not spending the user's credits or
quota by accident.

---

## 0. Connecting

The hosted server is streamable HTTP. Add the URL and nothing else:
`claude mcp add --transport http cast https://cast-mcp.mubert.com/mcp`, or the same URL in a JSON
config. On first use the client opens a browser page: the user signs in to Cast and approves the
connection. Cast creates a token for this client; spending credits stays off unless the user
ticks it. They can revoke it any time in Cast → Settings → API & MCP.

A backend or CI that cannot open a browser sends a token from that settings page as a header:
`Authorization: Bearer mvl_pat_…`.

If a tool answers 401, the client is not connected (or the token was revoked): tell the user to
reconnect. Never ask them to paste a token into the chat.

---

## 1. Mental model

A Cast **project** is what the user ends up with: the recording on the voice lane, cuts applied
through the transcript, music on its own lane ducked under the voice, chapters. `cast_build_project`
creates it and returns an editor link. `cast_export` renders it.

Most of the pipeline is free. Three things cost money, and each of them answers with a **quote**
first — `quote_id`, the price, the balance before and after — and spends only when the same tool
is called again with that `quote_id`:

| Action                             | Costs                                   |
| ---------------------------------- | --------------------------------------- |
| `cast_first_pass` `action="run"`   | a preview beyond the free one           |
| `cast_first_pass` `action="apply"` | the whole episode — a paid-plan feature |
| `cast_add_music` `mode="generate"` | a generated track                       |

**Show the user the quote and wait for a yes before confirming.** Never confirm a quote on your
own, even when the balance covers it.

---

## 2. The order of operations

1. **`cast_get_account` first.** Plan, credits, and usage against limits. It decides what is
   possible in this session — a Free account over MCP gets half the app's upload minutes,
   projects, storage and credits, and 3 exports a month.
2. **`cast_import_audio`** with a URL the user gave you. The remote server cannot read files from
   the user's disk; ask for a link (Dropbox, Drive, S3, a direct URL).
3. **`cast_transcribe`**. Everything later works from word timings.
4. **Edit — pick one route:**
   - **`cast_first_pass`** when the user wants it done for them. `action="status"` shows the free
     preview Cast makes of the first stretch of the episode — what it cut, the chapter title,
     the music it picked. Let the user hear it (the editor link) before any `run` or `apply`.
   - **`cast_analyze` + `cast_plan_cuts`** when the user wants control or has specific asks —
     "remove the part about my ex", "cut every um but keep the 'you know's". `cast_plan_cuts` is a
     dry run: show its cut list, then build.
5. **`cast_enhance_voice`** only when the recording needs it (noise, echo). Free plans get a
   60-second preview.
6. **`cast_add_music`** — try `mode="curated"` or `mode="formats"` before `mode="generate"`: they
   are free and often enough. Use `record_mode="jingle"` for a sting, `"loop"` for a bed.
7. **`cast_build_project`** → hand the user the editor link.
8. **`cast_export`** when they are happy: `mp3` or `wav`, a loudness preset (`podcast`,
   `youtube`, `broadcast`), optional stems and license PDFs.

---

## 3. Long jobs

Transcribing, enhancing, music and exports are jobs. Each tool waits up to `wait_seconds`
(default 50 — most clients time a call out at 60) and otherwise returns a `task_id`. Poll it with
`cast_get_task`. Never start the same job twice because the first one is still running.

---

## 4. When something fails

- **402 / 403 plan walls** come back with a next step — usually a link to finish that exact
  project in the Cast editor, where more is free than over the API, or `cast_checkout` for an
  upgrade link. Hand the link over; do not retry.
- **A quote expired** (they live 10 minutes): call the tool again without `quote_id` for a fresh
  one and show it again.
- **401**: reconnect (section 0).

---

## 5. Anti-patterns

- Confirming a `quote_id` without the user's explicit yes.
- Running `cast_first_pass action="apply"` before the user heard the preview.
- Generating music before trying curated or formats.
- Re-importing the same file to "start clean" — every upload counts against the plan.
- Asking the user to paste a Cast token into the chat.
- Promising what Cast does not do: it edits audio only (no video), and it does not publish to
  Spotify, Apple or YouTube — the user uploads the export themselves.
