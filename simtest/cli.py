import typer
import shutil
from pathlib import Path
from simtest.core.loader import load_graph
from simtest.utils.table import print_graph_table
from simtest.core.graph_builder import GraphBuilder
from simtest.seeds.loader import load_seed_file
from simtest.seeds.qa_seeds import qa_suite  # ✅ NEW

app = typer.Typer()

@app.command()
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


@app.command()
def seed(suite: str = typer.Option(..., help="Seed suite to copy (tool-schema-sanity, negation-flip, cost-spike)")):
    """
    Copy curated seed pack to ./seeds/ (skip if already exists).
    """
    src = Path(f"seeds/{suite}.yaml")
    dst = Path(f"seeds/{suite}.yaml")

    if not src.exists():
        print(f"❌ Seed suite not found: {src}")
        raise typer.Exit(1)

    if src.resolve() == dst.resolve():
        print(f"⚠️  Skipping copy: {dst.name} is already in the target folder.")
        return

    dst.parent.mkdir(exist_ok=True)
    shutil.copy(src, dst)
    print(f"✅ Copied seed suite to: {dst}")


@app.command()
def qa():
    """
    Run QA over all curated seeds and print noise stats.
    """
    seed_dir = Path("seeds")
    total_pass, total_fail = 0, 0

    for path in seed_dir.glob("*.yaml"):
        print(f"\n🔍 QA: {path.name}")
        passed, failed = qa_suite(path)
        total_pass += passed
        total_fail += failed

    total = total_pass + total_fail
    noise = (total_fail / total) * 100 if total > 0 else 0
    print(f"\n✅ Seed QA complete: {total_pass} passed / {total} total")
    print(f"🧪 Noise ratio: {noise:.1f}%")

    if noise > 20:
        print("❌ Noise too high! Trim bad seeds before public use.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()


