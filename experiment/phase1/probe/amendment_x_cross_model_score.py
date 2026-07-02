#!/usr/bin/env python3
"""Amendment X — CPU scorer: is the two-signal readout SIZE-general (within Qwen3)?

Reads ONE Amendment X mixed-pool extraction (one model) and computes the locked §4
per-model gates. Unlike W (two extraction dirs: S answerable + W SelfAware), X carries
the dial source AND the veto target in the SAME extraction, partitioned by `outcome`:
  correct / wrong  -> the per-model correctness DIAL (post-gen)
  hallucination    -> SelfAware-unknown answered (VETO target, post-gen)
  known_answered   -> SelfAware-known answered (gate known side + control)

  X-G1  gate: within-SelfAware known-vs-unknown answerability AUROC on the PRE-gen
        anchor (known_answered vs hallucination), best layer swept, >=0.65, CI excl 0.50.
  X-G2  dial: correct-vs-wrong post-gen AUROC (OOF), best layer swept, >=0.65, CI excl 0.50.
  X-G3 (PRIMARY) veto: dial fit on THIS model's correct/wrong at --dial-layer (best
        X-G2 layer if unset), correct scored OOF, hallucination scored COLD;
        AUROC(correct vs hallucination) >=0.65, CI excl 0.50.
  descriptive (NOT gated): 3-way dial means; within-SelfAware control
        AUROC(known_answered vs hallucination) via the cold dial.

Per-model verdict on the locked gates; the cross-size SUCCESS/PARTIAL/FALSIFIER
roll-up is assembled across the per-model result JSONs in §7 of the amendment doc.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from safetensors.torch import load_file

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from amendment_s_correctness_probe_score import oof_probe  # noqa: E402
from amendment_u_two_signal_score import boot_auroc_ci  # noqa: E402


def load_x_positions(ext_dir: Path, position: str):
    """Load answered-row vectors at one position, keyed by `outcome`.

    Returns (by_layer{layer->X[n,d]}, outcome[n]) over rows that are answered, carry
    an outcome in {correct, wrong, hallucination, known_answered}, and have a present
    shard for this position.
    """
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8")
            if l.strip()]
    by_layer: dict[int, list] = {}
    outcomes = []
    for r in rows:
        if not r.get("answered"):
            continue
        outcome = r.get("outcome")
        if outcome not in ("correct", "wrong", "hallucination", "known_answered"):
            continue
        safe = str(r["row_key"]).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{position}.safetensors"
        if not shard.exists():
            continue
        t = load_file(str(shard))
        for name, vec in t.items():
            by_layer.setdefault(int(name[1:]), []).append(np.asarray(vec, dtype=np.float64))
        outcomes.append(outcome)
    X = {layer: np.vstack(vs) for layer, vs in by_layer.items()}
    return X, np.asarray(outcomes)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--x-dir", type=Path, required=True,
                    help="Amendment X mixed-pool extraction dir (one model)")
    ap.add_argument("--dial-layer", type=int, default=None,
                    help="post layer for the veto dial; default = best X-G2 layer")
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--n-jobs", type=int, default=-1,
                    help="workers for the per-layer probe sweeps; layers are "
                         "independent and seed-fixed, so any value returns "
                         "identical numbers (-1 = all cores, 1 = old serial path)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    x_dir = a.x_dir.resolve()
    manifest = json.loads((x_dir / "manifest.json").read_text(encoding="utf-8"))
    model_name = manifest.get("base_model", "unknown")
    model_tag = manifest.get("model_tag", "unknown")

    Xpost, out_post = load_x_positions(x_dir, "post")
    Xpre, out_pre = load_x_positions(x_dir, "pre")

    # ---- X-G2 dial: correct vs wrong, post-gen, OOF, sweep layers ----
    dmask = np.isin(out_post, ["correct", "wrong"])
    yd = (out_post[dmask] == "correct").astype(int)
    n_correct, n_wrong = int((yd == 1).sum()), int((yd == 0).sum())
    dial_layers = sorted(Xpost)
    dial_oofs = Parallel(n_jobs=a.n_jobs)(
        delayed(oof_probe)(Xpost[layer][dmask], yd, a.seed) for layer in dial_layers)
    dial_surface = {layer: float(roc_auc_score(yd, oof))
                    for layer, oof in zip(dial_layers, dial_oofs)}
    dial_best = max(dial_surface, key=dial_surface.get)
    dial_layer = a.dial_layer if a.dial_layer is not None else dial_best
    d_oof = oof_probe(Xpost[dial_layer][dmask], yd, a.seed)
    g2 = boot_auroc_ci(yd, d_oof, a.n_boot, a.seed)
    dial_correct_oof = d_oof[yd == 1]
    dial_wrong_oof = d_oof[yd == 0]

    # full-fit dial at dial_layer for COLD application to hallucinations / known_ans
    dscaler = StandardScaler().fit(Xpost[dial_layer][dmask])
    dclf = LogisticRegression(C=1.0, max_iter=2000)
    dclf.fit(dscaler.transform(Xpost[dial_layer][dmask]), yd)

    def dial(X):
        return dclf.predict_proba(dscaler.transform(X))[:, 1]

    halluc_post = (out_post == "hallucination")
    known_post = (out_post == "known_answered")
    dial_halluc = dial(Xpost[dial_layer][halluc_post]) if halluc_post.any() else np.array([])
    dial_known = dial(Xpost[dial_layer][known_post]) if known_post.any() else np.array([])

    # ---- X-G3 PRIMARY veto: correct(OOF, 1) vs hallucination(cold, 0) ----
    y_g3 = np.concatenate([np.ones(len(dial_correct_oof)), np.zeros(len(dial_halluc))])
    s_g3 = np.concatenate([dial_correct_oof, dial_halluc])
    g3 = boot_auroc_ci(y_g3, s_g3, a.n_boot, a.seed)

    # within-SelfAware control: known_answered(1) vs hallucination(0), cold dial
    control = None
    if len(dial_known) and len(dial_halluc):
        y_c = np.concatenate([np.ones(len(dial_known)), np.zeros(len(dial_halluc))])
        s_c = np.concatenate([dial_known, dial_halluc])
        control = boot_auroc_ci(y_c, s_c, a.n_boot, a.seed)

    # ---- X-G1 gate: within-SelfAware known vs unknown at PRE anchor, OOF, sweep ----
    gmask = np.isin(out_pre, ["known_answered", "hallucination"])
    yg = (out_pre[gmask] == "known_answered").astype(int)
    n_known_ans, n_unknown_ans = int((yg == 1).sum()), int((yg == 0).sum())
    gate_layers = sorted(Xpre)
    gate_oofs = Parallel(n_jobs=a.n_jobs)(
        delayed(oof_probe)(Xpre[layer][gmask], yg, a.seed) for layer in gate_layers)
    gate_surface = {layer: float(roc_auc_score(yg, oof))
                    for layer, oof in zip(gate_layers, gate_oofs)}
    gate_best = max(gate_surface, key=gate_surface.get)
    g1 = boot_auroc_ci(yg, oof_probe(Xpre[gate_best][gmask], yg, a.seed), a.n_boot, a.seed)

    n_halluc = int(halluc_post.sum())
    g1_pass = (g1["auroc"] >= 0.65) and (g1["ci_lo"] > 0.50)
    g2_pass = (g2["auroc"] >= 0.65) and (g2["ci_lo"] > 0.50)
    g3_pass = (g3["auroc"] >= 0.65) and (g3["ci_lo"] > 0.50)
    floor_ok = (n_wrong >= 30) and (n_halluc >= 50)

    if not floor_ok:
        verdict = (f"DATA_STAGE_STOP (need wrong>=30 AND halluc>=50; "
                   f"got wrong={n_wrong} halluc={n_halluc})")
    elif g1_pass and g2_pass and g3_pass:
        verdict = "PASS (all three gates)"
    elif g3["auroc"] < 0.65 and g3["ci_lo"] <= 0.50:
        verdict = "FALSIFIER_CONTRIB (primary veto fails on this model)"
    else:
        verdict = "PARTIAL (not all gates pass)"

    result = {
        "amendment": "X",
        "analysis": "cross_size_training_free_two_signal",
        "base_model": model_name,
        "model_tag": model_tag,
        "checkpoint": f"raw {model_name} (no adapter)",
        "dial_layer_used": dial_layer,
        "dial_best_layer": dial_best,
        "n_correct": n_correct,
        "n_wrong": n_wrong,
        "n_hallucination": n_halluc,
        "n_known_answered": int(known_post.sum()),
        "data_adequacy_ok": bool(floor_ok),
        "X_G1_gate": {
            "best_layer": gate_best,
            "answerability_auroc": round(g1["auroc"], 4),
            "ci_95": [round(g1["ci_lo"], 4), round(g1["ci_hi"], 4)],
            "n_known": n_known_ans, "n_unknown": n_unknown_ans,
            "auroc_surface": {str(k): round(v, 4) for k, v in sorted(gate_surface.items())},
            "pass_ge_0.65_ci_excl_0.50": bool(g1_pass),
        },
        "X_G2_dial": {
            "auroc_correct_vs_wrong": round(g2["auroc"], 4),
            "ci_95": [round(g2["ci_lo"], 4), round(g2["ci_hi"], 4)],
            "best_layer": dial_best,
            "auroc_surface": {str(k): round(v, 4) for k, v in sorted(dial_surface.items())},
            "pass_ge_0.65_ci_excl_0.50": bool(g2_pass),
        },
        "X_G3_veto_PRIMARY": {
            "auroc_correct_vs_hallucination": round(g3["auroc"], 4),
            "ci_95": [round(g3["ci_lo"], 4), round(g3["ci_hi"], 4)],
            "pass_ge_0.65_ci_excl_0.50": bool(g3_pass),
        },
        "descriptive": {
            "dial_mean_correct": round(float(dial_correct_oof.mean()), 4),
            "dial_mean_wrong": round(float(dial_wrong_oof.mean()), 4),
            "dial_mean_hallucination": (round(float(dial_halluc.mean()), 4)
                                        if len(dial_halluc) else None),
            "dial_mean_known_answered": (round(float(dial_known.mean()), 4)
                                         if len(dial_known) else None),
            "within_selfaware_control_auroc_known_vs_halluc": (
                round(control["auroc"], 4) if control else None),
            "within_selfaware_control_ci": (
                [round(control["ci_lo"], 4), round(control["ci_hi"], 4)] if control else None),
        },
        "verdict": verdict,
        "verdict_rule": ("PASS = X-G1 AND X-G2 AND X-G3 each >=0.65 with CI excl 0.50, "
                         "given wrong>=30 AND halluc>=50; FALSIFIER_CONTRIB = X-G3 <0.65 "
                         "AND CI includes 0.50. Cross-size roll-up over all models in §7."),
    }
    print(json.dumps(result, indent=2))
    out = a.out or (x_dir / f"amendment_x_{model_tag}_result.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); pass --out <writable path>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
