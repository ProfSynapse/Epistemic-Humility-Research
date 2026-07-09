"""Path helpers for Probe-as-Reward legacy producer scripts."""

from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (
            (candidate / "experiment" / "phase1" / "probe").is_dir()
            and (candidate / "experiments" / "probe-as-reward").is_dir()
        ):
            return candidate
    raise RuntimeError(f"Could not locate repository root from {here}")


def phase1_probe_dir() -> Path:
    return repo_root() / "experiment" / "phase1" / "probe"


def phase1_eval_dir() -> Path:
    return repo_root() / "experiment" / "phase1" / "eval"


def artifact_dir() -> Path:
    return repo_root() / "experiments" / "probe-as-reward" / "artifacts"
