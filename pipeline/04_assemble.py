#!/usr/bin/env python3
"""
04_assemble.py — Assemble the final film from storyboard, shots, narration, and score.

This is the main composition stage.  It orchestrates FFmpeg to:
    1. Build a concatenated video track from per-shot MP4 clips.
    2. Build a narration audio timeline (each WAV placed at its absolute timestamp).
    3. Duck the background music under narration using sidechaincompress.
    4. Mix video + ducked music + narration.
    5. Burn English subtitles (SRT) into the picture.
    6. Normalise loudness to EBU R128 (target −14 LUFS, peak −1 dBTP).
    7. Export outputs/film_16x9.mp4   (1920×1080)
       and  outputs/film_9x16.mp4    (1080×1920)

Shot source priority (per shot):
    1. assets/shots/<shot_id>.mp4         ← Wan 2.2 real video (best)
    2. assets/shots/<shot_id>_fallback.mp4 ← Ken Burns fallback
    3. ABORT with a helpful message if neither exists

Usage:
    python pipeline/04_assemble.py [--radio-cut] [--no-subtitles] [--force]

Options:
    --radio-cut     Assemble narration + music over black; skip video track.
                    Use this for Phase 1 checkpoint.
    --no-subtitles  Skip subtitle burning (useful while testing audio mix).
    --force         Overwrite existing outputs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT    = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.utils.srt import write_srt, measure_wav_durations

ASSETS  = ROOT / "assets"
SHOTS   = ASSETS / "shots"
MUSIC   = ASSETS / "music" / "score.wav"
OUTPUTS = ROOT / "outputs"

FPS       = 24
VIDEO_W16 = 1920
VIDEO_H16 = 1080


# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------

def _ff() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    for c in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]:
        if Path(c).exists():
            return c
    raise FileNotFoundError(
        "ffmpeg not found on PATH.\n"
        "Install: winget install Gyan.FFmpeg   (or download from ffmpeg.org)"
    )


def _run(cmd: list[str], *, label: str) -> None:
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed [{label}]:\n"
            f"{result.stderr.decode(errors='replace')[-1200:]}"
        )


# ---------------------------------------------------------------------------
# Shot resolution
# ---------------------------------------------------------------------------

def _resolve_shot(shot_id: str) -> Path:
    real     = SHOTS / f"{shot_id}.mp4"
    fallback = SHOTS / f"{shot_id}_fallback.mp4"
    if real.exists():
        return real
    if fallback.exists():
        return fallback
    raise FileNotFoundError(
        f"No video clip for {shot_id}.\n"
        f"  Expected: {real}\n"
        f"       or: {fallback}\n"
        f"Run:  python pipeline/02_video_fallback.py"
    )


# ---------------------------------------------------------------------------
# Radio-cut black-frame generator
# ---------------------------------------------------------------------------

def _black_shot(duration_s: float, out: Path) -> None:
    _run([
        _ff(), "-y",
        "-f",  "lavfi", "-i", f"color=black:size={VIDEO_W16}x{VIDEO_H16}:rate={FPS}",
        "-t",  str(duration_s),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
        str(out),
    ], label=f"black {out.name}")


# ---------------------------------------------------------------------------
# Audio timeline builder
# ---------------------------------------------------------------------------

def _build_narration_timeline(
    storyboard: dict,
    wav_durations: dict[str, float],
    total_s: float,
    tmp_dir: Path,
) -> Path:
    """
    Combine all narration WAV clips into a single timeline WAV using FFmpeg adelay.
    Returns the path to the mixed narration WAV.
    """
    clips: list[tuple[Path, float]] = []  # (abs_path, absolute_start_s)
    cursor = 0.0
    for shot in storyboard["shots"]:
        for clip in shot.get("narration_clips", []):
            abs_path = ROOT / clip["path"]
            abs_start = cursor + clip["offset_s"]
            if abs_path.exists():
                clips.append((abs_path, abs_start))
        cursor += shot["duration_s"]

    if not clips:
        # No narration at all — return silence
        silence = tmp_dir / "narration_timeline.wav"
        _run([
            _ff(), "-y", "-f", "lavfi",
            "-i", f"anullsrc=r=44100:cl=stereo",
            "-t", str(total_s), "-c:a", "pcm_s16le",
            str(silence),
        ], label="narration silence")
        return silence

    # Build filter_complex with adelay for each clip
    ff_cmd: list[str] = [_ff(), "-y"]
    filter_parts: list[str] = []
    for i, (path, _) in enumerate(clips):
        ff_cmd += ["-i", str(path)]

    for i, (_, start_s) in enumerate(clips):
        delay_ms = int(start_s * 1000)
        # Stereo-safe adelay: use same delay on all channels
        filter_parts.append(
            f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
            f"adelay={delay_ms}|{delay_ms}[n{i}]"
        )

    mix_inputs = "".join(f"[n{i}]" for i in range(len(clips)))
    filter_parts.append(
        f"{mix_inputs}amix=inputs={len(clips)}:duration=longest:normalize=0[narr]"
    )

    out = tmp_dir / "narration_timeline.wav"
    ff_cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-map", "[narr]",
        "-t", str(total_s + 1),  # slight pad; assembler trims to total_s
        "-c:a", "pcm_s16le",
        str(out),
    ]
    _run(ff_cmd, label="narration_timeline")
    return out


# ---------------------------------------------------------------------------
# Audio mix: duck music under narration
# ---------------------------------------------------------------------------

def _mix_audio(
    music_wav: Path,
    narration_wav: Path,
    total_s: float,
    tmp_dir: Path,
) -> Path:
    """
    Duck music under narration and mix into a single stereo WAV.

    Strategy:
      1. Loop/trim music to total_s.
      2. sidechaincompress: narration drives gain-reduction on music.
      3. amix music + narration at unity.
    """
    music_trimmed = tmp_dir / "music_trimmed.wav"
    _run([
        _ff(), "-y",
        "-stream_loop", "-1",    # loop the music indefinitely
        "-i", str(music_wav),
        "-t", str(total_s),
        "-c:a", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(music_trimmed),
    ], label="music_trim")

    out = tmp_dir / "mixed_audio.wav"
    # sidechaincompress: narration sidechain compresses music to ~−12 dB when speaking
    _run([
        _ff(), "-y",
        "-i", str(music_trimmed),
        "-i", str(narration_wav),
        "-filter_complex",
        (
            "[0:a]volume=0.5[music_in];"           # music base at −6 dB
            "[1:a]asplit=2[narr_sc][narr_mix];"    # split narration: sidechain + mix
            "[music_in][narr_sc]sidechaincompress="
            "threshold=0.02:ratio=8:attack=50:release=500:level_sc=0.9[music_ducked];"
            "[music_ducked][narr_mix]amix=inputs=2:duration=longest:normalize=0[out]"
        ),
        "-map", "[out]",
        "-t", str(total_s),
        "-c:a", "pcm_s16le",
        str(out),
    ], label="audio_mix")
    return out


# ---------------------------------------------------------------------------
# Main assembly
# ---------------------------------------------------------------------------

def assemble(radio_cut: bool, no_subtitles: bool, force: bool) -> int:
    ff = _ff()

    sb_path = ROOT / "storyboard.json"
    if not sb_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1

    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    shots      = storyboard["shots"]
    total_s    = sum(s["duration_s"] for s in shots)
    wav_durs   = measure_wav_durations(ROOT, storyboard)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    out_16x9 = OUTPUTS / "film_16x9.mp4"
    out_9x16 = OUTPUTS / "film_9x16.mp4"

    if out_16x9.exists() and not force:
        print(f"⚠  {out_16x9} already exists. Use --force to overwrite.")
        return 0

    with tempfile.TemporaryDirectory(prefix="heritage_assemble_") as _tmp:
        tmp = Path(_tmp)

        # ---- 1. Collect / build per-shot video clips ----
        shot_clips: list[Path] = []
        print("Step 1/6: resolving shot clips …")
        for shot in shots:
            sid = shot["id"]
            if radio_cut:
                blk = tmp / f"{sid}_black.mp4"
                _black_shot(shot["duration_s"], blk)
                shot_clips.append(blk)
            else:
                try:
                    shot_clips.append(_resolve_shot(sid))
                except FileNotFoundError as exc:
                    print(f"  ✗ {exc}", file=sys.stderr)
                    return 1
            print(f"  [{sid}] ✓")

        # ---- 2. Concatenate video track ----
        print("Step 2/6: concatenating video track …")
        concat_list = tmp / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in shot_clips),
            encoding="utf-8",
        )
        video_track = tmp / "video_track.mp4"
        _run([
            ff, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "18",
            str(video_track),
        ], label="video_concat")
        print("  ✓ video track ready")

        # ---- 3. Build narration timeline ----
        print("Step 3/6: building narration timeline …")
        narr_wav = _build_narration_timeline(storyboard, wav_durs, total_s, tmp)
        print(f"  ✓ narration timeline: {narr_wav.name}")

        # ---- 4. Music + ducking ----
        print("Step 4/6: mixing music with ducking …")
        if not MUSIC.exists():
            print(f"  ⚠  score.wav not found — using silence. Run 03_music.py first.")
            # Generate silence placeholder on the fly
            silence = tmp / "score_silence.wav"
            _run([
                ff, "-y", "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(total_s), "-c:a", "pcm_s16le",
                str(silence),
            ], label="inline_silence")
            music_src = silence
        else:
            music_src = MUSIC

        mixed_audio = _mix_audio(music_src, narr_wav, total_s, tmp)
        print("  ✓ audio mix ready")

        # ---- 5. Generate SRT ----
        srt_path = tmp / "film.srt"
        if not no_subtitles:
            print("Step 5/6: generating subtitles …")
            write_srt(storyboard, wav_durs, srt_path)
            # Count entries
            entries = srt_path.read_text(encoding="utf-8").count(" --> ")
            print(f"  ✓ {entries} subtitle entries → {srt_path.name}")

        # ---- 6a. Export 16:9 ----
        print("Step 6/6: exporting 16:9 …")
        sub_filter = ""
        if not no_subtitles and srt_path.exists():
            # FFmpeg needs forward slashes and escaped colons on Windows
            srt_safe = srt_path.as_posix().replace(":", "\\:")
            sub_filter = f",subtitles='{srt_safe}':force_style='FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV=40'"

        _run([
            ff, "-y",
            "-i", str(video_track),
            "-i", str(mixed_audio),
            "-map", "0:v",
            "-map", "1:a",
            "-vf", f"scale={VIDEO_W16}:{VIDEO_H16}:force_original_aspect_ratio=decrease,"
                   f"pad={VIDEO_W16}:{VIDEO_H16}:-1:-1:color=black"
                   f"{sub_filter}",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            "-c:a", "aac", "-b:a", "192k",
            "-af", "loudnorm=I=-14:TP=-1:LRA=11",
            "-t", str(total_s),
            str(out_16x9),
        ], label="export_16x9")
        print(f"  ✓ {out_16x9}")

        # ---- 6b. Export 9:16 ----
        print("     exporting 9:16 …")
        _run([
            ff, "-y",
            "-i", str(out_16x9),
            "-vf", (
                f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
                f"scale=1080:1920"
                f"{sub_filter}"
            ),
            "-c:v", "libx264", "-crf", "18", "-preset", "slow",
            "-c:a", "copy",
            str(out_9x16),
        ], label="export_9x16")
        print(f"  ✓ {out_9x16}")

    print(
        f"\n✓ Assembly complete.\n"
        f"  16:9 → {out_16x9}\n"
        f"  9:16 → {out_9x16}\n"
        f"  Duration: {total_s:.1f}s"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--radio-cut",     action="store_true",
                        help="Phase 1: assemble narration+music over black frames")
    parser.add_argument("--no-subtitles",  action="store_true",
                        help="Skip subtitle burning")
    parser.add_argument("--force",         action="store_true",
                        help="Overwrite existing outputs")
    args = parser.parse_args()

    try:
        ff = _ff()
    except FileNotFoundError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    return assemble(
        radio_cut=args.radio_cut,
        no_subtitles=args.no_subtitles,
        force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main())
