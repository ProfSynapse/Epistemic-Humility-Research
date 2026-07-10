#!/usr/bin/env python3
"""PAR sensor refit — union surface scored under the FULL-FIT (in-loop) probe.

The OOF scores in union_refit_rows_*.jsonl are the right basis for AUROC and
constants (no in-sample inflation), but pool MEMBERSHIP must be classified
under the sensor the reward actually reads (prereg AI section 1.3), which is
the FULL-FIT frozen probe. This script scores every union row with the frozen
probes (same decision path as the reward loop) and writes a companion file
the pool builder consumes. Analogous to par_sensor_refit_mining_step.py,
which already scores mining rows full-fit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
import joblib

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from path_compat import repo_root  # noqa: E402

CANONICAL = repo_root()
REFIT_ROOT = CANONICAL / "archive/experiment/phase1/probe/analysis/par_sensor_refit"
LAYERS = ["L20", "L24", "L28"]
SENSOR_LAYER = "L24"
UNION_EXPECTED = 18496

VARIANTS = {
    "v2": {"union": "union_pregen_4bit", "probes": "probes_v2",
           "suffix": "cleansft4bit"},
}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=list(VARIANTS), default="v2")
    v = VARIANTS[ap.parse_args().variant]
    union_dir = REFIT_ROOT / v["union"]
    probes_dir = REFIT_ROOT / v["probes"]

    rows = [json.loads(l) for l in (union_dir / "rows.jsonl").open() if l.strip()]
    if len(rows) < UNION_EXPECTED:
        print(f"union incomplete: {len(rows)}/{UNION_EXPECTED}", file=sys.stderr)
        return 1

    X = {l: [] for l in LAYERS}
    kept = []
    for r in rows:
        fp = union_dir / f"{r['safe_key']}__pre.safetensors"
        if not fp.exists():
            continue
        with safe_open(str(fp), "pt") as st:
            for l in LAYERS:
                X[l].append(st.get_tensor(l).float().numpy())
        kept.append(r)
    X = {l: np.asarray(a) for l, a in X.items()}

    probes = {l: joblib.load(probes_dir / f"probe_{l}_{v['suffix']}.joblib")
              for l in LAYERS}
    ms = {l: probes[l]["clf"].decision_function(
              probes[l]["scaler"].transform(X[l])) for l in LAYERS}
    mp = sigmoid(-ms[SENSOR_LAYER])

    n_div = 0
    out = REFIT_ROOT / f"union_inloop_rows_{v['suffix']}.jsonl"
    with out.open("w") as fh:
        for i, r in enumerate(kept):
            gold_abstain = r["label"] == "unknown"
            probe_abstain = bool(mp[i] > 0.5)
            divergent = probe_abstain != gold_abstain
            n_div += int(divergent)
            fh.write(json.dumps({
                "row_key": r["row_key"], "source": r["source"],
                "label": r["label"],
                "p_unanswerable": float(mp[i]),
                "divergent_inloop": divergent,
            }) + "\n")

    summary = {"n_scored": len(kept), "divergent_inloop": n_div,
               "out": str(out)}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
