"""Streaming JSONL recorder (stub). Real logic added in Phase A Step 3."""
from __future__ import annotations
from pathlib import Path

class TraceRecorder:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_line(self, obj: dict) -> None:
        # real impl will canonicalize & sort; placeholder writes nothing yet
        with self.path.open("a", encoding="utf-8") as f:
            f.write("{}\n")
