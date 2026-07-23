#!/usr/bin/env python3
"""Mandatory GPU preflight for margin-evidence-responsiveness-worldknown
(M4-WK) (lead dispatch RUN PLAN step 4; cell.yaml `preflight`). An 8-row
CAPTURE smoke (channel-1's own pathway, all 3 arms x both directions) and an
8-row GENERATION smoke (channel-2's erase-write dosing pathway, one
reference-dose pass per direction), both manifest-checked, MUST pass before
any full channel-1 or channel-2 run. Writes the code-enforced pass marker
`analysis/preflight/PASS.json` that `capture_channel1.py` (full-population
mode) refuses to run without.

Requires the native direction to already be fit (RUN PLAN step 3) -- this is
run AFTER fit_native.py, not before, so both directions' c_hat vectors exist.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import batching  # noqa: E402
import popqa_pool  # noqa: E402
import dose_ladder  # noqa: E402
import sc1_checks  # noqa: E402
import capture_channel1 as capture_mod  # noqa: E402

PREFLIGHT_DIR = config.EXPERIMENT_DIR / "analysis" / "preflight"


def _is_finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Capture smoke: channel-1's own pathway, 3 arms x 2 directions, N rows.
# ---------------------------------------------------------------------------

def run_capture_smoke() -> dict:
    out_dir = PREFLIGHT_DIR / "capture_smoke"
    rows = capture_mod.load_test_population()
    distractor_mapping = capture_mod.load_distractor_mapping()
    pool = popqa_pool.load_pool()

    ordered_keys = batching.canonical_order(list(rows.keys()))[: config.PREFLIGHT_CAPTURE_SMOKE_ROWS]
    smoke_rows = {rk: rows[rk] for rk in ordered_keys}

    sample_row = next(iter(smoke_rows.values()))
    anchor_check = capture_mod.assert_anchor_identical_across_arms(sample_row, distractor_mapping, pool)

    raw = capture_mod.capture_all_arms(smoke_rows, distractor_mapping, pool, config.PREFLIGHT_CAPTURE_SMOKE_ROWS, out_dir)

    import torch
    from safetensors.torch import load_file

    per_arm_checks = {}
    for arm in config.ARMS:
        manifest = common.load_json(out_dir / arm / "capture_manifest.json")
        integrity = manifest["integrity"]
        index = common.load_jsonl(out_dir / arm / "capture" / "capture.jsonl")
        key = f"anchor__L{config.TRANSFER_HS_INDEX}"
        dtype_checks, shape_checks = [], []
        for rec in index:
            tensors = load_file(str(out_dir / arm / "capture" / rec["file"]))
            t = tensors[key]
            dtype_checks.append(t.dtype == torch.float32)
            shape_checks.append(t.shape[-1] == config.HIDDEN_DIM)
        per_arm_checks[arm] = {
            "n_captured": integrity["n_captured"],
            "zero_silent_drops": integrity["zero_silent_drops"],
            "all_positions_match": integrity["all_positions_match"],
            "all_tensors_fp32": all(dtype_checks) and len(dtype_checks) == len(smoke_rows),
            "all_shapes_hidden_dim": all(shape_checks) and len(shape_checks) == len(smoke_rows),
        }

    readout_finite = {}
    for direction in config.DIRECTIONS:
        scores = [
            capture_mod.registered_score(raw[arm][direction][rk], direction)
            for arm in config.ARMS for rk in smoke_rows
        ]
        readout_finite[direction] = all(_is_finite(s) for s in scores) and len(scores) == len(config.ARMS) * len(smoke_rows)

    checks = {
        "n_smoke_rows": len(smoke_rows),
        "anchor_identical_across_arms": anchor_check["identical"],
        "anchor_check_detail": anchor_check,
        "layer_index_matches_cell_yaml_19": config.TRANSFER_LAYER_INDEX == 19 and config.NATIVE_LAYER_INDEX == 19,
        "per_arm": per_arm_checks,
        "readout_scores_finite_by_direction": readout_finite,
    }
    checks["pass"] = bool(
        checks["anchor_identical_across_arms"]
        and checks["layer_index_matches_cell_yaml_19"]
        and all(c["zero_silent_drops"] and c["all_positions_match"] and c["all_tensors_fp32"] and c["all_shapes_hidden_dim"] for c in per_arm_checks.values())
        and all(readout_finite.values())
    )
    common.write_json(out_dir / "smoke_check.json", checks)
    return checks


# ---------------------------------------------------------------------------
# Generation smoke: channel-2's erase-write dosing pathway, N rows per
# direction, single reference-dose (1.0x) pass, readback-checked.
# ---------------------------------------------------------------------------

def _rows_for_generation_smoke(pool: dict, row_keys: list[str]) -> list[dict]:
    out = []
    for rk in row_keys:
        r = pool[rk]
        out.append({"row_key": rk, "question": r["question"], "aliases": r["aliases"], "category_canon": r["category"], "role": None, "split": "preflight_smoke", "source": "popqa"})
    return out


def run_generation_smoke() -> dict:
    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    out_dir = PREFLIGHT_DIR / "generation_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    pool = popqa_pool.load_pool()
    ordered_keys = batching.canonical_order(list(pool.keys()))[: config.PREFLIGHT_GENERATION_SMOKE_ROWS]
    rows = _rows_for_generation_smoke(pool, ordered_keys)

    model, tokenizer, device = steer_lib.load_model(config.MODEL_REPO, config.MODEL_REVISION)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX)

    results: dict = {}
    all_passed = True
    try:
        for direction in config.DIRECTIONS:
            setpoint = dose_ladder.rung_dose_abs(direction, 1.0)
            sigma, gain = dose_ladder.c_hat_write_params(direction, setpoint)
            direction_record = capture_mod.load_direction(direction)
            vector = torch.tensor(direction_record["vector"], dtype=torch.float32)

            tag = f"{direction}__preflight_generation_smoke"
            log_path = out_dir / f"{tag}.jsonl"
            log = RunLog(log_path, run_config={"stage": "preflight_generation_smoke", "direction": direction, "setpoint": setpoint, "sigma": sigma, "gain": gain, "n_rows": len(rows)}, fresh=True)
            hook, ctrl = steer_lib.build_hook_and_controller(vector, sigma)
            handle = layer_module.register_forward_hook(ctrl)
            try:
                steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows, gain, config.GEN_MAX_NEW_TOKENS, len(rows), log)
                log.finalize({"n_rows": len(rows)})
            finally:
                handle.remove()
                ctrl.reset()
                log.close()

            logged = common.load_jsonl(log_path)
            checks = [
                sc1_checks.check_readback(r["row_key"], direction, r.get("readback_measured"), setpoint, setpoint)
                for r in logged
            ]
            passed = len(checks) == len(rows) and all(c["passed"] for c in checks)
            all_passed = all_passed and passed
            results[direction] = {
                "setpoint": setpoint, "sigma": sigma, "gain": gain,
                "n_rows": len(checks), "readback_passed": passed, "checks": checks,
            }
            print(f"[preflight] generation_smoke direction={direction}: setpoint={setpoint} sigma={sigma} gain={gain} readback_passed={passed}", flush=True)
            for c in checks:
                print(f"[preflight]   row_key={c['row_key']} readback_measured={c.get('readback_measured')} passed={c['passed']}", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    checks_out = {"n_smoke_rows": len(rows), "per_direction": results, "pass": bool(all_passed)}
    common.write_json(out_dir / "smoke_check.json", checks_out)
    return checks_out


def main() -> int:
    ap_argv = sys.argv[1:]
    if "--i-know-this-runs-on-gpu" not in ap_argv:
        print("[preflight] this loads the model and runs capture+generation smokes on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    config.assert_pinned_hashes()
    if not config.NATIVE_C_HAT_PATH.is_file():
        raise SystemExit(f"preflight FAIL: native direction not yet fit ({config.NATIVE_C_HAT_PATH} missing); run fit_native.py first (RUN PLAN step 3 precedes step 4).")

    capture_checks = run_capture_smoke()
    generation_checks = run_generation_smoke()

    overall_pass = bool(capture_checks["pass"] and generation_checks["pass"])
    marker = {"pass": overall_pass, "capture_smoke": capture_checks, "generation_smoke": generation_checks}
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(PREFLIGHT_DIR / "PASS.json", marker)

    print(json.dumps({"capture_smoke_pass": capture_checks["pass"], "generation_smoke_pass": generation_checks["pass"], "overall_pass": overall_pass}, indent=2), flush=True)

    if not overall_pass:
        raise SystemExit(f"preflight FAILED: capture_pass={capture_checks['pass']} generation_pass={generation_checks['pass']}; PASS marker written with pass=False, full channel-1/channel-2 runs remain blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
