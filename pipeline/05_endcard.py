#!/usr/bin/env python3
"""
05_endcard.py — Generate the AI end-card image and bake it into the storyboard.

The end card is shot_10 in the storyboard, type=music_only.
Its keyframe image can be generated three ways (in preference order):

    1. Cloudflare Workers AI (FLUX) — same as 01_keyframes.py
    2. FFmpeg lavfi text overlay — no API needed, fully local
    3. Python Pillow — if FFmpeg unavailable but Pillow is installed

The fallback text overlay produces a simple dark frame with the film's
title and AI credit in white text — good enough for submission.

Output:
    assets/keyframes/shot_10.png   (convenience file for the assembler)

Usage:
    python pipeline/05_endcard.py [--local] [--force]

Options:
    --local   Force the local FFmpeg/Pillow fallback; skip Cloudflare.
    --force   Regenerate even if output already exists.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT      = Path(__file__).parent.parent
KEYFRAMES = ROOT / "assets" / "keyframes"

VIDEO_W = 1920
VIDEO_H = 1080


def _ff() -> str:
    p = shutil.which("ffmpeg")
    if p:
        return p
    for c in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]:
        if Path(c).exists():
            return c
    raise FileNotFoundError("ffmpeg not found")


def _make_local_endcard(title: str, out: Path) -> None:
    """Generate end card using FFmpeg drawtext — no APIs required."""
    ff = _ff()
    # Escape special chars for FFmpeg drawtext
    def _esc(s: str) -> str:
        return s.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")

    title_safe  = _esc(title)
    credit_safe = _esc("Made with AI · Wan 2.2 · FLUX.2 · ACE-Step · Gemini")

    vf = (
        f"color=c=0x080500:size={VIDEO_W}x{VIDEO_H}[bg];"
        f"[bg]drawtext=text='{title_safe}':"
        f"fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h-text_h)/2-40:"
        f"shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='{credit_safe}':"
        f"fontcolor=0xFFBB55:fontsize=26:x=(w-text_w)/2:y=(h-text_h)/2+40:"
        f"shadowcolor=black:shadowx=1:shadowy=1"
    )

    result = subprocess.run([
        ff, "-y",
        "-f", "lavfi", "-i", f"color=c=0x080500:size={VIDEO_W}x{VIDEO_H}:rate=1",
        "-vf", (
            f"drawtext=text='{title_safe}':"
            f"fontcolor=white:fontsize=52:x=(w-text_w)/2:y=(h/2)-50:"
            f"shadowcolor=black:shadowx=2:shadowy=2,"
            f"drawtext=text='{credit_safe}':"
            f"fontcolor=0xFFBB55:fontsize=24:x=(w-text_w)/2:y=(h/2)+30:"
            f"shadowcolor=black:shadowx=1:shadowy=1"
        ),
        "-frames:v", "1",
        str(out),
    ], capture_output=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg drawtext failed:\n{result.stderr.decode(errors='replace')}"
        )


def _make_cf_endcard(title: str, shot: dict, out: Path) -> None:
    """Generate end card via Cloudflare Workers AI."""
    import time
    import requests

    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    api_token  = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not account_id or not api_token:
        raise EnvironmentError("Cloudflare credentials not set")

    sys.path.insert(0, str(ROOT))
    from pipeline.utils.logger import log_call

    models = [
        "@cf/black-forest-labs/flux-2-klein",
        "@cf/black-forest-labs/flux-1-schnell",
    ]
    prompt = shot["image_prompt"]

    for model in models:
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{account_id}/ai/run/{model}"
        )
        payload = {
            "prompt":    prompt,
            "width":     VIDEO_W,
            "height":    VIDEO_H,
            "num_steps": 4,
            "seed":      shot.get("seed", 110),
        }
        headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

        t0 = time.perf_counter()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
        except Exception as exc:
            print(f"  Network error: {exc}")
            continue
        latency = time.perf_counter() - t0

        if resp.status_code == 404:
            continue
        if resp.status_code != 200:
            print(f"  API error {resp.status_code}: {resp.text[:200]}")
            continue

        ct = resp.headers.get("Content-Type", "")
        if "application/json" in ct:
            import base64
            d = resp.json()
            if d.get("success"):
                img_bytes = base64.b64decode(d["result"]["image"])
            else:
                continue
        else:
            img_bytes = resp.content

        out.write_bytes(img_bytes)
        log_call(
            stage="endcard", shot_id="shot_10", model=model,
            provider="cloudflare-workers-ai",
            params={"prompt_prefix": prompt[:80], "width": VIDEO_W,
                    "height": VIDEO_H, "num_steps": 4, "seed": shot.get("seed", 110)},
            cache_hit=False, latency_s=latency, cost_usd=0.0,
            cost_note="within Cloudflare Workers AI daily free allowance",
            output_path=out.relative_to(ROOT), ok=True,
        )
        print(f"  ✓ Cloudflare FLUX end card → {out.name}  ({latency:.1f}s)")
        return

    raise RuntimeError("All Cloudflare models failed for end card")


def run(local: bool, force: bool) -> int:
    sb_path = ROOT / "storyboard.json"
    if not sb_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1

    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    title = storyboard["film"]["title"]
    shot_10 = next((s for s in storyboard["shots"] if s["id"] == "shot_10"), None)
    if not shot_10:
        print("ERROR: shot_10 not found in storyboard.", file=sys.stderr)
        return 1

    KEYFRAMES.mkdir(parents=True, exist_ok=True)
    out = KEYFRAMES / "shot_10.png"

    if out.exists() and not force:
        print(f"✓ End card already exists: {out}")
        print("  Use --force to regenerate.")
        return 0

    # Try Cloudflare first (unless --local forced)
    if not local:
        try:
            print("Attempting Cloudflare FLUX end card …")
            _make_cf_endcard(title, shot_10, out)
            return 0
        except EnvironmentError:
            print("  Cloudflare credentials not set — using local fallback.")
        except Exception as exc:
            print(f"  Cloudflare failed ({exc}) — using local fallback.")

    # Local FFmpeg fallback
    try:
        print("Generating local end card via FFmpeg drawtext …")
        _make_local_endcard(title, out)
        print(f"  ✓ End card → {out}")
        return 0
    except FileNotFoundError:
        print("  FFmpeg not found — trying Pillow …")

    # Pillow last resort
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        img = Image.new("RGB", (VIDEO_W, VIDEO_H), color=(8, 5, 0))
        draw = ImageDraw.Draw(img)
        try:
            font_title  = ImageFont.truetype("arial.ttf", 56)
            font_credit = ImageFont.truetype("arial.ttf", 26)
        except Exception:
            font_title  = ImageFont.load_default()
            font_credit = ImageFont.load_default()

        # Title
        draw.text((VIDEO_W // 2, VIDEO_H // 2 - 50), title,
                  fill="white", font=font_title, anchor="mm")
        # Credit
        credit = "Made with AI · Wan 2.2 · FLUX.2 · ACE-Step · Gemini"
        draw.text((VIDEO_W // 2, VIDEO_H // 2 + 40), credit,
                  fill=(255, 187, 85), font=font_credit, anchor="mm")

        img.save(str(out))
        print(f"  ✓ Pillow end card → {out}")
        return 0
    except ImportError:
        pass

    print(
        "ERROR: Could not generate end card.\n"
        "Install one of:\n"
        "  - ffmpeg (recommended)   → winget install Gyan.FFmpeg\n"
        "  - Pillow                 → pip install Pillow\n"
        "Or set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN.",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--local", action="store_true", help="Use local fallback only")
    parser.add_argument("--force", action="store_true", help="Regenerate if exists")
    args = parser.parse_args()
    return run(local=args.local, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
