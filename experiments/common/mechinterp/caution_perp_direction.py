#!/usr/bin/env python3
"""Build the doubt-orthogonalized caution direction (caution_perp) at L35.

Refined-B1 isolates the caution-SPECIFIC gate from the bundled doubt axis. The
raw caution direction theta (known_refused - known_correct_answered) is ~83%
aligned with the knowledge/doubt axis, so ablating it also ablates most of doubt.
caution_perp removes the rank-1 doubt direction from caution:

    caution      = mean(known_refused) - mean(known_correct_answered)
    doubt (unit) = unit(mean(known_correct_answered) - mean(unknown_refused))
    caution_perp = caution - (caution . doubt) * doubt

Orientation is preserved (positive projection = more refusal), so shift arms keep
the same sign convention as the raw-theta direction. Writes a direction JSON in
the same schema the residual-intervention runner consumes (layer, theta, sigma).

Usage:
  python experiments/common/mechinterp/caution_perp_direction.py [--out <path>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
sys.path.insert(0, str(PROBE_DIR))
from phase3_latent_knowledge_probe import load_layers  # noqa: E402

REPO = ROOT
EXTRACT = (PROBE_DIR / "qwen3-4b-clean-sft-grpo-v2-seed1-selfaware"
           / "hidden_states_selfaware_clean_sft_grpo_v2_full" / "extraction__55254a04aa1f")
OVERLAY = (PROBE_DIR / "analysis/current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl")
RAW = (PROBE_DIR / "analysis/current_clean_grpo_v2_caution_residual_direction/caution_direction_L35.json")
L = 35


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def cell_keys(overlay: list[dict], cell: str) -> list[str]:
    return [r["probe_pool_row_key"] for r in overlay if r["behavior_cell"] == cell]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path,
                    default=RAW.with_name("caution_perp_direction_L35.json"))
    args = ap.parse_args()

    overlay = [json.loads(l) for l in OVERLAY.open() if l.strip()]
    kr = cell_keys(overlay, "known_refused")
    ka = cell_keys(overlay, "known_correct_answered")
    ur = cell_keys(overlay, "unknown_refused")
    print(f"rows: known_refused={len(kr)} known_correct_answered={len(ka)} unknown_refused={len(ur)}",
          file=sys.stderr)

    Xkr = load_layers(EXTRACT, kr, [L])[L]
    Xka = load_layers(EXTRACT, ka, [L])[L]
    Xur = load_layers(EXTRACT, ur, [L])[L]

    caution = Xkr.mean(0) - Xka.mean(0)              # refuse(+) - answer(-)
    doubt_u = unit(Xka.mean(0) - Xur.mean(0))        # known(+) - unknown(-)
    align = float(unit(caution) @ doubt_u)
    caution_perp = caution - (caution @ doubt_u) * doubt_u
    perp_frac = float(np.linalg.norm(caution_perp) / np.linalg.norm(caution))
    theta_u = unit(caution_perp)

    # projection stats onto the unit caution_perp for the two intervened cells
    proj_kr = Xkr @ theta_u
    proj_ka = Xka @ theta_u
    sigma = float(np.concatenate([proj_kr, proj_ka]).std())

    raw = json.loads(RAW.read_text()) if RAW.exists() else {}
    out = {
        "schema_version": "phase3-residual-caution-direction/v1",
        "layer": L,
        "block": L - 1,
        "source": raw.get("source", "h_lora"),
        "hidden_dim": int(theta_u.shape[0]),
        "theta": [float(v) for v in caution_perp],   # runner unit-normalizes
        "sigma": sigma,
        "mu_pos": float(proj_kr.mean()),
        "mu_neg": float(proj_ka.mean()),
        "n_pos": int(len(kr)),
        "n_neg": int(len(ka)),
        "raw_cos_caution_doubt": align,
        "perp_fraction_of_caution": perp_frac,
        "pos_cell": "known_refused",
        "neg_cell": "known_correct_answered",
        "extraction_dir": str(EXTRACT.relative_to(REPO)),
        "behavior_rows": str(OVERLAY.relative_to(REPO)),
        "notice": ("doubt-orthogonalized caution (caution_perp); rank-1 doubt axis "
                   "removed; isolates the caution-specific gate for refined B1"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"raw cos(caution,doubt)={align:.3f}  perp_fraction={perp_frac:.3f}  sigma={sigma:.3f}")
    print(f"mu_pos(kr)={out['mu_pos']:.2f}  mu_neg(ka)={out['mu_neg']:.2f}  gap={out['mu_pos']-out['mu_neg']:.2f}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
