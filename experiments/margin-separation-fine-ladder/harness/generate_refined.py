#!/usr/bin/env python3
"""Generation runner for margin-separation-fine-ladder (M1b): the 4 new rungs
over the 53-row refined subset (cell.yaml `ladder`/`population`; gates.yaml
SC0/SC1/SC3).

GPU. Structure adapted (logic ported) from `margin-mapping/run_margin.py`
(read in full before writing this), simplified for M1b's own design: no
dose-0 baseline, no gate, and a FIXED small population (the 53-row refined
subset committed at `analysis-committed/refined_subset_ids_qwen35_4b.json`)
dosed at exactly 4 new rungs (0.55x/0.6x/0.65x/0.7x). erase_write at
anchor_onward, greedy decode, batch_size 4 (cell.yaml `ladder.write`/
`ladder.generation`), RunLog-checkpointed per rung and resumable.

REFUSES to run without BOTH:
  1. --i-know-this-runs-on-gpu
  2. a passing GPU preflight marker (analysis/preflight/PASS) for THIS
     experiment (gates.yaml SC1_dose_and_preflight: "MANDATORY GPU preflight
     before the full run")
  3. a PASSING rg0_drift_check report (analysis/preflight/rg0_drift_report.json,
     all_match == True) -- cell.yaml `preflight.rg0_drift_check`: "any
     mismatch halts the run ... before the full run"; this script enforces
     that as a hard precondition rather than trusting the caller to have
     checked, since a byte-identical-reuse assumption failure invalidates
     the merge rule for the reused 0.5x/0.75x endpoints this same run's
     analysis depends on.

This harness-BUILD task writes this script only; per the lead's phase-1
scope it is NOT invoked here. The lead reviews this build and launches the
full 212-generation run separately, after the SC0 rg0_drift_check and SC1
preflight gates both show PASS.
"""

from __future__ import annotations

import argparse
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
PREFLIGHT_DIR = ANALYSIS / "preflight"
STAGED = ANALYSIS / "staged_inputs"

FAMILY = "qwen35_4b"


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"{tag}.jsonl"


def refined_row_keys() -> list[str]:
    payload = common.load_json(COMMITTED / "refined_subset_ids_qwen35_4b.json")
    keys = sorted(payload["row_keys"])
    if len(keys) != config.REFINED_SUBSET_N:
        raise SystemExit(f"[generate-refined] FAIL: committed refined subset has {len(keys)} rows, expected {config.REFINED_SUBSET_N}.")
    return keys


def _require_preconditions() -> None:
    pass_marker = PREFLIGHT_DIR / "PASS"
    if not pass_marker.is_file():
        raise SystemExit(
            f"[generate-refined] REFUSING: no GPU preflight PASS marker at {pass_marker}. "
            f"Run `run_margin_preflight.py --i-know-this-runs-on-gpu` first (gates.yaml SC1)."
        )
    drift_report_path = PREFLIGHT_DIR / "rg0_drift_report.json"
    if not drift_report_path.is_file():
        raise SystemExit(
            f"[generate-refined] REFUSING: no rg0_drift_report.json at {drift_report_path}. "
            f"Run `rg0_drift_check.py --i-know-this-runs-on-gpu` first (cell.yaml preflight.rg0_drift_check)."
        )
    drift_report = common.load_json(drift_report_path)
    if not drift_report.get("all_match"):
        raise SystemExit(
            f"[generate-refined] REFUSING: rg0_drift_check did NOT pass (all_match={drift_report.get('all_match')}). "
            f"The byte-identical-reuse assumption for M1's 0.5x/0.75x endpoints is invalid; "
            f"do not generate until this is resolved and lifted to the PI."
        )


def load_c_hat_vector():
    import numpy as np

    path = STAGED / config.PINNED_INPUTS["c_hat_direction"]["dest"]
    c_hat = common.load_json(path)["vector"]
    return np.asarray(c_hat, dtype=np.float64)


def _live_sc1_after_first_batch(rung_label: str, target: float):
    state = {"checked": False}

    def _cb(batch_records: list[dict[str, Any]]) -> None:
        if state["checked"]:
            return
        state["checked"] = True
        checks = [
            sc1_checks.check_readback(r["row_key"], FAMILY, r.get("readback_measured"), target)
            for r in batch_records
        ]
        failed = [c for c in checks if not c["passed"]]
        if failed:
            raise SystemExit(
                f"LIVE SC1 FAIL ({FAMILY}/{rung_label}): first-batch readback outside "
                f"tolerance; {len(failed)}/{len(checks)} rows failed; worst={max(failed, key=lambda c: c['rel_delta'])}"
            )
        print(
            f"[live-sc1] {FAMILY}/{rung_label}: first-batch readback OK "
            f"({len(checks)} rows, max_rel_delta={max(c['rel_delta'] for c in checks):.6f})",
            flush=True,
        )

    return _cb


def _live_sc1_rung_completion(rung_label: str, tag: str, target: float) -> None:
    rows = common.load_jsonl(runlog_path(tag))
    checks = [
        sc1_checks.check_readback(r["row_key"], FAMILY, r.get("readback_measured"), target)
        for r in rows if r.get("readback_measured") is not None
    ]
    failed = [c for c in checks if not c["passed"]]
    if failed:
        raise SystemExit(
            f"LIVE SC1 FAIL ({FAMILY}/{rung_label}): rung-completion readback outside tolerance "
            f"for {len(failed)}/{len(checks)} rows; worst={max(failed, key=lambda c: c['rel_delta'])}"
        )
    print(
        f"[live-sc1] {FAMILY}/{rung_label}: rung-completion readback OK "
        f"({len(checks)} rows, max_rel_delta={(max((c['rel_delta'] for c in checks), default=0.0)):.6f})",
        flush=True,
    )


def cmd_generate(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print(
            "[generate-refined] this loads the model and generates the 4 new "
            "rungs over the 53-row refined subset on GPU; refusing without "
            "--i-know-this-runs-on-gpu.",
            file=sys.stderr,
        )
        return 2
    _require_preconditions()

    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    row_keys = refined_row_keys()
    qpool = row_pool.question_pool(FAMILY)
    missing = [rk for rk in row_keys if rk not in qpool]
    if missing:
        raise SystemExit(f"[generate-refined] FAIL: {len(missing)} refined row_keys missing from staged question pool: {missing[:5]}")
    rows = [{"row_key": rk, **qpool[rk]} for rk in row_keys]

    c_hat = load_c_hat_vector()
    sigma = config.SIGMA_C[FAMILY]

    model_name, revision = config.SUBSTRATE[FAMILY], config.REVISION[FAMILY]
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[FAMILY])

    try:
        for multiplier in config.NEW_RUNGS:
            setpoint = dose_ladder.rung_dose_abs(FAMILY, multiplier)
            _, gain = dose_ladder.c_hat_write_params(FAMILY, setpoint)
            rung_tag = dose_ladder.rung_tag(multiplier)
            tag = f"{FAMILY}__refined_rung_{rung_tag}"
            log = RunLog(runlog_path(tag), run_config={"stage": "refined_ladder_rung", "family": FAMILY, "multiplier": multiplier, "setpoint": setpoint, "sigma": sigma, "gain": gain}, fresh=False)
            hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma)
            handle = layer_module.register_forward_hook(ctrl)
            try:
                steer_lib.run_rows(
                    model, tokenizer, device, ctrl, "gen_stream", rows, gain,
                    config.GEN_MAX_NEW_TOKENS, args.batch_size, log,
                    after_batch=_live_sc1_after_first_batch(f"rung_{multiplier}", setpoint),
                )
                log.finalize({"n_rows": len(rows)})
            finally:
                handle.remove()
                ctrl.reset()
                log.close()
            _live_sc1_rung_completion(f"rung_{multiplier}", tag, setpoint)
            print(f"[generate-refined] {FAMILY}: rung {multiplier}x done -> {runlog_path(tag)}", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    ap.set_defaults(func=cmd_generate)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
