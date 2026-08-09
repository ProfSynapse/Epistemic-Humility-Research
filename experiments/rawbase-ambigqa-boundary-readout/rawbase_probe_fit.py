#!/usr/bin/env python3
"""M1 probe fit for rawbase-ambigqa-boundary-readout.

The pinned item-26 module `internal_panel_probe_gate.py` computes BOTH the
held-out probe AUROC and the emitted-channel margin, and therefore requires
`--scored-rows` and restricts `--arm` to {A1, A4}. A raw pretrained base has
no emitted-confidence surface, and this cell's gates.yaml registers the
margin sub-check as NOT_READ. This module therefore imports the pinned
module and reuses its probe-fit path UNCHANGED for the one registered
statistic:

  - `internal_panel_probe_gate.load_panel_pool` (same 2748-row pool, same
    label construction)
  - `internal_panel_probe_gate._cv_auroc_with_oof` (StandardScaler + L2
    LogisticRegression(C=0.5) + StratifiedKFold(5, seed 0), identical
    constants, identical fold seeding)
  - the same `latent_knowledge_probe.load_layers(..., source="anchor")`
    loading path at LAYER = 35 via the pinned module's own imports

No threshold, protocol constant, layer, or fold seed differs from the
pinned G7 computation. The ONLY difference is the absence of the emitted
margin block, registered as NOT_READ for this cell (gates.yaml
m1_heldout_probe_auroc.emitted_margin_subcheck). Registered pre-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

EXP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP_DIR.parent / "ood-breadth-beyond-selfaware"))

import internal_panel_probe_gate as ipg  # pinned module, unmodified


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extraction-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    pool = ipg.load_panel_pool()
    row_keys = [r["row_key"] for r in pool]
    y = np.array([1 if r["label"] == "known" else 0 for r in pool])

    import latent_knowledge_probe as lkp  # resolved via ipg's own sys.path setup
    mats = lkp.load_layers(args.extraction_dir, row_keys, [ipg.LAYER], source="anchor")
    X = mats[ipg.LAYER]
    if X.ndim == 3:
        # Same singleton-position squeeze as internal_panel_probe_gate.compute
        # (its lines 110-124, comment and guard reproduced): the MechInterp
        # extraction backend saves the anchor family as (1, hidden) per row.
        if X.shape[1] != 1:
            raise SystemExit(
                f"expected exactly 1 captured position per row for the anchor "
                f"family, got {X.shape[1]}; extraction spec drifted from "
                "extract_rawbase.yaml (families: [anchor])"
            )
        X = X[:, 0, :]

    mean_auc, std_auc, _oof = ipg._cv_auroc_with_oof(X, y, folds=5, C=0.5, seed=0)

    report = {
        "cell": "rawbase-ambigqa-boundary-readout",
        "statistic": "m1_heldout_probe_auroc",
        "layer": ipg.LAYER,
        "n_panel": int(len(pool)),
        "n_panel_known": int(y.sum()),
        "n_panel_unknown": int(len(y) - y.sum()),
        "heldout_probe_auroc": round(float(mean_auc), 4),
        "heldout_probe_auroc_std_across_folds": round(float(std_auc), 4),
        "emitted_margin_subcheck": "NOT_READ (registered; raw base has no emitted surface)",
        "protocol": "internal_panel_probe_gate._cv_auroc_with_oof unchanged (folds=5, C=0.5, seed=0)",
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
