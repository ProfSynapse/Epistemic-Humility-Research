#!/usr/bin/env python3
"""Amendment AC — build the per-row doubt gain map for the coupled arm (CPU).

SPEC: experiments/doubt-regulated-caution/AMENDMENT.md §2/§6.

Sensor side of the doubt->caution loop. From the frozen L35 extraction +
behavior overlay: fit the doubt axis u_d = unit(mean(known_correct_answered)
- mean(unknown_refused)) (same anchors as build_caution_perp_direction, so
u_d is by construction orthogonal to the committed caution_perp actuator),
project every eval row (known_refused, known_correct_answered,
unknown_refused), standardize over the eval population, and emit

    g_i = -alpha * z_i, clipped to [-clip, +clip]     (alpha=1, clip=2)

plus a seed-fixed permuted copy of the SAME gains (the magnitude-matched
placebo: identical distribution, information removed). The runner resolves a
couple-arm's per-row alpha from this file; a row missing from the map is a
hard error there, so the map must cover every eval row.

Pure read: never touches the extraction or overlay. Paths are explicit args
because the frozen data lives untracked in the main working tree.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LATENT_CONTROLS_DIR = ROOT / "experiments/selfaware-latent-knowledge-controls"
if str(LATENT_CONTROLS_DIR) not in sys.path:
    sys.path.insert(0, str(LATENT_CONTROLS_DIR))
from latent_knowledge_probe import load_layers  # noqa: E402

L = 35
EVAL_CELLS = ("known_refused", "known_correct_answered", "unknown_refused")
DOUBT_POS_CELL = "known_correct_answered"
DOUBT_NEG_CELL = "unknown_refused"
PERMUTATION_SEED = 20260702


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n == 0.0:
        raise ValueError("zero-norm direction")
    return v / n


def compute_gains(z: np.ndarray, *, alpha: float, clip: float) -> np.ndarray:
    """g = -alpha*z clipped to [-clip, +clip]. Known-side rows (z>0) get a
    negative gate setpoint (answer); unknown-side rows (z<0) a positive one
    (refuse)."""
    return np.clip(-alpha * z, -clip, clip)


def build_gain_map(h_by_cell: dict[str, np.ndarray],
                   keys_by_cell: dict[str, list[str]], *,
                   alpha: float, clip: float,
                   permutation_seed: int = PERMUTATION_SEED) -> dict:
    """Pure-numpy core (unit-tested offline). h arrays are [n, hidden]."""
    for cell in EVAL_CELLS:
        if cell not in h_by_cell or cell not in keys_by_cell:
            raise ValueError(f"missing eval cell {cell!r}")
        if len(h_by_cell[cell]) != len(keys_by_cell[cell]):
            raise ValueError(f"cell {cell!r}: activations/keys misaligned")

    u_d = unit(h_by_cell[DOUBT_POS_CELL].mean(0) - h_by_cell[DOUBT_NEG_CELL].mean(0))

    keys: list[str] = []
    cells: list[str] = []
    projs: list[np.ndarray] = []
    for cell in EVAL_CELLS:
        keys.extend(keys_by_cell[cell])
        cells.extend([cell] * len(keys_by_cell[cell]))
        projs.append(h_by_cell[cell] @ u_d)
    d = np.concatenate(projs)
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate row keys across eval cells")

    mu_d, sigma_d = float(d.mean()), float(d.std())
    if sigma_d == 0.0:
        raise ValueError("degenerate doubt projections (sigma_d == 0)")
    z = (d - mu_d) / sigma_d
    g = compute_gains(z, alpha=alpha, clip=clip)

    rng = np.random.default_rng(permutation_seed)
    perm = rng.permutation(len(g))

    per_cell_mean_z = {c: float(np.mean([zv for zv, cc in zip(z, cells) if cc == c]))
                       for c in EVAL_CELLS}
    return {
        "schema_version": "doubt-gain-map/v1",
        "layer": L,
        "alpha": alpha,
        "clip": clip,
        "doubt_pos_cell": DOUBT_POS_CELL,
        "doubt_neg_cell": DOUBT_NEG_CELL,
        "eval_cells": list(EVAL_CELLS),
        "mu_d": mu_d,
        "sigma_d": sigma_d,
        "per_cell_mean_z": per_cell_mean_z,
        "n_rows": len(keys),
        "permutation_seed": permutation_seed,
        "gains": {k: {"cell": c, "z": float(zv), "gain": float(gv)}
                  for k, c, zv, gv in zip(keys, cells, z, g)},
        "gains_permuted": {k: {"cell": c, "z": float(z[j]), "gain": float(g[j])}
                           for k, c, j in zip(keys, cells, perm)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extraction-dir", required=True, type=Path)
    ap.add_argument("--overlay", required=True, type=Path,
                    help="behavior rows.jsonl with probe_pool_row_key + behavior_cell")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--alpha", type=float, default=1.0)
    ap.add_argument("--clip", type=float, default=2.0)
    args = ap.parse_args(argv)

    overlay = [json.loads(l) for l in args.overlay.open() if l.strip()]
    keys_by_cell = {c: [r["probe_pool_row_key"] for r in overlay
                        if r["behavior_cell"] == c] for c in EVAL_CELLS}
    for c in EVAL_CELLS:
        print(f"rows: {c}={len(keys_by_cell[c])}", file=sys.stderr)
    h_by_cell = {c: load_layers(args.extraction_dir, keys_by_cell[c], [L])[L]
                 for c in EVAL_CELLS}

    gm = build_gain_map(h_by_cell, keys_by_cell, alpha=args.alpha, clip=args.clip)
    gm["extraction_dir"] = str(args.extraction_dir)
    gm["overlay"] = str(args.overlay)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(gm, indent=2) + "\n", encoding="utf-8")
    pc = gm["per_cell_mean_z"]
    print(f"mu_d={gm['mu_d']:.2f} sigma_d={gm['sigma_d']:.2f} "
          f"mean_z: kr={pc['known_refused']:.2f} ka={pc['known_correct_answered']:.2f} "
          f"ur={pc['unknown_refused']:.2f}")
    print(f"wrote {args.out} ({gm['n_rows']} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
