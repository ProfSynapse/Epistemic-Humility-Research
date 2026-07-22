#!/usr/bin/env python3
"""GPU preflight for margin-separation-fine-ladder (M1b) (gates.yaml
`SC1_dose_and_preflight`; cell.yaml `preflight.gpu_preflight`).

Mandatory before `generate_refined.py`. Doses the first 4 refined rows (by
lexicographic row_key, from the SC0-committed
`refined_subset_ids_qwen35_4b.json`) at EACH of the two new-rung extremes
(0.55x and 0.7x) -- the SAME 4 rows at both rung-points, mirroring M1's own
build-time interpretation ("the SAME rows across all rung-points ... a
build-time interpretation, not a spec value"). Verifies readback within
`sc1_checks.check_readback` at every dosed row. Writes
`analysis/preflight/PASS` ONLY if every row at every rung passes.

Structure adapted (logic ported) from `margin-mapping/run_margin.py::
cmd_preflight` (read in full before writing this).
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import row_pool  # noqa: E402
import dose_ladder  # noqa: E402
import sc1_checks  # noqa: E402

ANALYSIS = EXPERIMENT_DIR / "analysis"
COMMITTED = EXPERIMENT_DIR / "analysis-committed"
STAGED = ANALYSIS / "staged_inputs"
PREFLIGHT_DIR = ANALYSIS / "preflight"

FAMILY = "qwen35_4b"


def _preflight_report_path() -> Path:
    return PREFLIGHT_DIR / "preflight_report.json"


def _preflight_pass_marker_path() -> Path:
    return PREFLIGHT_DIR / "PASS"


def _preflight_row_keys(n_rows: int) -> list[str]:
    payload = common.load_json(COMMITTED / "refined_subset_ids_qwen35_4b.json")
    row_keys = sorted(payload["row_keys"])
    if len(row_keys) < n_rows:
        raise SystemExit(f"[preflight] FAIL: refined subset has only {len(row_keys)} rows, need {n_rows}.")
    return row_keys[:n_rows]


def load_c_hat_vector():
    import numpy as np

    path = STAGED / config.PINNED_INPUTS["c_hat_direction"]["dest"]
    c_hat = common.load_json(path)["vector"]
    return np.asarray(c_hat, dtype=np.float64)


def cmd_preflight(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print(
            "[preflight] this loads the model and generates on GPU (a few "
            "rows at the new-rung extremes) to verify dosing before any "
            "refined-subset generation; refusing without "
            "--i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2

    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    n_rows = args.rows
    preflight_row_keys = _preflight_row_keys(n_rows)
    qpool = row_pool.question_pool(FAMILY)
    missing = [rk for rk in preflight_row_keys if rk not in qpool]
    if missing:
        raise SystemExit(f"[preflight] FAIL: {len(missing)} preflight row_keys missing from staged question pool: {missing}")
    rows = [{"row_key": rk, **qpool[rk]} for rk in preflight_row_keys]

    c_hat = load_c_hat_vector()
    sigma = config.SIGMA_C[FAMILY]

    model_name, revision = config.SUBSTRATE[FAMILY], config.REVISION[FAMILY]
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[FAMILY])

    results: dict[str, Any] = {}
    all_passed = True
    try:
        for multiplier in config.PREFLIGHT_RUNG_MULTIPLIERS:
            setpoint = dose_ladder.rung_dose_abs(FAMILY, multiplier)
            _, gain = dose_ladder.c_hat_write_params(FAMILY, setpoint)
            rung_tag = dose_ladder.rung_tag(multiplier)
            tag = f"{FAMILY}__preflight_rung_{rung_tag}"
            log_path = PREFLIGHT_DIR / f"{tag}.jsonl"
            log = RunLog(log_path, run_config={"stage": "preflight", "family": FAMILY, "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain, "n_rows": n_rows}, fresh=True)
            hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma)
            handle = layer_module.register_forward_hook(ctrl)
            try:
                steer_lib.run_rows(model, tokenizer, device, ctrl, "gen_stream", rows, gain, config.GEN_MAX_NEW_TOKENS, n_rows, log)
                log.finalize({"n_rows": n_rows})
            finally:
                handle.remove()
                ctrl.reset()
                log.close()
            logged = common.load_jsonl(log_path)
            checks = [sc1_checks.check_readback(r["row_key"], FAMILY, r.get("readback_measured"), setpoint) for r in logged]
            passed = len(checks) == n_rows and all(c["passed"] for c in checks)
            all_passed = all_passed and passed
            n_well_formed = sum(1 for r in logged if r.get("well_formed"))
            results[str(multiplier)] = {
                "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain,
                "n_rows": len(checks), "readback_passed": passed,
                "n_well_formed": n_well_formed, "well_formed_frac": (n_well_formed / len(logged) if logged else None),
                "checks": checks,
            }
            print(f"[preflight] {FAMILY}/{multiplier}x: setpoint={setpoint} sigma={sigma} gain={gain} well_formed={n_well_formed}/{len(logged)}", flush=True)
            for c in checks:
                print(f"[preflight]   row_key={c['row_key']} readback_measured={c['readback_measured']} rel_delta={c.get('rel_delta')} passed={c['passed']}", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    report_path = _preflight_report_path()
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    report = common.load_json(report_path) if report_path.is_file() else {}
    report[FAMILY] = {
        "all_passed": all_passed,
        "n_rows": n_rows,
        "preflight_row_keys": preflight_row_keys,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "results": results,
    }
    common.write_json(report_path, report)

    if all_passed:
        _preflight_pass_marker_path().parent.mkdir(parents=True, exist_ok=True)
        _preflight_pass_marker_path().write_text(
            f"PASS written {datetime.datetime.now(datetime.timezone.utc).isoformat()} "
            f"(most recent passing family: {FAMILY}); see preflight_report.json for detail.\n",
            encoding="utf-8",
        )

    if not all_passed:
        print(f"[preflight] {FAMILY}: FAIL -- see per-row checks above; PASS marker NOT written; generate_refined.py will refuse.", file=sys.stderr)
        return 1
    print(f"[preflight] {FAMILY}: PASS -- report at {report_path}, marker at {_preflight_pass_marker_path()}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", type=int, default=config.PREFLIGHT_ROWS_DEFAULT)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    ap.set_defaults(func=cmd_preflight)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
