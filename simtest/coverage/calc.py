from typing import List, Dict

class CoverageCalculator:
    def __init__(self, graph: dict, traces: List[Dict]):
        self.graph = graph
        self.traces = traces

    def compute(self) -> dict:
        total_nodes = {n["id"] for n in self.graph["nodes"]}
        total_tools = {n["tool_schema"] for n in self.graph["nodes"]}

        visited_nodes = {t["node_id"] for t in self.traces}
        visited_tools = {t["tool_name"] for t in self.traces}

        node_coverage = 100 * len(visited_nodes) / len(total_nodes) if total_nodes else 0
        tool_coverage = 100 * len(visited_tools) / len(total_tools) if total_tools else 0

        return {
            "node_visit_pct": round(node_coverage, 1),
            "tool_schema_visit_pct": round(tool_coverage, 1),
            "nodes_hit": list(visited_nodes),
            "tools_hit": list(visited_tools),
        }
