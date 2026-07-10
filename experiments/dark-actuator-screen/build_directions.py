#!/usr/bin/env python3
"""Stage the 12 frozen dark-displacement candidates + fit the screen's controls.

CPU-ONLY. Lab-diagnostic build script for the dark-actuator-screen (Tier-2
exploratory dose SCREEN). Does not run any steering arm; it only prepares the
`mechinterp-direction/v1` JSONs the cell.yaml `readouts:` block references.

Three jobs, each documented where it runs:

1. Stage the 12 AUTHORITATIVE frozen raw-base candidate JSONs (dark
   displacement census, PR #222) into this experiment's gitignored
   `directions/` dir, ADAPTING them from the census's own
   `phase3-residual-caution-direction/v1` schema (field `theta`, capture-index
   `layer`) to the tuner's `mechinterp-direction/v1` schema (field `vector`,
   0-indexed decoder-block `layer`). See ADAPTER NOTE below for the layer/block
   distinction -- getting this wrong silently hooks the wrong decoder block.

2. Fit the screen's positive control (raw-base answer-vs-refuse mass-mean) and
   negative control (raw-base confab-propensity) at every layer that hosts a
   frozen candidate, by calling the EXACT formulas at
   experiments/dark-actuator-screen/dark_displacement_census.py:206-215 (`build_span`'s
   pre-QR `refuse`/`propensity` directions) on the same raw-base pool the
   census used. Reusing build_span's own math (not the QR-mixed basis it
   returns) keeps these controls identical in derivation to the "named axes"
   the census already projects out, per the AMENDMENT's instruction.

3. Generate one seeded random-unit-direction control per candidate, at the
   candidate's own layer/block and hidden_dim, so "matched norm" holds
   trivially (every direction here is unit-norm with sigma=1.0, so dose
   strength alone parametrizes the write magnitude identically across
   candidate / positive / negative / random cells).

ADAPTER NOTE (layer vs block)
------------------------------
The census's frozen candidate JSON carries TWO layer numbers:
  "layer": lnum       -- the AK Stage-1 capture-time label (e.g. "L16" -> 16),
                          the 1-indexed hidden_states() convention (index 0 is
                          the embedding output).
  "block": lnum - 1    -- the 0-indexed decoder-module index matching that same
                          capture, i.e. what synaptic-tuner's
                          MechInterp.intervention.get_decoder_layer(model, idx)
                          must be given to hook the SAME residual-stream point.
The tuner's steer engine (`MechInterp/cli.py::run_steer`) reads
`active_readout["layer"]` and passes it straight to `get_decoder_layer` as
`layer_idx`. This script therefore writes the tuner-schema "layer" field as the
census's "block" (lnum - 1), NOT its "layer" (lnum). Every emitted direction
JSON keeps the original capture label under
`provenance.census_capture_layer_label` for a human sanity check.

Usage
-----
  python experiments/dark-actuator-screen/build_directions.py \
      --candidates-src /path/to/authoritative/dark_displacement_census \
      --pool-root /home/profsynapse/ak_census_data \
      --out experiments/dark-actuator-screen/directions \
      --prep-manifest experiments/dark-actuator-screen/analysis/prep_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import dark_displacement_census as census  # noqa: E402  (reused, not reimplemented)

CANDIDATE_NAMES = [
    "L16_arel_pc7", "L20_arel_pc5", "L20_arel_pc8", "L20_succ_pc5",
    "L24_arel_pc5", "L24_arel_pc7", "L24_succ_pc4", "L28_arel_pc11",
    "L28_succ_pc0", "L28_succ_pc3", "L28_succ_pc4", "L34_succ_pc0",
]
SCREEN_LAYERS = ["L16", "L20", "L24", "L28", "L34"]
RANDOM_SEED_BASE = 20260706  # AMENDMENT / census seed


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(v: np.ndarray) -> np.ndarray:
    return census.unit(v)


# --------------------------------------------------------------------------
# Job 1: stage + adapt the 12 authoritative candidates
# --------------------------------------------------------------------------

def stage_candidates(src_dir: Path, out_dir: Path) -> list[dict]:
    """Adapt each frozen candidate JSON to mechinterp-direction/v1; return
    per-file provenance records for the prep manifest."""
    records = []
    for name in CANDIDATE_NAMES:
        fname = f"dark_cand_raw-base_{name}.json"
        src = src_dir / fname
        if not src.is_file():
            raise FileNotFoundError(f"authoritative candidate missing: {src}")
        orig = json.loads(src.read_text())
        theta = orig["theta"]
        lnum = int(orig["layer"])
        block = int(orig.get("block", lnum - 1))
        adapted = {
            "schema_version": "mechinterp-direction/v1",
            "layer": block,
            "hidden_dim": int(orig["hidden_dim"]),
            "normalized": True,
            "vector": theta,
            "raw_norm": 1.0,
            "intercept": 0.0,
            "mu": [0.0] * int(orig["hidden_dim"]),
            "sigma": float(orig.get("sigma", 1.0)),
            "calibration": {},
            "recipe": {"source": "dark_displacement_census.py:freeze_candidates"},
            "provenance": {
                **orig["provenance"],
                "role": "candidate",
                "census_capture_layer_label": f"L{lnum}",
                "census_block_index": block,
                "adapted_by": "experiments/dark-actuator-screen/build_directions.py",
                "adapted_from_schema": orig.get("schema_version"),
            },
        }
        out_path = out_dir / f"dark_cand_raw-base_{name}.json"
        out_path.write_text(json.dumps(adapted, indent=2))
        records.append({
            "candidate": name,
            "authoritative_source": str(src),
            "authoritative_sha256": _sha256_file(src),
            "staged_path": str(out_path),
            "census_layer_label": f"L{lnum}",
            "block_index": block,
        })
        print(f"[stage] {name}: layer L{lnum} -> block {block}, "
              f"src sha256 {records[-1]['authoritative_sha256'][:12]}...")
    return records


# --------------------------------------------------------------------------
# Job 2: fit positive (refuse) / negative (propensity) controls per layer
# --------------------------------------------------------------------------

def _raw_refuse_and_propensity(H_anchor: np.ndarray, y_confab: np.ndarray
                               ) -> tuple[np.ndarray, np.ndarray]:
    """Pre-QR refuse / propensity directions -- VERBATIM the math at
    dark_displacement_census.py:206-215 (build_span), before the QR mixes them
    into an orthonormal basis. Returns (refuse_unit, propensity_unit)."""
    from sklearn.preprocessing import StandardScaler

    refuse_mean = H_anchor[y_confab == 0].mean(0)
    confab_mean = H_anchor[y_confab == 1].mean(0)
    refuse_dir = unit(refuse_mean - confab_mean)

    sc = StandardScaler().fit(H_anchor)
    Z = sc.transform(H_anchor)
    clf = census.logreg().fit(Z, y_confab)
    prop_raw = clf.coef_.ravel() / sc.scale_
    prop_dir = unit(prop_raw)
    return refuse_dir, prop_dir


def fit_layer_controls(pool_root: Path, out_dir: Path) -> list[dict]:
    """Fit refuse (positive) + propensity (negative) directions at every
    SCREEN_LAYERS layer on the raw-base pool; write both as direction JSONs."""
    data_root = pool_root
    data_dir = data_root / "ak-stage1-raw-base-r1" / "data"
    tens_dir = data_root / "ak-stage1-raw-base-r1" / "tensors" / "extracted"
    rows = census.load_rows(data_dir)
    print(f"[controls] raw-base pool: {len(rows)} rows")

    records = []
    for layer in SCREEN_LAYERS:
        anchors, ys = [], []
        for r in rows:
            got = census.load_row_window(tens_dir, r, layer)
            if got is None:
                continue
            _, anchor = got
            anchors.append(anchor)
            ys.append(int(bool(r["confab_on_unanswerable"])))
        H = np.asarray(anchors, dtype=np.float64)
        y = np.asarray(ys, dtype=int)
        if H.shape[0] < 20:
            raise RuntimeError(f"too few rows with layer {layer} captures: {H.shape[0]}")
        refuse_dir, prop_dir = _raw_refuse_and_propensity(H, y)
        lnum = int(layer[1:])
        block = lnum - 1
        for role, vec, tag in (
            ("positive_control", refuse_dir, "refuse_vs_confab_mass_mean"),
            ("negative_control", prop_dir, "confab_propensity_logistic"),
        ):
            rec = {
                "schema_version": "mechinterp-direction/v1",
                "layer": block,
                "hidden_dim": int(H.shape[1]),
                "normalized": True,
                "vector": [float(v) for v in vec],
                "raw_norm": 1.0,
                "intercept": 0.0,
                "mu": [0.0] * int(H.shape[1]),
                "sigma": 1.0,
                "calibration": {"n_confab": int(y.sum()), "n_refuse": int((1 - y).sum())},
                "recipe": {
                    "source": "dark_displacement_census.py:build_span (lines 206-215, pre-QR)",
                    "seed": census.SEED,
                },
                "provenance": {
                    "role": role,
                    "signal": tag,
                    "amendment": "dark-actuator-screen",
                    "arm": "raw-base",
                    "census_capture_layer_label": layer,
                    "census_block_index": block,
                    "pool_root": str(pool_root),
                    "n_rows_used": int(H.shape[0]),
                },
            }
            name = f"{'pos_ctrl' if role == 'positive_control' else 'neg_ctrl'}_{layer}"
            out_path = out_dir / f"{name}.json"
            out_path.write_text(json.dumps(rec, indent=2))
            records.append({"name": name, "role": role, "layer_label": layer,
                             "block_index": block, "path": str(out_path)})
            print(f"[controls] {name}: layer {layer} -> block {block} "
                  f"(n_confab={int(y.sum())}, n_refuse={int((1 - y).sum())})")
    return records


# --------------------------------------------------------------------------
# Job 3: seeded random-unit-direction controls, one per candidate
# --------------------------------------------------------------------------

def _stable_subseed(name: str) -> int:
    """Deterministic per-candidate sub-seed derived from RANDOM_SEED_BASE and
    the candidate name (stable across runs/machines; not cryptographic)."""
    h = hashlib.sha256(f"{RANDOM_SEED_BASE}:{name}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def build_random_controls(candidate_records: list[dict], out_dir: Path,
                          hidden_dim: int = 2560) -> list[dict]:
    records = []
    for rec in candidate_records:
        name = rec["candidate"]
        block = rec["block_index"]
        seed = _stable_subseed(name)
        rng = np.random.default_rng(seed)
        v = rng.normal(size=hidden_dim)
        v = unit(v)
        out = {
            "schema_version": "mechinterp-direction/v1",
            "layer": block,
            "hidden_dim": hidden_dim,
            "normalized": True,
            "vector": [float(x) for x in v],
            "raw_norm": 1.0,
            "intercept": 0.0,
            "mu": [0.0] * hidden_dim,
            "sigma": 1.0,
            "calibration": {},
            "recipe": {"source": "np.random.default_rng(stable_subseed(candidate))",
                       "seed": seed, "seed_base": RANDOM_SEED_BASE},
            "provenance": {
                "role": "random_control",
                "amendment": "dark-actuator-screen",
                "paired_candidate": name,
                "census_block_index": block,
            },
        }
        out_path = out_dir / f"randctrl_{name}.json"
        out_path.write_text(json.dumps(out, indent=2))
        records.append({"name": f"randctrl_{name}", "paired_candidate": name,
                        "seed": seed, "path": str(out_path)})
        print(f"[random-control] randctrl_{name}: block {block}, seed {seed}")
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates-src", type=Path, required=True,
                    help="Authoritative census output dir holding the 12 "
                         "dark_cand_raw-base_*.json files")
    ap.add_argument("--pool-root", type=Path, required=True,
                    help="$HOME/ak_census_data (holds ak-stage1-raw-base-r1/)")
    ap.add_argument("--out", type=Path, required=True,
                    help="experiments/dark-actuator-screen/directions")
    ap.add_argument("--prep-manifest", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    args.prep_manifest.parent.mkdir(parents=True, exist_ok=True)

    cand_records = stage_candidates(args.candidates_src, args.out)
    ctrl_records = fit_layer_controls(args.pool_root, args.out)
    rand_records = build_random_controls(cand_records, args.out)

    manifest = {
        "seed_base": RANDOM_SEED_BASE,
        "authoritative_candidates_src": str(args.candidates_src),
        "authoritative_candidates_src_sha256": {
            r["candidate"]: r["authoritative_sha256"] for r in cand_records
        },
        "census_script_sha256": _sha256_file(
            THIS_DIR / "dark_displacement_census.py"
        ),
        "pool_root": str(args.pool_root),
        "pool_data_dir": str(args.pool_root / "ak-stage1-raw-base-r1" / "data"),
        "pool_tensors_dir": str(
            args.pool_root / "ak-stage1-raw-base-r1" / "tensors" / "extracted"
        ),
        "pool_tensors_tarball_ref": str(
            args.pool_root / "ak-stage1-raw-base-r1" / "tensors"
            / "ak_stage1_tensors.tar.gz"
        ),
        "candidates": cand_records,
        "controls": ctrl_records,
        "random_controls": rand_records,
        "layer_block_adapter_note": (
            "tuner-schema 'layer' field = census 'block' (lnum - 1), the "
            "0-indexed decoder module get_decoder_layer expects; NOT the "
            "census's 1-indexed capture label 'layer' (lnum)."
        ),
    }
    args.prep_manifest.write_text(json.dumps(manifest, indent=2))
    print(f"WROTE {args.prep_manifest}")
    print(f"Staged {len(cand_records)} candidates, {len(ctrl_records)} controls, "
          f"{len(rand_records)} random controls -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
