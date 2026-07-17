#!/usr/bin/env python3
"""RG0 drift check for margin-separation-fine-ladder (M1b) (cell.yaml
`preflight.rg0_drift_check`; gates.yaml `SC0_provenance_staging`, NEW item;
Decision record item 7).

GPU. Regenerates the 8 refined rows with the lexicographically smallest
row_key (from the SC0-committed `refined_subset_ids_qwen35_4b.json`) at the
0.75x rung, and byte-compares the completion TEXT against the SAME rows in
the staged copy of M1's pinned `rung_0p75` runlog.

The merge rule leans on M1's 0.5x/0.75x endpoint values being reproducible
on today's environment; this check converts that assumption into evidence
for 8 generations of cost, BEFORE any of the 212-generation full run is
spent. Any mismatch halts and is reported straight -- never a silent retry
or patch (cell.yaml: "any mismatch halts the run (substrate/environment
drift), reported in NOTEBOOK and lifted to the PI, never a silent retry or
patch").

Never writes to any governed file; only to `analysis/preflight/
rg0_drift_report.json` (new directory/file, this script's own output).
"""

from __future__ import annotations

import argparse
import datetime
import gc
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


def _drift_check_row_keys() -> list[str]:
    payload = common.load_json(COMMITTED / "refined_subset_ids_qwen35_4b.json")
    row_keys = sorted(payload["row_keys"])  # lexicographic
    n = config.RG0_DRIFT_CHECK_N_ROWS
    if len(row_keys) < n:
        raise SystemExit(f"[rg0-drift] FAIL: refined subset has only {len(row_keys)} rows, need {n}.")
    return row_keys[:n]


def _staged_rung_0p75_records() -> dict[str, dict[str, Any]]:
    path = STAGED / config.PINNED_INPUTS["rung_0p75"]["dest"]
    if not path.is_file():
        raise SystemExit(f"[rg0-drift] FAIL: staged rung_0p75 runlog missing at {path}; run staging.py first.")
    return {r["row_key"]: r for r in common.load_jsonl(path)}


def load_c_hat_vector():
    import numpy as np

    path = STAGED / config.PINNED_INPUTS["c_hat_direction"]["dest"]
    c_hat = common.load_json(path)["vector"]
    return np.asarray(c_hat, dtype=np.float64)


def _first_divergence_offset(a: str, b: str) -> int | None:
    """Index of the first differing character, or None if identical. Never
    returns the diverging text itself (containment: no generation text in
    any committed/reported artifact beyond this script's own gitignored
    analysis/ directory, and even there this report carries offsets only)."""
    if a == b:
        return None
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n  # one is a strict prefix of the other


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true", required=True)
    args = ap.parse_args()

    drift_row_keys = _drift_check_row_keys()
    staged_0p75 = _staged_rung_0p75_records()
    missing_in_staged = [rk for rk in drift_row_keys if rk not in staged_0p75]
    if missing_in_staged:
        raise SystemExit(f"[rg0-drift] FAIL: {len(missing_in_staged)} drift-check row_keys missing from staged rung_0p75 runlog: {missing_in_staged}")

    qpool = row_pool.question_pool(FAMILY)
    missing_in_qpool = [rk for rk in drift_row_keys if rk not in qpool]
    if missing_in_qpool:
        raise SystemExit(f"[rg0-drift] FAIL: {len(missing_in_qpool)} drift-check row_keys missing from staged question pool: {missing_in_qpool}")
    rows = [{"row_key": rk, **qpool[rk]} for rk in drift_row_keys]

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer

    setpoint = dose_ladder.rung_dose_abs(FAMILY, config.RG0_DRIFT_CHECK_RUNG_MULT)
    _, gain = dose_ladder.c_hat_write_params(FAMILY, setpoint)
    c_hat = load_c_hat_vector()
    sigma = config.SIGMA_C[FAMILY]

    model_name, revision = config.SUBSTRATE[FAMILY], config.REVISION[FAMILY]
    print(f"[rg0-drift] loading {model_name}@{revision}", flush=True)
    model, tokenizer, device = steer_lib.load_model(model_name, revision)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX[FAMILY])

    per_row: list[dict[str, Any]] = []
    try:
        hook, ctrl = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma)
        handle = layer_module.register_forward_hook(ctrl)
        try:
            prompts = [steer_lib.render_prompt(r) for r in rows]
            gen, _raw_rb = steer_lib.run_batch_fixed(
                model, tokenizer, device, ctrl, prompts, "gen_stream", gain, config.GEN_MAX_NEW_TOKENS,
            )
        finally:
            handle.remove()
            ctrl.reset()
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    all_match = True
    for row, res in zip(rows, gen):
        rk = row["row_key"]
        fresh_text = res["text"]
        staged_text = staged_0p75[rk]["answer_text"]
        readback_check = sc1_checks.check_readback(rk, FAMILY, res.get("readback_measured"), setpoint)
        match = fresh_text == staged_text
        all_match = all_match and match
        per_row.append({
            "row_key": rk,
            "match": match,
            "first_divergence_offset": None if match else _first_divergence_offset(fresh_text, staged_text),
            "fresh_len": len(fresh_text),
            "staged_len": len(staged_text),
            "readback_check": readback_check,
        })
        print(f"[rg0-drift] row_key={rk} match={match} readback_passed={readback_check['passed']}", flush=True)

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "family": FAMILY,
        "rung_multiplier": config.RG0_DRIFT_CHECK_RUNG_MULT,
        "setpoint_dose_abs": setpoint,
        "n_rows": len(rows),
        "row_keys": drift_row_keys,
        "all_match": all_match,
        "per_row": per_row,
        "note": (
            "byte-comparison of the completion TEXT (answer_text) between a "
            "fresh 0.75x-rung generation and M1's staged rung_0p75 runlog, "
            "for the 8 lexicographically-smallest refined-subset row_keys. "
            "On mismatch: this is a substrate/environment drift signal; the "
            "merge rule's byte-identical-reuse assumption for M1's 0.5x/0.75x "
            "endpoints is INVALID and the run must not proceed until resolved."
        ),
    }
    PREFLIGHT_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(PREFLIGHT_DIR / "rg0_drift_report.json", report)

    if not all_match:
        n_mismatch = sum(1 for r in per_row if not r["match"])
        print(
            f"[rg0-drift] HALT: {n_mismatch}/{len(rows)} rows diverged from M1's staged "
            f"rung_0p75 runlog. See analysis/preflight/rg0_drift_report.json "
            f"(row_keys + first divergence offsets only, no text). Lift to the PI "
            f"before proceeding with ANY further generation.",
            file=sys.stderr,
        )
        return 1

    print(f"[rg0-drift] PASS: all {len(rows)} rows byte-match M1's staged rung_0p75 runlog.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
