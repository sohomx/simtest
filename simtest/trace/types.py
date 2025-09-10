"""Trace type stubs for Phase A (filled in next steps)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Literal

@dataclass
class TraceStep:
    run_id: str
    step_idx: int
    node_id: str
    kind: Literal["llm","tool","policy","python"]
    input_canon: Dict[str, Any] | None = None
    output_canon: Dict[str, Any] | None = None
    error: Optional[Dict[str, Any]] = None

@dataclass
class FailureRecord:
    node_id: str
    error_kind: Literal["schema_mismatch","exception","policy_violation"]
    signature: str
