import time
import random
from contextlib import contextmanager
from typing import TypedDict

class Trace(TypedDict):
    node_id: str
    tool_name: str
    input_tokens: int
    output_tokens: int
    latency_ms: int

class SandboxExecutor:
    def __init__(self, graph: dict, timeout_s: int = 30):
        self.graph = graph
        self.timeout = timeout_s
        self._rng = random.Random(42)  # deterministic

    def __enter__(self):
        print("🔒 Entered sandbox (no external net access)")
        # optionally patch env, restrict fs, etc.
        return self.run_seed

    def __exit__(self, exc_type, exc_val, tb):
        print("🔓 Exited sandbox")

    def run_seed(self, seed: dict) -> list[Trace]:
        trace: list[Trace] = []
        for node in self.graph["nodes"]:
            start = time.time()
            input_tokens = self._rng.randint(10, 50)
            output_tokens = self._rng.randint(10, 100)
            time.sleep(self._rng.uniform(0.01, 0.05))  # simulate latency
            end = time.time()

            trace.append({
                "node_id": node["id"],
                "tool_name": node["tool_schema"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": int((end - start) * 1000),
            })
        return trace
