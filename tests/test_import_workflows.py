from simtest.importer.trace import import_trace
from pathlib import Path
import json

def test_workflows_import(tmp_path):
    trace_file = tmp_path / "trace.json"
    trace_file.write_text(Path("tests/fixtures/workflows_trace.json").read_text())
    
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    
    import_trace(str(trace_file), output_dir=output_dir)  # Pass as Path, not str
    
    graph_path = output_dir / ".simgraph.json"
    seeds_dir = output_dir / "seeds"
    
    print(f"✅ Debug: graph at {graph_path}, seeds dir: {seeds_dir}")
    print(f"✅ Debug: seeds dir contents: {list(seeds_dir.glob('*.yaml'))}")
    
    graph = json.loads(graph_path.read_text())
    assert len(graph["nodes"]) == 3
    
    # Detect actual seed file dynamically
    seed_files = list(seeds_dir.glob("trace_*.yaml"))
    assert seed_files, "No seed files found in seeds directory"
    print(f"✅ Debug: Found seed file: {seed_files[0]}")
    assert seed_files[0].exists()