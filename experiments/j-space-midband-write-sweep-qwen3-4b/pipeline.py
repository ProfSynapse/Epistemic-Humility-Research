#!/usr/bin/env python3
"""Run the J-space mid-band write sweep locally on the 3090.

This is a causal layer-site test. Each candidate layer has its own FIT-only
doubt gate and c_hat write direction. HELD-OUT rows are generated once per
layer under the same gated erase-write law. The primary contrast is best
mid-band layer hs=23/26/29 versus late reference hs=34.
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
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

sys.path.insert(0, str(HERE))
import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from layers import HS_INDICES, LATE_REFERENCE_HS, layer_dir_name  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402

EXTRACT_TENSORS = ANALYSIS / "layer_sweep_anchor_extract.safetensors"
ROWS_WITH_TEXT = ANALYSIS / "rows_with_text.jsonl"
BUILD_MANIFEST_PATH = COMMITTED / "build_manifest_layers.json"
GATE_FIT_PATH = COMMITTED / "gate_fit_layers.json"

DOSE_TARGET_DEFAULT = 200.0
MAX_NEW = gl.MAX_NEW_CAP


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def tensor_key(hs_index: int, row_key: str) -> str:
    return f"hs{hs_index}__{_sanitize_key(row_key)}"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.open(encoding="utf-8") if ln.strip()]


def load_direction_vector(path: Path) -> np.ndarray:
    data = json.loads(path.read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def layer_paths(hs_index: int) -> dict[str, Path]:
    layer_name = layer_dir_name(hs_index)
    root = COMMITTED / "layers" / layer_name
    return {
        "u_d": root / f"u_d_{layer_name}.json",
        "c_hat": root / f"c_hat_{layer_name}.json",
        "random_direction": root / f"random_direction_{layer_name}.json",
    }


def load_rows(role: str, split: str) -> list[dict]:
    return [r for r in load_jsonl(ROWS_WITH_TEXT) if r["role"] == role and r["split"] == split]


def stratified_subset(rows: list[dict], n: int) -> list[dict]:
    by_cat: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in sorted(rows, key=lambda rec: rec["row_key"]):
        cat = r.get("category_canon")
        if cat not in by_cat:
            by_cat[cat] = []
            order.append(cat)
        by_cat[cat].append(r)
    out: list[dict] = []
    idx = 0
    while len(out) < n:
        added = False
        for cat in order:
            if idx < len(by_cat[cat]):
                out.append(by_cat[cat][idx])
                added = True
                if len(out) >= n:
                    break
        if not added:
            break
        idx += 1
    return out[:n]


def compute_gate_decisions(rows: list[dict], hs_index: int) -> list[dict]:
    tensors = __import__("safetensors.numpy", fromlist=["load_file"]).load_file(str(EXTRACT_TENSORS))
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors.items()}
    layer_name = layer_dir_name(hs_index)
    u_d = load_direction_vector(layer_paths(hs_index)["u_d"])
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


def run_one_row(model, controller, tokenizer, dev, row: dict, strength_if_dosed: float) -> dict:
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, max_new=MAX_NEW
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    if row["fire"]:
        dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
            model, controller, enc, "gen_stream", strength_if_dosed, tokenizer, max_new=MAX_NEW
        )
        out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
        n_new = int(dosed_new.shape[0])
    else:
        out_text = base_text
        readback = None
        terminated_naturally = base_terminated
        n_new = int(base_new.shape[0])

    ct = gl.grade_clean_tighten(out_text, terminated_naturally)
    old_grade = grader.grade_one(out_text, row.get("aliases"))
    return {
        "row_key": row["row_key"],
        "role": row["role"],
        "category_canon": row.get("category_canon"),
        "hs_index": row["hs_index"],
        "fire": row["fire"],
        "readback_measured": readback,
        "n_new_tokens": n_new,
        "terminated_naturally": terminated_naturally,
        "clean_tighten": ct["clean_tighten"],
        "semantic_refuse": ct["semantic_refuse"],
        "well_formed_correct": old_grade["well_formed_correct"],
        "not_well_formed_correct": not old_grade["well_formed_correct"],
        "grade": ct,
        "old_grade": old_grade,
    }


def grade_population(records: list[dict], metric: str) -> dict:
    n = len(records)
    successes = sum(1 for r in records if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def run_layer(model, tokenizer, hs_index: int, rows: list[dict], dose_target: float) -> dict:
    layer_name = layer_dir_name(hs_index)
    build = json.loads(BUILD_MANIFEST_PATH.read_text())["layers"][layer_name]
    strength = dose_target / build["sigma_c"]
    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(layer_paths(hs_index)["c_hat"])
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)
    try:
        records = [run_one_row(model, controller, tokenizer, dev, r, strength) for r in rows]
    finally:
        h_ctrl.remove()
        controller.reset()
    confab = [r for r in records if r["role"] == "confab"]
    known = [r for r in records if r["role"] == "known_correct_answered"]
    dosed = [r for r in records if r["fire"]]
    readbacks = [r["readback_measured"] for r in dosed if r["readback_measured"] is not None]
    within = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    return {
        "hs_index": hs_index,
        "n_rows": len(records),
        "n_fired": len(dosed),
        "readback_mean": float(np.mean(readbacks)) if readbacks else None,
        "frac_readback_within_tol": (sum(within) / len(within)) if within else None,
        "collapse_rate_on_dosed": (
            sum(1 for r in dosed if r["grade"]["degenerate"]) / len(dosed)
            if dosed else None
        ),
        "confab_tighten": grade_population(confab, "clean_tighten"),
        "known_correct_cost_control": grade_population(known, "not_well_formed_correct"),
    }


def evaluate_layer_contrast(layer_results: dict[str, dict]) -> dict:
    late_name = layer_dir_name(LATE_REFERENCE_HS)
    late = layer_results[late_name]
    mid_names = [layer_dir_name(h) for h in HS_INDICES if h != LATE_REFERENCE_HS]
    best_mid_name = max(
        mid_names,
        key=lambda name: layer_results[name]["confab_tighten"]["rate"],
    )
    best_mid = layer_results[best_mid_name]
    tighten_delta = best_mid["confab_tighten"]["rate"] - late["confab_tighten"]["rate"]
    cost_delta = (
        best_mid["known_correct_cost_control"]["rate"]
        - late["known_correct_cost_control"]["rate"]
    )
    return {
        "best_mid_layer": best_mid_name,
        "late_reference_layer": late_name,
        "tighten_delta_best_mid_minus_late": tighten_delta,
        "cost_delta_best_mid_minus_late": cost_delta,
        "g1_midband_superiority_pass": tighten_delta >= 0.10,
        "g2_no_cost_regression_pass": cost_delta <= 0.02,
    }


def selected_rows(n_rows: int | None) -> list[dict]:
    confab = load_rows("confab", "held_out")
    known = load_rows("known_correct_answered", "held_out")
    if n_rows is None:
        return confab + known
    n_confab = n_rows // 2
    n_known = n_rows - n_confab
    return stratified_subset(confab, n_confab) + stratified_subset(known, n_known)


def run_smoke(n_rows: int, dose_target: float) -> dict:
    base_rows = selected_rows(n_rows)
    model, tokenizer = ml.load_model()
    try:
        layer_results = {}
        for hs_index in HS_INDICES:
            rows = compute_gate_decisions(base_rows, hs_index)
            layer_results[layer_dir_name(hs_index)] = run_layer(
                model, tokenizer, hs_index, rows, dose_target
            )
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    summary = {"mode": "smoke", "dose_target": dose_target, "layers": layer_results}
    out = ANALYSIS / "smoke_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


def run_full(dose_target: float) -> dict:
    base_rows = selected_rows(None)
    rng = pyrandom.Random(20260707)
    rng.shuffle(base_rows)
    model, tokenizer = ml.load_model()
    try:
        layer_results = {}
        for hs_index in HS_INDICES:
            rows = compute_gate_decisions(base_rows, hs_index)
            layer_results[layer_dir_name(hs_index)] = run_layer(
                model, tokenizer, hs_index, rows, dose_target
            )
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    summary = {
        "mode": "full",
        "dose_target": dose_target,
        "layers": layer_results,
        "layer_contrast": evaluate_layer_contrast(layer_results),
    }
    out = ANALYSIS / "full_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    parser.add_argument("--dose", type=float, default=DOSE_TARGET_DEFAULT)
    parser.add_argument("--i-know-this-is-the-confirmatory-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "smoke":
        run_smoke(args.n_rows, args.dose)
        return 0

    if not args.i_know_this_is_the_confirmatory_run:
        print(
            "[pipeline] full mode is the signed held-out run; refusing without "
            "--i-know-this-is-the-confirmatory-run",
            file=sys.stderr,
        )
        return 2
    run_full(args.dose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
