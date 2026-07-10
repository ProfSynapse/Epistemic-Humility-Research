#!/usr/bin/env python3
"""Amendment T — SECONDARY cross-checkpoint cold-transfer (CPU, descriptive).

Pre-registered in
experiments/correctness-readout-deployment-port/AMENDMENT.md §3 step 5
/ §4 "Secondary (descriptive, NOT gated)". This is NOT a gate — it reports
whether the correctness-readout DIRECTION is shared across checkpoints.

Question: fit the Amendment S correctness probe on the Instruct-base extraction,
then apply it COLD (no refit) to the Amendment T deployment-checkpoint post-gen
hidden states. If transfer AUROC stays high, the readout direction is shared
across checkpoints (the cross-checkpoint analogue of Amendment P's cross-dataset
answerability transfer). If it collapses, the deployed checkpoint represents its
own correctness along a DIFFERENT direction than the Instruct base — the readout
survives (per the gated T-G1/T-G2) but is not the same linear object.

Method (post-gen position only; that is where the S signal lives):
  * Fit StandardScaler + LogisticRegression(C=1.0) on ALL Amendment S post-gen
    vectors at the transfer layer (default = S best post layer = L20). This is
    the same estimator family as the gated probe (amendment_s ... _score.py),
    fit on the full S set (no CV split — we are transferring, not evaluating S).
  * Apply that fixed scaler+clf to the Amendment T post-gen vectors at the SAME
    layer; AUROC vs T's correct/wrong labels = cold-transfer AUROC.
  * For context, also report T's IN-DISTRIBUTION post-gen AUROC at that layer
    (5-fold CV, the gated recipe) so transfer can be read against the ceiling.

Baselines for interpretation: chance 0.50; the gated in-dist T post-gen AUROC is
the ceiling cold-transfer is compared against.
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

# Reuse the gated scorer's loaders + in-dist probe so transfer is read by the
# identical estimator family.
from amendment_s_correctness_probe_score import (  # noqa: E402
    load_position_layers,
    oof_probe,
)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--s-dir", type=Path, required=True,
                    help="Amendment S Instruct-base extraction dir (probe source)")
    ap.add_argument("--t-dir", type=Path, required=True,
                    help="Amendment T deployment-checkpoint extraction dir (target)")
    ap.add_argument("--layer", type=int, default=20,
                    help="transfer layer (default S best post-gen layer = 20)")
    ap.add_argument("--seed", type=int, default=20260630)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    s_dir = a.s_dir.resolve()
    t_dir = a.t_dir.resolve()
    layer = a.layer

    # Source: ALL Amendment S post-gen vectors at the transfer layer.
    Xs, ys, _ = load_position_layers(s_dir, "post")
    if layer not in Xs:
        raise SystemExit(f"layer L{layer} absent in S extraction (have "
                         f"{min(Xs)}..{max(Xs)})")
    # Target: Amendment T post-gen vectors at the same layer.
    Xt, yt, _ = load_position_layers(t_dir, "post")
    if layer not in Xt:
        raise SystemExit(f"layer L{layer} absent in T extraction (have "
                         f"{min(Xt)}..{max(Xt)})")

    # Fit S probe on the FULL S set (transfer, not S-eval -> no held-out split).
    scaler = StandardScaler().fit(Xs[layer])
    clf = LogisticRegression(C=1.0, max_iter=2000)
    clf.fit(scaler.transform(Xs[layer]), ys)

    # Cold-apply to T.
    p_transfer = clf.predict_proba(scaler.transform(Xt[layer]))[:, 1]
    transfer_auroc = float(roc_auc_score(yt, p_transfer))

    # Context: T in-distribution post-gen AUROC at the same layer (gated recipe).
    p_indist = oof_probe(Xt[layer], yt, a.seed)
    t_indist_auroc = float(roc_auc_score(yt, p_indist))

    result = {
        "amendment": "T",
        "analysis": "cross_checkpoint_cold_transfer_secondary",
        "gated": False,
        "transfer_layer": layer,
        "s_source_dir": str(s_dir),
        "t_target_dir": str(t_dir),
        "s_n": int(len(ys)),
        "s_n_correct": int((ys == 1).sum()),
        "s_n_wrong": int((ys == 0).sum()),
        "t_n": int(len(yt)),
        "t_n_correct": int((yt == 1).sum()),
        "t_n_wrong": int((yt == 0).sum()),
        "cold_transfer_auroc": round(transfer_auroc, 4),
        "t_in_distribution_auroc_same_layer": round(t_indist_auroc, 4),
        "interpretation": (
            "high transfer -> correctness-readout DIRECTION shared across "
            "Instruct base and deployed checkpoint (cross-checkpoint analogue of "
            "Amendment P). Collapse -> readout survives but along a different "
            "linear object on the deployed checkpoint."
        ),
    }
    print(json.dumps(result, indent=2))
    out = a.out or (t_dir / "amendment_t_cold_transfer.json")
    try:
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out}")
    except OSError as exc:
        print(f"\n[warn] could not write {out} ({exc}); result printed above. "
              "Pass --out <writable path> to persist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
