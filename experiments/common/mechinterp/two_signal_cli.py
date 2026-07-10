#!/usr/bin/env python3
"""Talk to the model and watch the trust signal — interactive CLI demo.

A thin REPL over two_signal_runtime.TwoSignalReadout. Load the base model + the
fitted gate/dial artifacts once, then type questions and see, per answer:

  * answerability  - the calibrated gate (abstains below threshold instead of guessing)
  * the model's answer (only when gated through)
  * trust          - the calibrated dial: P(this specific answer is correct)
  * a LOW-TRUST flag when the dial vetoes a confident-looking confabulation

Single-process reference pipeline (NOT production serving). Needs a GPU; the base
model loads on start. Reads artifacts from experiments/common/artifacts/two_signal_calibration/.

Usage:
  python3 experiments/common/mechinterp/two_signal_cli.py                 # interactive REPL
  python3 experiments/common/mechinterp/two_signal_cli.py -q "Who wrote Dune?"   # one-shot
  python3 experiments/common/mechinterp/two_signal_cli.py --gate-threshold 0.6 --veto-threshold 0.35

Run inside the unsloth Docker GPU container (entrypoint python), same image as the
extractors. Interactive mode needs `docker run -it`; for one-shot use -q.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_DIR / "experiment/phase1/probe"
for _p in (Path(__file__).resolve().parent, PROBE_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from two_signal_runtime import TwoSignalReadout, MODEL_NAME  # noqa: E402


BANNER = """\
================================================================
 Two-signal trust readout  -  talk to the model
   gate  = answerability (abstains instead of guessing)
   trust = calibrated P(this answer is correct), with veto on
           confident confabulation
 Type a question. Commands: :q quit, :set gate <x>, :set veto <x>
================================================================"""


def _print_result(r) -> None:
    print(r.render())
    print()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=MODEL_NAME)
    ap.add_argument("--gate-artifact", type=Path, default=None)
    ap.add_argument("--dial-artifact", type=Path, default=None)
    ap.add_argument("--gate-threshold", type=float, default=0.5,
                    help="abstain when calibrated answerability < this")
    ap.add_argument("--veto-threshold", type=float, default=0.3,
                    help="flag LOW-TRUST when calibrated correctness < this")
    ap.add_argument("--max-new-tokens", type=int, default=48)
    ap.add_argument("-q", "--question", default=None,
                    help="one-shot: answer this and exit (no REPL)")
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args(argv)

    rt = TwoSignalReadout(
        model_name=a.model, gate_artifact=a.gate_artifact, dial_artifact=a.dial_artifact,
        gate_threshold=a.gate_threshold, veto_threshold=a.veto_threshold,
        max_new_tokens=a.max_new_tokens, device=a.device,
    )
    rt.load()
    print(f"[cli] gate L{rt.gate.layer} (AUROC {rt.gate.auroc}, ECE {rt.gate.ece_calibrated}) "
          f"| dial L{rt.dial.layer} (AUROC {rt.dial.auroc}, ECE {rt.dial.ece_calibrated})")
    print(f"[cli] gate_threshold={rt.gate_threshold} veto_threshold={rt.veto_threshold}")

    if a.question is not None:
        _print_result(rt.generate_with_trust(a.question))
        return 0

    print(BANNER)
    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in (":q", ":quit", ":exit"):
            break
        if line.startswith(":set "):
            try:
                _, knob, val = line.split()
                fv = float(val)
                if knob == "gate":
                    rt.gate_threshold = fv
                elif knob == "veto":
                    rt.veto_threshold = fv
                else:
                    print(f"unknown knob {knob!r} (gate|veto)"); continue
                print(f"[cli] gate_threshold={rt.gate_threshold} "
                      f"veto_threshold={rt.veto_threshold}")
            except ValueError:
                print("usage: :set gate 0.6  |  :set veto 0.35")
            continue
        _print_result(rt.generate_with_trust(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
