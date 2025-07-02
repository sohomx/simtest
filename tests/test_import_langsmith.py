from simtest.importer.langsmith import convert_langsmith_trace
import json
import os

def test_convert_langsmith_trace(tmp_path):
    # Setup fixture path and copy the test file
    fixture = "tests/fixtures/langsmith_trace.json"
    test_file = tmp_path / "trace.json"
    test_file.write_text(open(fixture).read())

    # Run conversion
    os.chdir(tmp_path)
    convert_langsmith_trace(str(test_file))

    # Check output files
    assert os.path.exists(".simgraph.json")
    assert os.path.exists("seeds/trace-import.yaml")

    # Optional: check structure
    graph = json.loads(open(".simgraph.json").read())
    assert "nodes" in graph
    assert graph["nodes"][0]["tool_schema"] == "StartTool"