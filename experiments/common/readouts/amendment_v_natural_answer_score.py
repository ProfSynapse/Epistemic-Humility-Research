#!/usr/bin/env python3
"""Amendment V — CPU scorer: does the FORCED-fit dial transfer to NATURAL answers?

Reads the Amendment V natural-answer extraction and the Amendment T forced-answer
extraction (the dial source). Fits the T correctness dial on ALL T post-gen vectors
at --dial-layer (no refit), applies it COLD to V's natural groups, and computes the
locked §4 metrics:

  V-G2  (PRIMARY) AUROC(natural-correct vs natural-hallucination) >= 0.65, CI excl 0.50.
  V-G1            AUROC(natural-correct vs natural-wrong)         >= 0.65, CI excl 0.50.
  descriptive     3-way dial-score distribution; gate AUROC on the natural anchor.

T reference groups are scored OUT-OF-FOLD (honest); V groups are cold-applied
(external to the T fit). Reuses the vetted Amendment S/U primitives.
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
    from .path_compat import knowledge_probe_dir
except ImportError:  # direct script execution
    from path_compat import knowledge_probe_dir

PROBE_DIR = knowledge_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from amendment_s_correctness_probe_score import load_position_layers, oof_probe  # noqa: E402
from amendment_u_two_signal_score import boot_auroc_ci  # noqa: E402


def load_v_positions(ext_dir: Path, position: str):
    """Answered V rows at one position -> (by_layer, outcome[], answerable[], keys)."""
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8") if l.strip()]
    by_layer: dict[int, list] = {}
    outcomes, answerable, keys = [], [], []
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
        outcomes.append(r.get("outcome"))
        answerable.append(bool(r.get("answerable")))
        keys.append(r["row_key"])
    X = {layer: np.vstack(vs) for layer, vs in by_layer.items()}
    return X, np.asarray(outcomes), np.asarray(answerable), keys


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--v-dir", type=Path, required=True)
    ap.add_argument("--t-dir", type=Path, required=True, help="dial source (forced)")
    ap.add_argument("--dial-layer", type=int, default=22)
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    v_dir, t_dir = a.v_dir.resolve(), a.t_dir.resolve()

    # Dial: full-fit on T for COLD application to V; OOF on T for the honest T-ref.
    Xt_post, yt, _ = load_position_layers(t_dir, "post")
    dscaler = StandardScaler().fit(Xt_post[a.dial_layer])
    dclf = LogisticRegression(C=1.0, max_iter=2000)
    dclf.fit(dscaler.transform(Xt_post[a.dial_layer]), yt)

    def dial(X):
        return dclf.predict_proba(dscaler.transform(X))[:, 1]

    Xv_post, v_out, v_ans, _ = load_v_positions(v_dir, "post")
    d_correct = dial(Xv_post[a.dial_layer][v_out == "correct"])
    d_wrong = dial(Xv_post[a.dial_layer][v_out == "wrong"])
    d_halluc = dial(Xv_post[a.dial_layer][v_out == "hallucination"])

    def auroc_block(pos, neg):
        if len(pos) == 0 or len(neg) == 0:
            return None
        y = np.concatenate([np.ones(len(pos)), np.zeros(len(neg))])
        s = np.concatenate([pos, neg])
        return boot_auroc_ci(y, s, a.n_boot, a.seed)

    g2 = auroc_block(d_correct, d_halluc)   # PRIMARY: correct vs hallucination
    g1 = auroc_block(d_correct, d_wrong)    # correct vs wrong

    # Gate (answerability) on the natural anchor, descriptive.
    Xv_pre, _, v_ans_pre, _ = load_v_positions(v_dir, "pre")
    gate = None
    if len(np.unique(v_ans_pre)) == 2:
        y_gate = v_ans_pre.astype(int)
        best, bestv = None, -1
        for layer in sorted(Xv_pre):
            au = float(roc_auc_score(y_gate, oof_probe(Xv_pre[layer], y_gate, a.seed)))
            if au > bestv:
                best, bestv = layer, au
        gate = {"best_layer": best, "answerability_auroc": round(bestv, 4)}

    floor_ok = (len(d_wrong) >= 30) and (len(d_halluc) >= 20)
    g2_pass = bool(g2 and g2["auroc"] >= 0.65 and g2["ci_lo"] > 0.50)
    g1_pass = bool(g1 and g1["auroc"] >= 0.65 and g1["ci_lo"] > 0.50)
    if not floor_ok:
        verdict = "DATA_STAGE_STOP (safety finding: model rarely errs/hallucinates naturally)"
    elif g2_pass and g1_pass:
        verdict = "SUCCESS"
    elif g2 and g2["auroc"] < 0.65 and g2["ci_lo"] <= 0.50:
        verdict = "FALSIFIER"
    else:
        verdict = "AMBIGUOUS"

    result = {
        "amendment": "V", "analysis": "natural_answer_generalization",
        "checkpoint": "qwen3-4b clean-sft-merged-16bit + grpo-v2-lora (NATURAL prompt)",
        "dial_layer": a.dial_layer,
        "n_natural_correct": int((v_out == "correct").sum()),
        "n_natural_wrong": int((v_out == "wrong").sum()),
        "n_natural_hallucination": int((v_out == "hallucination").sum()),
        "data_adequacy_ok": floor_ok,
        "V_G2_correct_vs_hallucination_PRIMARY": (
            {"auroc": round(g2["auroc"], 4), "ci_95": [round(g2["ci_lo"], 4), round(g2["ci_hi"], 4)],
             "pass": g2_pass} if g2 else None),
        "V_G1_correct_vs_wrong": (
            {"auroc": round(g1["auroc"], 4), "ci_95": [round(g1["ci_lo"], 4), round(g1["ci_hi"], 4)],
             "pass": g1_pass} if g1 else None),
        "dial_means": {
            "natural_correct": round(float(d_correct.mean()), 4) if len(d_correct) else None,
            "natural_wrong": round(float(d_wrong.mean()), 4) if len(d_wrong) else None,
            "natural_hallucination": round(float(d_halluc.mean()), 4) if len(d_halluc) else None,
        },
        "gate_on_natural_anchor_descriptive": gate,
        "verdict": verdict,
        "verdict_rule": "SUCCESS = V-G2 AND V-G1 (both >=0.65, CI excl 0.50) given adequacy; "
                        "FALSIFIER = V-G2 <0.65 AND CI includes 0.50",
    }
    print(json.dumps(result, indent=2))
    out = a.out or (v_dir / "amendment_v_natural_answer_result.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); pass --out <writable path>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
