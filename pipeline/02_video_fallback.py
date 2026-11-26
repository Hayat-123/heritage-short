#!/usr/bin/env python3
"""
02_video_fallback.py — Ken Burns pan/zoom fallback using FFmpeg.

Converts each shot's keyframe PNG into a short MP4 clip using FFmpeg's
``zoompan`` filter.  This produces a watchable, submittable film with
no GPU or cloud access required.

If a shot has no keyframe yet (01_keyframes.py not run), a solid-colour
placeholder frame is generated automatically using FFmpeg's lavfi source.

Each shot alternates between zoom-in and zoom-out based on its seed,
giving the edit a natural sense of motion variety.

Output:
    assets/shots/<shot_id>_fallback.mp4   (1920×1080, H.264, 24 fps)

Caching:
    If the output file already exists, the shot is skipped.
    Delete the file to force regeneration.

Usage:
    python pipeline/02_video_fallback.py [--shot shot_01] [--force]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT        = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
KEYFRAMES   = ROOT / "assets" / "keyframes"
SHOTS_DIR   = ROOT / "assets" / "shots"

# Placeholder colours keyed by shot_id — dark warm tones matching the film palette
_PLACEHOLDER_COLOURS: dict[str, str] = {
    "shot_01": "0x0d0600",   # near-black, pre-dawn
    "shot_02": "0x1a0a00",   # very dark sienna
    "shot_03": "0x2a1200",   # dark amber
    "shot_04": "0x3a1800",   # dark burnt orange
    "shot_05": "0x1e1000",   # dark brown
    "shot_06": "0x2e1600",   # ochre-dark
    "shot_07": "0x241000",   # coffee brown
    "shot_08": "0x1a1a28",   # dark blue-grey (city night)
    "shot_09": "0x2a1200",   # warm dark
    "shot_10": "0x060606",   # near-black end card
}
_DEFAULT_COLOUR = "0x1a0a00"

VIDEO_W = 1920
VIDEO_H = 1080
FPS     = 24


def _ffmpeg_path() -> str:
    """Return 'ffmpeg' or raise if not found."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    # Common Windows install locations
    candidates = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]
    import os
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        candidates.extend([str(p) for p in Path(local_app).glob("Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg*/bin/ffmpeg.exe")])
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "ffmpeg not found on PATH.\n"
        "Install it from https://ffmpeg.org/download.html and add it to your PATH.\n"
        "On Windows: winget install Gyan.FFmpeg"
    )


def _make_placeholder(shot_id: str, out_png: Path) -> None:
    """Create a solid-colour PNG placeholder via FFmpeg lavfi."""
    colour = _PLACEHOLDER_COLOURS.get(shot_id, _DEFAULT_COLOUR)
    ff = _ffmpeg_path()
    cmd = [
        ff, "-y",
        "-f", "lavfi",
        "-i", f"color=c={colour}:size={VIDEO_W}x{VIDEO_H}:rate=1",
        "-frames:v", "1",
        str(out_png),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg placeholder failed for {shot_id}:\n"
            f"{result.stderr.decode(errors='replace')}"
        )


def _ken_burns(image_path: Path, duration_s: float, out_mp4: Path, seed: int) -> None:
    """
    Apply Ken Burns pan/zoom to *image_path* and write *out_mp4*.

    Alternates motion across 4 gentle cinematic patterns based on seed:
        seed % 4 == 0: slow zoom-in (1.0 -> 1.12)
        seed % 4 == 1: slow zoom-out (1.12 -> 1.0)
        seed % 4 == 2: gentle pan left to right
        seed % 4 == 3: gentle pan right to left
    """
    ff     = _ffmpeg_path()
    frames = int(duration_s * FPS)

    pattern = seed % 4
    if pattern == 0:
        z = "min(zoom+0.0006,1.12)"
        x = "(iw-iw/zoom)/2"
        y = "(ih-(iw/zoom)*9/16)/2"
    elif pattern == 1:
        z = "if(eq(on,1),1.12,max(1.0,zoom-0.0006))"
        x = "(iw-iw/zoom)/2"
        y = "(ih-(iw/zoom)*9/16)/2"
    elif pattern == 2:
        z = "1.08"
        x = f"(iw-iw/1.08)*(on/{frames})"
        y = "(ih-(iw/1.08)*9/16)/2"
    else:
        z = "1.08"
        x = f"(iw-iw/1.08)*(1-on/{frames})"
        y = "(ih-(iw/1.08)*9/16)/2"

    # Scale square / arbitrary input to 2560x2560 so zoompan's 16:9 window
    # frames the full image area crisply without extreme zoom-in blur
    vf = (
        f"scale=2560:2560:force_original_aspect_ratio=increase,crop=2560:2560,"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={VIDEO_W}x{VIDEO_H}:fps={FPS}"
    )

    cmd = [
        ff, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", vf,
        "-t", str(duration_s),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "20",
        str(out_mp4),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg Ken Burns failed for {image_path.name}:\n"
            f"{result.stderr.decode(errors='replace')[-800:]}"
        )


def run(only_shot: str | None = None, force: bool = False) -> int:
    storyboard_path = ROOT / "storyboard.json"
    if not storyboard_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1

    with storyboard_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    # Verify ffmpeg is available before we touch any shot
    try:
        ff = _ffmpeg_path()
    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    KEYFRAMES.mkdir(parents=True, exist_ok=True)

    shots = storyboard["shots"]
    if only_shot:
        shots = [s for s in shots if s["id"] == only_shot]
        if not shots:
            print(f"ERROR: shot '{only_shot}' not found.", file=sys.stderr)
            return 1

    ok = skip = fail = 0

    for shot in shots:
        shot_id  = shot["id"]
        dur      = shot["duration_s"]
        seed     = shot.get("seed", 42)
        out_mp4  = SHOTS_DIR / f"{shot_id}_fallback.mp4"

        if out_mp4.exists() and not force:
            print(f"  [{shot_id}] cache hit → {out_mp4.name}")
            skip += 1
            continue

        # Find keyframe — look for any PNG whose stem might match the shot
        # (01_keyframes.py saves them as <hash>.png, not <shot_id>.png).
        # For the fallback we just grab the first PNG in keyframes/ alphabetically,
        # or generate a placeholder.
        keyframe_png: Path | None = None

        # Check for a symlink-style convenience file: keyframes/shot_01.png
        convenience = KEYFRAMES / f"{shot_id}.png"
        if convenience.exists():
            keyframe_png = convenience
        else:
            # Try to match via storyboard cache key (hash)
            from pipeline.utils.cache import cache_key
            key = cache_key("keyframes", shot, extra={"steps": 4})
            hashed = KEYFRAMES / f"{key}.png"
            if hashed.exists():
                keyframe_png = hashed

        if keyframe_png is None:
            # No FLUX image yet — generate a colour placeholder
            placeholder = KEYFRAMES / f"{shot_id}_placeholder.png"
            if not placeholder.exists():
                print(f"  [{shot_id}] no keyframe — creating placeholder …", end="", flush=True)
                try:
                    _make_placeholder(shot_id, placeholder)
                    print(" ✓")
                except Exception as exc:
                    print(f" ✗ {exc}")
                    fail += 1
                    continue
            keyframe_png = placeholder

        print(f"  [{shot_id}] Ken Burns ({dur}s, seed={seed}) …", end="", flush=True)
        try:
            _ken_burns(keyframe_png, dur, out_mp4, seed)
            print(f" ✓ → {out_mp4.name}")
            ok += 1
        except Exception as exc:
            print(f" ✗\n    {exc}")
            fail += 1

    print(f"\nFallback video: {ok} generated, {skip} cached, {fail} failed.")
    return 0 if fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--shot",  metavar="SHOT_ID", help="Process only this shot")
    parser.add_argument("--force", action="store_true", help="Regenerate even if output exists")
    args = parser.parse_args()
    return run(only_shot=args.shot, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
