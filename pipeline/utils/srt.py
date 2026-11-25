"""
srt.py — Generate a SubRip (.srt) subtitle file from the storyboard.

The assembler calls build_srt() to produce a file that FFmpeg's
``subtitles=`` filter can burn into the final video.

Each narration_clip entry in a shot has:
  - offset_s   : seconds from shot start
  - subtitle_en: English text to display

Combined with the cumulative shot start time, we get absolute timestamps.
"""

from __future__ import annotations

from pathlib import Path


def _fmt_time(seconds: float) -> str:
    """Convert fractional seconds to SRT HH:MM:SS,mmm format."""
    ms  = int(round(seconds * 1000))
    hh  = ms // 3_600_000; ms -= hh * 3_600_000
    mm  = ms //    60_000; ms -=  mm *    60_000
    ss  = ms //     1_000; ms -=  ss *     1_000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def build_srt(storyboard: dict, wav_durations: dict[str, float]) -> str:
    """
    Build and return the full SRT text from a loaded storyboard dict.

    Args:
        storyboard:    parsed storyboard.json dict
        wav_durations: mapping {relative_wav_path: duration_in_seconds}
                       so we can set subtitle end times correctly.
    Returns:
        SRT text as a single string (UTF-8 safe).
    """
    entries: list[tuple[float, float, str]] = []  # (start_s, end_s, text)
    cursor = 0.0  # cumulative start time of the current shot

    for shot in storyboard["shots"]:
        for clip in shot.get("narration_clips", []):
            abs_start = cursor + clip["offset_s"]
            duration  = wav_durations.get(clip["path"], 3.0)
            abs_end   = abs_start + duration
            # Clamp end to shot boundary
            abs_end   = min(abs_end, cursor + shot["duration_s"] - 0.1)
            entries.append((abs_start, abs_end, clip["subtitle_en"]))
        cursor += shot["duration_s"]

    lines: list[str] = []
    for idx, (start, end, text) in enumerate(entries, start=1):
        lines.append(str(idx))
        lines.append(f"{_fmt_time(start)} --> {_fmt_time(end)}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def write_srt(storyboard: dict, wav_durations: dict[str, float], out_path: Path) -> Path:
    """Write the SRT file to *out_path* and return the path."""
    text = build_srt(storyboard, wav_durations)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path


def measure_wav_durations(project_root: Path, storyboard: dict) -> dict[str, float]:
    """
    Return a dict mapping each narration clip path to its duration in seconds.
    Uses stdlib ``wave`` — no extra dependencies.
    """
    import wave as _wave

    durations: dict[str, float] = {}
    for shot in storyboard["shots"]:
        for clip in shot.get("narration_clips", []):
            rel = clip["path"]
            if rel in durations:
                continue
            abs_path = project_root / rel
            if abs_path.exists():
                with _wave.open(str(abs_path)) as wf:
                    durations[rel] = wf.getnframes() / float(wf.getframerate())
            else:
                durations[rel] = 0.0
    return durations
