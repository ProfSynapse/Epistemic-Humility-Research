#!/usr/bin/env python3
"""CPU helper (Stage 3 output consumer): score held-out rows against a site's
frozen answerability gate (cell.yaml `gate`: score = neg_z_d = -clip(z_d,
-2,2), z_d standardized against FIT mu_d/sigma_d, tau via Youden J -- all
already fitted and persisted by `build_directions.py`).

Not a registered pipeline stage on its own; used by `run_held_out.py` (Stage
6, to build each held-out row's `gate_score`/`gate_fire` fields for the
`gated` arm's `score_field`/`threshold` selector) and by `run_pairs.py`
(Stage 8, same selection, at the two paired sites). Reads cached anchor
activations from `analysis/extract_<substrate>/` -- the same artifact
`build_directions.py` consumes -- so no fresh GPU forward pass is needed to
gate held-out rows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import ANALYSIS, COMMITTED, DIRECTIONS_DIR  # noqa: E402


def sanitize_key(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_").replace("/", "_")


def load_gate_params(substrate: str, site_name: str) -> dict:
    u_d_rec = json.loads((DIRECTIONS_DIR / substrate / site_name / f"u_d_{site_name}.json").read_text())
    manifest = json.loads((COMMITTED / substrate / "build_gate_manifest.json").read_text())
    site_report = manifest["sites"][site_name]
    return {
        "u_d": np.asarray(u_d_rec["vector"], dtype=np.float64),
        "mu_d": float(u_d_rec["provenance"]["mu_d"]),
        "sigma_d": float(u_d_rec["provenance"]["sigma_d"]),
        "tau": float(site_report["tau"]),
        "hs_index": int(u_d_rec["provenance"]["hs_index"]),
    }


def gate_score_for_rows(substrate: str, site_name: str, row_keys: list[str]) -> dict[str, dict]:
    from safetensors.numpy import load_file

    params = load_gate_params(substrate, site_name)
    extract_dir = ANALYSIS / f"extract_{substrate}"
    key = f"L{params['hs_index']}"
    out = {}
    for rk in row_keys:
        path = extract_dir / f"{sanitize_key(rk)}__anchor.safetensors"
        if not path.exists():
            continue
        tensors = load_file(str(path))
        if key not in tensors:
            continue
        h = np.asarray(tensors[key][0], dtype=np.float64)
        proj_d = float(h @ params["u_d"])
        z_d = float(np.clip((proj_d - params["mu_d"]) / params["sigma_d"], -2.0, 2.0))
        score = -z_d
        out[rk] = {"gate_score": score, "gate_fire": bool(score >= params["tau"]), "gate_tau": params["tau"]}
    return out
