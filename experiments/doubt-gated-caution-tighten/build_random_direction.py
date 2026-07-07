#!/usr/bin/env python3
"""Doubt-gated caution snap -- G3(i) placebo direction (CPU-only, no GPU).

A fixed-seed random unit vector in R^2560 at L34, used by pipeline.py's
random-direction placebo arm: dose the SAME gated rows with a write along
THIS direction (matched realized-projection magnitude, sigma=1.0 so
strength==setpoint exactly) instead of c_hat, to test whether the tighten/
false-refusal effect is specific to the caution direction or just "any
large-enough perturbation at L34 induces confusion" (AMENDMENT.md G3(i)).

Output: analysis-committed/random_direction_L34.json (mechinterp-direction/v1
schema, sigma=1.0 so pipeline.py's dose/sigma == dose exactly -- no
population-derived scale, unlike c_hat's sigma_c).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
COMMITTED = HERE / "analysis-committed"

LAYER_BLOCK = 33
HIDDEN_DIM = 2560
RANDOM_DIRECTION_SEED = 20260707


def main() -> int:
    rng = np.random.RandomState(RANDOM_DIRECTION_SEED)
    v = rng.normal(size=HIDDEN_DIM)
    v = v / np.linalg.norm(v)

    record = {
        "schema_version": "mechinterp-direction/v1",
        "layer": LAYER_BLOCK,
        "hidden_dim": HIDDEN_DIM,
        "normalized": True,
        "vector": [float(x) for x in v],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * HIDDEN_DIM,
        "sigma": 1.0,
        "calibration": {},
        "recipe": {"source": "build_random_direction.py", "seed": RANDOM_DIRECTION_SEED,
                   "method": "np.random.RandomState(seed).normal(size=hidden_dim), unit-normalized"},
        "provenance": {"role": "g3_random_direction_placebo",
                       "amendment": "doubt-gated-caution-tighten",
                       "note": "Not fit from data; a fixed-seed random unit vector for the "
                               "matched-norm random-direction placebo (AMENDMENT.md G3(i))."},
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    out_path = COMMITTED / "random_direction_L34.json"
    out_path.write_text(json.dumps(record, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
