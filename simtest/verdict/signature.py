"""Failure signature utilities.

Produces deterministic signatures for failing steps so that replays
can assert stability (Phase A PRD).

Signature format:
    "{node_id}|{error_kind}|{hash8}"

Where `hash8` is the first 8 hex chars of a SHA1 over a canonicalized
payload that depends on the failure kind.

- For schema mismatches: hash({"expected": ..., "found": ...})
- For exceptions:       hash({"class": ..., "message": scrubbed_message})

Canonicalization rules:
- JSON dump with sort_keys=True, separators=(",", ":")
- Normalize floats to ~6 significant digits
- Scrub variable substrings in messages (timestamps, UUIDs, hex ptrs)
"""
from __future__ import annotations

from typing import Any, Dict
import hashlib
import json
import re

try:
    # Optional, for type hints and convenience
    from .engine import FailureDetails
except Exception:  # pragma: no cover
    FailureDetails = Any  # type: ignore

__all__ = [
    "make_signature",
    "signature_from_step",
]


# ---------------------- canonicalization helpers ----------------------

def _normalize_numbers(obj: Any) -> Any:
    if isinstance(obj, float):
        try:
            return float(f"{obj:.6g}")
        except Exception:
            return obj
    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, dict):
        return {k: _normalize_numbers(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        t = type(obj)
        return t(_normalize_numbers(v) for v in obj)
    # Fallback to string if not JSON-serializable
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")
_ISO_DT_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
_HEX_PTR_RE = re.compile(r"0x[0-9a-fA-F]+")


def _scrub_message(msg: str) -> str:
    """Remove unstable substrings that could vary across runs."""
    if not msg:
        return ""
    m = _UUID_RE.sub("<uuid>", msg)
    m = _ISO_DT_RE.sub("<ts>", m)
    m = _HEX_PTR_RE.sub("<hex>", m)
    # collapse runs of whitespace
    m = re.sub(r"\s+", " ", m).strip()
    return m[:500]


def _json_canon(obj: Any) -> str:
    return json.dumps(_normalize_numbers(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ----------------------------- core API -------------------------------

def make_signature(
    node_id: str,
    *,
    error_kind: str | None = None,
    schema_expected: Any | None = None,
    schema_found: Any | None = None,
    error_class: str | None = None,
    message: str | None = None,
) -> str:
    """Compute a deterministic failure signature string.

    Parameters mirror FailureDetails. Only the relevant fields are used
    depending on `error_kind`.
    """
    kind = (error_kind or "unknown").strip()
    if kind == "schema_mismatch":
        payload: Dict[str, Any] = {
            "expected": schema_expected,
            "found": schema_found,
        }
    elif kind == "exception":
        payload = {
            "class": error_class or "",
            "message": _scrub_message(message or ""),
        }
    else:
        # Best-effort fallback — include whatever is available so we still get a stable token
        payload = {
            "class": error_class or "",
            "message": _scrub_message(message or ""),
            "expected": schema_expected,
            "found": schema_found,
        }

    h = hashlib.sha1(_json_canon(payload).encode("utf-8")).hexdigest()[:8]
    return f"{node_id}|{kind}|{h}"


def signature_from_step(step: Dict[str, Any]) -> str:
    """Derive a signature from a trace step dict (as produced by the sandbox/CLI).

    Looks for `schema_expected/schema_found` or `error_class/error_message`, and an
    `error.kind` if present, otherwise infers the kind.
    """
    node_id = step.get("node_id", "")
    error = step.get("error", {}) or {}

    kind = error.get("kind")
    if not kind:
        if "schema_expected" in step or "schema_found" in step:
            kind = "schema_mismatch"
        elif step.get("error_class") or step.get("error_message"):
            kind = "exception"
        else:
            kind = "unknown"

    return make_signature(
        node_id,
        error_kind=kind,
        schema_expected=step.get("schema_expected"),
        schema_found=step.get("schema_found"),
        error_class=step.get("error_class") or error.get("class"),
        message=step.get("error_message") or error.get("message"),
    )
