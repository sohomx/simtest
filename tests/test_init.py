from simtest.cli import init

def test_init_returns_graph_dict():
    graph = init(path="examples/toy_agent.py")

    assert isinstance(graph, dict)
    assert "nodes" in graph
    assert len(graph["nodes"]) == 3

    ids = {node["id"] for node in graph["nodes"]}
    assert ids == {"start", "analyze", "end"}
