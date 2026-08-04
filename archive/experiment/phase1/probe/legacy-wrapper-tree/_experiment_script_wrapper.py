"""Compatibility loader for scripts moved into experiment-owned directories."""

from __future__ import annotations

import runpy
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _script_dir(experiment_slug: str) -> Path:
    return _repo_root() / "experiments" / experiment_slug / "scripts"


def load_experiment_script(experiment_slug: str, module_name: str):
    script_dir = _script_dir(experiment_slug)
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    path = script_dir / f"{module_name}.py"
    existing = sys.modules.get(module_name)
    if existing is not None and Path(getattr(existing, "__file__", "")).resolve() == path:
        return existing
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_experiment_script(experiment_slug: str, module_name: str) -> None:
    script_dir = _script_dir(experiment_slug)
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    runpy.run_path(str(script_dir / f"{module_name}.py"), run_name="__main__")
