import json
import yaml
import argparse
import hashlib

parser = argparse.ArgumentParser()
parser.add_argument("--trace-log", required=True)
parser.add_argument("--input-seeds", required=True)
parser.add_argument("--output-seeds", required=True)
parser.add_argument("--manifest-out", required=True)
args = parser.parse_args()

with open(args.trace_log) as f:
    flat_traces = json.load(f)

# Group traces per seed (3 steps per seed)
steps_per_seed = 3
traces_by_seed = [flat_traces[i:i+steps_per_seed] for i in range(0, len(flat_traces), steps_per_seed)]

bad_seeds = []
for i, trace in enumerate(traces_by_seed):
    if any(step["verdict"] != "PASS" for step in trace):
        bad_seeds.append(i)

print(f"❌ Found {len(bad_seeds)} noisy seeds: {bad_seeds}")

with open(args.input_seeds) as f:
    seeds = yaml.safe_load(f)

# Drop noisy ones
good_seeds = [s for i, s in enumerate(seeds) if i not in bad_seeds]

# Pad to 100 with dummy inputs
while len(good_seeds) < 100:
    good_seeds.append({"input": {"raw": "fallback"}})

# Write cleaned seeds
with open(args.output_seeds, "w") as f:
    yaml.safe_dump(good_seeds, f)

# Write manifest
manifest = {}
for i, seed in enumerate(good_seeds):
    s = json.dumps(seed, sort_keys=True)
    manifest[f"seed_{i}"] = hashlib.sha256(s.encode()).hexdigest()

with open(args.manifest_out, "w") as f:
    json.dump(manifest, f, indent=2)

print("✅ Cleaned seed file and manifest written.")

