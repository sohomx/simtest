import json
from pathlib import Path
from typing import Any

class GraphBuilder:
    def __init__(self, graph_dict: dict[str, Any]):
        self.graph = graph_dict

    def to_dict(self) -> dict[str, Any]:
        """
        Canonicalize: sort nodes by ID, remove junk keys, ensure determinism
        """
        nodes = sorted(self.graph.get("nodes", []), key=lambda x: x["id"])
        return {
            "nodes": nodes,
            "meta": {
                "format_version": 1,
                "node_count": len(nodes),
            },
        }

    def write_json(self, path: str = ".simgraph.json") -> None:
        path = Path(path)
        data = self.to_dict()

        with path.open("w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

        print(f"✅ GraphBuilder: wrote {len(data['nodes'])} nodes to {path}")
