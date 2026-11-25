"""
cache.py — Shot-level output caching.

Each stage computes a deterministic cache key from the shot's prompt,
parameters, and seed.  If the expected output file already exists its
key is logged as a cache hit and the stage skips regeneration.

Usage:
    from pipeline.utils.cache import cache_key, is_cached, mark_cached

    key  = cache_key("keyframes", shot, extra={"width": 1920})
    path = KEYFRAMES_DIR / f"{key}.png"
    if is_cached(path):
        print(f"Cache hit: {path}")
    else:
        # ... generate ...
        mark_cached(path)   # no-op; existence of the file is the cache signal
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def cache_key(stage: str, shot: dict, extra: dict | None = None) -> str:
    """
    Return a 16-character hex cache key for a stage + shot combination.

    The key is a SHA-256 hash of:
        stage, shot["id"], shot["image_prompt"], shot["motion_prompt"],
        shot["seed"], and any additional ``extra`` parameters.

    Changing any of those fields produces a different key, forcing
    regeneration.  Unchanged shots keep their existing output files and
    are skipped automatically.
    """
    payload: dict = {
        "stage":         stage,
        "id":            shot.get("id", ""),
        "image_prompt":  shot.get("image_prompt", ""),
        "motion_prompt": shot.get("motion_prompt", ""),
        "seed":          shot.get("seed", 0),
    }
    if extra:
        payload.update(extra)

    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return digest[:16]


def is_cached(path: Path) -> bool:
    """Return True if *path* already exists (the output file is the cache token)."""
    return Path(path).exists()


def mark_cached(path: Path) -> None:
    """
    No-op: the output file's presence is the cache signal.
    Call this for documentation / future hook purposes.
    """
    pass
