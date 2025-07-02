import json
from pathlib import Path
from uuid import uuid4

def convert_langsmith_trace(path: str):
    with open(path) as f:
        trace = json.load(f)

    steps = trace.get("steps", [])

    # SimGraph structure
    graph = {
        "meta": {"format_version": 1, "node_count": len(steps)},
        "nodes": []
    }

    seeds = []

    for i, step in enumerate(steps):
        node_id = step.get("name", f"step_{i}")
        tool_name = step.get("tool", "UnknownTool")
        input_text = step.get("inputs", {}).get("input", "")
        output_text = step.get("outputs", {}).get("output", "")

        graph["nodes"].append({
            "id": node_id,
            "type": "task",
            "tool_schema": tool_name
        })

        seeds.append({
            "node_id": node_id,
            "input": {"raw": input_text},
            "expect": output_text,
            "vars": {},
            "description": f"Imported from LangSmith step {node_id}"
        })

    # Write outputs
    Path(".simgraph.json").write_text(json.dumps(graph, indent=2))
    Path("seeds/trace-import.yaml").parent.mkdir(exist_ok=True)
    with open("seeds/trace-import.yaml", "w") as f:
        import yaml
        yaml.dump(seeds, f)

