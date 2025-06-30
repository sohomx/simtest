from simtest.core.graph_builder import GraphBuilder
from simtest.core.loader import load_graph
import json
import os

def test_graph_round_trip(tmp_path):
    input_graph = load_graph("examples/toy_agent.py")

    out_path = tmp_path / ".simgraph.json"
    builder = GraphBuilder(input_graph)
    builder.write_json(out_path)

    with open(out_path) as f:
        roundtrip_graph = json.load(f)

    # Normalise both sides
    input_ids = sorted(node["id"] for node in input_graph["nodes"])
    output_ids = sorted(node["id"] for node in roundtrip_graph["nodes"])

    assert input_ids == output_ids
    assert roundtrip_graph["meta"]["node_count"] == 3
