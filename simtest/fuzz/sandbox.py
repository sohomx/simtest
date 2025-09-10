import time
import random
import uuid
import os
from typing import TypedDict, Any
from simtest.verdict.engine import VerdictEngine, Verdict

class Trace(TypedDict, total=False):
    node_id: str
    tool_name: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    verdict: str  # PASS, FAIL_SCHEMA, FAIL_EXCEPTION
    stubbed: dict
    input: dict
    output: Any
    schema_expected: dict
    schema_found: Any
    error_class: str
    error_message: str


# Deterministic stubs for time/random/uuid
class DeterminismStubs:
    """Context manager to stub time/random/uuid for deterministic runs.

    - time.time() → starts at fixed epoch and advances by time.sleep(dt)
    - time.sleep(dt) → advances virtual clock; does not actually sleep
    - random.random/randint/uniform → seeded RNG
    - uuid.uuid4() → deterministic sequence via uuid5(namespace, counter)
    """
    def __init__(self, seed: int = 1337, epoch: float = 1700000000.0):
        self.seed = seed
        self.epoch = epoch
        self._rng = random.Random(seed)
        self._t = float(epoch)
        self._uuid_counter = 0
        # originals
        self._orig_time = time.time
        self._orig_sleep = time.sleep
        self._orig_uuid4 = uuid.uuid4
        self._orig_random = random.random
        self._orig_randint = random.randint
        self._orig_uniform = random.uniform

    def __enter__(self):
        def _fake_time():
            return self._t

        def _fake_sleep(dt: float):
            try:
                self._t += float(dt)
            except Exception:
                pass
            return None

        def _fake_uuid4():
            self._uuid_counter += 1
            # stable, deterministic UUID derived from counter
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"simtest-{self.seed}-{self._uuid_counter}")

        time.time = _fake_time  # type: ignore[assignment]
        time.sleep = _fake_sleep  # type: ignore[assignment]
        random.random = self._rng.random  # type: ignore[assignment]
        random.randint = self._rng.randint  # type: ignore[assignment]
        random.uniform = self._rng.uniform  # type: ignore[assignment]
        uuid.uuid4 = _fake_uuid4  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type, exc, tb):
        # restore originals
        time.time = self._orig_time  # type: ignore[assignment]
        time.sleep = self._orig_sleep  # type: ignore[assignment]
        random.random = self._orig_random  # type: ignore[assignment]
        random.randint = self._orig_randint  # type: ignore[assignment]
        random.uniform = self._orig_uniform  # type: ignore[assignment]
        uuid.uuid4 = self._orig_uuid4  # type: ignore[assignment]
        return False

class SandboxExecutor:
    def __init__(self, graph: dict, timeout_s: int = 30, deterministic: bool = True, seed: int = 42):
        self.graph = graph
        self.timeout = timeout_s
        self._rng = random.Random(seed)
        self._seed = seed
        self._deterministic = deterministic
        self._stubs: DeterminismStubs | None = None
        self.verdict_engine = VerdictEngine()

    def __enter__(self):
        print("🔒 Entered sandbox (no external net access)")
        if self._deterministic:
            self._stubs = DeterminismStubs(seed=self._seed)
            self._stubs.__enter__()
        return self.run_seed

    def __exit__(self, exc_type, exc_val, tb):
        if self._stubs is not None:
            self._stubs.__exit__(exc_type, exc_val, tb)
            self._stubs = None
        print("🔓 Exited sandbox")

    def run_seed(self, seed: dict) -> list[Trace]:
        trace: list[Trace] = []

        for node in self.graph["nodes"]:
            start = time.time()
            input_tokens = self._rng.randint(10, 50)
            output_tokens = self._rng.randint(10, 100)
            time.sleep(self._rng.uniform(0.01, 0.05))
            end = time.time()

            tool = node["tool_schema"]

            # Simulate output shape based on tool
            fake_output = {
                "StartTool": {"ack": True},
                "AnalyzeTool": {"summary": "text"},
                "EndTool": {"success": True},
            }.get(tool, {})

            # Optional demo toggle: harmless perturbation on a non-failing node
            # This should NOT change the failing EndTool signature
            if os.getenv("SIMTEST_PERTURB_NONCRITICAL") == "1" and tool == "AnalyzeTool":
                # Keep schema valid; add a trailing space deterministically
                fake_output = {"summary": "text "}

            # Optional demo toggle: force a wrong shape to exercise schema mismatch
            if os.getenv("SIMTEST_FORCE_BAD_OUTPUT") == "1" and tool == "EndTool":
                mode = os.getenv("SIMTEST_FORCE_BAD_OUTPUT_MODE", "default")
                if mode == "alt":
                    fake_output = {"approved": False}  # different value → different signature
                else:
                    fake_output = {"approved": True}   # wrong key on purpose

            verdict, details = self.verdict_engine.validate_with_details(fake_output, tool)

            stubbed_flags = {
                "time": self._stubs is not None,
                "rand": self._stubs is not None,
                "uuid": self._stubs is not None,
                "net": False,
            }

            step: Trace = {
                "node_id": node["id"],
                "tool_name": tool,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": int((end - start) * 1000),
                "verdict": verdict.value,
                # echo into trace so the CLI streamer can pick them up
                "input": seed if isinstance(seed, dict) else {"raw": str(seed)},
                "output": fake_output,
                "stubbed": stubbed_flags,
            }

            # Attach structured failure details when applicable
            if getattr(details, "kind", None) == "schema_mismatch":
                step["schema_expected"] = details.schema_expected or {}
                step["schema_found"] = details.schema_found
            elif getattr(details, "kind", None) == "exception":
                step["error_class"] = details.error_class or ""
                step["error_message"] = details.message or ""

            trace.append(step)

        return trace
