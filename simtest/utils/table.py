from rich.table import Table
from rich.console import Console

def print_graph_table(graph: dict) -> None:
    table = Table(title="Agent Graph")
    table.add_column("Node ID")
    table.add_column("Node Type")
    table.add_column("Tool Schema")

    for node in graph.get("nodes", []):
        table.add_row(node["id"], node["type"], node["tool_schema"])

    Console().print(table)
