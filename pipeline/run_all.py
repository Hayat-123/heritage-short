#!/usr/bin/env python3
"""
run_all.py — Run the full heritage-short pipeline end-to-end.

This is the Python equivalent of `make film` for systems without GNU Make.
Run from the heritage-short/ directory:

    python pipeline/run_all.py [--radio-cut] [--force]

Stages (in order):
    00_validate    → validate storyboard.json against schema
    03_music       → ensure score.wav exists (creates placeholder if not)
    05_endcard     → generate end-card keyframe
    02_video_fallback → Ken Burns clips for every shot
    04_assemble    → final film (both aspect ratios)

Optional:
    01_keyframes   → Cloudflare FLUX keyframes (run separately; not forced here)
    02_video       → Wan 2.2 video (run on Kaggle; not forced here)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def run_stage(name: str, fn, *args, **kwargs) -> int:
    print(f"\n{'='*60}")
    print(f"  Stage: {name}")
    print(f"{'='*60}")
    rc = fn(*args, **kwargs)
    if rc not in (0, 2):  # 2 = soft skip (e.g. missing optional creds)
        print(f"\n✗ Stage '{name}' failed with exit code {rc}.", file=sys.stderr)
        return rc
    return 0


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--radio-cut", action="store_true", help="Assemble radio cut (black frames)")
    parser.add_argument("--force",     action="store_true", help="Force regeneration of all outputs")
    args = parser.parse_args()

    import importlib
    stages_modules = {
        "00_validate":        "pipeline.00_validate",
        "03_music":           "pipeline.03_music",
        "05_endcard":         "pipeline.05_endcard",
        "02_video_fallback":  "pipeline.02_video_fallback",
        "04_assemble":        "pipeline.04_assemble",
    }

    for stage_name, module_path in stages_modules.items():
        mod = importlib.import_module(module_path)
        # Each module exposes main() → delegates to run()
        rc = run_stage(stage_name, mod.main)
        if rc != 0:
            return rc

    print("\n✓ Pipeline complete — check outputs/ for film_16x9.mp4 and film_9x16.mp4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
