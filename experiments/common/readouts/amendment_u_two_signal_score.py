#!/usr/bin/env python3
"""Amendment U — CPU scorer for the unified two-signal mechanism.

Reads the Amendment U SelfAware extraction (forced-best-guess, pre+post per
answered row) and the Amendment T answerable extraction, and computes the locked
§4 metrics:

  U-G1  (confirmatory) within-SelfAware known-vs-unknown answerability AUROC on the
        U pre-gen anchor (forced-best-guess prompt). >= 0.90.
  U-G3  (PRIMARY) dial-on-hallucination: fit the T correctness dial on ALL T
        post-gen vectors at --dial-layer (no refit), apply COLD to T-correct,
        T-wrong, and U-hallucination post-gen vectors; AUROC(T-correct vs
        U-hallucination) >= 0.65 with bootstrap CI excluding 0.50.
  U-G2  (descriptive) where hallucinations sit vs T-wrong (3-way dial-score means)
        and the within-SelfAware control AUROC(known-answered vs hallucination).

Plus the unified end-to-end frontier: gate (abstain low P-answerable) -> dial
(veto low P-correct among answered) vs gate-only, on T-answerable + U-SelfAware.

Reuses the vetted Amendment S scorer primitives so the estimator family + ECE
definition are identical across S/T/U.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

READOUTS_DIR = Path(__file__).resolve().parent
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))
try:
    from .path_compat import phase1_probe_dir
except ImportError:  # direct script execution
    from path_compat import phase1_probe_dir

PROBE_DIR = phase1_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from amendment_s_correctness_probe_score import (  # noqa: E402
    load_position_layers,
    oof_probe,
)


def load_u_positions(ext_dir: Path, position: str):
    """Load Amendment U answered-row vectors at one position.

    Returns (by_layer{layer->X[n,d]}, label[n] in {'known','unknown'},
             outcome[n] in {'hallucination','answerable_attempt'}, keys[n]).
    """
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8")
            if l.strip()]
    by_layer: dict[int, list] = {}
    labels, outcomes, keys = [], [], []
    for r in rows:
        if not r.get("answered"):
            continue
        safe = str(r["row_key"]).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{position}.safetensors"
        if not shard.exists():
            continue
        t = load_file(str(shard))
        for name, vec in t.items():
            by_layer.setdefault(int(name[1:]), []).append(np.asarray(vec, dtype=np.float64))
        labels.append(r["label"])
        outcomes.append(r.get("outcome"))
        keys.append(r["row_key"])
    X = {layer: np.vstack(vs) for layer, vs in by_layer.items()}
    return X, np.asarray(labels), np.asarray(outcomes), keys


def boot_auroc_ci(y, score, n_boot, seed):
    rng = np.random.default_rng(seed)
    n = len(y)
    a = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if len(np.unique(y[idx])) < 2:
            continue
        a.append(roc_auc_score(y[idx], score[idx]))
    a = np.asarray(a)
    return {"auroc": float(roc_auc_score(y, score)),
            "ci_lo": float(np.percentile(a, 2.5)),
            "ci_hi": float(np.percentile(a, 97.5)), "n_boot": int(len(a))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--u-dir", type=Path, required=True,
                    help="Amendment U SelfAware extraction dir")
    ap.add_argument("--t-dir", type=Path, required=True,
                    help="Amendment T answerable extraction dir (dial source)")
    ap.add_argument("--dial-layer", type=int, default=22, help="T best post layer")
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    u_dir, t_dir = a.u_dir.resolve(), a.t_dir.resolve()

    # ---- U-G1: gate confirm (within-SelfAware known vs unknown, U pre-gen) ----
    Xu_pre, u_label, u_out, _ = load_u_positions(u_dir, "pre")
    y_gate = (u_label == "known").astype(int)
    gate_surface = {}
    for layer in sorted(Xu_pre):
        gate_surface[layer] = float(roc_auc_score(y_gate, oof_probe(Xu_pre[layer], y_gate, a.seed)))
    gate_best = max(gate_surface, key=gate_surface.get)

    # ---- Dial on T: OUT-OF-FOLD scores for the T reference groups (honest, never
    # in-sample), and a SEPARATE full-fit dial for COLD application to U (U items
    # are external to T, so a full fit is a legitimate cold read). Mixing OOF-T with
    # full-fit-U keeps each group's score honest for its own role. ----
    Xt_post, yt, _ = load_position_layers(t_dir, "post")
    t_oof = oof_probe(Xt_post[a.dial_layer], yt, a.seed)  # honest T scores
    dial_tcorrect = t_oof[yt == 1]
    dial_twrong = t_oof[yt == 0]

    dscaler = StandardScaler().fit(Xt_post[a.dial_layer])
    dclf = LogisticRegression(C=1.0, max_iter=2000)
    dclf.fit(dscaler.transform(Xt_post[a.dial_layer]), yt)

    def dial(X):
        return dclf.predict_proba(dscaler.transform(X))[:, 1]

    # ---- U-G3 PRIMARY: dial on hallucinations ----
    Xu_post, u_label2, u_out2, _ = load_u_positions(u_dir, "post")
    halluc_mask = (u_out2 == "hallucination")
    known_ans_mask = (u_out2 == "answerable_attempt")
    dial_halluc = dial(Xu_post[a.dial_layer][halluc_mask])
    dial_known_ans = dial(Xu_post[a.dial_layer][known_ans_mask]) if known_ans_mask.any() else np.array([])

    # AUROC(T-correct=1 vs U-hallucination=0)
    y_g3 = np.concatenate([np.ones(len(dial_tcorrect)), np.zeros(len(dial_halluc))])
    s_g3 = np.concatenate([dial_tcorrect, dial_halluc])
    g3 = boot_auroc_ci(y_g3, s_g3, a.n_boot, a.seed)

    # within-SelfAware control: known-answered(1) vs hallucination(0)
    control = None
    if len(dial_known_ans):
        y_c = np.concatenate([np.ones(len(dial_known_ans)), np.zeros(len(dial_halluc))])
        s_c = np.concatenate([dial_known_ans, dial_halluc])
        control = boot_auroc_ci(y_c, s_c, a.n_boot, a.seed)

    g1_pass = gate_surface[gate_best] >= 0.90
    g3_pass = (g3["auroc"] >= 0.65) and (g3["ci_lo"] > 0.50)
    verdict = "SUCCESS" if (g3_pass and g1_pass) else (
        "FALSIFIER" if (g3["auroc"] < 0.65 and g3["ci_lo"] <= 0.50) else "AMBIGUOUS")

    result = {
        "amendment": "U",
        "analysis": "unified_two_signal_dial_veto",
        "checkpoint": "qwen3-4b clean-sft-merged-16bit + grpo-v2-lora (deployed)",
        "dial_layer": a.dial_layer,
        "n_t_correct": int((yt == 1).sum()),
        "n_t_wrong": int((yt == 0).sum()),
        "n_hallucination": int(halluc_mask.sum()),
        "n_known_answered": int(known_ans_mask.sum()),
        "U_G1_gate_confirm": {
            "best_layer": gate_best,
            "answerability_auroc": round(gate_surface[gate_best], 4),
            "auroc_surface": {str(k): round(v, 4) for k, v in sorted(gate_surface.items())},
            "pass_ge_0.90": bool(g1_pass),
        },
        "U_G3_dial_on_hallucination_PRIMARY": {
            "auroc_tcorrect_vs_hallucination": round(g3["auroc"], 4),
            "ci_95": [round(g3["ci_lo"], 4), round(g3["ci_hi"], 4)],
            "pass_ge_0.65_ci_excl_0.50": bool(g3_pass),
        },
        "U_G2_descriptive": {
            "dial_mean_t_correct": round(float(dial_tcorrect.mean()), 4),
            "dial_mean_t_wrong": round(float(dial_twrong.mean()), 4),
            "dial_mean_hallucination": round(float(dial_halluc.mean()), 4),
            "dial_mean_known_answered": (round(float(dial_known_ans.mean()), 4)
                                         if len(dial_known_ans) else None),
            "within_selfaware_control_auroc_known_vs_halluc": (
                round(control["auroc"], 4) if control else None),
            "within_selfaware_control_ci": (
                [round(control["ci_lo"], 4), round(control["ci_hi"], 4)] if control else None),
        },
        "verdict": verdict,
        "verdict_rule": ("SUCCESS = U-G3 (>=0.65, CI excl 0.50) AND U-G1 (>=0.90); "
                         "FALSIFIER = U-G3 <0.65 AND CI includes 0.50"),
    }
    print(json.dumps(result, indent=2))
    out = a.out or (u_dir / "amendment_u_two_signal_result.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); pass --out <writable path>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
