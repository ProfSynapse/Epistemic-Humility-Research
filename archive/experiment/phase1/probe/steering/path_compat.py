"""Path helpers for the archived steering harness.

The harness was originally located at ``experiment/phase1/probe/steering`` and
used fixed parent-depth path math. After archival, the still-live shared helpers
remain in the ``archive/experiment/phase1`` tree, so resolve them from repo-root
sentinels instead of from the archived directory depth.
"""

from __future__ import annotations

from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (
            (candidate / "archive" / "experiment" / "phase1" / "eval" / "scorers.py").exists()
            and (candidate / "archive" / "experiment" / "phase1" / "probe").exists()
        ):
            return candidate
    raise RuntimeError(
        "Could not locate Epistemic-Humility-Research repo root from "
        f"{here}; run from a complete checkout or pass explicit paths."
    )


def phase1_probe_dir() -> Path:
    return repo_root() / "archive" / "experiment" / "phase1" / "probe"


def phase1_eval_dir() -> Path:
    return repo_root() / "archive" / "experiment" / "phase1" / "eval"


def datasets_dir() -> Path:
    return repo_root() / "datasets"


def tuner_dir() -> Path:
    return repo_root() / "synaptic-tuner"
