"""Path helpers for shared readout modules."""

from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (
            (candidate / "experiments" / "common" / "knowledge_probe").is_dir()
            and (candidate / "experiment" / "phase1" / "eval" / "scorers.py").exists()
        ):
            return candidate
    raise RuntimeError(
        "Could not locate Epistemic-Humility-Research repo root from "
        f"{here}; run from a complete checkout or pass explicit paths."
    )


def knowledge_probe_dir() -> Path:
    return repo_root() / "experiments" / "common" / "knowledge_probe"


def locked_eval_dir() -> Path:
    return repo_root() / "experiment" / "phase1" / "eval"


def readouts_dir() -> Path:
    return Path(__file__).resolve().parent
