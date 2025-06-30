import typer
import shutil
from pathlib import Path

import yaml
from simtest.core.loader import load_graph
from simtest.utils.table import print_graph_table
from simtest.core.graph_builder import GraphBuilder
from simtest.seeds.loader import load_seed_file
from simtest.seeds.qa_seeds import qa_suite  
from simtest.seedgen.generator import SeedGenerator
import json
from simtest.fuzz.sandbox import SandboxExecutor
from simtest.fuzz.tracker import CostTracker, BudgetExceeded
from rich.console import Console
from rich.table import Table

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
    
@app.command()
def generate(
    suite: str = typer.Option(..., help="Tool name or seed suite"),
    n: int = typer.Option(100, help="How many seeds to generate"),
    domain: str = typer.Option("", help="Optional domain (e.g., finance-qa)")
):
    """
    Generate N LLM-based seed inputs for given tool or suite.
    """
    print(f"⚙️  Generating {n} seeds for: {suite}")
    gen = SeedGenerator(suite=suite, n=n, domain=domain)
    seeds, cost = gen.generate()

    out_path = Path(f"seeds/{suite}-gen.yaml")
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        yaml.dump([s.__dict__ for s in seeds], f)

    print(f"\n✅ Wrote {len(seeds)} seeds to {out_path}")
    print(f"💰 Total cost: ${cost.total_cost:.6f} using {cost.total_tokens} tokens")
    print(f"   ├── Prompt: {cost.prompt_tokens}  → ${cost.prompt_tokens / 1000 * 0.0005:.6f}")
    print(f"   └── Output: {cost.output_tokens}  → ${cost.output_tokens / 1000 * 0.0015:.6f}")

@app.command()
def fuzz(
    graph_path: str = typer.Option(".simgraph.json", help="Path to compiled simgraph"),
    suite: str = typer.Option("tool-schema-sanity", help="Seed YAML suite"),
    quick: bool = typer.Option(True, help="Limit to 100 seeds"),
    max_cost: float = typer.Option(3.0, help="Budget cap in USD")
):
    """
    Run fuzzing session: load graph + seeds → run sandboxed tool calls.
    """
    print(f"🧪 Running fuzz on: {suite} (budget=${max_cost})")

    with open(graph_path) as f:
        graph = json.load(f)

    seeds = load_seed_file(f"seeds/{suite}.yaml")
    if quick:
        seeds = seeds[:100]

    tracker = CostTracker(max_dollars=max_cost)
    total_runs = 0
    verdict_counts = {"PASS": 0, "FAIL_SCHEMA": 0, "FAIL_EXCEPTION": 0}
    first_fails: list[dict] = []

    with SandboxExecutor(graph) as run:
        for seed in seeds:
            trace = run(seed.input)
            tracker.consume_trace(trace)
            total_runs += 1

            for step in trace:
                v = step["verdict"]
                verdict_counts[v] += 1
                if v != "PASS" and len(first_fails) < 5:
                    first_fails.append(step)

    console = Console()
    print(f"\n✅ Fuzz complete: {total_runs} seeds run")
    print(f"💰 Total cost: ${tracker.compute_cost():.4f}")

    total = sum(verdict_counts.values())
    passed = verdict_counts["PASS"]
    console.print(f"[bold green]✅ PASS {passed} / {total}[/]")

    if first_fails:
        table = Table(title="First 5 Failures")
        table.add_column("Node")
        table.add_column("Tool")
        table.add_column("Verdict")
        table.add_column("Latency")

        for step in first_fails:
            table.add_row(
                step["node_id"],
                step["tool_name"],
                step["verdict"],
                f"{step['latency_ms']} ms",
            )

        console.print(table)



if __name__ == "__main__":
    app()


