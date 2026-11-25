#!/usr/bin/env python3
"""
03_music.py — Background music stage.

Primary path: ACE-Step 1.5 (open weights, Kaggle/Colab)
Fallback:     Generate a silent placeholder WAV locally.

The assembler (04_assemble.py) looks for assets/music/score.wav.
Put your chosen ACE-Step candidate there, or run this script to generate
a placeholder so the pipeline can complete immediately.

ACE-Step 1.5:
    Paper: https://arxiv.org/abs/2602.00744
    Code:  https://github.com/ACE-Step/ACE-Step-1.5
    Runs on Kaggle 2×T4 or Colab T4.
    Outputs: commercially usable, no watermark requirement.

Usage:
    python pipeline/03_music.py                   # generate placeholder
    python pipeline/03_music.py --write-notebook  # print Kaggle cell
    python pipeline/03_music.py --status          # check for real score
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT      = Path(__file__).parent.parent
MUSIC_DIR = ROOT / "assets" / "music"
SCORE     = MUSIC_DIR / "score.wav"


def _total_duration(storyboard: dict) -> float:
    return sum(s["duration_s"] for s in storyboard["shots"])


def _ffmpeg_path() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    for candidate in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "ffmpeg not found. Install from https://ffmpeg.org/download.html"
    )


def generate_placeholder(duration_s: float) -> None:
    """Generate a silent WAV file of *duration_s* seconds using FFmpeg."""
    ff = _ffmpeg_path()
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff, "-y",
        "-f",  "lavfi",
        "-i",  f"anullsrc=r=44100:cl=stereo",
        "-t",  str(duration_s),
        "-c:a", "pcm_s16le",
        str(SCORE),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg silent WAV failed:\n{result.stderr.decode(errors='replace')}"
        )
    print(f"✓ Placeholder silence written: {SCORE} ({duration_s:.1f}s)")
    print(
        "\n⚠  This is a silent placeholder.\n"
        "   Replace assets/music/score.wav with your ACE-Step 1.5 output\n"
        "   then re-run 04_assemble.py.\n"
    )


def write_notebook_cell(storyboard: dict) -> None:
    """Print an ACE-Step 1.5 Kaggle notebook cell."""
    total = _total_duration(storyboard)
    title = storyboard["film"]["title"]
    cell = f"""# ===== ACE-Step 1.5 — Kaggle Notebook Cell =====
# Install and run ACE-Step 1.5 to generate an original score.
# See: https://github.com/ACE-Step/ACE-Step-1.5

!git clone https://github.com/ACE-Step/ACE-Step-1.5 /kaggle/working/ace-step
!pip install -q -r /kaggle/working/ace-step/requirements.txt

import sys
sys.path.insert(0, "/kaggle/working/ace-step")

from ace_step import AceStep

model = AceStep.from_pretrained("ACE-Step/ACE-Step-1.5")
model.to("cuda")

# Generate 3 candidates with different seeds; listen and choose the best one.
# Style: warm Ethiopian ambient, solo masinko or krar string, contemplative, no lyrics.
PROMPT = (
    "Warm Ethiopian ambient music, solo masinko string instrument, slow tempo, "
    "contemplative and tender, no lyrics, gentle percussion, coffee ceremony mood, "
    "{total:.0f} seconds"
)
SEEDS = [42, 123, 7]

for seed in SEEDS:
    out_path = f"/kaggle/working/score_seed{{seed}}.wav"
    model.generate(
        prompt=PROMPT,
        duration_seconds={total:.1f},
        seed=seed,
        output_path=out_path,
    )
    print(f"Generated: {{out_path}}")

# Download all three, listen, then copy your favourite to:
#   heritage-short/assets/music/score.wav
# Record your choice and reasoning in EXPERIMENTS.md.
"""
    print(cell)


def status(storyboard: dict) -> None:
    total = _total_duration(storyboard)
    print(f"Film duration:  {total:.1f}s")
    if SCORE.exists():
        import wave
        with wave.open(str(SCORE)) as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        print(f"score.wav:      {SCORE}  ({dur:.1f}s)  ✓")
    else:
        print(f"score.wav:      NOT FOUND — run this script to create a placeholder")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-notebook", action="store_true")
    parser.add_argument("--status",         action="store_true")
    args = parser.parse_args()

    sb_path = ROOT / "storyboard.json"
    if not sb_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1
    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    if args.write_notebook:
        write_notebook_cell(storyboard)
        return 0

    if args.status:
        status(storyboard)
        return 0

    # Default: generate placeholder if score.wav doesn't exist
    if SCORE.exists():
        import wave
        with wave.open(str(SCORE)) as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        print(f"✓ score.wav already exists ({dur:.1f}s). Nothing to do.")
        print("  Replace it with an ACE-Step output for a real score.")
        return 0

    try:
        total = _total_duration(storyboard)
        generate_placeholder(total)
        return 0
    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        print(
            "\nFallback without ffmpeg:\n"
            "  python -c \"\n"
            "  import wave, struct, math\n"
            "  rate=44100; dur=72; ch=2\n"
            "  with wave.open('assets/music/score.wav','w') as f:\n"
            "      f.setnchannels(ch); f.setsampwidth(2); f.setframerate(rate)\n"
            "      f.writeframes(b'\\x00\\x00' * rate * ch * dur)\n"
            "  \"",
            file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
