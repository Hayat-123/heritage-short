"""
logger.py — Append-only structured logging to runs.jsonl.

Every real model call (Cloudflare, Wan 2.2, ACE-Step, etc.) must be
logged immediately after it completes — whether it succeeded or failed.

Do NOT log fabricated or placeholder entries.  If a stage is skipped
(cache hit or missing credentials), log nothing for it.

Schema of one JSON line:
{
  "ts":          ISO-8601 UTC timestamp,
  "stage":       stage name, e.g. "keyframes",
  "shot_id":     shot id, e.g. "shot_03"  (or null for film-level calls),
  "model":       exact model identifier used,
  "provider":    "cloudflare-workers-ai" | "kaggle-wan22" | "kaggle-acestep" | ...,
  "params":      dict of generation parameters sent to the API,
  "cache_hit":   bool — true if output was already cached,
  "latency_s":   float seconds of wall-clock time for the API call,
  "cost_usd":    float — 0.0 if within free tier,
  "cost_note":   human-readable explanation of cost,
  "output_path": relative path to the saved output file,
  "ok":          bool — true if the call succeeded
}
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Relative to the heritage-short project root (resolved at call time)
_DEFAULT_LOG = Path(__file__).parent.parent.parent / "runs.jsonl"


def log_call(
    *,
    stage: str,
    shot_id: str | None,
    model: str,
    provider: str,
    params: dict[str, Any],
    cache_hit: bool,
    latency_s: float,
    cost_usd: float,
    cost_note: str,
    output_path: str | Path | None,
    ok: bool,
    log_path: Path = _DEFAULT_LOG,
) -> None:
    """
    Append one JSON log entry to runs.jsonl.

    All arguments are keyword-only to prevent accidental mis-ordering.
    """
    entry = {
        "ts":          datetime.now(timezone.utc).isoformat(),
        "stage":       stage,
        "shot_id":     shot_id,
        "model":       model,
        "provider":    provider,
        "params":      params,
        "cache_hit":   cache_hit,
        "latency_s":   round(latency_s, 3),
        "cost_usd":    cost_usd,
        "cost_note":   cost_note,
        "output_path": str(output_path) if output_path else None,
        "ok":          ok,
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
