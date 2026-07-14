#!/usr/bin/env python3
"""Top-level CLI for rr3-corrected-placebo-replication:

  materialize (mistral, llama) -> fit_reuse reconstruct (mistral hs16, llama
  hs20; NOT refit) -> heldback decoy source pass (both families) -> core
  generation (mistral: baseline/gated/K-seed random_direction/
  dose_knowns_ungated) -> rider generation (mistral + llama placebo dose
  ladders, both populations) -> print adjudication instructions.

`all` stops after generation: it does NOT build the adjudication pool, run
adjudication, or compute RG1/RG2/RG3/the rider report, because the primary
rate (`refused_final`) requires the blinded adjudication lane, a separate,
out-of-band human/PI (or context-free-agent) step this script cannot and
must not automate. Instead it prints the exact next commands, mirroring
RR2's own `pipeline.py` structure (each phase checks its own prerequisite
artifacts and raises a clear error if a prior phase's output is missing).
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

FAMILIES = ("mistral", "llama")

ADJUDICATION_INSTRUCTIONS = """
[pipeline] Generation complete for both families. detector-v2-only summaries
written to analysis-committed/{core_heldout_summary,rider_mistral_heldout_summary,
rider_llama_heldout_summary}.json (provisional; RG1/RG2/RG3 NOT yet
computed). Next steps (out-of-band, human/PI-driven -- this script does not
and must not run them automatically):

  1. python3 build_adjudication_pool.py
     Builds the sharded blinded pool (analysis/shards/*.jsonl, gitignored)
     and its committed manifest. Dispatch each shard to a context-free
     adjudicator (the registered rubric, bare texts, output format only; no
     experiment context; no pattern matcher, per the standing PI directive).

  2. Each adjudicator grades every {opaque_id, text} pair in their shard
     once, against the registered rubric, and returns a graded file:
     {"opaque_id": ..., "is_abstention": true|false} per line, in the SAME
     line order as that shard's pool file (positional join).

  3. python3 apply_adjudication.py commit-hash --shard-id <ID> --graded-file <graded.jsonl>
     for EVERY shard. Commits each graded file's sha256 BEFORE unblinding.
     Must run on the file exactly as returned, before step 4.

  4. python3 apply_adjudication.py apply --grading-manifest <manifest.json>
     Verifies every committed hash, joins back to row keys, evaluates CG1
     (per-shard AND pooled), and writes analysis/adjudication_applied.jsonl
     + analysis-committed/adjudication_applied_manifest.json. Any shard
     failing CG1 is voided and regraded once (build_regrade.py); a second
     failure voids its cell and is reported straight.

  5. python3 rr3_scorer.py
     Computes RG1 (effect-ratio, max-over-K)/RG2 (benefit)/RG3 (cost) and the
     falsifier verdict (analysis-committed/core_final_report.json), plus the
     descriptive rider dose-response report
     (analysis-committed/rider_final_report.json). These are the reports the
     lead adjudicates against AMENDMENT.md's Gates section -- straight
     readouts, not themselves an Outcome verdict.
"""


def run(cmd: list[str]) -> int:
    print(f"[pipeline] $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(HERE)).returncode


def _materialize_report(family: str) -> dict[str, Any]:
    report_path = ANALYSIS / family / "materialize_report.json"
    precondition_path = ANALYSIS / family / "materialize_precondition_report.json"
    if report_path.is_file():
        return json.loads(report_path.read_text())
    return json.loads(precondition_path.read_text())


def cmd_all(args: argparse.Namespace) -> int:
    t0 = time.time()

    for family in FAMILIES:
        rc = run([sys.executable, "materialize_rows.py", "--family", family])
        if rc != 0:
            return rc

    reports = {family: _materialize_report(family) for family in FAMILIES}
    not_staged = [family for family, r in reports.items() if not r.get("staged_inputs_present", True)]
    if not_staged:
        print(
            f"[pipeline] staged inputs not present locally for: {not_staged}; stopping before "
            f"GPU work. Re-run `all` once the fleet row pool(s) and atlas capture(s) are staged "
            f"(see materialize_rows.py docstring).",
            flush=True,
        )
        return 0
    if not args.i_know_this_runs_on_gpu:
        print("[pipeline] materialize OK (both families); refusing to launch GPU phases without --i-know-this-runs-on-gpu", flush=True)
        return 0

    for family in FAMILIES:
        rc = run([sys.executable, "fit_reuse.py", "reconstruct", "--family", family])
        if rc != 0:
            return rc

    for family in FAMILIES:
        rc = run([sys.executable, "heldout_scorer.py", "heldback", "--family", family, "--batch-size", str(args.batch_size)])
        if rc != 0:
            return rc

    rc = run([sys.executable, "heldout_scorer.py", "core", "--batch-size", str(args.batch_size)])
    if rc != 0:
        return rc

    for family in FAMILIES:
        rc = run([sys.executable, "heldout_scorer.py", "rider", "--family", family, "--batch-size", str(args.batch_size)])
        if rc != 0:
            return rc

    elapsed = time.time() - t0
    print(f"[pipeline] generation done in {elapsed:.0f}s (this run's actual wall time).", flush=True)
    print(ADJUDICATION_INSTRUCTIONS, flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("all", help="materialize (both) -> fit_reuse (both) -> heldback (both) -> core -> rider (both) -> print adjudication instructions")
    p_all.add_argument("--batch-size", type=int, default=8)
    p_all.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_all.set_defaults(func=cmd_all)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
