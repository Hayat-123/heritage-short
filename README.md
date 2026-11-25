# The Coffee That Carries a Story

**A heritage short film — AI Video Generation Challenge, Week 0**

> *Through the quiet ritual of preparing coffee, I discover that home is not only a place — it is the stories, values, and love passed from one generation to the next.*

---

## Watch the Film

- YouTube (16:9): [link to be added]
- Instagram Reels (9:16): [link to be added]

---

## Repository Structure

```
heritage-short/
├── storyboard.json          ← single source of truth (10 shots, 71 s)
├── storyboard.schema.json   ← JSON Schema (validated before every run)
├── Makefile                 ← make film  runs the whole pipeline
├── pipeline/
│   ├── 00_validate.py       ← validate storyboard against schema
│   ├── 01_keyframes.py      ← FLUX.2 klein via Cloudflare Workers AI (optional)
│   ├── 02_video_fallback.py ← Ken Burns pan/zoom via FFmpeg (primary)
│   ├── 02_video.py          ← Wan 2.2 TI2V-5B runner / Kaggle notebook helper
│   ├── 03_music.py          ← ACE-Step 1.5 (Kaggle) or placeholder silence
│   ├── 04_assemble.py       ← FFmpeg: concat, duck, subtitles, both ratios
│   ├── 05_endcard.py        ← end-card keyframe (FLUX or FFmpeg drawtext)
│   ├── run_all.py           ← Python alternative to make film
│   └── utils/
│       ├── cache.py         ← SHA-256 prompt hash → skip unchanged shots
│       ├── logger.py        ← append real API calls to runs.jsonl
│       └── srt.py           ← generate SRT from storyboard timing
├── assets/
│   ├── audio/
│   │   ├── narration_am.wav          ← 44.9 s combined Amharic narration
│   │   └── narration/01.wav … 09.wav ← per-sentence clips
│   ├── keyframes/           ← FLUX PNG outputs (cached by prompt hash)
│   ├── shots/               ← Wan 2.2 or Ken Burns MP4 outputs
│   └── music/score.wav      ← ACE-Step output or silence placeholder
├── outputs/
│   ├── film_16x9.mp4        ← 1920×1080, H.264
│   └── film_9x16.mp4        ← 1080×1920, H.264
├── runs.jsonl               ← append-only log of every real model call
├── DESIGN.md                ← audience intent + user test notes
├── ETHICS.md                ← consent, licences, labelling plan
├── EXPERIMENTS.md           ← hypothesis → change → result log
├── FAILURES.md              ← blockers and resolutions
├── ARCHITECTURE.md          ← pipeline design and contracts
└── COSTS.md                 ← actual costs and free-tier usage
```

---

## Quick Start

```bash
# 1. Clone
git clone <your-repo-url>
cd heritage-short

# 2. Install Python dependencies
pip install jsonschema requests

# 3. Install FFmpeg
#    Windows: winget install Gyan.FFmpeg
#    macOS:   brew install ffmpeg
#    Linux:   sudo apt install ffmpeg

# 4. Run the pipeline
make film
#    or on Windows without Make:
python pipeline/run_all.py
```

This produces `outputs/film_16x9.mp4` and `outputs/film_9x16.mp4` using the
Ken Burns fallback (no GPU, no paid APIs).

### Optional: Cloudflare keyframes

```bash
cp .env.example .env
# Edit .env with your CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN
make keyframes      # generates FLUX.2 klein images for every shot
make film           # re-assemble with real keyframes
```

### Optional: Wan 2.2 moving shots (Kaggle)

```bash
python pipeline/02_video.py --write-notebook   # prints a Kaggle notebook cell
# Upload keyframes to Kaggle, run the notebook, download shots/ folder
# Then: make film
```

---

## Pipeline Stages

| Stage | What it does | Provider | Cost |
|-------|-------------|----------|------|
| 00_validate | Schema + timing checks | local | free |
| 01_keyframes | Generate one image per shot | Cloudflare Workers AI (FLUX) | free |
| 02_video_fallback | Ken Burns pan/zoom | FFmpeg, local | free |
| 02_video | Real video generation | Wan 2.2 on Kaggle | free |
| 03_music | Background score | ACE-Step 1.5 on Kaggle | free |
| 04_assemble | Concat, duck, subtitles, export | FFmpeg, local | free |
| 05_endcard | AI end-card image | FLUX or FFmpeg drawtext | free |

**Total cost: \$0.00**

---

## Caching

Each shot is identified by a 16-character SHA-256 hash of its `image_prompt`,
`motion_prompt`, and `seed`.  If the output file exists, the stage skips it.
Changing one shot in `storyboard.json` regenerates only that shot.

---

## Logging

Every real API call is appended to `runs.jsonl` immediately after it completes.
Cache hits and local FFmpeg calls are not logged (no API call occurred).

---

## Film Details

| Property | Value |
|---|---|
| Duration | 71 seconds |
| Shots | 10 (8 narrated + 2 music-only) |
| Narration language | Amharic (am) |
| Subtitle language | English (en) |
| Narration duration | 44.90 s (pre-recorded) |
| Aspect ratios | 16:9 (1920×1080) + 9:16 (1080×1920) |
| Narration WAVs | 9 individual clips, pre-recorded |
| Music | ACE-Step 1.5 or silence placeholder |

---

## Licence

Code: MIT  
Narration audio: personal, all rights reserved  
AI-generated images and video: see ETHICS.md for model licences
