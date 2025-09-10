"""Streaming JSONL recorder for SimTest traces.

Implements the v1 spec in docs/dev/trace_format.md:
- Line 1: run header (keys sorted)
- Lines 2..N: step events (keys sorted)
- Canonicalization: sort_keys=True, separators=(",", ":"), ~6 sig-fig float normalization
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

__all__ = ["TraceRecorder"]


def _normalize_numbers(obj: Any) -> Any:
    """Recursively normalize floating point numbers to ~6 significant digits.

    - ints are left untouched
    - floats are re-serialized via format "%.6g" and then cast back to float
    - containers are normalized recursively
    """
    # Fast path for exact types
    if isinstance(obj, float):
        try:
            # Use general format with 6 significant digits, then back to float
            return float(f"{obj:.6g}")
        except Exception:
            return obj
    if isinstance(obj, (str, bool)) or obj is None or isinstance(obj, int):
        return obj

    # Containers
    if isinstance(obj, dict):
        return {k: _normalize_numbers(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        t = type(obj)
        return t(_normalize_numbers(v) for v in obj)

    # Unknown types: attempt JSON-serializable fallback via str()
    try:
        json.dumps(obj)  # type: ignore[arg-type]
        return obj
    except Exception:
        return str(obj)


def _json_dumps_canon(obj: Any) -> str:
    """Dump JSON with canonical settings and normalized numbers."""
    canon = _normalize_numbers(obj)
    return json.dumps(canon, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class TraceRecorder:
    """Append-only JSONL writer for traces.

    Usage:
        rec = TraceRecorder("artifacts/run_1.jsonl")
        rec.write_header({ ... })
        rec.write_step({ ... })
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._header_written = False

    # --- public API -----------------------------------------------------
    def write_header(self, header: dict[str, Any]) -> None:
        """Write the run header (line 1). Safe to call once per file.

        If the file already exists and is non-empty, we will not write another
        header to avoid duplicating runs when appending steps across processes.
        """
        if self.path.exists() and self.path.stat().st_size > 0:
            # Assume header already present
            self._header_written = True
            return
        self._append_line(header)
        self._header_written = True

    def write_step(self, step: dict[str, Any]) -> None:
        """Write a single step event line (2..N)."""
        # We do not enforce header-first strictly to keep the API flexible, but
        # callers should call write_header() before any steps in new files.
        self._append_line(step)

    # --- internals ------------------------------------------------------
    def _append_line(self, obj: dict[str, Any]) -> None:
        line = _json_dumps_canon(obj)
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.write("\n")
            f.flush()
