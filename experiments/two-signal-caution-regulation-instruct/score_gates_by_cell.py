"""Cell-filtered gate adjudicator for two-signal-caution-regulation-instruct.

WHY THIS SCRIPT EXISTS (read gates.yaml's "DISCOVERED LIMITATION" comment
first): `tuner.py mechinterp score-gates` dispatches every gate through
`MechInterp/stats/evaluator.py`'s `_eval_kill_diff`, which does NOT read a
gate's `cell_field`/`cell` keys -- it only filters rows by arm. This cell's
surface is ONE combined 458-row pool (309 confab + 149 answerable_refused)
under each arm name, so running the generic CLI directly against this cell's
`gates.yaml` would silently score every G1/G2 gate over ALL 458 rows instead
of the intended cell subset.

This script imports `MechInterp.stats.gates.kill_diff_vs_control` directly
(the SAME primitive the tuner uses, no reimplementation, no tuner edit) and
does the cell-filtering itself, reading `primary_arm` / `control_arm` /
`cell_field` / `cell` / `primary_indicator` / `control_indicator` /
`pass_if_diff` / `pass_if_ci_excludes_zero` from gates.yaml so that file stays
the single source of truth for thresholds. It is CPU-only (no GPU, no model
load) -- it only reads an existing rows_out.jsonl.

This is a BUILD-TIME tool, not a run: as of this commit no full-sweep
rows_out.jsonl exists yet (SMOKE only). Running this script against the smoke
output is possible but not meaningful for G1/G2 (n=12, not the full 458-row
population); it becomes meaningful once a full run exists.

Usage:
    python experiments/two-signal-caution-regulation-instruct/score_gates_by_cell.py \\
        --gates-config experiments/two-signal-caution-regulation-instruct/gates.yaml \\
        --rows-path experiments/two-signal-caution-regulation-instruct/analysis/rows_out.jsonl \\
        [--out-path experiments/two-signal-caution-regulation-instruct/analysis/score_gates_report.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TUNER_ROOT = REPO_ROOT / "synaptic-tuner"
if str(TUNER_ROOT) not in sys.path:
    sys.path.insert(0, str(TUNER_ROOT))
from MechInterp.stats.gates import kill_diff_vs_control  # noqa: E402

_OP_RE = re.compile(r"^\s*(>=|<=|>|<|==)\s*(-?\d+(?:\.\d+)?)\s*$")


def _parse_pass_if(expr: str):
    m = _OP_RE.match(expr)
    if not m:
        raise ValueError(f"unrecognized pass_if_diff expression: {expr!r}")
    op, num_s = m.group(1), m.group(2)
    num = float(num_s)
    ops = {
        ">=": lambda x: x >= num,
        "<=": lambda x: x <= num,
        ">": lambda x: x > num,
        "<": lambda x: x < num,
        "==": lambda x: x == num,
    }
    return ops[op]


def _load_rows(rows_path: Path) -> list[dict]:
    rows = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _rows_for(rows: list[dict], arm: str, cell_field: Optional[str], cell: Optional[str]) -> dict[str, dict]:
    """row_key -> row, filtered to one arm and (optionally) one cell value."""
    out = {}
    for r in rows:
        if r.get("arm") != arm:
            continue
        if cell_field is not None and r.get(cell_field) != cell:
            continue
        key = r.get("row_key")
        if key is None:
            continue
        out[key] = r
    return out


def score_gate(gate: dict, rows: list[dict], seed: int, n_boot: int) -> dict:
    primary_arm = gate["primary_arm"]
    control_arm = gate["control_arm"]
    cell_field = gate.get("cell_field")
    cell = gate.get("cell")
    primary_ind_name = gate["primary_indicator"]
    control_ind_name = gate["control_indicator"]

    primary_rows = _rows_for(rows, primary_arm, cell_field, cell)
    control_rows = _rows_for(rows, control_arm, cell_field, cell)

    shared_keys = sorted(set(primary_rows) & set(control_rows))
    missing_primary = sorted(set(control_rows) - set(primary_rows))
    missing_control = sorted(set(primary_rows) - set(control_rows))

    primary_ind = [bool(primary_rows[k].get(primary_ind_name)) for k in shared_keys]
    control_ind = [bool(control_rows[k].get(control_ind_name)) for k in shared_keys]

    result = kill_diff_vs_control(primary_ind, control_ind, seed=seed, n_boot=n_boot)

    pred = _parse_pass_if(gate["pass_if_diff"])
    diff_pass = bool(pred(result["diff"]))
    ci_pass = True
    if gate.get("pass_if_ci_excludes_zero"):
        ci_pass = bool(result["ci_lo"] > 0.0 or result["ci_hi"] < 0.0)
    passed = diff_pass and ci_pass

    return {
        "primitive": "kill_diff_vs_control",
        "primary_arm": primary_arm,
        "control_arm": control_arm,
        "cell_field": cell_field,
        "cell": cell,
        "primary_indicator": primary_ind_name,
        "control_indicator": control_ind_name,
        "n_rows_scored": len(shared_keys),
        "n_missing_from_primary_arm": len(missing_primary),
        "n_missing_from_control_arm": len(missing_control),
        "value": result,
        "pass_if_diff": gate["pass_if_diff"],
        "pass_if_ci_excludes_zero": bool(gate.get("pass_if_ci_excludes_zero", False)),
        "diff_pass": diff_pass,
        "ci_pass": ci_pass,
        "passed": passed,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gates-config", required=True, type=Path)
    ap.add_argument("--rows-path", required=True, type=Path)
    ap.add_argument("--out-path", type=Path, default=None)
    args = ap.parse_args()

    with args.gates_config.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    seed = int(cfg.get("seed", 0))
    n_boot = int(cfg.get("n_boot", 1000))
    rows = _load_rows(args.rows_path)

    report = {
        "gates_config": str(args.gates_config),
        "rows_path": str(args.rows_path),
        "seed": seed,
        "n_boot": n_boot,
        "n_rows_total": len(rows),
        "gates": {},
    }
    overall_pass = True
    for gate in cfg.get("gates", []):
        name = gate["name"]
        try:
            scored = score_gate(gate, rows, seed=seed, n_boot=n_boot)
        except Exception as exc:  # noqa: BLE001 - surface any per-gate failure, keep going
            scored = {"error": str(exc), "passed": False}
        report["gates"][name] = scored
        if not scored.get("passed"):
            overall_pass = False
    report["overall_pass"] = overall_pass

    text = json.dumps(report, indent=2, sort_keys=False)
    if args.out_path is not None:
        args.out_path.parent.mkdir(parents=True, exist_ok=True)
        args.out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
