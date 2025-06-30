from simtest.fuzz.sandbox import SandboxExecutor
from simtest.fuzz.tracker import CostTracker

FAKE_GRAPH = {
    "nodes": [
        {"id": "start", "tool_schema": "StartTool"},
        {"id": "analyze", "tool_schema": "AnalyzeTool"},
        {"id": "end", "tool_schema": "EndTool"},
    ]
}

FAKE_SEEDS = [
    {"input": {"raw": "seed-1"}},
    {"input": {"raw": "seed-2"}},
    {"input": {"raw": "seed-3"}},
    {"input": {"raw": "seed-4"}},
    {"input": {"raw": "seed-5"}},
]

def test_fuzz_trace_cost_under_budget():
    tracker = CostTracker(max_dollars=3.00)
    with SandboxExecutor(graph=FAKE_GRAPH) as run:
        for seed in FAKE_SEEDS:
            trace = run(seed["input"])
            tracker.consume_trace(trace)

    assert tracker.compute_cost() <= 3.00
