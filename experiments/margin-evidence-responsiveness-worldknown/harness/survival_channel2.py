#!/usr/bin/env python3
"""Channel 2 single-dose survival for margin-evidence-responsiveness-
worldknown (M4-WK) (cell.yaml `channel2_margin.single_dose_survival`).

For each margin-eligible confab row (tipping_censored == False in that
direction's ladder-derive output, ~308 rows), pushes at that row's OWN
world-known tipping dose (a PER-ROW dose, fixed across all 3 arms) under
each of no_answer_baseline / true_answer / false_answer_placebo, greedy
decode. A row "survives" a pass if NOT refused_v2 (detector_v2) AND
well_formed (cell.yaml: "survival = NOT(detector_v2_refused OR
adjudicated_abstention) AND well_formed" -- the adjudicated_abstention term
is validated separately by the SC2 blinded abstention-calibration slice
(calibration.py) with a disagreement gate; this script, like the ladder
rebuild, scores every row via detector_v2 alone, matching the tipping-dose
derivation's own convention).

MAJOR M2 (red-team): the three arms MUST run under ONE pinned batch
composition (same row order/grouping every arm), never mixed regimes.

HETEROGENEOUS PER-ROW DOSING: unlike `steer_lib.run_rows` (which threads a
single scalar `strength` through every batch in a pass, used by census.py's
generation-only, and by ladder_channel2.py's single-rung-dose-for-all-rows
passes), survival needs a DIFFERENT dose per row, fixed within a row across
the 3 arms. `InterventionHook`/`GenerationInterventionController.begin_pass`
natively accept a per-row list/tensor of strengths (`_strength_per_row` in
`MechInterp/intervention/hooks.py`, read in full before writing this) so
`steer_lib.run_batch_fixed` (which passes `strength` straight through,
unmodified) already supports this -- but `run_rows` itself does not thread a
per-row dose through resumable batching, so this script implements its own
resume/batch loop (`_run_rows_heterogeneous_dose`) instead of modifying the
shared `run_rows` (which margin_channel2.py / preflight.py still use with
scalar-dose semantics; no change to that shared contract).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import batching  # noqa: E402
import popqa_pool  # noqa: E402
import dose_ladder  # noqa: E402
import sc1_checks  # noqa: E402
import stats  # noqa: E402
import capture_channel1 as capture_mod  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
SELECTION_DIR = COMMITTED / "selection"
LADDER_DIR = ANALYSIS / "channel2_ladder"
RUNLOG_DIR = ANALYSIS / "runlog"
OUT_DIR = ANALYSIS / "channel2_survival"


def rung_runlog_path(direction: str, arm: str) -> Path:
    return RUNLOG_DIR / f"channel2_survival_{direction}__{arm}.jsonl"


def load_margin_eligible_rows(direction: str) -> dict[str, dict[str, Any]]:
    """row_key -> {row_key, question, aliases, category_canon, own_tipping_dose_abs}
    for confab rows with a NON-CENSORED tipping dose in this direction's
    ladder-derive output. Requires ladder_channel2.py derive to have run
    first."""
    margin_rows_path = LADDER_DIR / f"{direction}_margin_rows.jsonl"
    if not margin_rows_path.is_file():
        raise SystemExit(f"survival_channel2 FAIL: no {margin_rows_path}; run `ladder_channel2.py derive --direction {direction}` first.")
    margin_rows = common.load_jsonl(margin_rows_path)
    pool = popqa_pool.load_pool()
    eligible: dict[str, dict[str, Any]] = {}
    for r in margin_rows:
        if r["role"] != "confab" or r["tipping_censored"]:
            continue
        rk = r["row_key"]
        pr = pool[rk]
        eligible[rk] = {
            "row_key": rk, "question": pr["question"], "aliases": pr["aliases"],
            "category_canon": pr["category"], "role": "confab", "source": "popqa",
            "own_tipping_dose_abs": r["tipping_dose_abs"],
        }
    return eligible


def _run_rows_heterogeneous_dose(
    model, tokenizer, device, controller, mode: str,
    rows: list[dict[str, Any]], gain_by_row_key: dict[str, float],
    max_new: int, batch_size: int, run_log, after_batch=None,
) -> None:
    """Bespoke analog of `steer_lib.run_rows` for a PER-ROW dose: same
    resume/RunLog/grading contract, but slices `gain_by_row_key` per batch
    and passes the resulting list as `strength` to `run_batch_fixed`
    (supported natively by `InterventionHook`'s per-row broadcasting; see
    module docstring)."""
    import steer_lib
    import gen_lib

    done = run_log.done_keys()
    pending = [r for r in rows if r["row_key"] not in done]
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [steer_lib.render_prompt(r) for r in batch]
        batch_gains = [gain_by_row_key[r["row_key"]] for r in batch]
        gen, raw_rb = steer_lib.run_batch_fixed(model, tokenizer, device, controller, prompts, mode, batch_gains, max_new)
        batch_records = []
        for row, res in zip(batch, gen):
            grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            rec = {
                "row_key": row["row_key"], "role": row.get("role"), "source": row.get("source"),
                "own_tipping_dose_abs": row.get("own_tipping_dose_abs"),
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            }
            run_log.record(row["row_key"], rec)
            batch_records.append(rec)
        if after_batch is not None:
            after_batch(batch_records)
        print(f"[survival_channel2] {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)


def cmd_generate(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("[survival_channel2 generate] this loads the model and generates 3 survival arms on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    marker_path = config.EXPERIMENT_DIR / config.PREFLIGHT_PASS_MARKER
    if not marker_path.is_file() or not common.load_json(marker_path).get("pass"):
        print(f"[survival_channel2 generate] refusing: no passing preflight PASS marker at {marker_path}.", file=sys.stderr)
        return 2

    config.assert_pinned_hashes()
    direction = args.direction

    import gc

    import torch
    import steer_lib
    from MechInterp.intervention import get_decoder_layer
    from shared.utilities.run_log import RunLog

    eligible = load_margin_eligible_rows(direction)
    if not eligible:
        raise SystemExit(f"survival_channel2 FAIL: zero margin-eligible confab rows for direction={direction}.")
    distractor_mapping = capture_mod.load_distractor_mapping()
    pool = popqa_pool.load_pool()

    ordered_keys = batching.canonical_order(list(eligible.keys()))
    composition = batching.batch_composition_record([{"row_key": rk} for rk in ordered_keys], config.SURVIVAL_BATCH_SIZE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(OUT_DIR / f"{direction}_batch_composition.json", composition)
    print(f"[survival_channel2 generate] {direction}: {len(ordered_keys)} margin-eligible rows, composition row_order_sha256={composition['row_order_sha256'][:16]}", flush=True)

    sigma_c = dose_ladder.sigma_c(direction)
    gain_by_row_key = {rk: eligible[rk]["own_tipping_dose_abs"] / sigma_c for rk in ordered_keys}
    target_by_row_key = {rk: eligible[rk]["own_tipping_dose_abs"] for rk in ordered_keys}

    direction_record = common.load_json(
        config.EXPERIMENT_DIR / "analysis" / "staged_inputs" / "directions" / "hs20" / "c_hat_transfer.json"
        if direction == "transfer" else config.NATIVE_C_HAT_PATH
    )
    vector = torch.tensor(direction_record["vector"], dtype=torch.float32)

    model, tokenizer, device = steer_lib.load_model(config.MODEL_REPO, config.MODEL_REVISION)
    layer_module = get_decoder_layer(model, config.DECODER_BLOCK_INDEX)

    try:
        for arm in config.ARMS:
            rows_this_arm = []
            for rk in ordered_keys:
                base = eligible[rk]
                context = capture_mod.context_for_arm(arm, base, distractor_mapping, pool)
                rows_this_arm.append({**base, "context": context})

            log_path = rung_runlog_path(direction, arm)
            hook, ctrl = steer_lib.build_hook_and_controller(vector, sigma_c)
            handle = layer_module.register_forward_hook(ctrl)
            checked_first_batch = {"done": False}

            def _after_batch(batch_records: list[dict[str, Any]]) -> None:
                if checked_first_batch["done"]:
                    return
                checked_first_batch["done"] = True
                checks = [
                    sc1_checks.check_readback(r["row_key"], direction, r.get("readback_measured"), target_by_row_key[r["row_key"]], dose_ladder.reference_dose_abs(direction))
                    for r in batch_records
                ]
                failed = [c for c in checks if not c["passed"]]
                if failed:
                    raise SystemExit(f"LIVE SC1 FAIL (survival/{direction}/{arm}): first-batch readback outside tolerance; {len(failed)}/{len(checks)} failed; worst={max(failed, key=lambda c: c.get('rel_delta', float('inf')))}")
                print(f"[live-sc1] survival/{direction}/{arm}: first-batch readback OK ({len(checks)} rows)", flush=True)

            try:
                log = RunLog(log_path, run_config={"stage": "channel2_survival", "direction": direction, "arm": arm, "row_order_sha256": composition["row_order_sha256"], "sigma_c": sigma_c}, fresh=False)
                _run_rows_heterogeneous_dose(model, tokenizer, device, ctrl, "gen_stream", rows_this_arm, gain_by_row_key, config.GEN_MAX_NEW_TOKENS, config.SURVIVAL_BATCH_SIZE, log, after_batch=_after_batch)
                log.finalize({"n_rows": len(rows_this_arm)})
                log.close()
            finally:
                handle.remove()
                ctrl.reset()

            logged = common.load_jsonl(log_path)
            readback_checks = [
                sc1_checks.check_readback(r["row_key"], direction, r.get("readback_measured"), target_by_row_key[r["row_key"]], dose_ladder.reference_dose_abs(direction))
                for r in logged if r.get("readback_measured") is not None
            ]
            failed = [c for c in readback_checks if not c["passed"]]
            if failed:
                raise SystemExit(f"LIVE SC1 FAIL (survival/{direction}/{arm}): pass-completion readback outside tolerance for {len(failed)}/{len(readback_checks)} rows; worst={max(failed, key=lambda c: c['rel_delta'])}")
            print(f"[survival_channel2 generate] {direction}/{arm}: done -> {log_path} ({len(logged)} rows, readback OK)", flush=True)
    finally:
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return 0


# ---------------------------------------------------------------------------
# score (CPU): survival per row/arm, baseline staleness check, primary test.
# ---------------------------------------------------------------------------

def _survives(rec: dict[str, Any]) -> bool:
    return bool(rec.get("well_formed")) and not bool(rec.get("refused_v2"))


def cmd_score(args: argparse.Namespace) -> int:
    config.assert_pinned_hashes()
    direction = args.direction

    eligible = load_margin_eligible_rows(direction)
    ordered_keys = batching.canonical_order(list(eligible.keys()))

    per_arm: dict[str, dict[str, dict[str, Any]]] = {}
    for arm in config.ARMS:
        log_path = rung_runlog_path(direction, arm)
        if not log_path.is_file():
            raise SystemExit(f"survival_channel2 score FAIL: no {log_path}; run `generate --direction {direction}` first.")
        table = {r["row_key"]: r for r in common.load_jsonl(log_path)}
        missing = [rk for rk in ordered_keys if rk not in table]
        if missing:
            raise SystemExit(f"survival_channel2 score FAIL: {len(missing)} margin-eligible rows missing from {log_path} (zero-drop violation): {missing[:10]}")
        per_arm[arm] = table

    import numpy as np

    survival_by_arm_row = {
        arm: np.array([1.0 if _survives(per_arm[arm][rk]) else 0.0 for rk in ordered_keys])
        for arm in config.ARMS
    }
    n = len(ordered_keys)

    baseline_survival_rate = float(survival_by_arm_row["no_answer_baseline"].mean())
    baseline_staleness = {
        "n": n, "no_answer_baseline_survival_rate": baseline_survival_rate,
        "ceiling": config.BASELINE_STALENESS_CEILING,
        "passed": baseline_survival_rate <= config.BASELINE_STALENESS_CEILING,
    }

    d2_absolute_floor_if_frozen_now = config.D2_WALD_Z * (0.25 / n) ** 0.5
    paired_diff = stats.bootstrap_paired_diff(survival_by_arm_row["true_answer"], survival_by_arm_row["false_answer_placebo"], n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED, statistic="mean")

    result = {
        "direction": direction, "n_margin_eligible": n,
        "baseline_staleness_check": baseline_staleness,
        "survival_rates": {arm: float(survival_by_arm_row[arm].mean()) for arm in config.ARMS},
        "d2_absolute_floor_if_frozen_now": d2_absolute_floor_if_frozen_now,
        "d2_absolute_floor_formula": "1.96 * sqrt(0.25 / n_margin_eligible)",
        "primary_test_paired_diff_true_minus_false": paired_diff,
        "point_estimate_ge_floor_if_frozen_now": paired_diff["point"] >= d2_absolute_floor_if_frozen_now,
        "note": (
            "d2_absolute_floor is REPORTED here as 'if_frozen_now' for review; "
            "the ACTUAL frozen numeric requires a separate `bin/exp repin` of "
            "gates.yaml the MOMENT n_margin_eligible is realized (before this "
            "primary_test is computed) per gates.yaml rederived_floors.d2_"
            "absolute_floor -- self-blinding order, not this script's job to "
            "enforce retroactively."
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    common.write_json(OUT_DIR / f"{direction}_survival_score.json", result)
    print(json.dumps(result, indent=2), flush=True)

    if not baseline_staleness["passed"]:
        print(
            f"[survival_channel2 score] BASELINE STALENESS CHECK FAILED for "
            f"direction={direction}: no_answer_baseline survival "
            f"{baseline_survival_rate:.4f} > ceiling {config.BASELINE_STALENESS_CEILING}. "
            f"Per gates.yaml S1_baseline_reproduction: channel 2 is VOIDED / "
            f"lifted to PI for this direction, NOT scored as a (d)-not-earned "
            f"failure.",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate", help="GPU: 3 survival arms at each row's own tipping dose, one direction")
    p_gen.add_argument("--direction", required=True, choices=config.DIRECTIONS)
    p_gen.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    p_gen.set_defaults(func=cmd_generate)

    p_score = sub.add_parser("score", help="CPU: survival rates, baseline staleness check, primary paired-diff test")
    p_score.add_argument("--direction", required=True, choices=config.DIRECTIONS)
    p_score.set_defaults(func=cmd_score)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
