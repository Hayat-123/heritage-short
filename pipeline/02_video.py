#!/usr/bin/env python3
"""
02_video.py — Wan 2.2 TI2V-5B image-to-video generation (optional upgrade).

This stage is NOT required for a working film.  Run 02_video_fallback.py
first to get a complete film using Ken Burns pan/zoom.

Wan 2.2 TI2V-5B runs on Kaggle (2×T4, ~30 GPU-h/week free).
See: https://github.com/Wan-Video/Wan2.2

Workflow:
    1. Upload your keyframe PNGs and this script to a Kaggle notebook.
    2. Run the notebook to generate 5-second 720p clips.
    3. Download the generated MP4 clips into assets/shots/.
    4. Re-run 04_assemble.py — it prefers real video over fallback clips.

This file provides:
    - A helper to write a Kaggle-ready notebook cell for Wan 2.2.
    - A local stub that checks for real video vs. fallback.

Usage (local check):
    python pipeline/02_video.py --status

Usage (generate notebook cell):
    python pipeline/02_video.py --write-notebook
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT      = Path(__file__).parent.parent
SHOTS_DIR = ROOT / "assets" / "shots"


def status() -> int:
    sb_path = ROOT / "storyboard.json"
    if not sb_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1

    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    print(f"{'Shot':<12} {'Wan 2.2 MP4':<25} {'Fallback MP4':<25} {'Status'}")
    print("-" * 80)
    for shot in storyboard["shots"]:
        sid         = shot["id"]
        real_mp4    = SHOTS_DIR / f"{sid}.mp4"
        fallback    = SHOTS_DIR / f"{sid}_fallback.mp4"
        has_real    = real_mp4.exists()
        has_fallback = fallback.exists()
        status_str  = "✓ real" if has_real else ("○ fallback" if has_fallback else "✗ MISSING")
        print(f"{sid:<12} {'✓' if has_real else '—':<25} {'✓' if has_fallback else '—':<25} {status_str}")
    return 0


def write_notebook_cell() -> None:
    """Print a Kaggle/Colab notebook cell that runs Wan 2.2 on your keyframes."""
    sb_path = ROOT / "storyboard.json"
    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    shots_info = [
        {
            "id":     s["id"],
            "dur":    s["duration_s"],
            "seed":   s.get("seed", 42),
            "prompt": s["motion_prompt"] or s["image_prompt"][:100],
        }
        for s in storyboard["shots"]
    ]

    cell = f"""# ===== Wan 2.2 TI2V-5B — Kaggle Notebook Cell =====
# Run this in a Kaggle notebook with GPU (2×T4).
# Upload your assets/keyframes/ folder to Kaggle datasets first.

!pip install -q "wan==2.2" diffusers accelerate

import os, json
from pathlib import Path

SHOTS = {json.dumps(shots_info, indent=2)}

KEYFRAMES_DIR = Path("/kaggle/input/coffee-keyframes")   # adjust to your dataset path
OUTPUT_DIR    = Path("/kaggle/working/shots")
OUTPUT_DIR.mkdir(exist_ok=True)

from wan import WanTI2V
model = WanTI2V.from_pretrained("Wan-AI/Wan2.2-TI2V-5B", torch_dtype="bfloat16")
model.to("cuda")

for shot in SHOTS:
    out = OUTPUT_DIR / f"{{shot['id']}}.mp4"
    if out.exists():
        print(f"Cache hit: {{shot['id']}}")
        continue
    img_path = KEYFRAMES_DIR / f"{{shot['id']}}.png"
    if not img_path.exists():
        # Try hashed filename — list available files
        candidates = list(KEYFRAMES_DIR.glob("*.png"))
        if candidates:
            img_path = candidates[0]  # adjust manually if needed
        else:
            print(f"No keyframe for {{shot['id']}}, skipping")
            continue

    print(f"Generating {{shot['id']}} ({shot['dur']}s) …")
    video = model.generate(
        image=str(img_path),
        prompt=shot["prompt"],
        num_frames=int(shot["dur"] * 16),   # Wan 2.2 default: 16 fps → adjust
        seed=shot["seed"],
    )
    video.save(str(out))
    print(f"  Saved → {{out}}")

print("Done. Download the shots/ folder and copy to heritage-short/assets/shots/")
"""
    print(cell)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--status",         action="store_true", help="Show real vs fallback video status")
    parser.add_argument("--write-notebook", action="store_true", help="Print a Kaggle notebook cell for Wan 2.2")
    args = parser.parse_args()

    if args.write_notebook:
        write_notebook_cell()
        return 0
    return status()


if __name__ == "__main__":
    sys.exit(main())
