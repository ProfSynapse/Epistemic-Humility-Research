#!/usr/bin/env python3
"""Five-arm evidential wrapper for ood-breadth-beyond-selfaware stage 8.

`gate_score.py` (PINNED, unmodified -- experiment.yaml instrument.pins) computes
`integrity_all_pass` as a flat `all()` over G1/G2/G3/G_docker_digest with no
per-arm scoping (gate_score.py lines 420-441). `gates.yaml`'s G1 block is scoped
to `[A2, A6, A7]` only (`on_failure: void_arms_A2_A6_A7_report_on_five_arms`),
and the lead has adjudicated (2026-08-09) that G1's registered FAIL should not
block G4/G5/G6 for the five surviving arms (A1, A3, A4, A5, A8), since G2 and
G3 each independently read PASS across those five arms.

This module removes ONLY that flat short-circuit. It imports `score_g1`,
`score_g2`, `score_g3`, `score_g_docker`, `score_g4`, `score_g5`, `score_g6`
from `gate_score.py` UNCHANGED (`import gate_score` then `gate_score.score_gN(...)`,
same call signatures gate_score.py's own `main()` uses) and calls them exactly
as `gate_score.py`'s `main()` would if `integrity_all_pass` were True. No
threshold, formula, resample count, seed, or comparison population is touched
anywhere in this file -- every number below G4/G5/G6 is produced by the pinned
function bodies, verbatim.

The integrity-gate statuses this module reads (via the same pinned score_g1/
score_g2/score_g3/score_g_docker calls) are recorded in the output header for
the record, alongside gate_score.py's own flat integrity_all_pass computation
(reproduced here for comparison, but NOT used to gate anything below it --
that is the one behavioral difference from gate_score.py).

Known constraint this wrapper does NOT paper over: `score_g4` (gate_score.py
lines 275-316) has its own internal arm-count gate -- `if len(arm_rr) < 8:
NOT_RUN` (line 297) -- independent of the flat integrity short-circuit this
module bypasses. With only five arms holding stage-5 results (A2/A6/A7 void),
`arm_rr` will contain 5 entries per surface, so `score_g4` unchanged will
report `NOT_RUN` for both S_KUQ and S_AMBIGQA regardless of this wrapper.
This module does not alter that behavior; it is reported, not fixed, per the
directive to call the pinned functions unchanged.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR))

import gate_score  # pinned module; sha256 in experiment.yaml instrument.pins, unmodified by this file


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docker-digest", default=None, help="live digest from `docker inspect`, for G_docker_digest")
    ap.add_argument("--g1-rerun-metrics", type=Path, default=None, help="stage-3 re-run A2 SelfAware metrics.json")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    gates = gate_score.load_gates()

    # Same four calls gate_score.py's main() makes, same arguments, unchanged functions.
    integrity = {
        "G1": gate_score.score_g1(gates, args.g1_rerun_metrics),
        "G2": gate_score.score_g2(gates),
        "G3": gate_score.score_g3(gates),
        "G_docker_digest": gate_score.score_g_docker(gates, args.docker_digest),
    }
    integrity_statuses = {name: g["status"] for name, g in integrity.items()}
    integrity_all_pass_flat = all(s == "PASS" for s in integrity_statuses.values())

    # The one behavioral difference from gate_score.py: score_g4/score_g5/score_g6
    # are called unconditionally rather than being replaced with NOT_READ when
    # integrity_all_pass_flat is False. Same functions, same zero-argument /
    # gates-argument call signatures gate_score.py's main() uses at lines 432-434.
    evidential = {
        "G4": gate_score.score_g4(gates),
        "G5": gate_score.score_g5(gates),
        "G6": gate_score.score_g6(),
    }

    report = {
        "scope": "five_surviving_arms_A1_A3_A4_A5_A8_per_lead_adjudication_2026-08-09",
        "wrapper_module": "score_evidential_fivearm.py",
        "wraps_unmodified_module": "gate_score.py",
        "integrity_gates_read_verbatim": integrity,
        "integrity_all_pass_flat_gate_score_semantics": integrity_all_pass_flat,
        "note": (
            "integrity_all_pass_flat_gate_score_semantics reproduces gate_score.py's "
            "own flat all()-over-every-integrity-gate computation (gate_score.py "
            "line 427) for the record only. This module does not gate the "
            "evidential block on it: gates.yaml scopes G1 to [A2, A6, A7] "
            "(on_failure: void_arms_A2_A6_A7_report_on_five_arms), not "
            "void-the-whole-cell, and G2/G3/G_docker_digest each independently "
            "read PASS above. score_g4/score_g5/score_g6 are called exactly as "
            "gate_score.py's main() calls them when integrity_all_pass is True -- "
            "unmodified functions, unmodified arguments. G4 may still read NOT_RUN "
            "below due to its own internal 8-arm requirement (see module "
            "docstring); that is a property of the pinned score_g4 body, not of "
            "this wrapper."
        ),
        "evidential_gates": evidential,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
