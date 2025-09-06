import importlib.util
import os
from pathlib import Path
from typing import Any


def load_graph(path: str) -> dict[str, Any]:
    print(f"✅ [loader.py] Called load_graph with path: {path}")

    p = Path(path)
    candidates: list[Path] = []

    # 1) Explicit project root via env (highest priority override)
    env_root = os.environ.get("SIMTEST_PROJECT_ROOT")
    if env_root:
        candidates.append(Path(env_root) / p)

    # 2) Given path as-is (absolute) or relative to CWD (pytest tmp)
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append(Path.cwd() / p)

    # 3) Repo root (../../ from this file)
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / p)

    # 4) Package root (../ from this file) — last resort
    pkg_root = Path(__file__).resolve().parents[1]
    candidates.append(pkg_root / p)

    resolved: Path | None = None
    tried: list[str] = []
    for c in candidates:
        tried.append(str(c))
        if c.exists():
            resolved = c.resolve()
            break

    if resolved is None:
        raise FileNotFoundError(f"❌ [loader.py] Could not find {p} in any of: {tried}")

    print(f"✅ [loader.py] Using path: {resolved}")

    spec = importlib.util.spec_from_file_location("agent", str(resolved))
    if spec is None or spec.loader is None:
        raise ImportError(f"❌ [loader.py] Could not load module from path: {resolved}")
    print(f"✅ [loader.py] Loaded spec: {spec}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    print("✅ [loader.py] Executed module. Looking for graph...")

    if hasattr(module, "build_graph"):
        graph = module.build_graph()
    elif hasattr(module, "GRAPH"):
        graph = getattr(module, "GRAPH")
    elif hasattr(module, "graph"):
        graph = getattr(module, "graph")
    else:
        raise RuntimeError("❌ [loader.py] Python workflow must define build_graph() or GRAPH/graph")

    if not isinstance(graph, dict):
        raise TypeError("❌ [loader.py] Workflow graph must be a dict")

    print(f"✅ [loader.py] Graph loaded with {len(graph.get('nodes', []))} nodes")
    return graph
