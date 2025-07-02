from typing import List, Optional
from pathlib import Path

class ReportWriter:
    def __init__(
        self,
        traces: List[dict],
        verdicts: dict,
        coverage: dict,
        total_cost: float,
        runtime_s: float,
        suite_name: str = "",
        cost_multiplier: float = 1.0,
        noise_pct: float = 0.0,
    ):
        self.traces = traces
        self.verdicts = verdicts
        self.coverage = coverage
        self.total_cost = total_cost
        self.runtime_s = runtime_s
        self.suite_name = suite_name
        self.cost_multiplier = cost_multiplier
        self.noise_pct = noise_pct

    def render(self) -> str:
        fail_rows = [
            f"| {t.get('seed_id', '?')} | {t['verdict']} | ${self._c(t)} | {t['latency_ms']} | {t.get('explanation', '')} |"
            for t in self.traces if t["verdict"] != "PASS"
        ]

        top_cost_nodes = sorted(
            self.traces, key=lambda t: t["input_tokens"] + t["output_tokens"], reverse=True
        )[:5]

        top_rows = [
            f"| {t['node_id']} | {t['tool_name']} | {t['input_tokens'] + t['output_tokens']} tokens |"
            for t in top_cost_nodes
        ]

        return f"""# SimTest Report: `{self.suite_name}`

**Stats**
- ✅ Passed: {self.verdicts['PASS']} / {sum(self.verdicts.values())}
- 📊 Coverage: {self.coverage['node_visit_pct']}% nodes / {self.coverage['tool_schema_visit_pct']}% schemas
- 💰 Cost: ${self.total_cost:.4f}
- 💸 Cost Multiplier: {self.cost_multiplier}
- 🎯 Noise Rate: {self.noise_pct:.2%}
- ⏱️ Runtime: {round(self.runtime_s, 2)} seconds

## ❌ Failures

| Seed | Verdict | Cost | Latency | Explanation |
|------|---------|------|---------|-------------|
{chr(10).join(fail_rows) or '_No failures_'}

## 🔥 Top 5 Costliest Nodes

| Node | Tool | Total Tokens |
|------|------|---------------|
{chr(10).join(top_rows)}
"""

    def write(self, path: str):
        Path(path).write_text(self.render())

    def _c(self, t: dict) -> str:
        tokens = t["input_tokens"] + t["output_tokens"]
        return f"{tokens / 1000 * 0.002:.4f}"
