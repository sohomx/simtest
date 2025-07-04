from simtest.importer.trace import import_trace
from pathlib import Path
import json

def test_autogen_import(tmp_path):
    trace_file = tmp_path / "trace.json"
    trace_file.write_text(Path("tests/fixtures/autogen_trace.json").read_text())

    # Use tmp_path for output
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    print(f"✅ Debug: using output_dir {output_dir}")

    import_trace(str(trace_file), output_dir=output_dir)

    graph_path = output_dir / ".simgraph.json"
    seeds_dir = output_dir / "seeds"

    print(f"✅ Debug: graph at {graph_path}, seeds dir: {seeds_dir}")

    # Check graph file exists
    assert graph_path.exists(), f"Graph file missing at {graph_path}"

    # Check seeds directory and its contents
    assert seeds_dir.exists(), f"Seeds directory missing at {seeds_dir}"
    seeds = list(seeds_dir.glob("trace_*.yaml"))
    print(f"✅ Debug: seeds dir contents: {seeds}")
    assert seeds, "No seed YAML files found in seeds directory"
    print(f"✅ Debug: Found seed file: {seeds[0]}")

    # Check node count in graph
    graph = json.loads(graph_path.read_text())
    assert len(graph["nodes"]) == 2