#!/usr/bin/env python3
"""Fresh per-seed random-direction draw for qwen3-4b-l34-placebo-seed-census.

Recipe pinned by AMENDMENT.md "New arms" / cell.yaml `arms[0].intervention`:
np.random.RandomState(seed).normal(size=hidden_dim), unit-normalized -- the
SAME recipe doubt-gated-caution-tighten/build_random_direction.py used for
the historical (seed 20260707) random_direction_L34.json draw (verified by
direct read of that script: `rng = np.random.RandomState(seed); v =
rng.normal(size=HIDDEN_DIM); v = v / np.linalg.norm(v)`). Reproduced here for
the K=15 fresh seeds 920001..920015 registered in gates.yaml
`seeds.random_census`.

This recipe uses np.random.RandomState (NOT np.random.default_rng, which
placebo-seed-distribution-census/direction_draw.py's own fresh_random_direction
uses for ITS family draws). The two census-style direction drawers in this
repo intentionally use different RNG classes because each reproduces a
different historical commitment -- this module's recipe matches THIS cell's
own historical draw (doubt-gated-caution-tighten's build_random_direction.py),
not the other census's.

CPU-only, no GPU, no model. Pure function of (seed, hidden_dim).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HIDDEN_DIM = 2560
LAYER_BLOCK = 33  # hs34


def fresh_random_direction(seed: int, hidden_dim: int = HIDDEN_DIM) -> np.ndarray:
    """Unit-norm direction in R^hidden_dim via np.random.RandomState(seed)
    .normal(...) -- byte-for-byte the same construction as
    doubt-gated-caution-tighten/build_random_direction.py's historical draw,
    applied to a fresh seed. Returns a float64 array of length hidden_dim."""
    rng = np.random.RandomState(seed)
    v = rng.normal(size=hidden_dim)
    return v / np.linalg.norm(v)


def direction_record(seed: int, hidden_dim: int = HIDDEN_DIM, layer: int = LAYER_BLOCK) -> dict:
    """mechinterp-direction/v1-shaped record (matches random_direction_L34.json's
    own schema) for provenance/audit. Not required by
    model_lib.setup_hook_from_vector (which takes a raw vector + sigma
    directly, per that function's own docstring: "used by the G3(i)
    random-direction placebo, which is not a committed direction JSON") but
    written to gitignored analysis/directions/ per seed at real-launch time so
    each of the 15 draws leaves an auditable artifact, mirroring
    build_random_direction.py's own output shape. sigma=1.0 (matched to the
    historical draw's convention) so strength == dose_target exactly, per
    pipeline.py's own random_direction arm: `strength_random_dir =
    dose_target`."""
    v = fresh_random_direction(seed, hidden_dim)
    return {
        "schema_version": "mechinterp-direction/v1",
        "layer": layer,
        "hidden_dim": hidden_dim,
        "normalized": True,
        "vector": [float(x) for x in v],
        "raw_norm": 1.0,
        "sigma": 1.0,
        "recipe": {
            "source": "direction_draw.py", "seed": seed,
            "method": "np.random.RandomState(seed).normal(size=hidden_dim), unit-normalized",
        },
        "provenance": {
            "role": "qg_random_census_arm",
            "amendment": "qwen3-4b-l34-placebo-seed-census",
            "note": (
                "One of K=15 fresh-seed random-direction census arms "
                "(gates.yaml seeds.random_census); NOT the historical "
                "seed-20260707 draw, which is reused frozen, not regenerated."
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    rec = direction_record(args.seed)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(rec, indent=2))
        print(f"wrote {args.out}")
    else:
        summary = {k: v for k, v in rec.items() if k != "vector"}
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
