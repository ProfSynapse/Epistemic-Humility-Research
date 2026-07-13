#!/usr/bin/env python3
"""Fit the raw mass-mean CAUTION direction for the residual read-trajectory (GPU-free).

Reads the SelfAware (or any) extraction + behavior rows already on disk and fits a
raw-space unit direction at one layer that separates ``known_refused`` (over-refusals)
from ``known_correct_answered``. This is the mass-mean cousin of the A2 caution axis
(``latent_knowledge_controls.a2_within_known``); unlike A2's whitened logistic
normal it applies frame-consistently to generation-position residuals, which is what
``mechinterp_residual_read_trajectory`` projects onto during decoding.

Writes a small JSON the GPU runner loads (analogous to ``steering_directions.json``):
``{schema_version, layer, block, source, hidden_dim, theta[hidden], sigma, mu_pos,
mu_neg, n_pos, n_neg, prompt_token_auroc, ...}``. ``prompt_token_auroc`` is an
in-sample construction sanity check, not a held-out claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

MECHINTERP_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
LATENT_CONTROLS_DIR = ROOT / "experiments/selfaware-latent-knowledge-controls"
for path in (MECHINTERP_DIR, LATENT_CONTROLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import latent_knowledge_probe as lkp  # noqa: E402
import residual_read_trajectory as rrt  # noqa: E402

SCHEMA_VERSION = "mechinterp-residual-caution-direction/v1"


def load_known_split(behavior_rows: Path) -> tuple[list[str], list[str]]:
    """Return (refused_keys, answered_keys) for KNOWN rows from behavior rows."""
    refused: list[str] = []
    answered: list[str] = []
    for line in behavior_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rk = r.get("probe_pool_row_key")
        if rk is None or r.get("label") != "known":
            continue
        cell = r.get("behavior_cell")
        if cell == rrt.KNOWN_REFUSED:
            refused.append(rk)
        elif cell == rrt.KNOWN_ANSWERED:
            answered.append(rk)
    if not refused or not answered:
        raise rrt.ResidualReadTrajectoryError(
            f"degenerate known split: refused={len(refused)} answered={len(answered)}")
    return refused, answered


def fit(extraction_dir: Path, behavior_rows: Path, *, layer: int,
        source: str = "h_lora") -> dict[str, Any]:
    refused, answered = load_known_split(behavior_rows)
    keys = refused + answered
    mats = lkp.load_layers(extraction_dir, keys, [layer], source=source)
    X = mats[layer]
    x_pos = X[: len(refused)]
    x_neg = X[len(refused):]
    theta = rrt.mass_mean_direction(x_pos, x_neg)
    sigma = rrt.projection_sigma(X, theta)
    auroc = rrt.projection_auroc(x_pos, x_neg, theta)
    return {
        "schema_version": SCHEMA_VERSION,
        "layer": int(layer),
        "block": int(layer - 1),
        "source": source,
        "hidden_dim": int(theta.shape[0]),
        "theta": [float(v) for v in theta],
        "sigma": float(sigma),
        "mu_pos": float((x_pos @ theta).mean()),
        "mu_neg": float((x_neg @ theta).mean()),
        "n_pos": int(len(refused)),
        "n_neg": int(len(answered)),
        "prompt_token_auroc": round(auroc, 4),
        "pos_cell": rrt.KNOWN_REFUSED,
        "neg_cell": rrt.KNOWN_ANSWERED,
        "extraction_dir": str(extraction_dir),
        "behavior_rows": str(behavior_rows),
        "notice": "raw mass-mean caution direction; prompt_token_auroc is in-sample (construction sanity)",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extraction-dir", required=True, type=Path)
    p.add_argument("--behavior-rows", required=True, type=Path)
    p.add_argument("--layer", type=int, default=35, help="hidden_states layer (default 35)")
    p.add_argument("--source", default="h_lora", choices=["h_lora", "h_base", "delta"])
    p.add_argument("--out", required=True, type=Path)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    direction = fit(args.extraction_dir, args.behavior_rows, layer=args.layer, source=args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(direction, indent=2) + "\n", encoding="utf-8")
    print(
        f"caution direction L{direction['layer']} (block {direction['block']}) source={direction['source']}: "
        f"n_pos={direction['n_pos']} n_neg={direction['n_neg']} sigma={direction['sigma']:.4f} "
        f"prompt_token_auroc={direction['prompt_token_auroc']:.4f} -> {args.out}",
        file=sys.stderr,
    )
    print(json.dumps({k: v for k, v in direction.items() if k != "theta"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
