import typer

from simtest.core.loader import load_graph
from simtest.utils.table import print_graph_table

app = typer.Typer()

@app.command()
def init(path: str = typer.Option("examples/toy_agent.py", help="Path to agent file")):
    """
    Parse agent file and print node_id | node_type | tool_schema.
    """
    print("✅ [cli.py > init()] CLI subcommand running with path =", path)
    graph = load_graph(path)
    print_graph_table(graph)
    return graph
