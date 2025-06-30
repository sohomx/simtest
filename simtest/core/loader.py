import importlib.util
from pathlib import Path
from typing import Any

def load_graph(path: str) -> dict[str, Any]:
    print(f"✅ [loader.py] Called load_graph with path: {path}")
    
    path_obj = Path(path).resolve()
    print(f"✅ [loader.py] Resolved absolute path: {path_obj}")

    spec = importlib.util.spec_from_file_location("agent", path_obj)
    if spec is None or spec.loader is None:
        raise ImportError(f"❌ [loader.py] Could not load module from path: {path_obj}")
    
    print(f"✅ [loader.py] Loaded spec: {spec}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore

    print("✅ [loader.py] Executed module. Now calling build_graph()")

    graph = module.build_graph()
    print(f"✅ [loader.py] Graph loaded with {len(graph.get('nodes', []))} nodes")
    
    return graph
