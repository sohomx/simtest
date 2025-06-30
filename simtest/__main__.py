import typer

from simtest.core.loader import load_graph
from simtest.utils.table import print_graph_table

app = typer.Typer()
from simtest.cli import app
import sys

@app.command()
def init(path: str = typer.Option("examples/toy_agent.py", help="Path to agent file")):
    """
    Parse agent file and print node_id | node_type | tool_schema.
    """
    print("✅ [cli.py > init()] CLI subcommand running with path =", path)
    graph = load_graph(path)
    print_graph_table(graph)
    return graph

if __name__ == "__main__":
    print("✅ [__main__.py] Running app() with args:", sys.argv)
    app(prog_name="simtest")
