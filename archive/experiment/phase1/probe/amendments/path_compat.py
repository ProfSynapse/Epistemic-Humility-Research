"""Path helpers for archived probe-root amendment scripts."""

from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (
            (candidate / "experiment" / "phase1" / "probe").is_dir()
            and (candidate / "experiment" / "phase1" / "eval" / "scorers.py").exists()
        ):
            return candidate
    raise RuntimeError(
        "Could not locate Epistemic-Humility-Research repo root from "
        f"{here}; run from a complete checkout or pass explicit paths."
    )


def phase1_probe_dir() -> Path:
    return repo_root() / "experiment" / "phase1" / "probe"


def phase1_eval_dir() -> Path:
    return repo_root() / "experiment" / "phase1" / "eval"
