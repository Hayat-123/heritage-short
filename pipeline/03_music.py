#!/usr/bin/env python3
"""
03_music.py — Local Acoustic Music Synthesizer & Music Stage.

Generates a genuine, warm, nostalgic acoustic instrumental underscore
specifically composed for 'The Coffee That Carries a Story':
- Style: Warm Ethiopian Tizita pentatonic / acoustic guitar & gentle warm strings.
- Tempo: 75 BPM.
- Physical modeling: Karplus-Strong plucked nylon/acoustic strings.
- Ambient bed: Warm multi-harmonic bowed strings pad with subtle analog vibrato.
- Acoustic resonance: Studio acoustic hall reverb and warmth shaping via FFmpeg.
- Exact duration: Matched to storyboard film duration (67.0s).
- Target output: assets/audio/music/background.wav

Zero external downloads, accounts, or cloud API dependencies needed.

Usage:
    python pipeline/03_music.py            # Generates assets/audio/music/background.wav
    python pipeline/03_music.py --status   # Verifies track properties
"""

from __future__ import annotations

import array
import json
import math
import random
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT         = Path(__file__).parent.parent
MUSIC_DIR    = ROOT / "assets" / "audio" / "music"
TARGET       = MUSIC_DIR / "background.wav"
FALLBACK_DIR = ROOT / "assets" / "music"
FALLBACK     = FALLBACK_DIR / "score.wav"


def _ffmpeg_path() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
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
    raise FileNotFoundError("ffmpeg not found on PATH.")


def _total_duration(storyboard: dict) -> float:
    return sum(s["duration_s"] for s in storyboard["shots"])


# ---------------------------------------------------------------------------
# Karplus-Strong Plucked Acoustic String Synthesizer
# ---------------------------------------------------------------------------

def synthesize_pluck(freq: float, duration_s: float, sample_rate: int = 44100, decay: float = 0.993) -> list[float]:
    """Synthesize a warm nylon/acoustic plucked string using Karplus-Strong."""
    period = int(round(sample_rate / freq))
    if period < 2:
        period = 2

    # Initialize with gentle low-passed noise (warm acoustic pluck, not harsh)
    raw_noise = [random.uniform(-1.0, 1.0) for _ in range(period)]
    buffer = [0.0] * period
    for i in range(period):
        buffer[i] = 0.5 * (raw_noise[i] + raw_noise[(i - 1) % period])

    total_samples = int(sample_rate * duration_s)
    samples: list[float] = []

    idx = 0
    prev = 0.0
    for _ in range(total_samples):
        val = buffer[idx]
        samples.append(val)
        # Average filter with decay
        new_val = 0.5 * (val + prev) * decay
        prev = val
        buffer[idx] = new_val
        idx = (idx + 1) % period

    return samples


# ---------------------------------------------------------------------------
# Warm Strings / Ambient Pad Synthesizer
# ---------------------------------------------------------------------------

def synthesize_pad_chord(
    freqs: list[float],
    duration_s: float,
    sample_rate: int = 44100,
    attack_s: float = 0.8,
    release_s: float = 0.9,
) -> list[float]:
    """Synthesize a warm bowed strings chord with subtle vibrato."""
    total_samples = int(sample_rate * duration_s)
    samples = [0.0] * total_samples
    attack_samples = int(sample_rate * attack_s)
    release_samples = int(sample_rate * release_s)

    # 4.5 Hz subtle vibrato
    vibrato_rate = 4.5
    vibrato_depth = 0.0035

    for freq in freqs:
        phase = random.uniform(0, 2 * math.pi)
        for i in range(total_samples):
            t = i / sample_rate
            # LFO vibrato
            mod_freq = freq * (1.0 + vibrato_depth * math.sin(2 * math.pi * vibrato_rate * t))
            phase += 2 * math.pi * mod_freq / sample_rate

            # Multi-harmonic warm string tone
            s1 = math.sin(phase)
            s2 = 0.35 * math.sin(2 * phase)
            s3 = 0.12 * math.sin(3 * phase)
            s4 = 0.04 * math.sin(4 * phase)
            val = (s1 + s2 + s3 + s4) / 1.51

            # Envelope
            env = 1.0
            if i < attack_samples:
                env = 0.5 * (1.0 - math.cos(math.pi * i / attack_samples))
            elif i > total_samples - release_samples:
                rem = total_samples - i
                env = 0.5 * (1.0 - math.cos(math.pi * rem / release_samples))

            samples[i] += val * env * 0.22

    return samples


# ---------------------------------------------------------------------------
# Composition: "The Coffee That Carries a Story" (Tizita Major Underscore)
# ---------------------------------------------------------------------------

def generate_acoustic_score(total_duration_s: float, raw_out_path: Path) -> None:
    """Compose and synthesize the complete acoustic score at 75 BPM."""
    sr = 44100
    n_samples = int(sr * total_duration_s)
    buf_l = array.array('f', [0.0] * n_samples)
    buf_r = array.array('f', [0.0] * n_samples)

    random.seed(42)  # Deterministic, repeatable generation

    bpm = 75.0
    beat_dur = 60.0 / bpm          # 0.8s
    measure_dur = beat_dur * 4     # 3.2s
    total_measures = int(math.ceil(total_duration_s / measure_dur))

    # Notes (Hz)
    D2 = 73.42   # Bass
    G2 = 98.00
    A2 = 110.00
    B2 = 123.47

    D3 = 146.83  # Mids
    E3 = 164.81
    Fs3 = 185.00
    G3 = 196.00
    A3 = 220.00
    B3 = 246.94

    D4 = 293.66  # Melody
    E4 = 329.63
    Fs4 = 369.99
    G4 = 392.00
    A4 = 440.00
    B4 = 493.88
    D5 = 587.33

    # Chord progression (Warm Tizita / Nostalgic cycle):
    # D (Tonic) -> G (Subdominant warm) -> Bm (Tender) -> A (Resolution)
    chords = [
        ([D3, Fs3, A3, D4], D2),
        ([G3, B3, D4, G4],  G2),
        ([B2, D3, Fs3, B3], B2),
        ([A2, E3, A3, Fs4], A2),
    ]

    # Pluck arpeggios & melodic motifs in Tizita pentatonic
    motifs = [
        # Measure type 0 (Tonic D arpeggio)
        [(0.0, D3, 0.40), (0.5, A3, 0.35), (1.0, D4, 0.45), (1.5, Fs4, 0.50), (2.0, A4, 0.45), (2.5, Fs4, 0.35), (3.0, D4, 0.40)],
        # Measure type 1 (G arpeggio)
        [(0.0, G3, 0.40), (0.5, B3, 0.35), (1.0, D4, 0.45), (1.5, G4, 0.50), (2.0, B4, 0.45), (2.5, A4, 0.35), (3.0, D4, 0.40)],
        # Measure type 2 (Bm arpeggio)
        [(0.0, B2, 0.40), (0.5, Fs3, 0.35), (1.0, B3, 0.45), (1.5, D4, 0.50), (2.0, Fs4, 0.50), (2.5, E4, 0.35), (3.0, B3, 0.40)],
        # Measure type 3 (A contemplative cadence)
        [(0.0, A2, 0.40), (0.5, E3, 0.35), (1.0, A3, 0.45), (1.5, D4, 0.50), (2.0, E4, 0.45), (2.5, Fs4, 0.40), (3.0, A3, 0.35)],
    ]

    print(f"Synthesizing {total_measures} measures of warm acoustic music ({total_duration_s:.1f}s at {bpm} BPM) …")

    for m in range(total_measures):
        m_start_s = m * measure_dur
        c_idx = m % len(chords)
        chord_freqs, bass_freq = chords[c_idx]

        # 1. Warm String Pad
        pad_dur = min(measure_dur * 1.15, total_duration_s - m_start_s)
        if pad_dur > 0.5:
            pad_samples = synthesize_pad_chord(chord_freqs, pad_dur, sr, attack_s=0.7, release_s=0.8)
            start_idx = int(m_start_s * sr)
            for i, val in enumerate(pad_samples):
                pos = start_idx + i
                if pos < n_samples:
                    buf_l[pos] += val * 0.42
                    buf_r[pos] += val * 0.45

        # 2. Soft Acoustic Bass (warm sine fundamental)
        bass_samples = int(measure_dur * sr)
        start_idx = int(m_start_s * sr)
        for i in range(bass_samples):
            pos = start_idx + i
            if pos < n_samples:
                t = i / sr
                env = math.exp(-t * 0.85)  # Natural warm bass decay
                b_val = (math.sin(2 * math.pi * bass_freq * t) + 0.3 * math.sin(4 * math.pi * bass_freq * t)) * env * 0.28
                buf_l[pos] += b_val * 0.5
                buf_r[pos] += b_val * 0.5

        # 3. Plucked Acoustic Guitar / Krar Arpeggios
        motif = motifs[c_idx]
        for note_beat, freq, vel in motif:
            note_time_s = m_start_s + (note_beat * beat_dur)
            if note_time_s >= total_duration_s - 0.2:
                continue

            pluck_dur = min(3.0, total_duration_s - note_time_s)
            decay = 0.9935 if freq < 350 else 0.991
            pluck_samples = synthesize_pluck(freq, pluck_dur, sr, decay=decay)

            p_start_idx = int(note_time_s * sr)
            # Subtle stereo panning based on pitch
            pan = (freq - 200) / 400.0  # -0.2 to 0.8
            pan_l = 0.5 - 0.25 * pan
            pan_r = 0.5 + 0.25 * pan

            for j, p_val in enumerate(pluck_samples):
                pos = p_start_idx + j
                if pos < n_samples:
                    buf_l[pos] += p_val * vel * pan_l * 0.48
                    buf_r[pos] += p_val * vel * pan_r * 0.48

    # Master gentle master fade out in last 2 seconds
    fade_samples = int(2.5 * sr)
    fade_start = max(0, n_samples - fade_samples)
    for i in range(fade_samples):
        pos = fade_start + i
        if pos < n_samples:
            mul = 0.5 * (1.0 + math.cos(math.pi * i / fade_samples))
            buf_l[pos] *= mul
            buf_r[pos] *= mul

    # Find peak to prevent digital clipping before write
    max_amp = 0.001
    for i in range(n_samples):
        if abs(buf_l[i]) > max_amp:
            max_amp = abs(buf_l[i])
        if abs(buf_r[i]) > max_amp:
            max_amp = abs(buf_r[i])

    gain = 0.85 / max_amp  # Leave headroom for FFmpeg reverb filter

    # Convert to 16-bit PCM bytes
    raw_out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(raw_out_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frame_bytes = bytearray()
        for i in range(n_samples):
            sl = int(max(-32767, min(32767, buf_l[i] * gain * 32767)))
            sr_val = int(max(-32767, min(32767, buf_r[i] * gain * 32767)))
            frame_bytes.extend(sl.to_bytes(2, "little", signed=True))
            frame_bytes.extend(sr_val.to_bytes(2, "little", signed=True))
        wf.writeframes(frame_bytes)

    print(f"✓ Raw acoustic score synthesized: {raw_out_path.name}")


# ---------------------------------------------------------------------------
# Studio Acoustic Post-Processing (FFmpeg Concert Hall Reverb & Warmth)
# ---------------------------------------------------------------------------

def postprocess_with_ffmpeg(raw_wav: Path, out_wav: Path, total_duration_s: float) -> None:
    """Apply acoustic hall reverb, gentle analog tone-shaping, and stereo polish."""
    ff = _ffmpeg_path()
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    fade_out_st = max(0.0, total_duration_s - 3.0)

    # Filter explanation:
    # 1. aecho: 3-tap warm studio acoustic hall reverb (delays 60ms, 120ms, 240ms)
    # 2. equalizer: slight low-mid warmth (+2dB at 280Hz)
    # 3. lowpass: soft analog rolloff above 6500Hz to keep strings intimate and warm
    # 4. stereowiden: subtle spatial immersion
    # 5. afade: gentle 1.5s intro fade and 3s outro fade
    reverb_filter = (
        "aecho=0.85:0.88:60|120|240:0.35|0.25|0.15,"
        "equalizer=f=280:t=q:w=1.2:g=2.5,"
        "lowpass=f=6200,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_st:.1f}:d=3.0"
    )

    cmd = [
        ff, "-y",
        "-i", str(raw_wav),
        "-af", reverb_filter,
        "-t", str(total_duration_s),
        "-c:a", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(out_wav),
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg reverb processing failed:\n{res.stderr.decode(errors='replace')}")

    print(f"✓ Studio acoustic mastering applied → {out_wav}")


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def status(storyboard: dict) -> None:
    total = _total_duration(storyboard)
    print(f"Film duration required: {total:.1f}s")
    if TARGET.exists():
        with wave.open(str(TARGET)) as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        print(f"background.wav:         {TARGET} ({dur:.1f}s)  ✓ [READY]")
    else:
        print(f"background.wav:         NOT FOUND — target location:")
        print(f"                        {TARGET}")


def generate(force: bool = False) -> int:
    sb_path = ROOT / "storyboard.json"
    if not sb_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1

    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    total_s = _total_duration(storyboard)

    if TARGET.exists() and not force:
        with wave.open(str(TARGET)) as wf:
            dur = wf.getnframes() / float(wf.getframerate())
        print(f"✓ {TARGET} already exists ({dur:.1f}s). Use --force to regenerate.")
        return 0

    import tempfile
    with tempfile.TemporaryDirectory(prefix="heritage_music_") as tmp_dir:
        raw_wav = Path(tmp_dir) / "raw_synth.wav"
        generate_acoustic_score(total_s, raw_wav)
        postprocess_with_ffmpeg(raw_wav, TARGET, total_s)

    # Also mirror to fallback for backward compatibility
    FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, FALLBACK)

    print(
        f"\n===========================================================\n"
        f"✓ Original background music track generated successfully!\n"
        f"  Location: {TARGET}\n"
        f"  Duration: {total_s:.1f}s\n"
        f"  Format:   Stereo 16-bit 44.1 kHz WAV\n"
        f"===========================================================\n"
    )
    return 0


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--status", action="store_true", help="Check status of background music")
    parser.add_argument("--force",  action="store_true", help="Force regenerate music track")
    args = parser.parse_args()

    sb_path = ROOT / "storyboard.json"
    if not sb_path.exists():
        print("ERROR: storyboard.json not found.", file=sys.stderr)
        return 1
    with sb_path.open(encoding="utf-8") as fh:
        storyboard = json.load(fh)

    if args.status:
        status(storyboard)
        return 0

    return generate(force=args.force or True)


if __name__ == "__main__":
    sys.exit(main())
