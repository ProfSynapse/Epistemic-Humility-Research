#!/usr/bin/env python3
"""PAR sensor refit — mining re-classification step only (CPU, fast path).

Companion to par_sensor_refit_fit.py for the case where the mining extraction
finishes AFTER the union refit: loads the already-fitted frozen probes and
runs ONLY the mining scoring + re-classification, then patches the mining
section into the existing result JSONs (canonical + committed copy). Output
is byte-identical to what a full rerun would produce for that section.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
import joblib

PROBE_DIR = Path(__file__).resolve().parent
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
REFIT_ROOT = CANONICAL / "experiment/phase1/probe/analysis/par_sensor_refit"
LAYERS = ["L20", "L24", "L28"]
SENSOR_LAYER = "L24"
MINING_EXPECTED = 9397

VARIANTS = {
    "v2": {"mining": "mining_pregen_4bit", "probes": "probes_v2",
           "result": "refit_result_v2.json", "copy": "par_sensor_refit_v2.json",
           "suffix": "cleansft4bit"},
}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=list(VARIANTS), default="v2")
    v = VARIANTS[ap.parse_args().variant]
    mining_dir = REFIT_ROOT / v["mining"]
    probes_dir = REFIT_ROOT / v["probes"]

    rows = [json.loads(l) for l in (mining_dir / "rows.jsonl").open() if l.strip()]
    if len(rows) < MINING_EXPECTED:
        print(f"mining incomplete: {len(rows)}/{MINING_EXPECTED}", file=sys.stderr)
        return 1

    X = {l: [] for l in LAYERS}
    kept = []
    for r in rows:
        fp = mining_dir / f"{r['safe_key']}__pre.safetensors"
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
    sensor_dover = mp < 0.5
    consensus_dover = ((ms["L20"] > 0) & (ms["L24"] > 0) & (ms["L28"] > 0))

    with (REFIT_ROOT / f"mining_refit_rows_{v['suffix']}.jsonl").open("w") as fh:
        for i, r in enumerate(kept):
            fh.write(json.dumps({
                "row_key": r["row_key"], "source": r.get("source"),
                "p_unanswerable": float(mp[i]),
                "sensor_dover": bool(sensor_dover[i]),
                "consensus_dover": bool(consensus_dover[i]),
            }) + "\n")

    by_source = {}
    for i, r in enumerate(kept):
        src = r.get("source", "unknown")
        e = by_source.setdefault(src, {"n": 0, "sensor_dover": 0,
                                       "consensus_dover": 0})
        e["n"] += 1
        e["sensor_dover"] += int(sensor_dover[i])
        e["consensus_dover"] += int(consensus_dover[i])
    section = {
        "n_scored": len(kept),
        "sensor_dover_total": int(sensor_dover.sum()),
        "consensus_dover_total": int(consensus_dover.sum()),
        "note": "sensor_dover (refit-L24 p<0.5) is the operative count "
                "for the training mixture; consensus is sensitivity.",
        "by_source": by_source,
        "mean_margin_sensor_dover": (
            round(float(np.abs(2 * mp[sensor_dover] - 1).mean()), 4)
            if sensor_dover.any() else None),
    }
    for path in (REFIT_ROOT / v["result"], PROBE_DIR / v["copy"]):
        res = json.loads(path.read_text())
        res["mining_reclassification_refit"] = section
        path.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(section, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
