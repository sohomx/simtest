from __future__ import annotations
import importlib.util
from pathlib import Path

def load_graph_from_py(path: str | Path):
    p = Path(path)
    if p.suffix != ".py":
        raise ValueError(f"Expected .py, got: {p}")
    spec = importlib.util.spec_from_file_location("simtest_user_workflow", str(p))
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    if hasattr(mod, "build_graph"):
        graph = mod.build_graph()
    elif hasattr(mod, "GRAPH"):
        graph = getattr(mod, "GRAPH")
    elif hasattr(mod, "graph"):
        graph = getattr(mod, "graph")
    else:
        raise RuntimeError("Python workflow must define build_graph() or GRAPH/graph")
    if not isinstance(graph, dict):
        raise TypeError("Workflow graph must be a dict")
    return graph
