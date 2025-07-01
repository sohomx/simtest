from dataclasses import dataclass
from typing import Any

@dataclass
class Seed:
    node_id: str
    input: dict[str, Any]
    expect: Any
    vars: dict[str, Any]
    description: str

    @classmethod
    def raw(cls, task: str) -> "Seed":
        return cls(
            node_id="start",
            input={"raw": task},
            expect=None,
            vars={},
            description=task,
        )
