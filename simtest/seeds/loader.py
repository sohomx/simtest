import yaml
from pathlib import Path
from typing import Any
from dataclasses import dataclass

@dataclass
class Seed:
    node_id: str
    input: dict[str, Any]
    expect: Any
    vars: dict[str, Any]
    description: str

def load_seed_file(path: str) -> list[Seed]:
    with open(path) as f:
        raw = yaml.safe_load(f)

    def to_seed(entry):
        if "input" in entry:  # already a full seed
            return Seed(**entry)
        if "raw" in entry:  # domain-style minimal seed
            return Seed(
                node_id="start",
                input={"raw": entry["raw"]},
                expect=None,
                vars={},
                description="domain-generated"
            )
        raise ValueError(f"Unrecognized seed entry: {entry}")

    return [to_seed(entry) for entry in raw]

