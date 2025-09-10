import os
from typing import Optional
import typer
from typer.models import OptionInfo
import shutil
from pathlib import Path
import dataclasses
import yaml
from simtest.core.loader import load_graph
from simtest.seeds.domain import DomainSeedGenerator
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
from simtest.verdict.judge import LLMJudge
from simtest.coverage.calc import CoverageCalculator

import platform
import sys
import importlib.metadata

app = typer.Typer()

@app.command()
def init(
    path: str = typer.Option("examples/toy_agent.py", help="Path to agent file"),
    write_graph: bool = typer.Option(False, help="Write .simgraph.json to disk"),
    trace: Optional[str] = typer.Option(None, help="Path to agent trace JSON"),
):
    """
    Parse agent and print node table. Optionally write .simgraph.json.
    """
    # When called directly (not via Typer), `trace` can be an OptionInfo.
    _trace_val = trace.default if isinstance(trace, OptionInfo) else trace
    if isinstance(_trace_val, str) and _trace_val:
        from simtest.importer.trace import import_trace
        import_trace(_trace_val)
        print("✅ Imported trace successfully; graph + seeds ready.")
        return

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
def fuzz(
    graph_path: str = typer.Option(".simgraph.json", help="Path to compiled simgraph"),
    suite: str = typer.Option("tool-schema-sanity", help="Seed YAML suite"),
    quick: bool = typer.Option(True, help="Limit to 100 seeds"),
    max_cost: float = typer.Option(3.0, help="Budget cap in USD"),
    semantic_check: bool = typer.Option(False, help="Use LLM to explain failed outputs"),
    report: Optional[str] = typer.Option(None, help="Write markdown report to this path"),
    trace_log: Optional[str] = typer.Option(None, help="Write full traces to JSON file"),
    max_per_node: float = typer.Option(0.01, help="Cost spike threshold (USD)"),
    soft_policy: bool = typer.Option(False, help="Warn on policy violations instead of failing"),
):
    """
    Run fuzzing session: load graph + seeds → run sandboxed tool calls.
    """
    import time, os, json
    from simtest.coverage.calc import CoverageCalculator
    from simtest.report.writer import ReportWriter
    from simtest.trace.recorder import TraceRecorder
    import uuid
    from datetime import datetime, timezone
    from simtest.verdict.signature import make_signature, signature_from_step

    print(f"🧪 Running fuzz on: {suite} (budget=${max_cost})")
    start = time.time()

    with open(graph_path) as f:
        graph = json.load(f)

    result = load_seed_file(f"seeds/{suite}.yaml")

    # Back-compat: loader may return a list or (list, meta)
    if isinstance(result, tuple):
        seeds, meta = result
    else:
        seeds = result
        meta = {}

    cost_multiplier = float(meta.get("cost_multiplier", 1.0))
    noise_threshold = float(meta.get("noise_threshold", 0.1))

    if quick:
        seeds = seeds[:100]

    tracker = CostTracker(max_dollars=max_cost / cost_multiplier)
    judge = LLMJudge() if semantic_check else None

    # Set up streaming JSONL trace recorder if requested
    rec = None
    if trace_log:
        rec = TraceRecorder(trace_log)
        try:
            sim_ver = importlib.metadata.version("simtest")
        except Exception:
            sim_ver = "0.0.0"
        run_id = uuid.uuid4().hex
        header = {
            "run_id": run_id,
            "seed_id": suite,
            "git_sha": os.getenv("GIT_SHA", ""),
            "started_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),
            "simtest_version": sim_ver,
            "env": {"python": platform.python_version()},
        }
        rec.write_header(header)
        _step_idx = 0

    total_runs = 0
    verdict_counts = {
        "PASS": 0,
        "FAIL_SCHEMA": 0,
        "FAIL_EXCEPTION": 0,
        "FAIL_POLICY": 0,
        "FAIL_COST_SPIKE": 0
    }
    all_traces: list[dict] = []
    first_fails: list[dict] = []

    with SandboxExecutor(graph) as run:
        debug = os.getenv("SIMTEST_DEBUG", "0") == "1"
        console = Console()

        for seed in seeds:
            trace = run(seed.input)
            tracker.consume_trace(trace)
            total_runs += 1

            for step in trace:
                v = step["verdict"]

                # semantic check → FAIL_POLICY
                if semantic_check and judge:
                    task_text = seed.input.get("raw", "no input")
                    judgement = judge.evaluate(
                        node_id=step["node_id"],
                        tool_name=step["tool_name"],
                        task=task_text,
                        output={"fake": True}
                    )
                    step["explanation"] = judgement.explanation
                    if "policy violation" in judgement.explanation.lower():
                        v = "FAIL_POLICY"
                        if soft_policy:
                            console.print("[yellow]⚠️ Policy violation (soft fail)[/]")

                # cost spike check → FAIL_COST_SPIKE
                step_cost = (step["input_tokens"] + step["output_tokens"]) / 1000 * 0.002
                if step_cost > max_per_node:
                    v = "FAIL_COST_SPIKE"

                step["verdict"] = v
                verdict_counts[v] = verdict_counts.get(v, 0) + 1

                if v != "PASS" and len(first_fails) < 5:
                    first_fails.append(step)

                all_traces.append(step)

                if rec is not None:
                    kind = "tool" if step.get("tool_name") else "python"
                    model = step.get("tool_name", "python")
                    input_tokens = step.get("input_tokens", 0) or 0
                    output_tokens = step.get("output_tokens", 0) or 0
                    computed_cost = (input_tokens + output_tokens) / 1000 * 0.002
                    line = {
                        "run_id": run_id,
                        "step_idx": _step_idx,
                        "node_id": step.get("node_id", ""),
                        "kind": kind,
                        "input_canon": step.get("input", {}),
                        "output_canon": step.get("output", None),
                        "model": model,
                        "latency_ms": step.get("latency_ms", 0),
                        "cost_usd": computed_cost,
                        "stubbed": step.get("stubbed", {"time": True, "rand": True, "uuid": True, "net": False}),
                    }
                    if "schema_expected" in step:
                        line["schema_expected"] = step["schema_expected"]
                    if "schema_found" in step:
                        line["schema_found"] = step["schema_found"]

                    if v != "PASS":
                        if v == "FAIL_POLICY":
                            error_kind = "policy_violation"
                        elif ("schema_expected" in step) or ("schema_found" in step):
                            error_kind = "schema_mismatch"
                        elif step.get("error_class") or step.get("error_message"):
                            error_kind = "exception"
                        else:
                            error_kind = "unknown"

                        line["error"] = {
                            "kind": error_kind,
                            "class": step.get("error_class", ""),
                            "message": step.get("error_message") or step.get("explanation", ""),
                            "stack": None,
                        }

                        # Compute deterministic failure signature
                        line["signature"] = make_signature(
                            node_id=line["node_id"],
                            error_kind=error_kind,
                            schema_expected=line.get("schema_expected"),
                            schema_found=line.get("schema_found"),
                            error_class=line["error"]["class"],
                            message=line["error"]["message"],
                        )

                    rec.write_step(line)
                    _step_idx += 1

            if debug:
                print(f"\n--- Trace for seed #{total_runs} ---")
                print(json.dumps(trace, indent=2))

    console = Console()
    print(f"\n✅ Fuzz complete: {total_runs} seeds run")
    total_cost = tracker.compute_cost()
    print(f"💰 Total cost: ${total_cost:.4f}")

    coverage = CoverageCalculator(graph, all_traces).compute()
    print(f"📊 Coverage: {coverage['node_visit_pct']}% nodes / {coverage['tool_schema_visit_pct']}% schemas")

    if quick and coverage["node_visit_pct"] < 80:
        print("⚠️  Warning: node coverage < 80% in quick-mode")

    total = sum(verdict_counts.values())
    passed = verdict_counts.get("PASS", 0)
    noise_pct = 1.0 - (passed / total if total else 1.0)
    console.print(f"[bold green]✅ PASS {passed} / {total}[/]")

    if quick and noise_pct > noise_threshold:
        print(f"❌ Noise too high: {noise_pct:.2%} > {noise_threshold:.0%} — CI check will fail.")
        raise typer.Exit(1)

    if first_fails:
        table = Table(title="First 5 Failures")
        table.add_column("Node")
        table.add_column("Tool")
        table.add_column("Verdict")
        table.add_column("Latency")
        table.add_column("Explanation", overflow="fold")
        for step in first_fails:
            table.add_row(
                step["node_id"],
                step["tool_name"],
                step["verdict"],
                f"{step['latency_ms']} ms",
                step.get("explanation", ""),
            )
        console.print(table)

    if report:
        writer = ReportWriter(
            traces=all_traces,
            verdicts=verdict_counts,
            coverage=coverage,
            total_cost=total_cost,
            runtime_s=round(time.time() - start, 2),
            suite_name=suite,
            cost_multiplier=cost_multiplier,
            noise_pct=noise_pct,
        )
        writer.write(report)
        print(f"📝 Wrote markdown report to {report}")

    if trace_log:
        # Streaming JSONL recorder already wrote per-step lines
        print(f"📝 Streamed trace JSONL to {trace_log}")

    # 🚨 CI Exit Checks
    if quick and (verdict_counts.get("FAIL_SCHEMA", 0) > 0 or verdict_counts.get("FAIL_EXCEPTION", 0) > 0):
        print("❌ Fuzz found new failures — CI check will fail.")
        raise typer.Exit(1)

    if quick and total_cost > max_cost * 1.10:
        print("❌ Fuzz cost increased >10% — CI check will fail.")
        raise typer.Exit(1)



@app.command()
def diagnose():
    """
    Print environment and graph stats to help debug installs.
    """
    from pathlib import Path

    print("🔍 SimTest Diagnostic Report\n")

    print(f"Python version : {platform.python_version()}")
    print(f"Platform       : {platform.system()} {platform.machine()}")
    print(f"SimTest version: {importlib.metadata.version('simtest')}")

    simgraph_path = Path(".simgraph.json")
    if simgraph_path.exists():
        import json
        with open(simgraph_path) as f:
            graph = json.load(f)
        print(f"\nGraph loaded   : {len(graph['nodes'])} nodes / {len(set(n['tool_schema'] for n in graph['nodes']))} tools")
    else:
        print("\nGraph not found: .simgraph.json is missing")

    debug = os.getenv("SIMTEST_DEBUG", "0")
    print(f"Debug logging  : {'ON' if debug == '1' else 'off'}")

@app.command()
def seed_from(
    domain: str = typer.Argument(..., help="Domain name (e.g. 'finance-qa')"),
    n: int = typer.Argument(100, help="Number of seeds to generate"),
):
    """
    Generate domain-specific seeds via GPT.
    """
    with open(".simgraph.json") as f:
        graph = json.load(f)
    tool_names = [node["tool_schema"] for node in graph["nodes"]]
    gen = DomainSeedGenerator(domain=domain, tools=tool_names, count=n)
    seeds = gen.generate()
    print(f"✅ Generated {len(seeds)} seeds")
    for s in seeds:
        print("-", s)


@app.command("seed-from")
def seed_from(
    domain: str = typer.Argument(..., help="Target domain (e.g. finance-qa)"),
    n: int = typer.Argument(..., help="Number of seeds to generate"),
    output: Optional[str] = typer.Option(None, help="Optional path to save as YAML")
):
    """
    Generate domain-specific seeds using LLM.
    """
    import yaml
    import dataclasses
    from simtest.seeds.domain import DomainSeedGenerator

    with open(".simgraph.json") as f:
        graph = json.load(f)

    tool_names = [node["tool_schema"] for node in graph["nodes"]]
    gen = DomainSeedGenerator(domain=domain, tools=tool_names, count=n)
    seeds = gen.generate()

    print(f"✅ Final seed count: {len(seeds)}")

    if output:
        with open(output, "w") as f:
            yaml.safe_dump([dataclasses.asdict(s) for s in seeds], f)
        print(f"📁 Wrote seed file to {output}")

@app.command("import")
def import_cmd(
    source: str = typer.Argument(..., help="Import source type (e.g., langsmith)"),
    path: str = typer.Argument(..., help="Path to input file"),
):
    """
    Import external traces into SimTest format.
    """
    if source == "langsmith":
        from simtest.importer.langsmith import convert_langsmith_trace
        convert_langsmith_trace(path)
        print(f"✅ Imported LangSmith trace: wrote .simgraph.json and seeds/trace-import.yaml")
    else:
        print(f"❌ Unsupported import source: {source}")
        raise typer.Exit(1)



if __name__ == "__main__":
    app()
