from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List


@dataclass
class TargetFailure:
    signature: str
    node_id: str
    error_kind: str
    seed_id: str


def _read_first_header_and_signature(trace_path: str | Path) -> Tuple[Optional[dict], Optional[TargetFailure]]:
    """Return (header, target) where target is the first failing signature found.

    The trace is expected to be JSONL with header on line 1.
    """
    header: Optional[dict] = None
    target: Optional[TargetFailure] = None

    with Path(trace_path).open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if i == 1 and isinstance(obj, dict):
                header = obj
                continue
            if isinstance(obj, dict) and obj.get("error") and obj.get("signature"):
                err = obj.get("error", {}) or {}
                target = TargetFailure(
                    signature=obj["signature"],
                    node_id=obj.get("node_id", ""),
                    error_kind=err.get("kind", "unknown"),
                    seed_id=(header or {}).get("seed_id", ""),
                )
                break
    return header, target


def _run_fuzz_once(suite: str, out_path: Path, extra_env: Optional[dict] = None) -> None:
    """Invoke `python -m simtest fuzz` to generate a fresh JSONL trace for the suite.

    Uses --no-quick so failure rates do not short-circuit the run.
    """
    cmd = [
        sys.executable,
        "-m",
        "simtest",
        "fuzz",
        "--suite",
        suite,
        "--no-quick",
        "--trace-log",
        str(out_path),
    ]
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    subprocess.run(cmd, check=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def _signatures_in_trace(path: Path) -> List[str]:
    sigs: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict) and "signature" in obj:
                sigs.append(obj["signature"])
    return sigs


def _stub_flags_report(path: Path) -> tuple[bool, str]:
    """Check that every step line has deterministic stub flags set correctly.

    Expectation from PRD:
      - time: True
      - rand: True
      - uuid: True
      - net:  False
    Returns (ok, message). If not ok, message lists the first problems found.
    """
    problems: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            flags = obj.get("stubbed")
            if not isinstance(flags, dict):
                # header or non-step line; skip
                continue
            expected = {"time": True, "rand": True, "uuid": True, "net": False}
            for k, exp in expected.items():
                actual = flags.get(k)
                if actual is not exp:
                    node = obj.get("node_id", "?")
                    problems.append(f"line {lineno} node={node}: stubbed.{k}={actual} expected {exp}")
    return (len(problems) == 0, "; ".join(problems))


def audit(trace_path: str | Path, runs: int = 5, extra_env: Optional[dict] = None) -> bool:
    """Audit determinism: re-run fuzz N times and ensure the same failure signature appears every time.

    Also asserts there is **no unstubbed entropy** in each replayed trace:
      time=True, rand=True, uuid=True, net=False on all steps.

    Returns True if stable, False otherwise.
    """
    header, target = _read_first_header_and_signature(trace_path)
    if header is None:
        print("❓ Audit: could not read header from trace")
        return False
    if target is None:
        print("ℹ️  Audit: no failing signature found in trace — nothing to verify")
        return False

    suite = target.seed_id or header.get("seed_id") or ""
    if not suite:
        print("❓ Audit: seed_id (suite) not present in header")
        return False

    print(f"🔁 Audit target: signature={target.signature} node={target.node_id} kind={target.error_kind} suite={suite}")

    ok_runs = 0
    with tempfile.TemporaryDirectory(prefix="simtest_audit_") as td:
        td_path = Path(td)
        for i in range(1, runs + 1):
            out = td_path / f"audit_run_{i}.jsonl"
            try:
                _run_fuzz_once(suite=suite, out_path=out, extra_env=extra_env)
                sigs = _signatures_in_trace(out)
                stubs_ok, stub_msg = _stub_flags_report(out)
                if not stubs_ok:
                    print(f"  ❌ run {i}/{runs}: unstubbed entropy detected → {stub_msg}")
                    continue
                if target.signature in sigs:
                    ok_runs += 1
                    print(f"  ✅ run {i}/{runs}: signature matched & stubs ok")
                else:
                    print(f"  ❌ run {i}/{runs}: signature NOT found (stubs ok)")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ run {i}/{runs}: fuzz execution failed ({e.returncode})")
                return False

    stable = ok_runs == runs
    if stable:
        print(f"✅ Audit stable: {ok_runs}/{runs} runs reproduced the signature")
    else:
        print(f"❌ Audit unstable: {ok_runs}/{runs} runs reproduced the signature")
    return stable