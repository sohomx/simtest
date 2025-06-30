import typer
from simtest.core.loader import load_graph
from simtest.utils.table import print_graph_table
from simtest.core.graph_builder import GraphBuilder

def init(
    path: str = typer.Option("examples/toy_agent.py", help="Path to agent file"),
    write_graph: bool = typer.Option(False, help="Write .simgraph.json to disk")
):
    """
    Parse agent and print node table. Optionally write .simgraph.json.
    """
    print("✅ [cli.py > init()] CLI running with path =", path)
    graph = load_graph(path)
    print_graph_table(graph)

    if write_graph:
        builder = GraphBuilder(graph)
        builder.write_json(".simgraph.json")
        print("✅ .simgraph.json written")

    return graph

if __name__ == "__main__":
    typer.run(init)

