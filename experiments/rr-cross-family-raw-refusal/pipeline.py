#!/usr/bin/env python3
"""Top-level CLI for rr-cross-family-raw-refusal: materialize -> FIT dose
ladder -> held-out four-arm scoring -> outcome-shape report, per family.

Each phase's own module (materialize_rows.py, dose_ladder.py,
heldout_scorer.py) checks for its own prerequisite artifacts and raises a
clear, actionable error if a prior phase's output is missing, so this
orchestrator adds no separate phase-manifest layer: relaunching `all` after
a crash re-enters at whichever phase's precondition first fails, and RunLog
resumability inside each GPU phase means a killed mid-phase run does not
lose completed rows either.

`--mode smoke` is instrument validation ONLY (never a result): it forces
`materialize_rows.py`'s heldout-power / manifest checks (CPU-only, always
safe) and, if `--i-know-this-runs-on-gpu` is also passed, runs the FIT dose
ladder and held-out scorer on a small probe row count for wall-time
bracketing. The bracket this prints is a MEASUREMENT, not a commitment: it
is produced from whatever batch size and probe count are passed, on
whatever GPU is actually available, and should be re-measured at launch
time rather than trusted from this build.
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
    fit_report_path = COMMITTED / args.family / "fit_dose_ladder_report.json"
    if not fit_report_path.is_file():
        raise SystemExit(f"missing {fit_report_path}; run `pipeline.py fit --family {args.family}` first")
    fit_report = json.loads(fit_report_path.read_text())
    report: dict[str, Any] = {
        "family": args.family,
        "fit_dose_ladder": fit_report,
    }
    if fit_report["selected_operating_point"] is None:
        report["outcome_shape"] = "F"
        report["gates"] = None
        report["heldout_summary"] = None
        report["summary_sentence"] = (
            f"{args.family}: no FIT-viable (layer, dose) exists in the "
            f"bracketed grid (shape F) -- the write does not actuate clean "
            f"refusal at the atlas site even where the axis is maximally "
            f"readable; NOT promoted. [FILLED BY LEAD -- this is the "
            f"harness's straight readout, not the adjudicated Outcome text.]"
        )
    else:
        heldout_path = COMMITTED / args.family / "heldout_summary.json"
        if not heldout_path.is_file():
            raise SystemExit(f"missing {heldout_path}; run `pipeline.py heldout --family {args.family}` first")
        heldout = json.loads(heldout_path.read_text())
        report["heldout_summary"] = heldout
        report["outcome_shape"] = heldout["outcome_shape"]
        report["gates"] = heldout["gates"]
        report["summary_sentence"] = (
            f"{args.family}: shape {heldout['outcome_shape']} at layer "
            f"{heldout['layer']} dose {heldout['dose_abs']:.4f} -- "
            f"[FILLED BY LEAD -- this is the harness's straight readout, "
            f"not the adjudicated Outcome text]."
        )
    write_json(COMMITTED / args.family / "family_report.json", report)
    print(json.dumps(report, indent=2, default=str), flush=True)
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
    fit_report = json.loads((COMMITTED / args.family / "fit_dose_ladder_report.json").read_text())
    if fit_report["selected_operating_point"] is not None:
        rc = run([sys.executable, "heldout_scorer.py", "--family", args.family, "--batch-size", str(args.batch_size)])
        if rc != 0:
            return rc
    rc = run([sys.executable, "pipeline.py", "report", "--family", args.family])
    elapsed = time.time() - t0
    print(f"[pipeline] family {args.family} done in {elapsed:.0f}s (this run's actual wall time, not a projection)", flush=True)
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="materialize -> fit -> heldout -> report, in order")
    p_all.add_argument("--family", required=True, choices=("llama", "mistral"))
    p_all.add_argument("--batch-size", type=int, default=8)
    p_all.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_all.set_defaults(func=cmd_all)

    p_report = sub.add_parser("report", help="combine fit + heldout artifacts into one family report")
    p_report.add_argument("--family", required=True, choices=("llama", "mistral"))
    p_report.set_defaults(func=cmd_report)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
