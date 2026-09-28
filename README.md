# Mubert Agent Skills

Agent Skills for the [Mubert Music API v3](https://mubert.com/api) — royalty-free AI music generation, streaming, and library access for your apps, games, videos, and other projects.

## Skills

| Skill | Description |
|-------|-------------|
| [mubert-setup](mubert-setup/) | Onboarding wizard — get API key, validate, save to `.env`, choose single-user or multi-user setup |
| [mubert-generate](mubert-generate/) | Generate tracks from text prompts, images, or playlists. Edit instruments and stems. |
| [mubert-streaming](mubert-streaming/) | Stream real-time AI music with intensity control, loop mode, and restart |
| [mubert-library](mubert-library/) | Browse and filter the pre-made music library by genre, theme, BPM, activity |
| [mubert-manage](mubert-manage/) | Manage licenses, customers, and webhooks (service-level administration) |

## MCP servers

When one of these servers is connected, its skill tells the agent how to use the tools; the raw-API skills above stay the right choice for writing code that calls the Mubert API.

| Skill | Server | For |
|-------|--------|-----|
| [mubert-music-mcp](mubert-music-mcp/) | `https://mcp.mubert.com/mcp` | Generate, edit and stream royalty-free music; search the library |
| [cast-mcp](cast-mcp/) | `https://cast-mcp.mubert.com/mcp` | Turn a raw podcast recording into a finished episode with [Mubert Cast](https://mubert.com/tools/cast): transcript, filler and pause removal, voice enhancement, music with auto-ducking, chapters, export |

## Installation

```bash
npx skills add MubertAI/skills
```

## Getting Started

1. Get your API key at [mubert.com/api](https://mubert.com/api)
2. Ask your AI assistant: **"Set up Mubert API"** — the `mubert-setup` skill will walk you through configuration
3. Start creating: **"Generate a 30 second chill lo-fi track"**

## Typical Flow

```
mubert-setup → configure credentials
    ↓
mubert-generate → create tracks from prompts/playlists/images
mubert-streaming → stream real-time music in your app
mubert-library → discover tracks by genre, mood, BPM
    ↓
mubert-manage → manage customers, licenses, webhooks at scale
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Required by | Description |
|----------|-------------|-------------|
| `MUBERT_COMPANY_ID` | manage, setup (also generate/streaming when minting a customer) | Company identifier (service-level) |
| `MUBERT_LICENSE_TOKEN` | manage, setup | License token (service-level) |
| `MUBERT_CUSTOMER_ID` | generate, streaming, library | Customer identifier (public-level) — `data.id` from `POST /service/customers` |
| `MUBERT_ACCESS_TOKEN` | generate, streaming, library | Access token (public-level) — `data.access.token` from the same response |
| `MUBERT_NAMESPACE` | multi-user setups | Prefix scoping per-user `custom_id`s to one app **and** environment |

The signup email contains only the two service-level values. The public-level pair exists only after a customer is created via the service API — service credentials are rejected by public endpoints.

In a multi-user app the public-level pair is minted per user at runtime and belongs in your database, not in `.env` — a shared `MUBERT_CUSTOMER_ID` means every user draws on one customer and one usage counter. `MUBERT_NAMESPACE` keeps staging from colliding with production: `custom_id` is unique per company and creation is find-or-create, so two deployments that derive the same `custom_id` silently share one customer and one token.

## All Music is Royalty-Free

Every track generated or streamed through the Mubert API is **royalty-free** and cleared for commercial use — apps, games, videos, podcasts, social media, and more. No copyright claims, no additional licensing fees.

## Structure

```
skills/
├── README.md
├── .env.example
├── mubert-setup/
│   └── SKILL.md
├── mubert-generate/
│   ├── SKILL.md
│   └── references/
├── mubert-streaming/
│   ├── SKILL.md
│   └── references/
├── mubert-library/
│   ├── SKILL.md
│   └── references/
├── mubert-manage/
│   ├── SKILL.md
│   └── references/
├── mubert-audio-montage/
│   └── SKILL.md
├── mubert-music-mcp/
│   └── SKILL.md
├── cast-mcp/
│   └── SKILL.md
├── tests/
│   ├── README.md
│   ├── lint_docs.py
│   └── contract/
└── evals/
    ├── mubert-setup/
    │   ├── evals.json
    │   └── trigger_eval.json
    ├── mubert-generate/
    │   ├── evals.json
    │   └── trigger_eval.json
    ├── mubert-streaming/
    │   ├── evals.json
    │   └── trigger_eval.json
    ├── mubert-library/
    │   ├── evals.json
    │   └── trigger_eval.json
    └── mubert-manage/
        ├── evals.json
        └── trigger_eval.json
```

## API Documentation

- [Mubert API v3 Docs](https://mubert.com/api/docs)
- [Swagger](https://music-api.mubert.com/api/v3/swagger)
