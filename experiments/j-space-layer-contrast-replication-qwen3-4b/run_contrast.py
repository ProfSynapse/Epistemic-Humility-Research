#!/usr/bin/env python3
"""Fresh-pool replication of the calibrated J-space layer contrast.

This reuses the predecessor's frozen per-layer directions, gates, and calibrated
doses, but computes gate decisions on a freshly mined private eval pool. It
commits only aggregate summaries.
"""

from __future__ import annotations

import argparse
import gc
import json
import random as pyrandom
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
CALIBRATION = HERE.parent / "j-space-midband-dose-calibration-qwen3-4b"
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

for p in (str(SOURCE),):
    if p not in sys.path:
        sys.path.insert(0, p)

from layers import HS_INDICES, LATE_REFERENCE_HS, layer_dir_name  # noqa: E402
from model_lib import load_model  # noqa: E402
from pipeline import load_direction_vector, run_layer, stratified_subset  # noqa: E402

FRESH_ROWS = ANALYSIS / "fresh_eval_rows.jsonl"
FRESH_EXTRACT_TENSORS = ANALYSIS / "fresh_anchor_extract.safetensors"
SOURCE_COMMITTED = SOURCE / "analysis-committed"
BUILD_MANIFEST_PATH = SOURCE_COMMITTED / "build_manifest_layers.json"
GATE_FIT_PATH = SOURCE_COMMITTED / "gate_fit_layers.json"

EXPECTED_SELECTED_DOSES = {
    "hs23": 25.0,
    "hs26": 75.0,
    "hs29": 125.0,
    "hs34": 175.0,
}


def sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{sanitize_key(row_key)}"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def source_layer_paths(hs_index: int) -> dict[str, Path]:
    layer_name = layer_dir_name(hs_index)
    root = SOURCE_COMMITTED / "layers" / layer_name
    return {
        "u_d": root / f"u_d_{layer_name}.json",
        "c_hat": root / f"c_hat_{layer_name}.json",
    }


def load_selected_doses() -> dict[str, float]:
    path = CALIBRATION / "analysis-committed" / "dose_calibration_summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    selected = {str(k): float(v) for k, v in data["selected_doses"].items()}
    if selected != EXPECTED_SELECTED_DOSES:
        raise ValueError(
            "calibration selected_doses drifted; expected "
            f"{EXPECTED_SELECTED_DOSES}, got {selected}"
        )
    if not data.get("all_layers_have_usable_dose"):
        raise ValueError("calibration summary says not all layers have usable doses")
    if not data.get("collapsed_at_200_recovered"):
        raise ValueError("calibration summary says dose-200 collapse was not recovered")
    return selected


def compute_gate_decisions(rows: list[dict], hs_index: int) -> list[dict]:
    tensors = __import__("safetensors.numpy", fromlist=["load_file"]).load_file(
        str(FRESH_EXTRACT_TENSORS)
    )
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors.items()}
    layer_name = layer_dir_name(hs_index)
    u_d = load_direction_vector(source_layer_paths(hs_index)["u_d"])
    build = json.loads(BUILD_MANIFEST_PATH.read_text())["layers"][layer_name]
    gate = json.loads(GATE_FIT_PATH.read_text())["layers"][layer_name]
    mu_d, sigma_d, tau = build["mu_d"], build["sigma_d"], gate["tau_frozen"]

    out = []
    for row in rows:
        h = fresh[tensor_key(hs_index, row["row_key"])]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        score = -z_d
        rec = dict(row)
        rec.update({
            "hs_index": hs_index,
            "proj_d": proj_d,
            "z_d": z_d,
            "score_neg_z_d": score,
            "tau": tau,
            "fire": bool(score >= tau),
        })
        out.append(rec)
    return out


def selected_rows(n_rows: int | None) -> list[dict]:
    rows = load_jsonl(FRESH_ROWS)
    confab = [r for r in rows if r["role"] == "confab"]
    known = [r for r in rows if r["role"] == "known_correct_answered"]
    if n_rows is None:
        return confab + known
    n_confab = n_rows // 2
    n_known = n_rows - n_confab
    return stratified_subset(confab, n_confab) + stratified_subset(known, n_known)


def run_layers(rows: list[dict], selected_doses: dict[str, float]) -> dict[str, dict]:
    model, tokenizer = load_model()
    try:
        layer_results: dict[str, dict] = {}
        for hs_index in HS_INDICES:
            layer_name = layer_dir_name(hs_index)
            dose = selected_doses[layer_name]
            print(f"[replication] layer={layer_name} dose={dose}", flush=True)
            gate_rows = compute_gate_decisions(rows, hs_index)
            rec = run_layer(model, tokenizer, hs_index, gate_rows, dose)
            rec["dose_target"] = dose
            layer_results[layer_name] = rec
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    return layer_results


def evaluate_layer_contrast(layer_results: dict[str, dict]) -> dict:
    late_name = layer_dir_name(LATE_REFERENCE_HS)
    late = layer_results[late_name]
    mid_names = [layer_dir_name(h) for h in HS_INDICES if h != LATE_REFERENCE_HS]
    best_mid_name = max(
        mid_names,
        key=lambda name: (
            layer_results[name]["confab_tighten"]["rate"],
            -layer_results[name]["known_correct_cost_control"]["rate"],
        ),
    )
    best_mid = layer_results[best_mid_name]
    tighten_delta = best_mid["confab_tighten"]["rate"] - late["confab_tighten"]["rate"]
    cost_delta = (
        best_mid["known_correct_cost_control"]["rate"]
        - late["known_correct_cost_control"]["rate"]
    )
    late_ci_lo = late["confab_tighten"]["wilson_ci_95"][0]
    return {
        "best_mid_layer": best_mid_name,
        "late_reference_layer": late_name,
        "tighten_delta_best_mid_minus_late": tighten_delta,
        "cost_delta_best_mid_minus_late": cost_delta,
        "g1_midband_superiority_pass": tighten_delta >= 0.10,
        "g2_no_cost_regression_pass": cost_delta <= 0.02,
        "g3_predecessor_reference_viable_pass": (
            late["confab_tighten"]["rate"] >= 0.60 and late_ci_lo > 0.50
        ),
    }


def g0_smoke_pass(layer_results: dict[str, dict]) -> bool:
    for rec in layer_results.values():
        if rec["frac_readback_within_tol"] != 1.0:
            return False
        if rec["collapse_rate_on_dosed"] != 0.0:
            return False
    return True


def write_summary(name: str, summary: dict, commit_public: bool) -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    (ANALYSIS / name).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if commit_public:
        COMMITTED.mkdir(parents=True, exist_ok=True)
        (COMMITTED / name).write_text(json.dumps(summary, indent=2), encoding="utf-8")


def pool_counts() -> dict:
    rows = load_jsonl(FRESH_ROWS)
    return {
        "confab": sum(1 for r in rows if r["role"] == "confab"),
        "known_correct_answered": sum(
            1 for r in rows if r["role"] == "known_correct_answered"
        ),
        "total": len(rows),
    }


def run_smoke(n_rows: int) -> dict:
    selected_doses = load_selected_doses()
    rows = selected_rows(n_rows)
    layer_results = run_layers(rows, selected_doses)
    summary = {
        "mode": "smoke",
        "selected_doses": selected_doses,
        "pool_counts": pool_counts(),
        "n_rows": len(rows),
        "layers": layer_results,
        "g0_smoke_pass": g0_smoke_pass(layer_results),
    }
    write_summary("smoke_summary.json", summary, commit_public=False)
    print(json.dumps(summary, indent=2))
    return summary


def run_full() -> dict:
    selected_doses = load_selected_doses()
    rows = selected_rows(None)
    rng = pyrandom.Random(20260708)
    rng.shuffle(rows)
    layer_results = run_layers(rows, selected_doses)
    contrast = evaluate_layer_contrast(layer_results)
    summary = {
        "mode": "full",
        "selected_doses": selected_doses,
        "pool_counts": pool_counts(),
        "n_rows": len(rows),
        "layers": layer_results,
        "layer_contrast": contrast,
        "overall_pass": bool(
            g0_smoke_pass(layer_results)
            and contrast["g1_midband_superiority_pass"]
            and contrast["g2_no_cost_regression_pass"]
            and contrast["g3_predecessor_reference_viable_pass"]
        ),
    }
    write_summary("full_summary.json", summary, commit_public=True)
    print(json.dumps(summary, indent=2))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    parser.add_argument("--i-know-this-is-the-fresh-replication-run", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "smoke":
        return 0 if run_smoke(args.n_rows)["g0_smoke_pass"] else 4

    if not args.i_know_this_is_the_fresh_replication_run:
        print(
            "[replication] full mode is the signed fresh replication run; refusing "
            "without --i-know-this-is-the-fresh-replication-run",
            file=sys.stderr,
        )
        return 2
    run_full()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
