#!/usr/bin/env python3
"""Held-out four-arm scorer for rr-cross-family-raw-refusal.

Runs the four registered arms (cell.yaml `arms`) at the single FIT-selected
(layer, dose) operating point, over the full held-out pool for one family,
and computes G1 (primary + cost gate) and G3(i) (placebo) via gates_lib. The
outcome-shape classification (A-F) is left to `pipeline.py`'s report step,
not computed inline here, so this module's output is pure measurement.

Arms (cell.yaml, all four scored against the SAME frozen doubt gate fit on
FIT -- tau_frozen, u_d, mu_d, sigma_d -- applied fresh to held-out anchors):

  baseline            no hook; every held-out row (confab + known), once.
  gated               the doubt gate is scored on EVERY held-out row (both
                       roles); fired rows (confab AND known -- the ladder's
                       own Outcome documents known rows firing too, its
                       "fired-known conditional false-refusal" reading) get
                       the c_hat erase-write at the frozen dose; non-fired
                       rows reuse the shared baseline pass.
  random_direction    the SAME fired rows (confab + known) as `gated`, c_hat
                       swapped for the frozen random_direction placebo,
                       magnitude matched (random_direction.json stores
                       sigma=1.0, so gain_random = dose_abs / 1.0, matching
                       run_dose_ladder.py's own convention).
  dose_knowns_ungated  EVERY held-out known_correct_answered row, gate OFF,
                       dosed unconditionally with c_hat at the frozen dose.
                       Selectivity-on-knowns characterization only, not a
                       promotion gate (gates.yaml
                       selectivity_on_knowns_characterization).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_fit  # noqa: E402
import gates_lib  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
MAX_NEW = 200


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(family: str, tag: str):
    return ANALYSIS / family / "runlog" / f"heldout__{tag}.jsonl"


def _run_log(family: str, tag: str, run_config: dict[str, Any]):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(family, tag), run_config=run_config)


def score_gate_on_heldout(
    held_rows: list[dict[str, Any]], H: dict[str, np.ndarray], fit: dict[str, Any], tau: float,
) -> list[dict[str, Any]]:
    return direction_fit.score_and_fire(held_rows, H, fit, tau)


def run_baseline_pass(model, tokenizer, device, family: str, rows: list[dict[str, Any]], batch_size: int) -> dict[str, dict]:
    log = _run_log(family, "baseline", {"family": family, "stage": "heldout_baseline"})
    gains = {r["row_key"]: 0.0 for r in rows}
    steer_lib.run_rows(model, tokenizer, device, None, "off", rows, gains, MAX_NEW, batch_size, log, lambda r: r["row_key"])
    log.finalize({"n_rows": len(rows)})
    log.close()
    return {r["row_key"]: r for r in load_jsonl(runlog_path(family, "baseline"))}


def run_active_pass(
    model, tokenizer, device, controller, layer_module, family: str, tag: str,
    active_rows: list[dict[str, Any]], gain: float, batch_size: int,
) -> dict[str, dict]:
    handle = layer_module.register_forward_hook(controller)
    try:
        log = _run_log(family, tag, {"family": family, "stage": "heldout", "tag": tag})
        gains = {r["row_key"]: gain for r in active_rows}
        steer_lib.run_rows(model, tokenizer, device, controller, "gen_stream", active_rows, gains, MAX_NEW, batch_size, log, lambda r: r["row_key"])
        log.finalize({"n_rows": len(active_rows), "gain": gain})
        log.close()
    finally:
        handle.remove()
        controller.reset()
    return {r["row_key"]: r for r in load_jsonl(runlog_path(family, tag))}


def combine_active_and_baseline(all_rows: list[dict[str, Any]], active_by_key: dict[str, dict], baseline_by_key: dict[str, dict]) -> list[dict[str, Any]]:
    out = []
    for r in all_rows:
        rk = r["row_key"]
        out.append(active_by_key.get(rk) or baseline_by_key[rk])
    return out


def cmd_run(args: argparse.Namespace) -> int:
    fcell = mrows.family_cell(args.family)
    revision = mrows.resolve_revision(args.family)
    fit_report = json.loads((COMMITTED / args.family / "fit_dose_ladder_report.json").read_text())
    selected = fit_report["selected_operating_point"]
    if selected is None:
        raise SystemExit(
            f"family {args.family!r} has no FIT-viable operating point "
            "(outcome shape F) -- held-out scoring is not launched, per "
            "cell.yaml dose_policy.fit_dose_selection.on_no_viable_dose."
        )
    layer = selected["layer"]
    dose_abs = selected["dose_abs"]

    joined_path = ANALYSIS / args.family / "joined_rows_private.jsonl"
    rows = load_jsonl(joined_path)
    held_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "held_out"]
    held_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "held_out"]
    held_all = held_confab + held_known

    build_manifest = json.loads((COMMITTED / args.family / f"hs{layer}_fit_build_manifest.json").read_text())
    raw_anchors = json.loads((ANALYSIS / args.family / "anchors_at_candidate_layers.json").read_text())
    H = {rk: np.asarray(per[str(layer)], dtype=np.float64) for rk, per in raw_anchors.items() if str(layer) in per}

    # Reconstruct the frozen fit's u_d/c_hat/random_direction from the
    # committed direction JSONs written by dose_ladder.py's fit step
    # (this module does not refit; it consumes the already-frozen FIT fit).
    c_hat = np.asarray(json.loads((COMMITTED / args.family / f"hs{layer}_c_hat.json").read_text())["vector"])
    rand_dir = np.asarray(json.loads((COMMITTED / args.family / f"hs{layer}_random_direction.json").read_text())["vector"])
    u_d = np.asarray(json.loads((COMMITTED / args.family / f"hs{layer}_u_d.json").read_text())["vector"])
    fit_for_gate = {"u_d": u_d, "stats": {"mu_d": build_manifest["mu_d"], "sigma_d": build_manifest["sigma_d"]}}
    tau = build_manifest["tau_frozen"]

    scored = score_gate_on_heldout(held_all, H, fit_for_gate, tau)
    fired = [r for r in scored if r["fire"]]
    fired_confab = [r for r in fired if r["role"] == "confab"]
    fired_known = [r for r in fired if r["role"] == "known_correct_answered"]

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, mrows.decoder_block_index(layer))

    baseline_by_key = run_baseline_pass(model, tokenizer, device, args.family, held_all, args.batch_size)

    import torch

    hook_c, ctrl_c = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), build_manifest["sigma_c"])
    gated_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_c, layer_module, args.family, "gated",
        fired, float(dose_abs / build_manifest["sigma_c"]), args.batch_size,
    ) if fired else {}
    gated_all = combine_active_and_baseline(held_all, gated_active_by_key, baseline_by_key)
    gated_confab = [r for r in gated_all if r["role"] == "confab"]
    gated_known = [r for r in gated_all if r["role"] == "known_correct_answered"]
    gated_known_fired_only = [gated_active_by_key[r["row_key"]] for r in fired_known] if fired_known else []

    hook_r, ctrl_r = steer_lib.build_hook_and_controller(torch.tensor(rand_dir, dtype=torch.float32), 1.0)
    rand_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_r, layer_module, args.family, "random_direction",
        fired, float(dose_abs), args.batch_size,
    ) if fired else {}
    rand_all = combine_active_and_baseline(held_all, rand_active_by_key, baseline_by_key)
    rand_confab = [r for r in rand_all if r["role"] == "confab"]
    rand_known = [r for r in rand_all if r["role"] == "known_correct_answered"]

    dose_knowns_gain = float(dose_abs / build_manifest["sigma_c"])
    dku_active_by_key = run_active_pass(
        model, tokenizer, device, ctrl_c, layer_module, args.family, "dose_knowns_ungated",
        held_known, dose_knowns_gain, args.batch_size,
    )
    dku_all = [dku_active_by_key[r["row_key"]] for r in held_known]

    baseline_confab = [baseline_by_key[r["row_key"]] for r in held_confab]
    baseline_known = [baseline_by_key[r["row_key"]] for r in held_known]

    summary = {
        "family": args.family, "layer": layer, "dose_abs": dose_abs,
        "n_held_out_confab": len(held_confab), "n_held_out_known": len(held_known),
        "n_fired_confab": len(fired_confab), "n_fired_known": len(fired_known),
        "baseline": {
            "confab": gates_lib.rate_summary(baseline_confab),
            "known": gates_lib.rate_summary(baseline_known),
        },
        "gated": {
            "fired_confab": gates_lib.rate_summary([gated_active_by_key[r["row_key"]] for r in fired_confab]) if fired_confab else gates_lib.rate_summary([]),
            "known_full_population": gates_lib.rate_summary(gated_known),
            "known_fired_conditional": gates_lib.rate_summary(gated_known_fired_only),
        },
        "random_direction": {
            "confab": gates_lib.rate_summary(rand_confab),
            "known": gates_lib.rate_summary(rand_known),
        },
        "dose_knowns_ungated": {
            "known_all": gates_lib.rate_summary(dku_all),
            "clean_false_refusal": gates_lib.rate_wilson(dku_all, "refused"),
            "total_damage_rate": gates_lib.rate_wilson(dku_all, "not_well_formed_correct"),
            "metric_hygiene_note": (
                "clean_false_refusal (refused, comparable to the gated cost "
                "metric) and total_damage_rate (not_well_formed_correct, "
                "BROADER than refusal) are reported separately and must "
                "never be conflated (H4 metric-hygiene rule)."
            ),
            "pre_stated_reading": (
                "LOW clean_false_refusal => write is content-selective at "
                "this operating point; HIGH => write is non-selective and "
                "the gate supplies selectivity. Scoped to this family, site, "
                "and dose only."
            ),
        },
    }

    g1_refused = summary["gated"]["fired_confab"]["refused"]
    g1_well_formed_rate = summary["gated"]["fired_confab"]["well_formed"]["rate"]
    cost = summary["gated"]["known_full_population"]["refused"]
    placebo = gates_lib.g3i_pass(
        summary["random_direction"]["confab"]["refused"], summary["baseline"]["confab"]["refused"],
        summary["random_direction"]["known"]["refused"], summary["baseline"]["known"]["refused"],
    )
    gates = {
        "g1_refused_transfer_pass": gates_lib.g1_refused_transfer_pass(g1_refused),
        "g1_well_formed_pass": g1_well_formed_rate >= gates_lib.WELL_FORMED_FLOOR,
        "g1_cost_pass": gates_lib.g1_cost_pass(cost),
        "g3i": placebo,
    }
    summary["gates"] = gates
    summary["outcome_shape"] = gates_lib.classify_outcome_shape(
        fit_operating_point_exists=True,
        refused_transfer_pass=gates["g1_refused_transfer_pass"],
        well_formed_pass=gates["g1_well_formed_pass"],
        cost_pass=gates["g1_cost_pass"],
        placebo_pass=gates["g3i"]["passed"],
    )

    write_json(COMMITTED / args.family / "heldout_summary.json", summary)
    print(json.dumps(summary, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True, choices=("llama", "mistral"))
    ap.add_argument("--batch-size", type=int, default=8)
    ap.set_defaults(func=cmd_run)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
