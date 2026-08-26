#!/usr/bin/env python3
"""Stage 4 (trained_references, CPU) for base-refusal-direction-under-contract.

Re-derives the three trained-regimen L35 h_lora refusal (caution = mean(kr) -
mean(ka)) directions using the EXACT algorithm of the pinned Section-5
provenance script
(papers/paper-3-knows-but-doesnt-say/analysis/provenance/p3_section5_provenance_20260704/
reconstruct_section5_geometry.py's `unit()` / `geometry_full()` caution/doubt
convention: mass-mean, NOT logistic; kr=known_refused, ka=known_correct_answered,
ur=unknown_refused).

*** PATH ANOMALY, FLAG FOR LEAD, NOT SELF-ADJUDICATED ***
The pinned script hardcodes ROWS/EXTRACTION under
`archive/experiment/phase1/probe/...`, which does NOT exist in this canonical
checkout (verified: `ls archive/experiment/phase1/probe/analysis/
current_selfaware_behavior_rows` -> No such file or directory). The actual
data lives under a renamed sibling, `archive/experiment/phase1-data/probe/...`
(confirmed present, including the exact `extraction__55254a04aa1f` dir the
pinned script names for SFT->GRPO-v2). This script points at the
`phase1-data` paths, which are exactly the paths the CHECKED-IN provenance
manifest `experiment/phase1/probe/analysis/current_selfaware_behavior_rows/
manifest.json` (a symlinked, tracked-lineage artifact, not something invented
here) records as `rows` / `source_rows` for all three checkpoints. This is a
stale hardcoded path in the pinned script (post-dating a `phase1` ->
`phase1-data` repo reorg), not a missing archived input -- but that reading is
NOT self-adjudicated as authorizing BR-G0; report this anomaly to the lead
before the comparison numbers below are used in any gate call.

Does NOT import or modify the pinned script; reimplements its documented
`unit`/covariance-free mass-mean logic directly against the corrected paths,
for full transparency about what ran.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

ROOT = Path(__file__).resolve().parents[3]
LAYER = "L35"

# Corrected paths (archive/experiment/phase1-data/, NOT the pinned script's
# stale archive/experiment/phase1/), taken verbatim from the checked-in
# manifest experiment/phase1/probe/analysis/current_selfaware_behavior_rows/
# manifest.json (symlink-resolved).
CHECKPOINTS = {
    "clean_sft": {
        "rows": ROOT / "archive/experiment/phase1-data/probe/analysis/"
                       "current_selfaware_behavior_rows/clean_sft_merged/rows.jsonl",
        "extraction": ROOT / "archive/experiment/phase1-data/probe/"
                             "qwen3-4b-clean-sft-seed1-selfaware/"
                             "hidden_states_selfaware_clean_sft_full/"
                             "extraction__8dbd3f623393",
    },
    "sft_grpo_dpo": {
        "rows": ROOT / "archive/experiment/phase1-data/probe/analysis/"
                       "current_selfaware_behavior_rows/clean_sft_grpo_dpo/rows.jsonl",
        "extraction": ROOT / "archive/experiment/phase1-data/probe/"
                             "qwen3-4b-clean-sft-grpo-dpo-seed1-selfaware/"
                             "hidden_states_selfaware_clean_sft_grpo_dpo_full/"
                             "extraction__00af99a2efe7",
    },
    "sft_grpo_v2": {
        "rows": ROOT / "archive/experiment/phase1-data/probe/analysis/"
                       "current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl",
        "extraction": ROOT / "archive/experiment/phase1-data/probe/"
                             "qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/"
                             "hidden_states_selfaware_clean_sft_grpo_v2_full/"
                             "extraction__55254a04aa1f",
    },
}
PATH_ANOMALY_NOTE = (
    "Pinned reconstruct_section5_geometry.py hardcodes "
    "archive/experiment/phase1/probe/... (absent in this checkout); this "
    "script uses archive/experiment/phase1-data/probe/... instead, matching "
    "the checked-in manifest experiment/phase1/probe/analysis/"
    "current_selfaware_behavior_rows/manifest.json. Flagged for lead "
    "verification, not self-adjudicated."
)


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def load_cells(rows_path: Path, extraction_dir: Path) -> tuple[np.ndarray, np.ndarray, int]:
    X, cells = [], []
    n_missing = 0
    with rows_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            key = (r.get("probe_pool_row_key") or r["row_key"]).replace("::", "__")
            p = extraction_dir / f"{key}__h_lora.safetensors"
            if not p.exists():
                n_missing += 1
                continue
            X.append(load_file(str(p))[LAYER].astype(np.float64).reshape(-1))
            cells.append(r["behavior_cell"])
    return np.stack(X), np.asarray(cells), n_missing


def caution_direction(X: np.ndarray, cells: np.ndarray) -> dict:
    kr = X[cells == "known_refused"]
    ka = X[cells == "known_correct_answered"]
    caution = kr.mean(0) - ka.mean(0)
    return {"theta": unit(caution), "n_kr": int(len(kr)), "n_ka": int(len(ka))}


def doubt_direction(X: np.ndarray, cells: np.ndarray) -> dict:
    ka = X[cells == "known_correct_answered"]
    ur = X[cells == "unknown_refused"]
    doubt = unit(ka.mean(0) - ur.mean(0))
    return {"theta": doubt, "n_ka": int(len(ka)), "n_ur": int(len(ur))}


def main() -> int:
    result: dict = {"path_anomaly": PATH_ANOMALY_NOTE, "checkpoints": {}}
    thetas: dict[str, np.ndarray] = {}
    for name, paths in CHECKPOINTS.items():
        for k, p in paths.items():
            if not p.exists():
                result["checkpoints"][name] = {
                    "br_g0_missing_archived_input": str(p),
                }
                break
        else:
            X, cells, n_missing = load_cells(paths["rows"], paths["extraction"])
            cd = caution_direction(X, cells)
            thetas[name] = cd["theta"]
            entry = {
                "rows_path": str(paths["rows"].relative_to(ROOT)),
                "extraction_dir": str(paths["extraction"].relative_to(ROOT)),
                "n_rows_loaded": int(len(X)),
                "n_missing_tensors": n_missing,
                "n_known_refused": cd["n_kr"],
                "n_known_correct_answered": cd["n_ka"],
            }
            if name == "sft_grpo_v2":
                dd = doubt_direction(X, cells)
                entry["doubt_axis_n_known_correct_answered"] = dd["n_ka"]
                entry["doubt_axis_n_unknown_refused"] = dd["n_ur"]
                thetas["sft_grpo_v2__doubt"] = dd["theta"]
            result["checkpoints"][name] = entry

    out_dir = ROOT / "experiments/base-refusal-direction-under-contract/analysis/directions"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, theta in thetas.items():
        np.save(out_dir / f"trained_ref__{name}__L35_theta.npy", theta)
    (out_dir / "trained_references_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nwrote theta vectors for: {sorted(thetas)} -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
