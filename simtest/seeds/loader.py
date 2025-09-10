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
    """Load a YAML seed file and return a list[Seed].

    Back-compat: support two shapes
      1) Plain list of seed items
      2) Mapping with `seeds: [...]` (and optional `meta: {...}`)
    We intentionally ignore `meta` here because tests expect a list.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data: Any = yaml.safe_load(f) or []

    # Accept either a list or a mapping with `seeds` (or legacy `items`).
    if isinstance(data, dict):
        items = data.get("seeds") or data.get("items") or []
    else:
        items = data

    seeds: list[Seed] = []

    def to_seed(entry: Any) -> Seed:
        # Dict-shaped entries
        if isinstance(entry, dict):
            if "input" in entry:
                # Fill missing optional fields with safe defaults
                return Seed(
                    node_id=entry.get("node_id", "start"),
                    input=entry["input"],
                    expect=entry.get("expect", None),
                    vars=entry.get("vars", {}),
                    description=entry.get("description", "")
                )
            if "raw" in entry:
                return Seed(
                    node_id="start",
                    input={"raw": entry["raw"]},
                    expect=None,
                    vars={},
                    description=entry.get("description", "domain-generated"),
                )
            # Fallback: wrap the dict as a raw string
            return Seed(
                node_id="start",
                input={"raw": str(entry)},
                expect=None,
                vars={},
                description="Fallback raw input",
            )
        # String/primitive entries → wrap as raw
        return Seed(
            node_id="start",
            input={"raw": str(entry)},
            expect=None,
            vars={},
            description="Fallback raw input",
        )

    for item in items or []:
        seeds.append(to_seed(item))

    return seeds


