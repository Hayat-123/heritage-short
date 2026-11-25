#!/usr/bin/env python3
"""
00_validate.py — Validate storyboard.json against storyboard.schema.json.

Run:
    python pipeline/00_validate.py

Exits with code 0 on success, 1 on validation failure.
No API calls are made; no files other than the storyboard are read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def validate_timing(storyboard: dict) -> list[str]:
    """Additional checks beyond JSON Schema."""
    errors: list[str] = []
    for shot in storyboard.get("shots", []):
        shot_dur = shot["duration_s"]
        for clip in shot.get("narration_clips", []):
            if clip["offset_s"] >= shot_dur:
                errors.append(
                    f"{shot['id']}: narration clip offset_s ({clip['offset_s']}) "
                    f">= shot duration_s ({shot_dur})"
                )
    total = sum(s["duration_s"] for s in storyboard["shots"])
    target = storyboard["film"]["duration_target_s"]
    if not (60 <= total <= 90):
        errors.append(
            f"Total shot duration {total:.1f}s is outside 60–90 s requirement."
        )
    if abs(total - target) > 5:
        errors.append(
            f"Total shot duration {total:.1f}s differs from duration_target_s "
            f"({target}s) by more than 5 s."
        )
    return errors


def main() -> int:
    schema_path    = ROOT / "storyboard.schema.json"
    storyboard_path = ROOT / "storyboard.json"

    if not schema_path.exists():
        print(f"ERROR: schema not found at {schema_path}", file=sys.stderr)
        return 1
    if not storyboard_path.exists():
        print(f"ERROR: storyboard not found at {storyboard_path}", file=sys.stderr)
        return 1

    schema    = load_json(schema_path)
    storyboard = load_json(storyboard_path)

    # --- JSON Schema validation ---
    try:
        validate(instance=storyboard, schema=schema)
        print("✓ JSON Schema validation passed.")
    except ValidationError as exc:
        print(f"✗ JSON Schema validation FAILED:\n  {exc.message}", file=sys.stderr)
        return 1

    # --- Timing sanity checks ---
    timing_errors = validate_timing(storyboard)
    if timing_errors:
        for err in timing_errors:
            print(f"✗ Timing error: {err}", file=sys.stderr)
        return 1
    print("✓ Timing checks passed.")

    # --- Narration WAV existence check ---
    missing = []
    for shot in storyboard["shots"]:
        for clip in shot.get("narration_clips", []):
            wav = ROOT / clip["path"]
            if not wav.exists():
                missing.append(clip["path"])
    if missing:
        print("⚠  Missing narration WAV files (pipeline will fail at assembly):")
        for m in missing:
            print(f"   {m}")
    else:
        print("✓ All narration WAV files found.")

    n_shots    = len(storyboard["shots"])
    total_dur  = sum(s["duration_s"] for s in storyboard["shots"])
    n_narrated = sum(1 for s in storyboard["shots"] if s["type"] == "narrated")
    print(
        f"\nStoryboard summary:\n"
        f"  Shots:          {n_shots} ({n_narrated} narrated, "
        f"{n_shots - n_narrated} music-only)\n"
        f"  Total duration: {total_dur:.1f} s\n"
        f"  Aspect ratios:  {', '.join(storyboard['film']['aspect_ratios'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
