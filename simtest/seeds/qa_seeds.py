import yaml
from pathlib import Path
from simtest.seeds.loader import Seed, load_seed_file
from simtest.core.loader import load_graph

# === Fake tool runner ===
def simulate_tool_call(node_id: str, input: dict) -> bool:
    # Simulate strict schema logic
    if node_id == "start" and "user_message" in input:
        return True
    if node_id == "analyze" and "text" in input:
        return True
    if node_id == "end" and input.get("confirmation") in [True, False]:
        return True
    return False

def qa_suite(path: Path) -> tuple[int, int]:
    seeds = load_seed_file(str(path))
    passed, failed = 0, 0

    for seed in seeds:
        ok = simulate_tool_call(seed.node_id, seed.input)
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"❌ {path.name}: {seed.node_id} → {seed.input} [INVALID]")

    return passed, failed
