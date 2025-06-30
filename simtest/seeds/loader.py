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
    return [Seed(**entry) for entry in raw]
