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

## Quickstart

SimTest uses a 3-step workflow:

```bash
simtest init --path examples/basic_agent/main.py
simtest seed --suite tool-schema-sanity
simtest fuzz --quick --report simtest-report.md
```

This will:

* Parse your agent and extract the tool DAG
* Load a curated pack of test seeds
* Run 100 fuzz tests with sandboxed cost tracking
* Emit a markdown report of pass/fail verdicts, top latency/cost nodes, and schema coverage

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
