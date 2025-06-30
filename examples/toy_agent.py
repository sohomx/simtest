def build_graph():
    return {
        "nodes": [
            {"id": "start", "type": "task", "tool_schema": "StartTool"},
            {"id": "analyze", "type": "task", "tool_schema": "AnalyzeTool"},
            {"id": "end", "type": "task", "tool_schema": "EndTool"},
        ]
    }
