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

def load_seed_file(path: str) -> tuple[list[Seed], dict]:
    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict) or "seeds" not in raw:
        raise ValueError(f"Expected top-level keys: 'meta' and 'seeds'. Got: {raw}")

    meta = raw.get("meta", {})
    seeds_raw = raw["seeds"]

    def to_seed(entry):
        if "input" in entry:
            return Seed(**entry)
        if "raw" in entry:
            return Seed(
                node_id="start",
                input={"raw": entry["raw"]},
                expect=None,
                vars={},
                description="domain-generated"
            )
        raise ValueError(f"Unrecognized seed entry: {entry}")

    return [to_seed(entry) for entry in seeds_raw], meta


