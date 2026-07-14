#!/usr/bin/env python3
"""Build fixed-seed per-layer random direction placebos."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from layers import HS_INDICES, hs_to_block, layer_dir_name

HERE = Path(__file__).resolve().parent
COMMITTED = HERE / "analysis-committed"
HIDDEN_DIM = 2560
RANDOM_DIRECTION_SEED = 20260707


def main() -> int:
    COMMITTED.mkdir(parents=True, exist_ok=True)
    for hs_index in HS_INDICES:
        rng = np.random.RandomState(RANDOM_DIRECTION_SEED + hs_index)
        v = rng.normal(size=HIDDEN_DIM)
        v = v / np.linalg.norm(v)
        layer_name = layer_dir_name(hs_index)
        out_dir = COMMITTED / "layers" / layer_name
        out_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": "mechinterp-direction/v1",
            "layer": hs_to_block(hs_index),
            "hidden_dim": HIDDEN_DIM,
            "normalized": True,
            "vector": [float(x) for x in v],
            "raw_norm": 1.0,
            "intercept": 0.0,
            "mu": [0.0] * HIDDEN_DIM,
            "sigma": 1.0,
            "calibration": {},
            "recipe": {
                "source": "build_random_direction.py",
                "seed": RANDOM_DIRECTION_SEED + hs_index,
                "method": "np.random.RandomState(seed).normal(size=hidden_dim), unit-normalized",
            },
            "provenance": {
                "role": "g3_random_direction_placebo",
                "amendment": "j-space-midband-write-sweep-qwen3-4b",
                "hs_index": hs_index,
                "decoder_block_index": hs_to_block(hs_index),
                "note": "Not fit from data; fixed-seed random unit vector for the matched-norm placebo.",
            },
        }
        out_path = out_dir / f"random_direction_{layer_name}.json"
        out_path.write_text(json.dumps(record, indent=2))
        print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
