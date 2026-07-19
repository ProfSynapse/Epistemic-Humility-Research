#!/usr/bin/env python3
"""Top-level CLI for llama-atlas-gated-wide-instrument-retest: materialize ->
FIT dose ladder (every rung scored under BOTH instruments) -> report, per
family (llama only; adapted from rr-cross-family-raw-refusal's pipeline.py,
read in full before editing).

THE CHANGE vs rr: this cell is FIT-only (AMENDMENT.md "Scope: FIT-side
dose-ladder characterization") -- there is no held-out stage and no
heldout_scorer.py module (none was copied at sign, per experiment.yaml's
module list). `cmd_all` no longer branches on a selected operating point; it
always runs materialize -> dose_ladder (the full ladder, no early stop) ->
report.

Each phase's own module (materialize_rows.py, dose_ladder.py) checks for its
own prerequisite artifacts and raises a clear, actionable error if a prior
phase's output is missing, so this orchestrator adds no separate
phase-manifest layer: relaunching `all` after a crash re-enters at whichever
phase's precondition first fails, and RunLog resumability inside the GPU
phase means a killed mid-run does not lose completed rows either.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
COMMITTED = HERE / "analysis-committed"


def run(cmd: list[str]) -> int:
    print(f"[pipeline] $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(HERE)).returncode


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def cmd_report(args: argparse.Namespace) -> int:
    """THE CHANGE vs rr: this cell is FIT-only, every rung already scored
    under both instruments by dose_ladder.py -- there is no held-out stage
    and no heldout_scorer.py module (none was copied at sign). This just
    passes the FIT ladder report through as the family report, unchanged."""
    fit_report_path = COMMITTED / args.family / "fit_dose_ladder_report.json"
    if not fit_report_path.is_file():
        raise SystemExit(f"missing {fit_report_path}; run `pipeline.py fit --family {args.family}` first")
    fit_report = json.loads(fit_report_path.read_text())
    n_rungs = len(fit_report.get("rungs", []))
    report: dict[str, Any] = {
        "family": args.family,
        "fit_dose_ladder": fit_report,
        "summary_sentence": (
            f"{args.family}: FIT-only wide-instrument retest, {n_rungs} "
            f"(layer, dose, arm) rungs scored, no FIT dose selection and no "
            f"held-out stage (cell.yaml dose_policy.fit_dose_selection: "
            f"NONE). [FILLED BY LEAD -- this is the harness's straight "
            f"readout against G1/G-spec, not the adjudicated Outcome text.]"
        ),
    }
    write_json(COMMITTED / args.family / "family_report.json", report)
    print(json.dumps(report, indent=2, default=str)[:4000], flush=True)
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    t0 = time.time()
    rc = run([sys.executable, "materialize_rows.py", "--family", args.family])
    if rc != 0:
        return rc
    materialize_report = json.loads((HERE / "analysis" / args.family / "materialize_precondition_report.json").read_text()) \
        if not (HERE / "analysis" / args.family / "materialize_report.json").is_file() \
        else json.loads((HERE / "analysis" / args.family / "materialize_report.json").read_text())
    if not materialize_report.get("staged_inputs_present", True):
        print(
            "[pipeline] staged inputs are not present locally; stopping before "
            "the GPU dose ladder. Re-run `all` once the fleet row pool and "
            "atlas capture are staged (see materialize_rows.py docstring).",
            flush=True,
        )
        return 0
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] materialize OK; refusing to launch GPU phases without --i-know-this-runs-on-gpu", flush=True)
        return 0
    rc = run([sys.executable, "dose_ladder.py", "--family", args.family, "--batch-size", str(args.batch_size)])
    if rc != 0:
        return rc
    rc = run([sys.executable, "pipeline.py", "report", "--family", args.family])
    elapsed = time.time() - t0
    print(f"[pipeline] family {args.family} done in {elapsed:.0f}s (this run's actual wall time, not a projection)", flush=True)
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="materialize -> fit+full-ladder -> report, in order (no held-out stage in this cell)")
    p_all.add_argument("--family", required=True, choices=("llama",))
    p_all.add_argument("--batch-size", type=int, default=8)
    p_all.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_all.set_defaults(func=cmd_all)

    p_report = sub.add_parser("report", help="pass the FIT ladder report through as the family report")
    p_report.add_argument("--family", required=True, choices=("llama",))
    p_report.set_defaults(func=cmd_report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
