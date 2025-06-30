from simtest.coverage.calc import CoverageCalculator

def test_coverage_partial_graph():
    graph = {
        "nodes": [
            {"id": "start", "tool_schema": "StartTool"},
            {"id": "middle", "tool_schema": "MidTool"},
            {"id": "end", "tool_schema": "EndTool"},
            {"id": "unused", "tool_schema": "UnusedTool"},
        ]
    }

    traces = [
        {"node_id": "start", "tool_name": "StartTool"},
        {"node_id": "middle", "tool_name": "MidTool"},
        {"node_id": "end", "tool_name": "EndTool"},
    ]

    calc = CoverageCalculator(graph, traces)
    result = calc.compute()

    assert result["node_visit_pct"] == 75.0
    assert result["tool_schema_visit_pct"] == 75.0
    assert "unused" not in result["nodes_hit"]
    assert "UnusedTool" not in result["tools_hit"]
