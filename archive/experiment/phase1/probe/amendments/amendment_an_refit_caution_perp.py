#!/usr/bin/env python3
"""Refit the doubt-orthogonalized caution direction (caution_perp) on the
AI-TRUE checkpoint's pre-generation extraction, for Amendment AN.

Directions drift across checkpoints (Amendment T), so the AC actuator
(caution_perp on the caution coordinate) must be refit on the SAME checkpoint
the regulator writes into. AC/AL's committed caution_perp was fit on the
clean-SFT->GRPO-v2 extraction (extraction__55254a04aa1f). AN writes on the
AI-TRUE checkpoint (Amendment AI GRPO true seed1), whose 1,662-row A0
pre-generation activations live at true_a0/extract/data as per-row safetensors
keyed L0..L36 at the prompt_len-1 anchor.

Construction mirrors build_caution_perp_direction.py exactly:

    caution      = mean(known_refused) - mean(known_correct_answered)
    doubt (unit) = unit(mean(known_correct_answered) - mean(unknown_refused))
    caution_perp = caution - (caution . doubt) * doubt

Behavior cells are derived by joining the extraction rows (gold known/unknown)
with the AL baseline grades (answered/refused/correct from the frozen A0
surface in per_row_exhaust.jsonl):

    known_correct_answered : gold known  AND baseline answered & correct
    known_refused          : gold known  AND baseline refused
    unknown_refused        : gold unknown AND baseline refused

Emits a direction JSON in the same schema the residual-intervention runner
consumes, plus the cosine to the committed grpo-v2 caution_perp so the drift
is recorded (never actuate the grpo-v2 direction on this checkpoint blind).

CPU-only, deterministic (mass-mean; no fit randomness). No model load.

Usage:
  python archive/experiment/phase1/probe/amendments/amendment_an_refit_caution_perp.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from path_compat import phase1_probe_dir, repo_root

PROBE_DIR = phase1_probe_dir()
sys.path.insert(0, str(PROBE_DIR))
from phase3_latent_knowledge_probe import load_layers  # noqa: E402

REPO = repo_root()
L = 35

# AI-TRUE pre-generation extraction (all layers L0..L36 per row, anchor prompt_len-1)
TRUE_EXTRACT = (PROBE_DIR / "analysis/amendment_al_prep/true_a0/extract/data")
TRUE_ROWS = TRUE_EXTRACT / "rows.jsonl"
# AL frozen A0 baseline grades (untracked prep exhaust)
AL_EXHAUST = (PROBE_DIR / "analysis/amendment_al_prep/amendment_al_run/per_row_exhaust.jsonl")
# committed grpo-v2 caution_perp, for the drift cosine
GRPO_V2_PERP = (PROBE_DIR
                / "analysis/current_clean_grpo_v2_caution_residual_direction"
                / "caution_perp_direction_L35.json")
DEFAULT_OUT = (PROBE_DIR
               / "analysis/amendment_an_prep/caution_perp_direction_L35_ai_true.json")


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def build_cells(true_rows: Path, al_exhaust: Path) -> dict[str, list[str]]:
    """Join extraction gold labels with AL baseline grades -> behavior cells."""
    ex = {json.loads(l)["row_key"]: json.loads(l)
          for l in true_rows.open() if l.strip()}
    cells: dict[str, list[str]] = {
        "known_correct_answered": [],
        "known_refused": [],
        "unknown_refused": [],
    }
    for line in al_exhaust.open():
        if not line.strip():
            continue
        r = json.loads(line)
        rk = r["row_key"]
        if rk not in ex:
            raise RuntimeError(f"exhaust row {rk} absent from AI-TRUE extraction rows.jsonl")
        b = r["baseline"]
        known = r["gold_class"] == "answerable"
        if known and b["answered"] and b["correct"]:
            cells["known_correct_answered"].append(rk)
        elif known and b["refused"]:
            cells["known_refused"].append(rk)
        elif (not known) and b["refused"]:
            cells["unknown_refused"].append(rk)
    return cells


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extraction-dir", type=Path, default=TRUE_EXTRACT)
    ap.add_argument("--true-rows", type=Path, default=None,
                    help="rows.jsonl with gold labels; default <extraction-dir>/rows.jsonl")
    ap.add_argument("--al-exhaust", type=Path, default=AL_EXHAUST,
                    help="AL per_row_exhaust.jsonl carrying frozen A0 baseline grades")
    ap.add_argument("--grpo-v2-perp", type=Path, default=GRPO_V2_PERP,
                    help="committed grpo-v2 caution_perp JSON, for the drift cosine")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    true_rows = args.true_rows or (args.extraction_dir / "rows.jsonl")
    cells = build_cells(true_rows, args.al_exhaust)
    kr, ka, ur = (cells["known_refused"],
                  cells["known_correct_answered"],
                  cells["unknown_refused"])
    print(f"rows: known_refused={len(kr)} known_correct_answered={len(ka)} "
          f"unknown_refused={len(ur)}", file=sys.stderr)

    Xkr = load_layers(args.extraction_dir, kr, [L], source="pre")[L]
    Xka = load_layers(args.extraction_dir, ka, [L], source="pre")[L]
    Xur = load_layers(args.extraction_dir, ur, [L], source="pre")[L]

    caution = Xkr.mean(0) - Xka.mean(0)              # refuse(+) - answer(-)
    doubt_u = unit(Xka.mean(0) - Xur.mean(0))        # known(+) - unknown(-)
    align = float(unit(caution) @ doubt_u)
    caution_perp = caution - (caution @ doubt_u) * doubt_u
    perp_frac = float(np.linalg.norm(caution_perp) / np.linalg.norm(caution))
    theta_u = unit(caution_perp)

    proj_kr = Xkr @ theta_u
    proj_ka = Xka @ theta_u
    sigma = float(np.concatenate([proj_kr, proj_ka]).std())

    # drift cosine to the committed grpo-v2 caution_perp
    cos_to_grpo_v2 = None
    if args.grpo_v2_perp.is_file():
        g = json.loads(args.grpo_v2_perp.read_text())
        g_theta = unit(np.asarray(g["theta"], dtype=np.float64))
        cos_to_grpo_v2 = float(theta_u @ g_theta)

    out = {
        "schema_version": "phase3-residual-caution-direction/v1",
        "layer": L,
        "block": L - 1,
        "source": "pre",
        "hidden_dim": int(theta_u.shape[0]),
        "theta": [float(v) for v in caution_perp],   # runner unit-normalizes
        "sigma": sigma,
        "mu_pos": float(proj_kr.mean()),
        "mu_neg": float(proj_ka.mean()),
        "n_pos": int(len(kr)),
        "n_neg": int(len(ka)),
        "raw_cos_caution_doubt": align,
        "perp_fraction_of_caution": perp_frac,
        "cos_to_grpo_v2_caution_perp": cos_to_grpo_v2,
        "pos_cell": "known_refused",
        "neg_cell": "known_correct_answered",
        "checkpoint": "ai_true_grpo_seed1",
        "extraction_dir": str(args.extraction_dir),
        "behavior_rows": str(args.al_exhaust),
        "notice": ("doubt-orthogonalized caution (caution_perp) REFIT on the "
                   "AI-TRUE checkpoint pre-generation extraction for Amendment "
                   "AN; cells joined from AL frozen A0 grades; refit per "
                   "checkpoint (Amendment T drift)."),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"raw cos(caution,doubt)={align:.3f}  perp_fraction={perp_frac:.3f}  "
          f"sigma={sigma:.3f}")
    print(f"mu_pos(kr)={out['mu_pos']:.2f}  mu_neg(ka)={out['mu_neg']:.2f}  "
          f"gap={out['mu_pos']-out['mu_neg']:.2f}")
    if cos_to_grpo_v2 is not None:
        print(f"cos(AI-TRUE caution_perp, grpo-v2 caution_perp)={cos_to_grpo_v2:.4f}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
