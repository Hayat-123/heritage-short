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

## (Template for future failures)

## Failure NNN — [Short title]

**Date:** YYYY-MM-DD
**Stage:** [validate / keyframes / video / music / assemble]
**What happened:** [exact error message or symptom]
**What I tried:**
1. …
2. …
**How I resolved it:** [resolution or workaround]
**Time lost:** …
**Logged to runs.jsonl:** [yes / no / N/A — no API call involved]
