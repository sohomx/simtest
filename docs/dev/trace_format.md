# SimTest Trace Format (v1, Phase A)

**File:** JSONL (one JSON object per line)
- **Line 1:** run header
- **Lines 2..N:** step events in chronological order

> **Note:** Examples below use fenced code blocks. The schema example uses **JSONC** (JSON with comments) for readability; the actual on‑disk format is strict JSON **without comments**.

## Line 1 — Run header (keys sorted)
```json
{
  "run_id": "uuid-like",
  "seed_id": "refund_canary#17",
  "git_sha": "abcd1234",
  "started_at": "2025-09-06T12:00:00Z",
  "simtest_version": "0.1.0",
  "env": {"python": "3.11"}
}
```

## Step line schema (keys sorted)
```jsonc
{
  "run_id": "uuid-like",
  "step_idx": 0,
  "node_id": "RefundTool",
  "kind": "tool",                        // one of: "llm" | "tool" | "policy" | "python"
  "input_canon": { ... },                 // canonicalized JSON
  "output_canon": { ... },                // canonicalized JSON, or null on error
  "model": "gpt-4o-mini",               // for tools, put the tool name
  "latency_ms": 123,
  "cost_usd": 0.0007,
  "stubbed": {                            // determinism stubs in effect
    "time": true, "rand": true, "uuid": true, "net": false
  },
  "schema_expected": { ... },             // optional
  "schema_found": { ... },                // optional
  "error": {                              // present on failure only
    "kind": "schema_mismatch" | "exception" | "policy_violation",
    "class": "ValueError",
    "message": "short, scrubbed",
    "stack": "optional"
  },
  "signature": "RefundTool|schema_mismatch|a1b2c3d4"  // only on the failing step
}
```

## Canonicalization rules
- JSON dump with `sort_keys=True`, `separators=(",", ":")`
- Floats normalized to ~6 significant digits
- Error messages scrubbed of timestamps, PIDs, ports

## Invariants
- `run_id` constant across all lines in a file
- `step_idx` is 0..N-1 without gaps
- At most one step contains `error` **and** `signature` (the failing step)

## Tiny example (3 lines of JSONL)
```json
{"run_id":"r1","seed_id":"fixture#1","git_sha":"abcd1234","started_at":"2025-09-06T12:00:00Z","simtest_version":"0.1.0","env":{"python":"3.11"}}
{"run_id":"r1","step_idx":0,"node_id":"Input","kind":"python","input_canon":{"raw":"hello"},"output_canon":{"text":"hello"},"model":"python","latency_ms":2,"cost_usd":0.0,"stubbed":{"time":true,"rand":true,"uuid":true,"net":false}}
{"run_id":"r1","step_idx":1,"node_id":"RefundTool","kind":"tool","input_canon":{"approve":true,"amount":10.0},"output_canon":{"approved":true,"amount":10.0},"model":"RefundTool","latency_ms":87,"cost_usd":0.0007,"stubbed":{"time":true,"rand":true,"uuid":true,"net":false},"schema_expected":{"approve":"bool","amount":"number"},"schema_found":{"approved":"bool","amount":"number"},"error":{"kind":"schema_mismatch","class":"","message":"key 'approve' missing; found 'approved'"},"signature":"RefundTool|schema_mismatch|d3f9c21a"}
```
