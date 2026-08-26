"""Shared provenance helpers for wide-instrument-control-rescore: pin
verification against a source cell's own `experiment.yaml` (never a value
re-typed here) and small JSON/JSONL IO used by every stage script.

FAIL LOUDLY per the build task's binding invariant: `verify_pins` raises
SystemExit (does not return a soft warning) on any hash mismatch. Files this
harness depends on but that the source cell's OWN experiment.yaml does not
list under `instrument.pins` cannot be verified against anything -- they are
reported as UNPINNED, not silently treated as pinned-and-passing. See
pipeline_rescore.py's module docstring and this build's final report for the
concrete unpinned-file list found in doubt-gated-caution-tighten/experiment.yaml.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def verify_pins(cell_dir: Path, *, label: str) -> dict[str, Any]:
    """Reads `<cell_dir>/experiment.yaml`'s `instrument.pins` mapping
    (filename -> committed sha256, relative to cell_dir) and recomputes each
    file's current sha256. Raises SystemExit on ANY mismatch. Returns a
    report dict: {"label", "verified": [{"file", "sha256"}], "pin_source"}.
    Does NOT invent pins for files the source cell's own experiment.yaml
    does not list -- callers must separately record those as unpinned."""
    exp_path = cell_dir / "experiment.yaml"
    exp = load_yaml(exp_path)
    pins = ((exp.get("instrument") or {}).get("pins")) or {}
    if not pins:
        raise SystemExit(f"[provenance] {label}: no instrument.pins found in {exp_path}; refusing to proceed unverified.")

    verified = []
    mismatches = []
    for rel_name, expected_sha in pins.items():
        p = cell_dir / rel_name
        if not p.is_file():
            mismatches.append({"file": rel_name, "error": "missing", "expected": expected_sha})
            continue
        actual = sha256_of_file(p)
        if actual != expected_sha:
            mismatches.append({"file": rel_name, "expected": expected_sha, "actual": actual})
        else:
            verified.append({"file": rel_name, "sha256": actual})

    if mismatches:
        raise SystemExit(
            f"[provenance] PIN VERIFICATION FAILED for {label} ({exp_path}): "
            f"{json.dumps(mismatches, indent=2)}\n"
            f"Refusing to regenerate against drifted source scripts."
        )

    return {"label": label, "pin_source": str(exp_path), "verified": verified}


def record_unpinned(cell_dir: Path, files: list[str], *, label: str) -> dict[str, Any]:
    """Computes current sha256 for load-bearing files the source cell's own
    experiment.yaml does NOT pin (no comparison possible; recorded for
    provenance and flagged to the lead, per this build's report). Does not
    raise -- absence of a pin is a spec gap to report, not a hard stop by
    itself, since the cell that owns those files is itself already
    registered+resolved and this harness cannot retroactively pin it."""
    out = []
    for rel_name in files:
        p = cell_dir / rel_name
        out.append({
            "file": rel_name,
            "sha256": sha256_of_file(p) if p.is_file() else None,
            "status": "observed_no_committed_pin" if p.is_file() else "missing",
        })
    return {"label": label, "unpinned_load_bearing_files": out}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
