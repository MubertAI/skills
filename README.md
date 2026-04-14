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
| `MUBERT_COMPANY_ID` | manage, setup | Company identifier (service-level) |
| `MUBERT_LICENSE_TOKEN` | manage, setup | License token (service-level) |
| `MUBERT_CUSTOMER_ID` | generate, streaming, library | Customer identifier (public-level) |
| `MUBERT_ACCESS_TOKEN` | generate, streaming, library | Access token (public-level) |

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
