import os
from simtest.cli import app
import sys

import typer
from typing import List
from simtest.audit.runner import audit as audit_runner

print("✅ [__main__.py] __main__ path =", __file__)

if __name__ == "__main__":
    print("✅ [__main__.py] Running app() with args:", sys.argv)
    app(prog_name="simtest")

@app.command()
def ci():
    """Run all curated test packs in CI mode."""
    os.system("poetry run simtest fuzz --suite policy-violation --quick")
    os.system("poetry run simtest fuzz --suite long-context --quick")


# New audit command
@app.command()
def audit(
    trace: str = typer.Option(..., "--trace", "-t", help="Path to JSONL trace (from --trace-log)."),
    runs: int = typer.Option(5, "--runs", help="Number of replays (default: 5)."),
    env: List[str] = typer.Option(None, "--env", help="KEY=VALUE to inject into the environment; repeatable."),
) -> None:
    """Audit determinism: re-run fuzz multiple times and assert the same failure signature appears."""
    # Parse repeated --env KEY=VALUE pairs
    env_dict: dict[str, str] | None = None
    if env:
        env_dict = {}
        for kv in env:
            if "=" not in kv:
                raise typer.BadParameter(f"--env expects KEY=VALUE, got: {kv}")
            k, v = kv.split("=", 1)
            env_dict[k] = v

    ok = audit_runner(trace_path=trace, runs=runs, extra_env=env_dict)
    if ok:
        typer.echo("✅ Audit stable")
        raise typer.Exit(code=0)
    else:
        typer.echo("❌ Audit unstable", err=True)
        raise typer.Exit(code=1)
