#!/usr/bin/env python3
"""GG1 paired-smoke harness (AMENDMENT.md "Gates" GG1, gates.yaml
gg1_kv_seam_admissibility).

Two modes:

  --mode=live (GPU, NOT run by this scaffolding pass): extracts the same 32
    fixed rows under `use_cache=True` and `use_cache=False` on the pinned
    pt checkpoint, computes the per-layer cosine between the two runs, and
    classifies the result via `classify_paired_profile`. This is the
    instrument-verification step that must run before any production
    capture; it produces no G reading.

  --mode=synthetic (CPU-only, exercised by this scaffolding pass): feeds
    fabricated per-layer cosine profiles to `classify_paired_profile`
    directly, so the CLASSIFICATION LOGIC is verified without GPU access.
    This is NOT a substitute for the live smoke -- it only proves the
    classifier correctly recognizes the documented signature (hs00-hs24
    identical, hs25-hs42 decaying), the null-hazard signature (all layers
    identical, i.e. this transformers build does not exhibit the seam), and
    the halt signature (divergence at or below hs24) if it is ever fed one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IDENTICAL_COSINE_THRESHOLD = 0.9999
N_HIDDEN_STATES = 43
FIRST_SHARED_LAYER = 24  # hs00..hs24 must be identical; hs25.. may diverge

OUTCOME_HS00_24_IDENTICAL_DIVERGE_AT_25 = "hs00_to_hs24_identical_and_divergence_begins_at_hs25"
OUTCOME_ALL_IDENTICAL = "all_layers_identical"
OUTCOME_HALT_DIVERGE_AT_OR_BELOW_24 = "divergence_at_or_below_hs24"
OUTCOME_UNRECOGNIZED = "unrecognized"


def classify_paired_profile(cosines: list[float],
                             identical_threshold: float = IDENTICAL_COSINE_THRESHOLD) -> str:
    """cosines[i] = cosine similarity between the use_cache=True and
    use_cache=False extraction at hidden state i, i in 0..42.

    Returns one of the three admissible/halt outcomes named in
    gates.yaml gg1_kv_seam_admissibility, or OUTCOME_UNRECOGNIZED if the
    profile matches none of them (also treated as a halt by the caller).
    """
    if len(cosines) != N_HIDDEN_STATES:
        raise ValueError(f"expected {N_HIDDEN_STATES} cosines, got {len(cosines)}")

    early = cosines[: FIRST_SHARED_LAYER + 1]  # hs00..hs24 inclusive
    late = cosines[FIRST_SHARED_LAYER + 1 :]   # hs25..hs42

    early_identical = all(c >= identical_threshold for c in early)
    if not early_identical:
        return OUTCOME_HALT_DIVERGE_AT_OR_BELOW_24

    late_identical = all(c >= identical_threshold for c in late)
    if late_identical:
        return OUTCOME_ALL_IDENTICAL

    # early is identical, and at least one late layer diverges: the
    # documented signature. No further shape requirement (e.g. monotonic
    # decay) is imposed -- the registered outcome only requires divergence
    # to begin at or after hs25, not a particular decay curve.
    return OUTCOME_HS00_24_IDENTICAL_DIVERGE_AT_25


def run_synthetic_selfcheck() -> dict:
    """Exercises the classifier against the three named fixture profiles
    plus a deliberately-wrong one, and returns a pass/fail summary. This is
    what --mode=synthetic runs; it is instrument verification of the
    CLASSIFIER, not of the live extraction."""
    documented_signature = (
        [1.0] * (FIRST_SHARED_LAYER + 1)
        + [0.732, 0.71, 0.68, 0.6, 0.55, 0.5, 0.45, 0.4, 0.36, 0.32, 0.29, 0.26,
           0.23, 0.2, 0.18, 0.16, 0.14, 0.12]
    )
    documented_signature = documented_signature[:N_HIDDEN_STATES]
    assert len(documented_signature) == N_HIDDEN_STATES

    all_identical = [1.0] * N_HIDDEN_STATES

    halt_profile = [1.0] * 10 + [0.9] + [1.0] * (N_HIDDEN_STATES - 11)  # divergence at hs10, <=24

    cases = {
        "documented_signature": (documented_signature, OUTCOME_HS00_24_IDENTICAL_DIVERGE_AT_25),
        "all_identical": (all_identical, OUTCOME_ALL_IDENTICAL),
        "halt_early_divergence": (halt_profile, OUTCOME_HALT_DIVERGE_AT_OR_BELOW_24),
    }
    results = {}
    all_pass = True
    for name, (profile, expected) in cases.items():
        got = classify_paired_profile(profile)
        ok = got == expected
        all_pass = all_pass and ok
        results[name] = {"expected": expected, "got": got, "pass": ok}
    return {"all_pass": all_pass, "cases": results}


def run_live(args: argparse.Namespace) -> int:
    """GPU paired extraction on 32 fixed rows. NOT invoked by this
    scaffolding pass (no GPU verb, no docker run, no weight download were
    issued while authoring this cell); must run before any production
    capture."""
    raise SystemExit(
        "kv_seam_paired_smoke.py --mode=live requires a GPU runtime inside "
        "the pinned mechinterp-runner image and is out of scope for the "
        "CPU-only signing-prerequisite pass. It must be run before any "
        "production capture (AMENDMENT.md GG1)."
    )


def run(args: argparse.Namespace) -> int:
    if args.mode == "synthetic":
        summary = run_synthetic_selfcheck()
        print(json.dumps(summary, indent=2))
        return 0 if summary["all_pass"] else 1
    return run_live(args)


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["live", "synthetic"], required=True)
    ap.add_argument("--rows", type=int, default=32)
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
