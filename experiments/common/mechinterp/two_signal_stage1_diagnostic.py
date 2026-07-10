#!/usr/bin/env python3
"""Two-signal mechanism — Stage 1 CPU diagnostic (lab-notebook, NOT an amendment).

This is a FEASIBILITY / GO-NO-GO diagnostic, not a gated evidence cell: it composes
two extractions that ALREADY exist on the deployed clean-SFT -> GRPO-v2 checkpoint
to decide whether the unified mixed-stream GPU run (Stage 2, which WOULD be a
signed Tier-2 amendment) is worth running. Per the experiment-runner
amendment-vs-lab-notebook rule, a diagnostic that informs a go/no-go is lab
notebook, not a new amendment.

The deployed two-signal mechanism (target):
  gate  : read the ANSWERABILITY axis at the prompt anchor; abstain if < tau_gate.
  dial  : on answered items, read the CORRECTNESS axis post-generation; surface it
          (calibrated) as a trust score.

What Stage 1 establishes on the SAME deployed checkpoint, on CPU, from existing
tensors:
  1. GATE component: answerability AUROC surface (known vs unknown), best layer,
     calibrated ECE, risk-coverage for abstaining on unknowns.
     Source: SelfAware deployed extraction, h_lora @ final_prompt_token (adapter
     active = deployed model).
  2. DIAL component: correctness AUROC (post-gen), best layer, calibrated ECE
     (the concrete fix for the S/T G3 miss), selective accuracy.
     Source: Amendment T stage2 post-gen extraction.
  3. Calibration: raw vs Platt vs isotonic ECE for each readout (cross-fit, so the
     calibrator is never measured on its own fit data).

HONEST LIMITATION (why Stage 2 exists): the gate and dial extractions are on
DIFFERENT question pools (SelfAware known/unknown vs PopQA/TriviaQA correct/wrong),
so Stage 1 CANNOT read both signals on the SAME item. The true per-item joint
read (one mixed answerable+unanswerable stream through one pipeline) is Stage 2.
Stage 1 reports each component honestly and a go/no-go; it does NOT claim an
integrated end-to-end frontier.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

REPO_DIR = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_DIR / "experiment/phase1/probe"
RESULT_DIR = REPO_DIR / "experiments" / "unified-two-signal-dial-veto" / "artifacts"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

# Reuse the Amendment S scorer's vetted primitives so gate and dial are read by
# the identical estimator family and the identical ECE definition.
from amendment_s_correctness_probe_score import (  # noqa: E402
    load_position_layers,
    oof_probe,
    ece,
    selective_prediction_curve,
)


def load_gate_h_lora(ext_dir: Path):
    """Return (layer -> X[n,d]), y[n] for the deployed SelfAware gate extraction.

    y = 1 for 'known' (answerable), 0 for 'unknown' (unanswerable). Reads the
    adapter-active hidden state (h_lora) at the final prompt token = the gate's
    deployment read position.
    """
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8")
            if l.strip()]
    by_layer: dict[int, list[np.ndarray]] = {}
    y: list[int] = []
    for r in rows:
        label = r.get("label")
        if label not in ("known", "unknown"):
            continue
        safe = str(r["row_key"]).replace("::", "__")
        shard = ext_dir / f"{safe}__h_lora.safetensors"
        if not shard.exists():
            continue
        t = load_file(str(shard))
        for name, vec in t.items():
            layer = int(name[1:])
            by_layer.setdefault(layer, []).append(np.asarray(vec, dtype=np.float64))
        y.append(1 if label == "known" else 0)
    X = {layer: np.vstack(vs) for layer, vs in by_layer.items()}
    return X, np.asarray(y, dtype=int)


def auroc_surface(X: dict, y: np.ndarray, seed: int):
    """OOF AUROC per layer; return (surface dict, best_layer, oof scores at best)."""
    surface, oof = {}, {}
    for layer in sorted(X):
        p = oof_probe(X[layer], y, seed)
        surface[layer] = float(roc_auc_score(y, p))
        oof[layer] = p
    best = max(surface, key=surface.get)
    return surface, best, oof[best]


def crossfit_calibrate(scores: np.ndarray, y: np.ndarray, seed: int):
    """Cross-fit Platt + isotonic calibration of a 1-D score; ECE never measured
    on its own fit data. Returns {raw, platt, isotonic} ECE plus the calibrated
    OOF probabilities for each method."""
    n = len(y)
    platt = np.full(n, np.nan)
    iso = np.full(n, np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in skf.split(scores.reshape(-1, 1), y):
        lr = LogisticRegression(C=1e6, max_iter=2000)  # ~unregularized Platt
        lr.fit(scores[tr].reshape(-1, 1), y[tr])
        platt[te] = lr.predict_proba(scores[te].reshape(-1, 1))[:, 1]
        ir = IsotonicRegression(out_of_bounds="clip")
        ir.fit(scores[tr], y[tr])
        iso[te] = ir.predict(scores[te])
    return {
        "raw": round(ece(scores, y), 4),
        "platt": round(ece(platt, y), 4),
        "isotonic": round(ece(iso, y), 4),
    }, platt, iso


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate-dir", type=Path, required=True,
                    help="deployed SelfAware extraction dir (h_lora @ final_prompt_token)")
    ap.add_argument("--dial-dir", type=Path, required=True,
                    help="Amendment T stage2 extraction dir (post-gen correctness)")
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    # ---- GATE component (answerability on the deployed checkpoint) ----
    Xg, yg = load_gate_h_lora(a.gate_dir.resolve())
    g_surface, g_best, g_oof = auroc_surface(Xg, yg, a.seed)
    g_cal, _, _ = crossfit_calibrate(g_oof, yg, a.seed)
    # risk-coverage: rank by P(answerable) DESC; "accuracy" = fraction truly
    # answerable among the top-coverage answered set (cost of answering unknowns).
    g_riskcov = selective_prediction_curve(g_oof, yg)

    # ---- DIAL component (correctness on the deployed checkpoint) ----
    Xd, yd, _ = load_position_layers(a.dial_dir.resolve(), "post")
    d_surface, d_best, d_oof = auroc_surface(Xd, yd, a.seed)
    d_cal, _, _ = crossfit_calibrate(d_oof, yd, a.seed)
    d_riskcov = selective_prediction_curve(d_oof, yd)

    gate_auroc = g_surface[g_best]
    dial_auroc = d_surface[d_best]
    # Go/no-go heuristic (NOT a locked gate; this is a diagnostic): both signals
    # usefully strong AND both calibratable below the S/T raw ECE (~0.15-0.17).
    go = (gate_auroc >= 0.90 and dial_auroc >= 0.70
          and min(d_cal["platt"], d_cal["isotonic"]) < 0.10)

    result = {
        "analysis": "two_signal_mechanism_stage1_cpu_diagnostic",
        "instrument": "lab-notebook diagnostic (NOT an amendment); go/no-go for Stage 2",
        "checkpoint": "qwen3-4b clean-sft-merged-16bit + grpo-v2-lora (deployed)",
        "gate": {
            "source": str(a.gate_dir),
            "read": "h_lora @ final_prompt_token (adapter active)",
            "label": "known(1) vs unknown(0) = answerable vs unanswerable",
            "n": int(len(yg)),
            "n_answerable": int((yg == 1).sum()),
            "n_unanswerable": int((yg == 0).sum()),
            "best_layer": g_best,
            "answerability_auroc": round(gate_auroc, 4),
            "auroc_surface": {str(k): round(v, 4) for k, v in sorted(g_surface.items())},
            "ece_calibration": g_cal,
            "risk_coverage": g_riskcov,
        },
        "dial": {
            "source": str(a.dial_dir),
            "read": "post-gen content token",
            "label": "correct(1) vs wrong(0)",
            "n": int(len(yd)),
            "n_correct": int((yd == 1).sum()),
            "n_wrong": int((yd == 0).sum()),
            "best_layer": d_best,
            "correctness_auroc": round(dial_auroc, 4),
            "ece_calibration": d_cal,
            "risk_coverage": d_riskcov,
        },
        "honest_limitation": (
            "gate and dial are fit on DIFFERENT question pools; Stage 1 reports "
            "each component on its native pool and does NOT read both signals on "
            "the same item. The per-item joint read on one mixed stream is Stage 2 "
            "(a signed GPU amendment)."
        ),
        "go_no_go": {
            "recommend_stage2": bool(go),
            "heuristic": "gate AUROC>=0.90 AND dial AUROC>=0.70 AND dial calibrated ECE<0.10",
        },
    }
    print(json.dumps(result, indent=2))
    out = a.out or (RESULT_DIR / "two_signal_stage1_diagnostic.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); result printed above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
