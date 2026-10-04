#!/usr/bin/env python3
"""Pre-sign check (lab-notebook tier), CPU, inside the Stage 0 runner image.

Stage 0 -> Stage 1 artifact contract: freeze a THROWAWAY direction with
MechInterp.probe.fit.freeze_direction (the function `mechinterp probe-fit`
calls) on the drill's 6 smoke-row anchor states at one layer, then load it with
the engine's own decision_core.confidence_analysis.load_direction (hidden size
2048) and score it with score_directions. Labels are arbitrary (alternating);
the numbers mean nothing and are not reported -- only that the schema, hidden
size, layer resolution and score rule round-trip.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
TUNER = REPO / "synaptic-tuner"
for p in (TUNER / "Trainers/decision", TUNER):
    sys.path.insert(0, str(p))

import numpy as np  # noqa: E402
from safetensors.numpy import load_file  # noqa: E402

from MechInterp.probe.fit import freeze_direction  # noqa: E402
from decision_core.confidence_analysis import DirectionSpec, load_direction, score_directions  # noqa: E402


def main() -> int:
    ext, out_dir, layer = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    X = np.stack([load_file(str(ext / f"smoke-{i}__anchor.safetensors"))[f"L{layer}"][0] for i in range(6)])
    y = np.array([i % 2 for i in range(6)])
    path = out_dir / "throwaway_direction.json"
    freeze_direction(X.astype(np.float64), y, layer=layer, out_path=path, n_components=128, seed=0)
    rec = load_direction(DirectionSpec(name="t", path=str(path)), path, hidden_size=X.shape[1])
    sc = score_directions([(DirectionSpec(name="t", path=str(path)), rec)], {layer: X})["t"]
    res = {"check": "direction_contract", "schema": rec["schema_version"], "hidden_dim": int(len(rec["vector"])),
           "resolved_layer": rec["resolved_layer"], "n_scored": int(sc.size), "finite": bool(np.isfinite(sc).all()),
           "pass": rec["resolved_layer"] == layer and len(rec["vector"]) == X.shape[1] and bool(np.isfinite(sc).all())}
    try:
        load_direction(DirectionSpec(name="t", path=str(path)), path, hidden_size=X.shape[1] + 1)
        res["hidden_size_mismatch_fails_loudly"] = False
    except ValueError:
        res["hidden_size_mismatch_fails_loudly"] = True
    res["pass"] = res["pass"] and res["hidden_size_mismatch_fails_loudly"]
    (out_dir / "check_direction_contract.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
