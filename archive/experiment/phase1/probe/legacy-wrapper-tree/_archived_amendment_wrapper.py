"""Compatibility loader for archived amendment modules."""

from __future__ import annotations

import runpy
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _archive_dir() -> Path:
    return _repo_root() / "archive" / "experiment" / "phase1" / "probe" / "amendments"


def load_archived_module(module_name: str):
    archive_dir = _archive_dir()
    if str(archive_dir) not in sys.path:
        sys.path.insert(0, str(archive_dir))
    path = archive_dir / f"{module_name}.py"
    existing = sys.modules.get(module_name)
    if existing is not None and Path(getattr(existing, "__file__", "")).resolve() == path:
        return existing
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load archived amendment module {module_name} from {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_archived_module(module_name: str) -> None:
    archive_dir = _archive_dir()
    if str(archive_dir) not in sys.path:
        sys.path.insert(0, str(archive_dir))
    runpy.run_path(str(archive_dir / f"{module_name}.py"), run_name="__main__")
