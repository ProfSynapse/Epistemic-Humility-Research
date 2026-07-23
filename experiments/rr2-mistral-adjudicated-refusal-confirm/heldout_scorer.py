#!/usr/bin/env python3
"""Held-out four-pass scorer for rr2-mistral-adjudicated-refusal-confirm.

Single fixed operating point (hs16, dose 12 sigma_c, mistral only); no dose
ladder, no layer sweep, no selection logic. Runs the four registered passes
(cell.yaml `arms`) over the full held-out pool, using the direction vectors
`fit_reuse.py` reconstructed (and cross-checked against RR's committed
stats) rather than a fresh fit or a `fit_dose_ladder_report.json` selection.

Passes (all scored against the SAME frozen doubt gate reconstructed by
fit_reuse.py -- tau_frozen, u_d, mu_d, sigma_d -- applied fresh to held-out
anchors):

  baseline            no hook; every held-out row (confab + known), once.
                      Reference for RG3.
  gated               the doubt gate is scored on EVERY held-out row (both
                       roles); fired rows get the c_hat erase-write at
                       dose_abs = 12 * sigma_c; non-fired rows reuse the
                       shared baseline pass. Primary population for RG1/RG2.
  random_direction    the SAME fired rows as `gated`, c_hat swapped for the
                       reconstructed random_direction placebo, magnitude
                       matched (random_direction stored at sigma=1.0, so
                       gain_random = dose_abs / 1.0).
  dose_knowns_ungated  EVERY held-out known_correct_answered row, gate OFF,
                       dosed unconditionally with c_hat at dose_abs.
                       Selectivity-on-knowns characterization only, per
                       gates.yaml (not a promotion gate).

Per the data-exhaust build-time rule (AMENDMENT.md), every row's FULL
generation text and FULL sub-grade dict (v1 AND v2 fields, matched_pattern_ids)
are persisted to the gitignored row-level run log via `steer_lib.run_rows` /
`gen_lib.grade_row` -- nothing is collapsed to a boolean before being
written.

This module computes and reports v1 (RR-comparable) and v2 (detector-v2)
rate summaries only. RG1/RG2/RG3 verdicts are NOT computed here: per
AMENDMENT.md "Design" item 2, the primary rate (refused_v2 OR
adjudicated_abstention) can only be computed once the blinded adjudication
lane has run, which is a separate, out-of-band human/PI step
(`build_adjudication_pool.py` then `apply_adjudication.py`). This module's
`analysis-committed/heldout_summary.json` is explicitly marked provisional
and `pipeline.py`'s `report` step prints the adjudication instructions
rather than a verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_fit  # noqa: E402
import gates_lib  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
DIRECTIONS = HERE / "directions"
LAYER = 16


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"heldout__{tag}.jsonl"


def _run_log(tag: str, run_config: dict[str, Any]):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(tag), run_config=run_config)


def load_cell_yaml() -> dict[str, Any]:
    with (HERE / "cell.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_reconstructed_directions() -> dict[str, Any]:
    """Reads the vectors/stats `fit_reuse.py reconstruct` wrote (NOT a
    `hs{layer}_c_hat.json`-under-`analysis-committed/` read, which is where
    RR's own heldout_scorer.py looked -- a path RR itself never actually
    populated; see fit_reuse.py's docstring)."""
    for name in ("hs16_c_hat.json", "hs16_random_direction.json", "hs16_u_d.json", "hs16_build_manifest.json"):
        if not (DIRECTIONS / name).is_file():
            raise SystemExit(
                f"missing {DIRECTIONS / name}; run `fit_reuse.py reconstruct` first."
            )
    c_hat = np.asarray(json.loads((DIRECTIONS / "hs16_c_hat.json").read_text())["vector"])
    rand_dir = np.asarray(json.loads((DIRECTIONS / "hs16_random_direction.json").read_text())["vector"])
    u_d = np.asarray(json.loads((DIRECTIONS / "hs16_u_d.json").read_text())["vector"])
    build_manifest = json.loads((DIRECTIONS / "hs16_build_manifest.json").read_text())
    return {"c_hat": c_hat, "random_direction": rand_dir, "u_d": u_d, "build_manifest": build_manifest}


def score_gate_on_heldout(
    held_rows: list[dict[str, Any]], H: dict[str, np.ndarray], u_d: np.ndarray, mu_d: float, sigma_d: float, tau: float,
) -> list[dict[str, Any]]:
    fit_for_gate = {"u_d": u_d, "stats": {"mu_d": mu_d, "sigma_d": sigma_d}}
    return direction_fit.score_and_fire(held_rows, H, fit_for_gate, tau)


def run_baseline_pass(model, tokenizer, device, rows: list[dict[str, Any]], batch_size: int) -> dict[str, dict]:
    log = _run_log("baseline", {"stage": "heldout_baseline"})
    gains = {r["row_key"]: 0.0 for r in rows}
    steer_lib.run_rows(model, tokenizer, device, None, "off", rows, gains, 200, batch_size, log, lambda r: r["row_key"])
    log.finalize({"n_rows": len(rows)})
    log.close()
    return {r["row_key"]: r for r in load_jsonl(runlog_path("baseline"))}


def run_active_pass(
    model, tokenizer, device, controller, layer_module, tag: str,
    active_rows: list[dict[str, Any]], gain: float, batch_size: int,
) -> dict[str, dict]:
    handle = layer_module.register_forward_hook(controller)
    try:
        log = _run_log(tag, {"stage": "heldout", "tag": tag})
        gains = {r["row_key"]: gain for r in active_rows}
        steer_lib.run_rows(model, tokenizer, device, controller, "gen_stream", active_rows, gains, 200, batch_size, log, lambda r: r["row_key"])
        log.finalize({"n_rows": len(active_rows), "gain": gain})
        log.close()
    finally:
        handle.remove()
        controller.reset()
    return {r["row_key"]: r for r in load_jsonl(runlog_path(tag))}


def combine_active_and_baseline(all_rows: list[dict[str, Any]], active_by_key: dict[str, dict], baseline_by_key: dict[str, dict]) -> list[dict[str, Any]]:
    out = []
    for r in all_rows:
        rk = r["row_key"]
        out.append(active_by_key.get(rk) or baseline_by_key[rk])
    return out


def cmd_run(args: argparse.Namespace) -> int:
    cell = load_cell_yaml()
    fcell = cell["family"]
    revision = mrows.resolve_revision()
    dose_mult = cell["fixed_operating_point"]["dose_multiplier"]

    joined_path = ANALYSIS / "joined_rows_private.jsonl"
    rows = load_jsonl(joined_path)
    held_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "held_out"]
    held_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out"]
    held_all = held_confab + held_known

    reconstructed = load_reconstructed_directions()
    build_manifest = reconstructed["build_manifest"]
    dose_abs = float(dose_mult * build_manifest["sigma_c"])

    raw_anchors = json.loads((ANALYSIS / "anchors_at_candidate_layers.json").read_text())
    H = {rk: np.asarray(per[str(LAYER)], dtype=np.float64) for rk, per in raw_anchors.items() if str(LAYER) in per}

    scored = score_gate_on_heldout(
        held_all, H, reconstructed["u_d"], build_manifest["mu_d"], build_manifest["sigma_d"], build_manifest["tau_frozen"],
    )
    fired = [r for r in scored if r["fire"]]
    fired_confab = [r for r in fired if r["role"] == "confab"]
    fired_known = [r for r in fired if r["role"] == "known_correct_answered"]

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, mrows.decoder_block_index(LAYER))

    baseline_by_key = run_baseline_pass(model, tokenizer, device, held_all, args.batch_size)

    import torch

    hook_c, ctrl_c = steer_lib.build_hook_and_controller(torch.tensor(reconstructed["c_hat"], dtype=torch.float32), build_manifest["sigma_c"])
    gated_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_c, layer_module, "gated",
        fired, float(dose_abs / build_manifest["sigma_c"]), args.batch_size,
    ) if fired else {}
    gated_all = combine_active_and_baseline(held_all, gated_active_by_key, baseline_by_key)
    gated_confab = [r for r in gated_all if r["role"] == "confab"]
    gated_known = [r for r in gated_all if r["role"] == "known_correct_answered"]
    gated_known_fired_only = [gated_active_by_key[r["row_key"]] for r in fired_known] if fired_known else []

    hook_r, ctrl_r = steer_lib.build_hook_and_controller(torch.tensor(reconstructed["random_direction"], dtype=torch.float32), 1.0)
    rand_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_r, layer_module, "random_direction",
        fired, float(dose_abs), args.batch_size,
    ) if fired else {}
    rand_all = combine_active_and_baseline(held_all, rand_active_by_key, baseline_by_key)
    rand_confab = [r for r in rand_all if r["role"] == "confab"]
    rand_known = [r for r in rand_all if r["role"] == "known_correct_answered"]

    dose_knowns_gain = float(dose_abs / build_manifest["sigma_c"])
    dku_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_c, layer_module, "dose_knowns_ungated",
        held_known, dose_knowns_gain, args.batch_size,
    )
    dku_all = [dku_active_by_key[r["row_key"]] for r in held_known]

    baseline_confab = [baseline_by_key[r["row_key"]] for r in held_confab]
    baseline_known = [baseline_by_key[r["row_key"]] for r in held_known]

    summary = {
        "status": "provisional_detector_v1_v2_only",
        "note": (
            "RG1/RG2/RG3 verdicts are NOT computed here. refused_final "
            "(detector_v2_refused OR adjudicated_abstention) requires the "
            "blinded adjudication lane; run build_adjudication_pool.py then "
            "apply_adjudication.py, per pipeline.py's printed instructions."
        ),
        "dose_abs": dose_abs, "dose_multiplier": dose_mult, "layer": LAYER,
        "n_held_out_confab": len(held_confab), "n_held_out_known": len(held_known),
        "n_fired_confab": len(fired_confab), "n_fired_known": len(fired_known),
        "baseline": {
            "confab": {"v1": gates_lib.rate_summary_v1(baseline_confab), "v2": gates_lib.rate_summary_v2(baseline_confab)},
            "known": {"v1": gates_lib.rate_summary_v1(baseline_known), "v2": gates_lib.rate_summary_v2(baseline_known)},
        },
        "gated": {
            "fired_confab": {
                "v1": gates_lib.rate_summary_v1([gated_active_by_key[r["row_key"]] for r in fired_confab]) if fired_confab else gates_lib.rate_summary_v1([]),
                "v2": gates_lib.rate_summary_v2([gated_active_by_key[r["row_key"]] for r in fired_confab]) if fired_confab else gates_lib.rate_summary_v2([]),
            },
            "known_full_population": {"v1": gates_lib.rate_summary_v1(gated_known), "v2": gates_lib.rate_summary_v2(gated_known)},
            "known_fired_conditional": {"v1": gates_lib.rate_summary_v1(gated_known_fired_only), "v2": gates_lib.rate_summary_v2(gated_known_fired_only)},
        },
        "random_direction": {
            "confab": {"v1": gates_lib.rate_summary_v1(rand_confab), "v2": gates_lib.rate_summary_v2(rand_confab)},
            "known": {"v1": gates_lib.rate_summary_v1(rand_known), "v2": gates_lib.rate_summary_v2(rand_known)},
        },
        "dose_knowns_ungated": {
            "known_all": {"v1": gates_lib.rate_summary_v1(dku_all), "v2": gates_lib.rate_summary_v2(dku_all)},
            "clean_false_refusal_v1": gates_lib.rate_wilson(dku_all, "refused_v1"),
            "clean_false_refusal_v2": gates_lib.rate_wilson(dku_all, "refused_v2"),
            "total_damage_rate": gates_lib.rate_wilson(dku_all, "not_well_formed_correct"),
            "metric_hygiene_note": (
                "clean_false_refusal (comparable to the gated cost metric) and "
                "total_damage_rate (not_well_formed_correct, BROADER than "
                "refusal) are reported separately and must never be conflated "
                "(H4 metric-hygiene rule, inherited via RR)."
            ),
        },
    }

    write_json(COMMITTED / "heldout_summary.json", summary)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.set_defaults(func=cmd_run)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
