# Basic Agent Example

This is a minimal agent DAG for SimTest CI.

## Quickstart

```bash
simtest init --path examples/basic_agent/main.py --write-graph
simtest seed --suite tool-schema-sanity
simtest fuzz --quick --report simtest-report.md
