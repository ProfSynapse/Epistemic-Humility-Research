"""Compatibility wrapper loader for scripts moved to experiments/common/mechinterp."""

from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _common_dir() -> Path:
    return _repo_root() / "experiments" / "common" / "mechinterp"


def load_common_mechinterp_module(module_name: str):
    common_dir = _common_dir()
    if str(common_dir) not in sys.path:
        sys.path.insert(0, str(common_dir))
    path = common_dir / f"{module_name}.py"
    existing = sys.modules.get(module_name)
    if existing is not None and Path(getattr(existing, "__file__", "")).resolve() == path:
        return existing
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load common mechinterp module {module_name} from {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def reexport_common_mechinterp_module(module_name: str, namespace: dict):
    module = load_common_mechinterp_module(module_name)
    old_name = namespace.get("__name__")
    if isinstance(old_name, str) and old_name != "__main__":
        sys.modules[old_name] = module
    for name in dir(module):
        if name not in {"__builtins__", "__cached__", "__file__", "__loader__", "__name__", "__package__", "__spec__"}:
            namespace[name] = getattr(module, name)
    return module
