---
name: cast-mcp
description: Use this skill whenever the user wants to EDIT or FINISH spoken audio — a podcast episode, interview, lecture, voice memo — and the Mubert Cast MCP server is connected (tools named `cast_get_account`, `cast_import_audio`, `cast_first_pass`, `cast_build_project`, `cast_export`). Triggers on {podcast, episode, raw recording, remove ums, filler words, cut pauses, clean up audio, enhance voice, add intro music, ducking, chapters, loudness, export for Spotify, finish my episode, make it shorter, cut to N minutes}. For music alone — a track, a jingle, a stream — with no recording to edit, the `mubert-music-mcp` skill is the right one.
metadata:
  author: mubert
  version: '1.1'
---

# Mubert Cast via MCP

The Cast MCP server (`https://cast-mcp.mubert.com/mcp`) turns a raw recording into a finished
episode in the user's Cast account: transcript, cleanup, voice enhancement, licensed Mubert music
ducked under the voice, chapters, and a loudness-normalised export.

Read this before the first tool call.

---

## 1. Who does what

Three layers make a great episode. Use each for what it is best at.

| Layer | Best at | Tools |
| --- | --- | --- |
| **First Pass**, Cast's own editor | The cleanup. It hears the audio: a verbatim transcript catches every um/uh; it cuts hesitations, false starts, restarts and repeats, keeps the discourse words that carry meaning, fixes names, shortens pauses, writes chapters and scores a music bed for this episode. | `cast_first_pass` |
| **You**, the agent | What the user asked for: a target length ("15 minutes"), topics to drop, an intro to keep, a batch of episodes, a pipeline around them. | `cast_get_transcript`, `cast_plan_cuts`, `cast_build_project` |
| **The Cast editor**, the user | Finishing by ear: swap or regenerate the music, set the ducking depth, fix any word as text, run Enhance. | the `editor_url` you hand over |

You cannot reproduce First Pass with `cast_analyze` + `cast_plan_cuts`. Those read a
non-verbatim transcript, so most um/uh are missing, and the filler detector also flags discourse
words ("so", "like", "well") that often carry meaning ("as well", "I like it"). The best result is
always **First Pass for the cleanup, your cuts on top, the editor for the finish**.

---

## 2. The order of operations

1. **`cast_get_account`.** Plan, credits and limits decide the route. A Free account over MCP gets
   half the app's upload minutes, projects, storage and credits, and 3 exports a month.
2. **Get the recording.** `cast_list_audio` if the user says it is already in Cast (pass a larger
   `limit` for older files); otherwise `cast_import_audio` with a direct download link. The remote
   server cannot read the user's disk.
3. **`cast_transcribe`**, then wait on its task. Never start it twice for the same file.
4. **`cast_first_pass action="status"`.** This is the before/after preview of the first minute.
   Tell the user what it found (the legend), give them the before/after links, and the editor link
   if there is one.
   - `offered` means there is no preview yet for this file: a preview costs a few credits (`run`).
   - A ready preview on a **paid** plan: offer `apply` for the whole episode. Quote first (below).
   - A ready preview on **Free**: whole-episode First Pass is on paid plans from Lite. Say what the
     preview did, and hand them `cast_checkout {plan:"lite"}`. This is the step that turns the
     preview into a finished episode.
5. **Your part, on top.** Read the transcript (`cast_get_transcript`) and turn the user's asks into
   `cast_plan_cuts {word_ranges | ranges | phrases}`, with `exclude_ranges` for anything they want
   intact. For a target length, keep the thread of the conversation and drop tangents and repeats,
   not the answers. Merge your cuts with the First Pass cuts.
   - **Without First Pass** (the user declined, or the plan cannot apply it), `markers.fillers`
     cuts hesitations only. Cut discourse words only when the user names them
     (`markers.discourse:true` or `phrases`).
6. **`cast_enhance_voice`** only when the recording needs it (noise, room). Free plans get a
   60-second preview over the API; the full file is free in the editor.
7. **Music.** The First Pass bed is scored for this episode, so prefer it. Otherwise:
   `library` (already owned) → `curated` (staff picks; check `duration_sec`, some are short) →
   `generate` (paid, quote). `formats` only lists the styles `generate` takes; it returns no audio.
8. **`cast_build_project`** with the cuts, chapters and music. Then **always** hand over the editor
   link and say what they can do there: swap or regenerate the music, set the ducking, fix any
   word as text, run Enhance.
9. **`cast_export`** when they are happy: `mp3` or `wav`, a loudness preset (`podcast`, `youtube`,
   `broadcast`). Plus and Max get a commercial-license PDF with every export. It is minted a moment
   after the render and lands on the Exports page.

---

## 3. Money: quotes, and selling honestly

Three things cost credits. Each answers with a **quote** first (`quote_id`, price, balance before
and after) and spends only when the same tool is called again with that `quote_id`:

| Action | Costs |
| --- | --- |
| `cast_first_pass action="run"` | a preview beyond the free one (a few credits) |
| `cast_first_pass action="apply"` | the whole episode: 100 credits per started 10 minutes, paid plans |
| `cast_add_music mode="generate"` | a full-length track, priced by length |

- **Show the quote, say what it buys, and wait for a yes.** "First Pass on the whole 33 minutes is
  400 credits: every um, false start and long pause cut, chapters, and a bed scored for it. You'd
  have 5,060 left." Never confirm a quote on your own, even when the balance covers it.
- **Sell with evidence, not adjectives.** The preview legend and the before/after links are the
  pitch. Let the user hear it.
- **At a wall, give both doors.** First, what is free in the editor: exports, full-length enhance,
  editing by text. Second, the upgrade that unlocks the step (`cast_checkout {plan}`). Agents
  cannot pay, so hand the link to the human.

---

## 4. Long jobs

Transcribing, enhancing, First Pass apply, music and exports are jobs. Each tool waits up to
`wait_seconds` (default 50; most clients time a call out at 60) and otherwise returns a
`task_id`. Poll it with `cast_get_task`. A queued job can sit at 0% for a few minutes: that is the
queue, not a failure. Wait, keep polling, and tell the user. Never start the same job twice.

---

## 5. When something fails

- **402 / 403 plan walls**: explain what the step needs, then give both doors (section 3). Do not
  retry.
- **A quote expired** (quotes live 10 minutes): call without `quote_id` for a fresh one and show
  it again.
- **401**: the connection was revoked or expired. Ask the user to reconnect the Cast server in
  their assistant. Never ask them to paste a token into the chat.

---

## 6. Anti-patterns

- Confirming a `quote_id` without the user's explicit yes.
- Cleaning up with `cast_analyze` + `cast_plan_cuts` when First Pass is available. The result is
  worse, and the user never hears what Cast can do.
- Cutting discourse words ("so", "like", "well", "actually") blind.
- Running `cast_first_pass action="apply"` before the user heard the preview.
- Ending without the editor link. The finish happens there.
- Generating music before checking the First Pass bed, the library and curated picks.
- Re-importing the same file to "start clean". Every upload counts against the plan.
- Promising what Cast does not do: it edits audio only (no video), and it does not publish to
  Spotify, Apple or YouTube. The user uploads the export themselves.
