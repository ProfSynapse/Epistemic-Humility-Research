#!/usr/bin/env python3
"""Amendment W — CPU scorer: is the two-signal mechanism training-free on the RAW base?

Reads the Amendment W RAW-base SelfAware extraction (pre+post per answered row) and
the Amendment S RAW-base answerable extraction (the dial source), and computes the
locked §4 metrics:

  W-G1  (PRIMARY) dial-on-hallucination, NO TRAINING: fit the S correctness dial on
        ALL S post-gen vectors at --dial-layer (no refit), apply COLD to S-correct,
        S-wrong, and W-hallucination post-gen vectors; AUROC(S-correct vs
        W-hallucination) >= 0.65 with bootstrap CI excluding 0.50. (Base analog of U-G3.)
  W-G2  gate reads on the base SelfAware anchor: within-SelfAware known-vs-unknown
        answerability AUROC on the W pre-gen anchor >= 0.65, CI excludes 0.50.
  descriptive (NOT gated): 3-way dial-score means (S-correct, base known-answered,
        W-hallucination); within-SelfAware control AUROC(known-answered vs halluc).

S reference groups are scored OUT-OF-FOLD (honest); W hallucinations are cold-applied
(external to the S fit). Mirrors the vetted Amendment U scorer exactly, swapping the
TRAINED-checkpoint dial source (T) for the RAW-base dial source (S).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from amendment_s_correctness_probe_score import load_position_layers, oof_probe  # noqa: E402
from amendment_u_two_signal_score import load_u_positions, boot_auroc_ci  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--w-dir", type=Path, required=True,
                    help="Amendment W RAW-base SelfAware extraction dir")
    ap.add_argument("--s-dir", type=Path, required=True,
                    help="Amendment S RAW-base answerable extraction dir (dial source)")
    ap.add_argument("--dial-layer", type=int, default=20, help="S best post layer")
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    w_dir, s_dir = a.w_dir.resolve(), a.s_dir.resolve()

    # ---- W-G2: gate confirm (within-SelfAware known vs unknown, W pre-gen anchor) ----
    Xw_pre, w_label, _w_out, _ = load_u_positions(w_dir, "pre")
    y_gate = (w_label == "known").astype(int)
    gate_surface = {}
    for layer in sorted(Xw_pre):
        gate_surface[layer] = float(roc_auc_score(y_gate, oof_probe(Xw_pre[layer], y_gate, a.seed)))
    gate_best = max(gate_surface, key=gate_surface.get)
    y_gate_best = y_gate
    gate_ci = boot_auroc_ci(y_gate_best,
                            oof_probe(Xw_pre[gate_best], y_gate_best, a.seed),
                            a.n_boot, a.seed)

    # ---- Dial on S: OUT-OF-FOLD for the S reference groups (honest), SEPARATE
    # full-fit dial for COLD application to W (W items are external to S). Mirrors U. ----
    Xs_post, ys, _ = load_position_layers(s_dir, "post")
    s_oof = oof_probe(Xs_post[a.dial_layer], ys, a.seed)
    dial_scorrect = s_oof[ys == 1]
    dial_swrong = s_oof[ys == 0]

    dscaler = StandardScaler().fit(Xs_post[a.dial_layer])
    dclf = LogisticRegression(C=1.0, max_iter=2000)
    dclf.fit(dscaler.transform(Xs_post[a.dial_layer]), ys)

    def dial(X):
        return dclf.predict_proba(dscaler.transform(X))[:, 1]

    # ---- W-G1 PRIMARY: dial on base hallucinations ----
    Xw_post, _w_label2, w_out2, _ = load_u_positions(w_dir, "post")
    halluc_mask = (w_out2 == "hallucination")
    known_ans_mask = (w_out2 == "answerable_attempt")
    dial_halluc = dial(Xw_post[a.dial_layer][halluc_mask])
    dial_known_ans = dial(Xw_post[a.dial_layer][known_ans_mask]) if known_ans_mask.any() else np.array([])

    # AUROC(S-correct=1 vs W-hallucination=0)
    y_g1 = np.concatenate([np.ones(len(dial_scorrect)), np.zeros(len(dial_halluc))])
    s_g1 = np.concatenate([dial_scorrect, dial_halluc])
    g1 = boot_auroc_ci(y_g1, s_g1, a.n_boot, a.seed)

    # within-SelfAware control: known-answered(1) vs hallucination(0)
    control = None
    if len(dial_known_ans):
        y_c = np.concatenate([np.ones(len(dial_known_ans)), np.zeros(len(dial_halluc))])
        s_c = np.concatenate([dial_known_ans, dial_halluc])
        control = boot_auroc_ci(y_c, s_c, a.n_boot, a.seed)

    g2_pass = (gate_ci["auroc"] >= 0.65) and (gate_ci["ci_lo"] > 0.50)
    g1_pass = (g1["auroc"] >= 0.65) and (g1["ci_lo"] > 0.50)
    floor_ok = int(halluc_mask.sum()) >= 50
    if not floor_ok:
        verdict = "DATA_STAGE_STOP (below 50-hallucination floor; base unexpectedly refused)"
    elif g1_pass and g2_pass:
        verdict = "SUCCESS"
    elif g1["auroc"] < 0.65 and g1["ci_lo"] <= 0.50:
        verdict = "FALSIFIER"
    else:
        verdict = "AMBIGUOUS"

    result = {
        "amendment": "W",
        "analysis": "training_free_base_model_two_signal",
        "checkpoint": "raw Qwen3-4B Instruct base (unsloth/Qwen3-4B-bnb-4bit, NO adapter)",
        "dial_source": "Amendment S RAW-base post-gen dial",
        "dial_layer": a.dial_layer,
        "n_s_correct": int((ys == 1).sum()),
        "n_s_wrong": int((ys == 0).sum()),
        "n_hallucination": int(halluc_mask.sum()),
        "n_known_answered": int(known_ans_mask.sum()),
        "data_adequacy_ok": bool(floor_ok),
        "W_G1_dial_on_hallucination_PRIMARY": {
            "auroc_scorrect_vs_hallucination": round(g1["auroc"], 4),
            "ci_95": [round(g1["ci_lo"], 4), round(g1["ci_hi"], 4)],
            "pass_ge_0.65_ci_excl_0.50": bool(g1_pass),
        },
        "W_G2_gate_on_base_anchor": {
            "best_layer": gate_best,
            "answerability_auroc": round(gate_ci["auroc"], 4),
            "ci_95": [round(gate_ci["ci_lo"], 4), round(gate_ci["ci_hi"], 4)],
            "auroc_surface": {str(k): round(v, 4) for k, v in sorted(gate_surface.items())},
            "pass_ge_0.65_ci_excl_0.50": bool(g2_pass),
        },
        "descriptive": {
            "dial_mean_s_correct": round(float(dial_scorrect.mean()), 4),
            "dial_mean_s_wrong": round(float(dial_swrong.mean()), 4),
            "dial_mean_hallucination": round(float(dial_halluc.mean()), 4),
            "dial_mean_known_answered": (round(float(dial_known_ans.mean()), 4)
                                         if len(dial_known_ans) else None),
            "within_selfaware_control_auroc_known_vs_halluc": (
                round(control["auroc"], 4) if control else None),
            "within_selfaware_control_ci": (
                [round(control["ci_lo"], 4), round(control["ci_hi"], 4)] if control else None),
        },
        "verdict": verdict,
        "verdict_rule": ("SUCCESS = W-G1 (>=0.65, CI excl 0.50) AND W-G2 (>=0.65, CI excl 0.50) "
                         "given >=50 hallucinations; FALSIFIER = W-G1 <0.65 AND CI includes 0.50"),
    }
    print(json.dumps(result, indent=2))
    out = a.out or (w_dir / "amendment_w_base_model_result.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); pass --out <writable path>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
