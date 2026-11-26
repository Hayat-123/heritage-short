# ARCHITECTURE.md — The Coffee That Carries a Story

## Overview

A linear five-stage pipeline that transforms a machine-readable storyboard into a finished film in two aspect ratios, using only free tools and APIs.

```
storyboard.json  ──►  00_validate
                           │
                           ▼
                       01_keyframes  ◄──  Cloudflare Workers AI (optional)
                           │                FLUX.2 klein / FLUX.1 schnell
                           ▼
           ┌───────────────┴──────────────────┐
           │                                  │
       02_video                       02_video_fallback
   (Wan 2.2, Kaggle)             (Ken Burns, FFmpeg, local)
           │                                  │
           └───────────────┬──────────────────┘
                           ▼
                       03_music  ◄──  ACE-Step 1.5 (Kaggle, optional)
                           │          or placeholder silence (local)
                           ▼
                       05_endcard  ◄─  Cloudflare FLUX or FFmpeg drawtext
                           │
                           ▼
                       04_assemble
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        film_16x9.mp4            film_9x16.mp4
       (1920×1080, H.264)      (1080×1920, H.264)
```

## Stage Contract

Every stage reads **only** from `storyboard.json` and cached outputs in `assets/`.  
No stage reaches into another stage's source files.

| Stage | Reads | Writes |
|-------|-------|--------|
| 00_validate | storyboard.json, storyboard.schema.json | — |
| 01_keyframes | storyboard.json | assets/keyframes/<hash>.png |
| 02_video | storyboard.json, assets/keyframes/ | assets/shots/<id>.mp4 |
| 02_video_fallback | storyboard.json, assets/keyframes/ | assets/shots/<id>_fallback.mp4 |
| 03_music | storyboard.json | assets/music/score.wav |
| 05_endcard | storyboard.json | assets/keyframes/shot_10.png |
| 04_assemble | storyboard.json, assets/shots/, assets/music/, assets/audio/ | outputs/film_16x9.mp4, outputs/film_9x16.mp4 |

## Caching

```python
# cache key = SHA-256(stage + shot_id + image_prompt + motion_prompt + seed)[:16]
key  = cache_key("keyframes", shot, extra={"width": 1360, "height": 768})
path = KEYFRAMES / f"{key}.png"
if path.exists():
    skip()   # no API call, no log entry
```

Changing any storyboard field for a shot changes its hash → that shot regenerates.  
All other shots keep their cached outputs.

## Shot Source Priority (04_assemble.py)

```
1. assets/shots/<id>.mp4            ← Wan 2.2 real video (best quality)
2. assets/shots/<id>_fallback.mp4   ← Ken Burns pan/zoom (always available)
```

## Audio Pipeline

```
assets/audio/narration/01.wav ─┐
assets/audio/narration/02.wav ─┤  adelay each clip to absolute timestamp
...                            ─┤
assets/audio/narration/09.wav ─┘
        │
        ▼
narration_timeline.wav   (all clips mixed at correct positions)
        │
assets/music/score.wav ──► sidechaincompress (narration ducks music −12 dB)
        │
        ▼
mixed_audio.wav   ──► loudnorm (EBU R128, −14 LUFS, −1 dBTP)
```

## Subtitle Burning

SRT is generated from `storyboard.json` narration_clips timing.  
Each clip's absolute timestamp = Σ(previous shot durations) + clip.offset_s.  
FFmpeg `subtitles=` filter burns open captions into the picture.

## Failure Handling & Resilience

The pipeline implements defensive programming and multi-tier fallbacks so execution never crashes unexpectedly:

1. **API Retries & Network Resiliency:**
   - In `pipeline/01_keyframes.py`, remote API calls implement retry loops with exponential backoff.
   - If Cloudflare Workers AI returns a 429 (rate-limit) or 5xx (server error), the script pauses and retries up to 3 times before recording the failure in `runs.jsonl`.

2. **Hierarchical Video Fallback:**
   - `04_assemble.py` checks for generated video in order of quality:
     1. `assets/shots/<id>.mp4` (Wan 2.2 real diffusion video).
     2. `assets/shots/<id>_fallback.mp4` (Ken Burns 24fps pan/zoom from keyframe).
   - If GPU access or quota runs out, the fallback stage runs in seconds on any CPU, guaranteeing a submittable film.

3. **Music Synthesis Fallback:**
   - `04_assemble.py` resolves music sources in priority order:
     1. `assets/audio/music/background.wav` (Primary synthesized or composed track).
     2. `assets/music/score.wav` (Legacy fallback score).
     3. Inline silence placeholder (automatically generated if neither exists, so video assembly can still be verified).

4. **Environment & Binary Discovery:**
   - Automated FFmpeg resolution: Checks `PATH`, default Windows Program Files, tools directories, and dynamically searches local WinGet package locations (`%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*`).
   - Fontconfig fallback: Explicitly maps Windows system TrueType fonts (`arial.ttf`, `arialbd.ttf`) with escaped drive colons to avoid libass/fontconfig crashes on Windows.

## Reproducibility

```bash
git clone <repo>
cd heritage-short
pip install jsonschema requests
# Install ffmpeg (winget install Gyan.FFmpeg on Windows)
make film          # or: python pipeline/run_all.py
```

One command produces the complete film using only the Ken Burns fallback path.  
Cloudflare keyframes and Wan 2.2 video are optional upgrades configured via `.env`.

## Logging

Every real model call appends one JSON line to `runs.jsonl`:
```json
{"ts":"…","stage":"keyframes","shot_id":"shot_03","model":"@cf/black-forest-labs/flux-2-klein",
 "provider":"cloudflare-workers-ai","params":{…},"cache_hit":false,"latency_s":1.84,
 "cost_usd":0.0,"cost_note":"within daily free allowance","output_path":"…","ok":true}
```
Cache hits are **not** logged (no API call occurred).  
Fake or placeholder entries are **never** written.
