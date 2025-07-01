# SimTest

![SimTest CI](https://github.com/sohomx/simtest/actions/workflows/simtest.yml/badge.svg)

**Fuzz testing and coverage reporting for LLM agents.**

SimTest is a zero-config test harness for validating multi-step LLM agents built with CrewAI, LangGraph, or custom DAGs.

It loads your agent graph, generates deterministic seed inputs, runs them in a controlled sandbox, and produces detailed cost/latency/failure/coverage reports. Ideal for teams that ship LLM agents in production and want CI-grade reliability.

---

## Installation

Install via PyPI:

```bash
pip install simtest
```

Or clone the repository directly:

```bash
git clone https://github.com/sohomx/simtest.git
cd simtest
pip install .
```

---

## Quick Start – 3 commands

```bash
pip install -e .                            # 1️⃣ editable install for fast iteration
simtest init examples/basic_agent/main.py   # 2️⃣ parse agent & write .simgraph.json
simtest fuzz --quick                        # 3️⃣ 100 seeds, <60 s, < $1
```
---

## What happens under the hood

1. **Editable install**

   Links your working directory into the Python environment. Any code edits are picked up instantly without reinstalling the package.

2. **`simtest init`**

   Parses your agent file (`main.py`, LangGraph/CrewAI/Python DAG) and builds a `.simgraph.json` file:

   * Lists all nodes and their tool schemas
   * Ensures graph structure is deterministic and reproducible
   * Used as the input for later test runs

3. **`simtest fuzz --quick`**

   Runs a default 100 curated seed cases in a sandboxed executor:

   * Tracks cost, latency, and verdict per node
   * Validates schema correctness and catches exceptions
   * Warns if coverage <80% (nodes or tool schemas)
   * Enforces a budget cap (`--max-cost $3` by default)
   * Can optionally emit a markdown report (`--report report.md`)

---

### 📽 Terminal Demo

Here’s a 30-second walkthrough of SimTest in action:

![SimTest Demo](assets/demo.svg)

This runs the core workflow:

```bash
simtest init --path examples/basic_agent/main.py
simtest seed --suite tool-schema-sanity
simtest fuzz --quick --report simtest-report.md
```

It parses the agent DAG, loads curated test seeds, runs sandboxed fuzz checks, and writes a markdown report — all under 30 seconds.

---

## CLI Commands

### `simtest init`

Parses your agent file and generates `.simgraph.json`:

```bash
simtest init --path path/to/your_agent.py --write-graph
```

### `simtest seed`

Copies a curated seed pack:

```bash
simtest seed --suite tool-schema-sanity
```

You can also generate LLM-based seeds:

```bash
simtest generate --suite analyze --n 100
```

### `simtest fuzz`

Runs all seeds in a sandbox and enforces cost limits:

```bash
simtest fuzz --suite tool-schema-sanity --quick --max-cost 3.0 --report simtest-report.md
```

Optional flag:

* `--semantic-check` (use LLM to explain failed outputs)

---

## What SimTest Checks

* Tool schema mismatches
* Runtime exceptions
* Over-budget completions
* High-latency steps
* Coverage gaps (nodes and schemas)

Each failure is classified and logged deterministically. Optional semantic verdicts use GPT-3.5 in zero-temperature mode for explanations.

---

## Output Example

```bash
✅ Fuzz complete: 100 seeds run
💰 Total cost: $0.74
📊 Coverage: 92.0% nodes / 85.0% schemas
✅ PASS 96 / 100
```

A markdown report (if `--report path.md` is provided) includes:

* Table of failed seeds (seed id, verdict, latency, explanation)
* Top 5 costliest nodes
* Total cost, runtime, and coverage stats

---

## CI Integration

To enforce test gates on pull requests, add this GitHub Action:

```yaml
# .github/workflows/simtest.yml
name: SimTest CI

on: [push, pull_request]

jobs:
  simtest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      - run: pip install .
      - run: simtest fuzz --quick --report simtest-report.md
```

---

## License

MIT License.

---

## Maintainers

SimTest is maintained by reliability engineers building mission-critical LLM workflows. Contributions are welcome.
