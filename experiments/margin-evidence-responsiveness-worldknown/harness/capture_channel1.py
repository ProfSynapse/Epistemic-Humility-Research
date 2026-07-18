#!/usr/bin/env python3
"""Channel 1 (projection collapse) capture for margin-evidence-
responsiveness-worldknown (M4-WK) (cell.yaml `channel1_projection`).

GPU (capture only, no generation). For each of the three arms
(no_answer_baseline / true_answer / false_answer_placebo), captures the hs20
anchor hidden state for every test-population row (confab 400 + correct 360
+ refused_available), via synaptic-tuner's `batch-capture` (engine
hf-batched, persist_dtype float32), mirroring `susceptibility-as-probe/
harness/capture.py` (read in full before writing this) exactly. Hidden
states are captured ONCE per arm and projected onto BOTH directions post-hoc
(a dot product) -- one capture pass per arm, two readouts.

Per-row anchor: EACH row is tokenized individually (no batch-level padding
ambiguity) via `tok(prompt, add_special_tokens=True)["input_ids"]`, position
= len(token_ids) - 1 -- byte-identical convention to M1/M2. Before the full
capture, `assert_anchor_identical_across_arms` verifies, on a sample row,
that the ANCHOR TOKEN ID is identical across all three arms (the injected
context sits BEFORE the question, so the tail of the prompt -- and hence the
anchor -- should be byte-for-byte unaffected by which arm is active).

This script computes but does NOT freeze: the transfer firing AUROC gate,
the native AUROC-reproduction gate, and the fresh baseline gap per
direction. Those numbers are written to `analysis-committed/channel1/
floor_inputs.json` for the lead to review before the SEPARATE floor-freeze
repin step (self-blinding: no true/false shift is computed by this script).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import batching  # noqa: E402
import popqa_pool  # noqa: E402
import stats  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
CHANNEL1_DIR = COMMITTED / "channel1"
CAPTURE_DIR = ANALYSIS / "channel1_capture"


def _sh(cmd: list[str]) -> None:
    print(f"[capture_channel1] $ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def load_test_population() -> dict[str, dict[str, Any]]:
    """row_key -> {role, question, context (per arm filled in by caller)}."""
    path = SELECTION_DIR / "test_population.json"
    if not path.is_file():
        raise SystemExit(f"capture_channel1 FAIL: no {path}; run selection.py first.")
    payload = common.load_json(path)
    pool = popqa_pool.load_pool()
    rows: dict[str, dict[str, Any]] = {}
    for short, row_keys in payload["row_keys"].items():
        role = {"confab": "confab", "correct": "correct_on_answerable", "refused": "refused_on_answerable"}[short]
        for rk in row_keys:
            r = pool[rk]
            rows[rk] = {"row_key": rk, "role": role, "question": r["question"], "gold": r["gold"]}
    return rows


def load_distractor_mapping() -> dict[str, str]:
    path = SELECTION_DIR / "distractor_mapping.json"
    if not path.is_file():
        raise SystemExit(f"capture_channel1 FAIL: no {path}; run distractor.py first.")
    return common.load_json(path)["mapping"]


def context_for_arm(arm: str, row: dict[str, Any], distractor_mapping: dict[str, str], pool: dict[str, dict[str, Any]]) -> str | None:
    if arm == "no_answer_baseline":
        return None
    if arm == "true_answer":
        return row["gold"]
    if arm == "false_answer_placebo":
        donor_rk = distractor_mapping[row["row_key"]]
        return pool[donor_rk]["gold"]
    raise ValueError(f"unknown arm {arm!r}")


def render_rows_for_arm(rows: list[dict[str, Any]], arm: str, distractor_mapping: dict[str, str], pool: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    os.environ["M4WK_RENDER_MODEL"] = config.MODEL_REPO
    os.environ["M4WK_RENDER_REVISION"] = config.MODEL_REVISION
    import render  # noqa: E402

    tok = render._tokenizer()
    cap_rows: list[dict[str, Any]] = []
    for row in rows:
        context = context_for_arm(arm, row, distractor_mapping, pool)
        prompt = render.render({"row_key": row["row_key"], "question": row["question"], "context": context})
        token_ids = tok(prompt, add_special_tokens=config.READOUT_ADD_SPECIAL_TOKENS)["input_ids"]
        cap_rows.append({
            "id": row["row_key"], "token_ids": token_ids,
            "positions": {"anchor": len(token_ids) - 1},
            "role": row["role"], "expected_token_count": len(token_ids),
        })
    template_sha256 = common.sha256_of_bytes(render.BASELINE_SYSTEM_PROMPT.encode("utf-8"))
    return cap_rows, template_sha256


def assert_anchor_identical_across_arms(sample_row: dict[str, Any], distractor_mapping: dict[str, str], pool: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """cell.yaml red-team M1 fix: verify the anchor TOKEN ID is identical
    across all three arms for a sample row, since context is injected
    BEFORE the question."""
    os.environ["M4WK_RENDER_MODEL"] = config.MODEL_REPO
    os.environ["M4WK_RENDER_REVISION"] = config.MODEL_REVISION
    import render  # noqa: E402

    tok = render._tokenizer()
    anchor_tokens = {}
    anchor_positions = {}
    for arm in config.ARMS:
        context = context_for_arm(arm, sample_row, distractor_mapping, pool)
        prompt = render.render({"row_key": sample_row["row_key"], "question": sample_row["question"], "context": context})
        token_ids = tok(prompt, add_special_tokens=config.READOUT_ADD_SPECIAL_TOKENS)["input_ids"]
        anchor_positions[arm] = len(token_ids) - 1
        anchor_tokens[arm] = token_ids[-1]
    identical = len(set(anchor_tokens.values())) == 1
    result = {"row_key": sample_row["row_key"], "anchor_tokens": anchor_tokens, "anchor_positions": anchor_positions, "identical": identical}
    if not identical:
        raise SystemExit(f"capture_channel1 FAIL: anchor token is NOT identical across arms for a sample row: {result}")
    print(f"[capture_channel1] anchor-identical-across-arms check PASS: {result}", flush=True)
    return result


def run_capture(cap_rows: list[dict[str, Any]], out_dir: Path, batch_size: int) -> None:
    cap_in = out_dir / "capture_rows.jsonl"
    common.write_jsonl(cap_in, cap_rows)
    _sh([
        sys.executable, str(TUNER), "batch-capture",
        "--rows", str(cap_in), "--model", config.MODEL_REPO, "--model-revision", config.MODEL_REVISION,
        "--out-dir", str(out_dir / "capture"), "--engine", config.READOUT_ENGINE,
        "--layers", str(config.TRANSFER_HS_INDEX), "--persist-dtype", config.READOUT_PERSIST_DTYPE,
        "--batch-size", str(batch_size), "--resume",
    ])


def verify_capture_integrity(cap_rows: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    index = common.load_jsonl(out_dir / "capture" / "capture.jsonl")
    index_by_id = {r["id"]: r for r in index}
    expected_ids = {r["id"] for r in cap_rows}
    captured_ids = set(index_by_id.keys())
    missing = sorted(expected_ids - captured_ids)
    extra = sorted(captured_ids - expected_ids)
    bad_position = []
    for r in cap_rows:
        rec = index_by_id.get(r["id"])
        if rec is None:
            continue
        if rec["positions"].get("anchor") != r["positions"]["anchor"]:
            bad_position.append(r["id"])
    return {
        "n_expected": len(expected_ids), "n_captured": len(captured_ids),
        "n_missing": len(missing), "missing_sample": missing[:10],
        "n_extra": len(extra), "extra_sample": extra[:10],
        "n_bad_position": len(bad_position), "bad_position_sample": bad_position[:10],
        "zero_silent_drops": len(missing) == 0 and len(extra) == 0,
        "all_positions_match": len(bad_position) == 0,
    }


def load_direction(direction: str) -> dict[str, Any]:
    if direction == "transfer":
        return common.load_json(config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / "directions" / "hs20" / "c_hat_transfer.json")
    return common.load_json(config.NATIVE_C_HAT_PATH)


def compute_raw_projections(cap_rows: list[dict[str, Any]], out_dir: Path, direction_record: dict[str, Any]) -> dict[str, float]:
    from safetensors.torch import load_file

    vector = np.asarray(direction_record["vector"], dtype=np.float64)
    mu = np.asarray(direction_record["mu"], dtype=np.float64)
    if vector.shape[0] != config.HIDDEN_DIM:
        raise SystemExit(f"capture_channel1 FAIL: direction vector dim {vector.shape[0]} != {config.HIDDEN_DIM}")

    index = common.load_jsonl(out_dir / "capture" / "capture.jsonl")
    key = f"anchor__L{config.TRANSFER_HS_INDEX}"
    out: dict[str, float] = {}
    for rec in index:
        tensors = load_file(str(out_dir / "capture" / rec["file"]))
        if key not in tensors:
            raise SystemExit(f"capture_channel1 FAIL: row {rec['id']!r} missing tensor key {key!r}")
        h = tensors[key].to(dtype=__import__("torch").float32).numpy().astype(np.float64)
        out[rec["id"]] = float(np.dot(h - mu, vector))
    return out


def capture_all_arms(rows: dict[str, dict[str, Any]], distractor_mapping: dict[str, str], pool: dict[str, dict[str, Any]], batch_size: int, out_root: Path) -> dict[str, dict[str, float]]:
    """Returns {arm: {row_key: raw_projection_on_TRANSFER_direction_vector}}
    -- but the raw hidden state is captured once and BOTH directions'
    projections are computed from the same tensors, so this returns
    {arm: {direction: {row_key: raw_proj}}}."""
    ordered_keys = batching.canonical_order(list(rows.keys()))
    ordered_rows = [rows[rk] for rk in ordered_keys]

    raw_by_arm_direction: dict[str, dict[str, dict[str, float]]] = {}
    for arm in config.ARMS:
        cap_rows, template_sha256 = render_rows_for_arm(ordered_rows, arm, distractor_mapping, pool)
        out_dir = out_root / arm
        out_dir.mkdir(parents=True, exist_ok=True)
        run_capture(cap_rows, out_dir, batch_size)
        integrity = verify_capture_integrity(cap_rows, out_dir)
        if not integrity["zero_silent_drops"] or not integrity["all_positions_match"]:
            raise SystemExit(f"capture_channel1 FAIL ({arm}): integrity check failed: {json.dumps(integrity, indent=2)}")
        # cap_rows key their row identity as "id" (tuner batch-capture's own
        # row schema); batch_composition_record expects "row_key" -- rename
        # on the way in, order/content otherwise untouched.
        composition_rows = [{"row_key": r["id"]} for r in cap_rows]
        common.write_json(out_dir / "capture_manifest.json", {"template_sha256": template_sha256, "integrity": integrity, "composition": batching.batch_composition_record(composition_rows, batch_size)})

        raw_by_arm_direction[arm] = {}
        for direction in config.DIRECTIONS:
            direction_record = load_direction(direction)
            raw_by_arm_direction[arm][direction] = compute_raw_projections(cap_rows, out_dir, direction_record)
        print(f"[capture_channel1] arm={arm}: captured + projected {len(cap_rows)} rows onto {list(config.DIRECTIONS)}", flush=True)
    return raw_by_arm_direction


def registered_score(raw_proj: float, direction: str) -> float:
    """registered score = SIGN * (raw_proj - mu_c) / sigma_c, per direction
    (cell.yaml `readout.score` + `directions.<dir>.snap_standardization`).
    TRANSFER's mu_c/sigma_c are sign-time-known cell.yaml constants
    (hardcoded in config.py: TRANSFER_MU_C/TRANSFER_SIGMA_C). NATIVE's are
    RE_DERIVED at the direction-fit stage (cell.yaml: "frozen at the
    direction-fit repin") and read at RUNTIME from the produced
    c_hat_worldknown.json's own `calibration.mu_c`/`calibration.sigma_c`
    (fit_native.py writes these there at fit time); cell.yaml itself is
    separately repinned with the same concrete numbers as the governance
    record, mirroring how dose_ladder.py's `_native_sigma_c()` already reads
    the RE_DERIVED sigma from this same produced file rather than from
    cell.yaml directly."""
    if direction == "transfer":
        mu_c, sigma_c = config.TRANSFER_MU_C, config.TRANSFER_SIGMA_C
    else:
        record = common.load_json(config.NATIVE_C_HAT_PATH)
        calibration = record.get("calibration") or {}
        if "mu_c" not in calibration or "sigma_c" not in calibration:
            raise SystemExit(
                f"registered_score FAIL: native c_hat record at "
                f"{config.NATIVE_C_HAT_PATH} has no calibration.mu_c/"
                f"calibration.sigma_c; fit_native.py must write these at fit time."
            )
        mu_c, sigma_c = calibration["mu_c"], calibration["sigma_c"]
    z = (raw_proj - mu_c) / sigma_c
    return config.READOUT_SIGN[direction] * z


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", type=int, default=None, help="cap population to first N rows per arm (smoke)")
    ap.add_argument("--batch-size", type=int, default=config.READOUT_CAPTURE_BATCH_SIZE)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    args = ap.parse_args()

    if not args.i_know_this_runs_on_gpu:
        print("[capture_channel1] this loads the model and runs forward passes on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    config.assert_pinned_hashes()

    rows = load_test_population()
    distractor_mapping = load_distractor_mapping()
    pool = popqa_pool.load_pool()

    if args.rows is None:
        marker_path = config.EXPERIMENT_DIR / config.PREFLIGHT_PASS_MARKER
        if not marker_path.is_file():
            raise SystemExit(f"capture_channel1 FAIL: full capture requested but no preflight PASS marker at {marker_path}; run preflight.py first.")
        marker = common.load_json(marker_path)
        if not marker.get("pass"):
            raise SystemExit("capture_channel1 FAIL: preflight PASS marker records pass=False.")

    sample_row = next(iter(rows.values()))
    assert_anchor_identical_across_arms(sample_row, distractor_mapping, pool)

    if args.rows is not None:
        ordered = batching.canonical_order(list(rows.keys()))[: args.rows]
        rows = {rk: rows[rk] for rk in ordered}
        out_root = ANALYSIS / "preflight" / "channel1_capture_smoke"
    else:
        out_root = CAPTURE_DIR

    raw = capture_all_arms(rows, distractor_mapping, pool, args.batch_size, out_root)

    if args.rows is not None:
        print(json.dumps({"smoke_rows": len(rows), "arms_captured": list(raw.keys())}, indent=2), flush=True)
        return 0

    # ---- Post-capture: per-row registered scores, both directions -------
    per_row_scores: list[dict[str, Any]] = []
    for rk, row in rows.items():
        rec = {"row_key": rk, "role": row["role"]}
        for arm in config.ARMS:
            for direction in config.DIRECTIONS:
                rec[f"{arm}__{direction}_z"] = registered_score(raw[arm][direction][rk], direction)
        per_row_scores.append(rec)
    CHANNEL1_DIR.mkdir(parents=True, exist_ok=True)
    common.write_jsonl(CHANNEL1_DIR / "per_row_projections.jsonl", sorted(per_row_scores, key=lambda r: r["row_key"]))

    # ---- Gates: transfer firing AUROC + native AUROC reproduction -------
    confab_scores = {d: np.array([r[f"no_answer_baseline__{d}_z"] for r in per_row_scores if r["role"] == "confab"]) for d in config.DIRECTIONS}
    correct_scores = {d: np.array([r[f"no_answer_baseline__{d}_z"] for r in per_row_scores if r["role"] == "correct_on_answerable"]) for d in config.DIRECTIONS}

    gate_results: dict[str, Any] = {}
    for direction in config.DIRECTIONS:
        labels = np.array([1] * len(confab_scores[direction]) + [0] * len(correct_scores[direction]))
        scores = np.concatenate([confab_scores[direction], correct_scores[direction]])
        auroc_ci = stats.bootstrap_auroc_ci(scores, labels, seed=config.BOOTSTRAP_SEED)
        baseline_gap = float(np.median(confab_scores[direction]) - np.median(correct_scores[direction]))
        gate_results[direction] = {
            "baseline_auroc_confab_vs_correct": auroc_ci,
            "baseline_gap_z": baseline_gap,
            "baseline_gap_positive": baseline_gap > 0.0,
            "collapse_floor_z_if_frozen_now": config.COLLAPSE_FLOOR_FRACTION * baseline_gap,
        }
    transfer_fires = gate_results["transfer"]["baseline_auroc_confab_vs_correct"]["point"] >= config.TRANSFER_FIRING_AUROC_FLOOR

    native_manifest_path = COMMITTED / "directions" / "hs20" / "native_direction_build_manifest.json"
    native_fit_auroc = None
    native_reproduction = None
    if native_manifest_path.is_file():
        native_manifest = common.load_json(native_manifest_path)
        native_fit_auroc = native_manifest.get("auc_confab_vs_known_fit_split_negz")
        test_auroc = gate_results["native"]["baseline_auroc_confab_vs_correct"]["point"]
        if native_fit_auroc is not None:
            native_reproduction = {
                "fit_split_auroc": native_fit_auroc, "test_auroc": test_auroc,
                "abs_diff": abs(test_auroc - native_fit_auroc),
                "within_tolerance": abs(test_auroc - native_fit_auroc) <= config.NATIVE_AUROC_REPRODUCTION_TOLERANCE,
            }

    floor_inputs = {
        "transfer_firing_gate": {"floor": config.TRANSFER_FIRING_AUROC_FLOOR, "observed_auroc": gate_results["transfer"]["baseline_auroc_confab_vs_correct"]["point"], "fires": transfer_fires},
        "native_auroc_reproduction": native_reproduction,
        "per_direction": gate_results,
        "note": "NO true/false shift is computed here (self-blinding). Floor numerics above are PROPOSED (if_frozen_now); the actual freeze is a separate repin step reviewed before proceeding.",
    }
    CHANNEL1_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(CHANNEL1_DIR / "floor_inputs.json", floor_inputs)
    print(json.dumps(floor_inputs, indent=2), flush=True)

    if not transfer_fires:
        print(
            f"[capture_channel1] TRANSFER FIRING FLOOR NOT MET: observed AUROC "
            f"{gate_results['transfer']['baseline_auroc_confab_vs_correct']['point']:.4f} < "
            f"{config.TRANSFER_FIRING_AUROC_FLOOR}. Per BLOCKER B1 / falsifier: this VOIDS "
            f"the primary (d) test and lifts to PI; it is NOT a (d)-not-earned failure. "
            f"Halting before any floor freeze or shift computation.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
