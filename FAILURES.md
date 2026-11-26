# FAILURES.md — The Coffee That Carries a Story

Record every real blocker: what failed, what you tried, and how you resolved or worked around it.
A log with no failures is not credible; every real pipeline run encounters something.

---

## Failure 001 — FFmpeg Not on PATH (Windows)

**Date:** 2026-11-25
**What happened:** `python pipeline/02_video_fallback.py` exited with:
```
ERROR: ffmpeg not found on PATH.
```
**What I tried:**
1. Checked `where ffmpeg` in PowerShell — command not found.
**How I resolved it:**
- Run: `winget install Gyan.FFmpeg`
- Then restart PowerShell to pick up the new PATH entry.
- Alternative: download static build from https://ffmpeg.org/download.html and add to PATH manually.

**Time lost:** ~10 minutes

---

## Failure 002 — jsonschema not installed

**Date:** 2026-11-25
**What happened:** `python pipeline/00_validate.py` failed with `ModuleNotFoundError: No module named 'jsonschema'`
**Resolution:** `pip install jsonschema`

---

## Failure 003 — Cloudflare Workers AI FLUX 400 Bad Request

**Date:** 2026-11-26  
**Stage:** Keyframes (`pipeline/01_keyframes.py`)  
**What happened:** POST requests to `@cf/black-forest-labs/flux-1-schnell` failed with HTTP 400 Bad Request.  
**What I tried:**
1. Passed full parameter dictionary: `width`, `height`, `num_steps`, `seed`.
2. Checked response body: Cloudflare FLUX endpoint rejects extra parameters.  
**How I resolved it:** Stripped payload to accepted schema: `{"prompt": "...", "steps": 4}`.  
**Time lost:** ~15 minutes.  
**Logged to runs.jsonl:** Yes.

---

## Failure 004 — Cloudflare Returns JSON Base64 Instead of Binary PNG

**Date:** 2026-11-26  
**Stage:** Keyframes (`pipeline/01_keyframes.py`)  
**What happened:** Output keyframes were saved as raw text files containing `{"result": {"image": "<base64>"}}` instead of binary image bytes, causing FFmpeg to fail with invalid image headers.  
**What I tried:**
1. Opened file in image viewer; failed to render.
2. Inspected file headers in terminal; noticed JSON opening braces.  
**How I resolved it:** Added JSON response parsing and `base64.b64decode()` in `01_keyframes.py`, and converted all 10 existing keyframe files to valid binary PNGs.  
**Time lost:** ~20 minutes.  
**Logged to runs.jsonl:** Yes.

---

## Failure 005 — FFmpeg Ken Burns Memory Lockup on 8000px Scaling

**Date:** 2026-11-26  
**Stage:** Video Fallback (`pipeline/02_video_fallback.py`)  
**What happened:** Running FFmpeg `zoompan` with `scale=8000:-1` caused high CPU/memory consumption and froze the process indefinitely.  
**What I tried:**
1. Attempted single threaded execution (`-threads 1`).
2. Reduced intermediate scale to `2560:2560` with square crop.  
**How I resolved it:** Used `scale=2560:2560:force_original_aspect_ratio=increase,crop=2560:2560`. Render time dropped to ~2.4 seconds per shot.  
**Time lost:** ~25 minutes.

---

## Failure 006 — Zoompan Syntax Error with `d` Variable

**Date:** 2026-11-26  
**Stage:** Video Fallback (`pipeline/02_video_fallback.py`)  
**What happened:** FFmpeg command failed with:
```
[Parsed_zoompan_2 @ 00000...] Variable 'd' not found in expression '(on/d)'
```
**What I tried:**
1. Looked up FFmpeg `zoompan` documentation; realized `d` is an option specifying total frame duration, not a runtime variable in math expressions.  
**How I resolved it:** Formatted total frame count directly into expression: `(on/{total_frames})`.  
**Time lost:** ~10 minutes.

---

## Failure 007 — Windows Fontconfig Error on FFmpeg drawtext

**Date:** 2026-11-26  
**Stage:** End Card (`pipeline/05_endcard.py`)  
**What happened:** `drawtext=font='Arial'` failed on Windows with `Cannot find font Arial / Fontconfig error`.  
**What I tried:**
1. Checked system fonts directory: `C:\Windows\Fonts\arial.ttf`.  
**How I resolved it:** Escaped full Windows font path: `fontfile='C\:/Windows/Fonts/arial.ttf'` and `arialbd.ttf`.  
**Time lost:** ~10 minutes.

---

## Failure 008 — Cloud Notebook Dependencies & Git Build Failure

**Date:** 2026-11-26  
**Stage:** Music (`pipeline/03_music.py`)  
**What happened:** Kaggle notebook failed to clone ACE-Step repository (`git clone exit code 128`), and Audiocraft installation failed with `Failed to build 'av' wheel` due to missing C++ compilation toolchain.  
**What I tried:**
1. Switched Kaggle session accelerators.
2. Evaluated browser-based free music generation platforms (Suno/Udio); hit download/export gating.  
**How I resolved it:** Built a 100% self-contained local acoustic synthesizer in Python (`03_music.py`) using Karplus-Strong string modeling and FFmpeg studio reverb. Runs offline in ~40 seconds with zero cloud dependencies.  
**Time lost:** ~60 minutes.

---

## Failure 009 — Shot 2 Macro Image Blur

**Date:** 2026-11-26  
**Stage:** Keyframes & Assembly  
**What happened:** Keyframe for Shot 2 ("Home is more than walls and a roof") rendered as an unidentifiable macro orange/brown mud texture.  
**What I tried:**
1. Updated prompt in `storyboard.json` to an evocative wide establishing exterior shot of an Ethiopian home at sunrise with `seed=202`.  
**How I resolved it:** Re-ran `pipeline/01_keyframes.py`. SHA-256 prompt-hash caching ensured only Shot 2 was regenerated while shots 1 and 3-10 were preserved from cache.  
**Time lost:** ~15 minutes.  
**Logged to runs.jsonl:** Yes.

---

## Failure 010 — Subtitle Virtual Canvas Coordinate Overflow

**Date:** 2026-11-26  
**Stage:** Assembly (`pipeline/04_assemble.py`)  
**What happened:** Subtitles rendered in the upper-middle of the screen, covering the child's face and coffee pouring action.  
**What I tried:**
1. Inspected FFmpeg `subtitles` filter behavior; discovered Windows ASS renderer uses a default 288px virtual canvas height when no custom header is provided, so `MarginV=180` pushed text over 60% up the frame.  
**How I resolved it:** Lowered `MarginV` to 70 with `Alignment=2` (bottom-center) and max 38 characters/line wrapping. Verified subtitles sit in the lower third safe area.  
**Time lost:** ~15 minutes.
