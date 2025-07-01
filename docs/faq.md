**Why is cost always under \$1?**

SimTest uses a strict budget cap (`--max-cost`) enforced by the `CostTracker` utility. By default, `--quick` mode runs 100 seeds and ensures total token usage stays within \~\$1 using GPT-3.5. If the cost exceeds the budget during a fuzz run, the test aborts gracefully with a `BudgetExceeded` error.

---

**How can I control runtime or lower seed counts?**

Use the `--quick` flag to limit fuzz runs to 100 seeds (default). You can also pass `--n <count>` when generating or running custom seeds. Runtime is kept under 90 seconds in CI by:

* running with fixed RNG and temp=0
* skipping semantic checks unless explicitly enabled
* parallelization in future versions is planned, but not required for quick mode

---

**What’s the difference between deterministic and semantic verdicts?**

By default, SimTest only evaluates schema validation and exceptions (deterministic). This ensures 100% reproducibility across runs.

When `--semantic-check` is enabled, SimTest sends task/output/tool schema to GPT-3.5 at `temperature=0` to get an explanation and pass/fail reasoning. This semantic layer is optional and used for traceability/debugging—not to gate CI.

---

**How do exit codes work in CI?**

The GitHub Action (composite) fails your pull request if:

* new FAILs are introduced compared to previous baseline
* or total cost increases >10%

SimTest emits a red/green badge and the markdown report includes:

* verdict breakdown
* top latency/cost steps
* coverage metrics

Use `--report` flag to output this to a file for CI parsing or human inspection.
