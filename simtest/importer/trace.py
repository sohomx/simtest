import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple
from simtest.seeds.loader import Seed
import yaml


def import_trace(path: str, output_dir: Path = Path(".")) -> Tuple[Dict[str, Any], List[Seed], str]:
    """Import a trace file and convert it into simgraph and seeds."""
    with open(path) as f:
        trace = json.load(f)

    if "workflow_version" in trace:
        trace_type = "workflows"
    elif trace.get("resource", {}).get("service.name") == "AutoGen":
        trace_type = "autogen"
    else:
        raise ValueError("Unknown trace format")

    if trace_type == "workflows":
        graph, seeds = _import_workflows(trace)
    elif trace_type == "autogen":
        graph, seeds = _import_autogen(trace)

    trace_hash = hashlib.sha1(json.dumps(trace, sort_keys=True).encode()).hexdigest()[:8]
    write_outputs(graph, seeds, trace_hash, output_dir=output_dir)
    return graph, seeds, trace_hash


def _import_workflows(trace: dict) -> Tuple[Dict[str, Any], List[Seed]]:
    steps = trace.get("steps", [])
    nodes = []
    edges = []
    seeds = []

    for i, step in enumerate(steps):
        node_id = f"node_{i}"
        nodes.append({
            "id": node_id,
            "tool_schema": step.get("tool", "UnknownTool"),
            "type": "task",
        })
        if i > 0:
            edges.append({"from": f"node_{i-1}", "to": node_id})

        seeds.append(Seed(
            node_id=node_id,
            input={"raw": step.get("input", "no_input")},
            expect=None,
            vars={},
            description=f"Imported from workflow step {i}"
        ))

    graph = {"nodes": nodes, "edges": edges, "meta": {"source": "workflows"}}
    return graph, seeds


def _import_autogen(trace: dict) -> Tuple[Dict[str, Any], List[Seed]]:
    spans = trace.get("spans", [])
    nodes = []
    edges = []
    seeds = []

    for i, span in enumerate(spans):
        node_id = f"node_{i}"
        nodes.append({
            "id": node_id,
            "tool_schema": span.get("attributes", {}).get("tool_name", "UnknownTool"),
            "type": "task",
        })
        if i > 0:
            edges.append({"from": f"node_{i-1}", "to": node_id})

        seeds.append(Seed(
            node_id=node_id,
            input={"raw": span.get("attributes", {}).get("input", "no_input")},
            expect=None,
            vars={},
            description=f"Imported from AutoGen span {i}"
        ))

    graph = {"nodes": nodes, "edges": edges, "meta": {"source": "autogen"}}
    return graph, seeds


def write_outputs(graph: dict, seeds: List[Seed], trace_hash: str, output_dir: Path = Path(".")):
    (output_dir / "seeds").mkdir(parents=True, exist_ok=True)
    (output_dir / ".simgraph.json").write_text(json.dumps(graph, indent=2))
    seed_path = output_dir / f"seeds/trace_{trace_hash}.yaml"
    seed_data = {
        "meta": {"cost_multiplier": 1.0, "noise_threshold": 0.1},
        "seeds": [s.__dict__ for s in seeds],
    }
    seed_path.write_text(yaml.dump(seed_data, sort_keys=False))