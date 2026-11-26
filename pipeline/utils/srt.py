"""
srt.py — Generate a SubRip (.srt) subtitle file from the storyboard.

Features:
  - Line wrapping to maximum 38 characters per line.
  - Maximum 2 lines per subtitle cue (split across the audio duration if needed)
    so subtitles never clip off the screen or crowd the video.
  - Correct formatting and UTF-8 encoding.
"""

from __future__ import annotations

import textwrap
from pathlib import Path


def _fmt_time(seconds: float) -> str:
    """Convert fractional seconds to SRT HH:MM:SS,mmm format."""
    ms  = max(0, int(round(seconds * 1000)))
    hh  = ms // 3_600_000; ms -= hh * 3_600_000
    mm  = ms //    60_000; ms -=  mm *    60_000
    ss  = ms //     1_000; ms -=  ss *     1_000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def _split_text_to_cues(
    text: str,
    start_s: float,
    end_s: float,
    max_chars: int = 38,
    max_lines: int = 2,
) -> list[tuple[float, float, str]]:
    """
    Wrap text to max_chars. If the wrapped text exceeds max_lines,
    split it into sequential cues proportioned across the available time window.
    """
    text = " ".join(text.strip().split())
    lines = textwrap.wrap(text, width=max_chars)
    if not lines:
        return []
    if len(lines) <= max_lines:
        return [(start_s, end_s, "\n".join(lines))]

    chunks = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]
    total_dur = end_s - start_s
    chunk_weights = [sum(len(l) for l in c) for c in chunks]
    total_weight = sum(chunk_weights) or 1.0

    cues: list[tuple[float, float, str]] = []
    cur_start = start_s
    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            cur_end = end_s
        else:
            fraction = chunk_weights[i] / total_weight
            cur_end = cur_start + (total_dur * fraction)
        cues.append((cur_start, cur_end, "\n".join(chunk)))
        cur_start = cur_end

    return cues


def build_srt(storyboard: dict, wav_durations: dict[str, float]) -> str:
    """
    Build and return the full SRT text from a loaded storyboard dict.

    Args:
        storyboard:    parsed storyboard.json dict
        wav_durations: mapping {relative_wav_path: duration_in_seconds}
    Returns:
        SRT text as a single string (UTF-8 safe).
    """
    entries: list[tuple[float, float, str]] = []
    cursor = 0.0

    for shot in storyboard.get("shots", []):
        for clip in shot.get("narration_clips", []):
            abs_start = cursor + clip["offset_s"]
            duration  = wav_durations.get(clip["path"], 3.0)
            abs_end   = abs_start + duration
            shot_boundary = cursor + shot["duration_s"] - 0.1
            abs_end   = min(abs_end, shot_boundary)
            if abs_end <= abs_start:
                abs_end = abs_start + 0.5

            raw_subtitle = clip.get("subtitle_en", "")
            raw_subtitle = raw_subtitle.replace("unfamiliar voice", "familiar voice")

            cues = _split_text_to_cues(raw_subtitle, abs_start, abs_end, max_chars=38, max_lines=2)
            entries.extend(cues)
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
    for shot in storyboard.get("shots", []):
        for clip in shot.get("narration_clips", []):
            rel = clip["path"]
            if rel in durations:
                continue
            abs_path = project_root / rel
            if abs_path.exists():
                try:
                    with _wave.open(str(abs_path)) as wf:
                        durations[rel] = wf.getnframes() / float(wf.getframerate())
                except Exception:
                    durations[rel] = 0.0
            else:
                durations[rel] = 0.0
    return durations
