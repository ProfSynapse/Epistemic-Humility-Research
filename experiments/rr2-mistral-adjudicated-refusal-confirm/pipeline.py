#!/usr/bin/env python3
"""Top-level CLI for rr2-mistral-adjudicated-refusal-confirm:
materialize -> fit_reuse (reconstruct, NOT refit) -> heldout (4 passes) ->
detector-v2 report, in order, at the ONE fixed operating point. No FIT stage,
no dose ladder, no selection logic (see cell.yaml, AMENDMENT.md).

`all` stops after generation and the detector-v2-only report: it does NOT
compute RG1/RG2/RG3 or a verdict, because the primary rate (`refused_final`)
requires the blinded adjudication lane, which is a separate, out-of-band
human/PI step this script cannot and must not automate. Instead it prints
the exact next commands. This mirrors RR's own pipeline.py structure (each
phase checks its own prerequisite artifacts and raises a clear error if a
prior phase's output is missing) with one added stop point.
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
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def run(cmd: list[str]) -> int:
    print(f"[pipeline] $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(HERE)).returncode


ADJUDICATION_INSTRUCTIONS = """
[pipeline] Generation complete. detector-v2-only summary written to
analysis-committed/heldout_summary.json (provisional; RG1/RG2/RG3 NOT yet
computed). Next steps (out-of-band, human/PI-driven -- this script does not
and must not run them automatically):

  1. python3 build_adjudication_pool.py
     Builds the blinded pool (analysis/adjudication_pool.jsonl, gitignored)
     and its committed manifest. Send the pool file to the adjudicator (the
     PI, or a context-free agent given ONLY the registered rubric in
     AMENDMENT.md).

  2. The adjudicator grades every {opaque_id, text} pair once, against the
     registered rubric, and returns a graded file:
     {"opaque_id": ..., "is_abstention": true|false} per line.

  3. python3 apply_adjudication.py commit-hash --graded-file <graded.jsonl>
     Commits the graded file's sha256 BEFORE unblinding (unblinding-order
     guarantee). This step must run on the file exactly as returned, before
     step 4.

  4. python3 apply_adjudication.py apply --graded-file <graded.jsonl>
     Verifies the committed hash, joins back to row keys, computes
     refused_final = refused_v2 OR adjudicated_abstention, and writes
     analysis-committed/final_report.json with RG1/RG2/RG3 and the falsifier
     verdict. This is the report the lead adjudicates against AMENDMENT.md's
     Gates section -- it is a straight readout, not itself an Outcome verdict.
"""


def cmd_all(args: argparse.Namespace) -> int:
    t0 = time.time()
    rc = run([sys.executable, "materialize_rows.py"])
    if rc != 0:
        return rc
    materialize_report_path = ANALYSIS / "materialize_report.json"
    precondition_path = ANALYSIS / "materialize_precondition_report.json"
    materialize_report = json.loads(materialize_report_path.read_text()) if materialize_report_path.is_file() \
        else json.loads(precondition_path.read_text())
    if not materialize_report.get("staged_inputs_present", True):
        print(
            "[pipeline] staged inputs are not present locally; stopping before "
            "GPU work. Re-run `all` once the fleet row pool and atlas capture "
            "are staged (see materialize_rows.py docstring).",
            flush=True,
        )
        return 0
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] materialize OK; refusing to launch GPU phases without --i-know-this-runs-on-gpu", flush=True)
        return 0

    rc = run([sys.executable, "fit_reuse.py", "reconstruct"])
    if rc != 0:
        return rc

    rc = run([sys.executable, "heldout_scorer.py", "--batch-size", str(args.batch_size)])
    if rc != 0:
        return rc

    elapsed = time.time() - t0
    print(f"[pipeline] generation done in {elapsed:.0f}s (this run's actual wall time).", flush=True)
    print(ADJUDICATION_INSTRUCTIONS, flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="materialize -> fit_reuse -> heldout -> print adjudication instructions")
    p_all.add_argument("--batch-size", type=int, default=8)
    p_all.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_all.set_defaults(func=cmd_all)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
