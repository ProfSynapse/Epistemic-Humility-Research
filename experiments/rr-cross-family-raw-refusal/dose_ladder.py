#!/usr/bin/env python3
"""FIT dose-ladder module for rr-cross-family-raw-refusal.

Per family: for each candidate layer, fits u_d/c_hat/random_direction fresh
on FIT rows (direction_fit.py), computes the sigma-relative dose grid
{2,4,6,8,12,16,20} x sigma_c (cell.yaml `dose_policy.grid_sigma_relative`),
runs the pre-sweep token-movement bracket check, then sweeps the `gated` arm
over every (layer, dose) grid point on FIT fired confabs + the full FIT
known_correct_answered population, and selects the single (layer, dose)
operating point with the lowest dose whose FIT floors clear
(`gates_lib.fit_dose_viable` / `select_fit_operating_point`). If no point
qualifies, the family is recorded as outcome shape F and held-out scoring is
never launched for it (cell.yaml `dose_policy.fit_dose_selection.on_no_viable_dose`).

Mirrors `qwen35-4b-midband-doubt-snap/run_dose_ladder.py`'s structure (read
in full before writing this), generalized from one model's 4 layers to a
per-family loop over `cell.yaml`'s 3 candidate layers, and REPLACING that
script's `permuted_gate` arm (not a registered RR arm, open adjudication A3
declined) with nothing at the FIT stage -- RR's FIT sweep only needs the
`gated` arm to select a dose; `random_direction` and `dose_knowns_ungated`
are held-out-only arms (heldout_scorer.py).
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
for _p in (str(HERE),):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import direction_fit  # noqa: E402
import gates_lib  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
DOSE_MULTIPLIERS = (2, 4, 6, 8, 12, 16, 20)
SEED = 20260713
MAX_NEW = 200


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(family: str, tag: str) -> Path:
    return ANALYSIS / family / "runlog" / f"{tag}.jsonl"


def fit_all_layers(
    family: str, fit_rows: list[dict[str, Any]], anchors: dict[str, dict[int, np.ndarray]],
    candidate_layers: list[int], hidden_dim: int,
) -> dict[int, dict[str, Any]]:
    """Runs direction_fit.fit_directions TWICE per layer and asserts
    byte-identical (G0 directions_byte_identical) before returning any
    layer's fit."""
    out: dict[int, dict[str, Any]] = {}
    for layer in candidate_layers:
        H = {rk: anchors[rk][layer] for rk in anchors if layer in anchors[rk]}
        fit1 = direction_fit.fit_directions(fit_rows, H, layer, hidden_dim, SEED)
        fit2 = direction_fit.fit_directions(fit_rows, H, layer, hidden_dim, SEED)
        if not direction_fit.fit_byte_identical(fit1, fit2):
            raise SystemExit(f"G0 directions_byte_identical FAIL at layer {layer}")
        gate = direction_fit.fit_gate(fit1)
        if gate["auc_neg_z_d_on_fit"] < gates_lib.FIT_GATE_AUC_FLOOR:
            raise SystemExit(
                f"G0 fit_gate_auc_floor FAIL at layer {layer}: "
                f"AUC={gate['auc_neg_z_d_on_fit']:.4f} < {gates_lib.FIT_GATE_AUC_FLOOR}"
            )
        out[layer] = {"fit": fit1, "gate": gate}
    return out


def dose_grid_abs(sigma_c: float) -> list[float]:
    return [round(m * sigma_c, 6) for m in DOSE_MULTIPLIERS]


def pre_sweep_bracket_check(
    strongest_dose_abs: float, probe_readback_rel_to_baseline: list[float],
) -> dict[str, Any]:
    """cell.yaml dose_policy.pre_sweep_bracketing: the grid's strongest arm
    must move tokens on probe rows. `probe_readback_rel_to_baseline` is one
    float per probe row: 0.0 means byte-identical output at the strongest
    dose (the mistral late-site signature this check exists to catch), any
    nonzero value means tokens moved. If every probe row is byte-identical,
    the grid needs the ONE permitted pre-sweep/pre-outcome re-bracket
    (log-span the empirically bracketed response region) -- this module
    reports that condition and stops rather than silently re-bracketing,
    since choosing a NEW grid is a registered dose-policy action the lead
    adjudicates, not a default the harness takes on its own."""
    moved = [x for x in probe_readback_rel_to_baseline if x != 0.0]
    passed = len(moved) > 0
    return {
        "strongest_dose_abs": strongest_dose_abs,
        "n_probe_rows": len(probe_readback_rel_to_baseline),
        "n_rows_with_token_movement": len(moved),
        "passed": passed,
        "action_if_failed": (
            "re-bracket pre-sweep and pre-outcome to log-span the empirically "
            "bracketed response region (cell.yaml dose_policy.pre_sweep_bracketing); "
            "this is the ONLY permitted grid change and this module does not "
            "apply it automatically -- it stops and reports for the lead to "
            "re-run with a new --dose-multipliers override."
        ),
    }


def sweep_layer_doses(
    model, tokenizer, device, layer, sigma_c: float, direction_vec, fired_confab_rows, known_rows, baseline_known_by_key, batch_size: int, family: str,
) -> list[dict[str, Any]]:
    """Runs the `gated` arm over every dose in this layer's grid, on FIT
    fired confabs (active for every dose) plus the full FIT
    known_correct_answered population (active for every dose too, per
    cell.yaml's fit_dose_selection rule: 'FIT known false-refusal <= 0.10' is
    evaluated on the SAME dosed pass, not baseline). Returns one record per
    dose with the FIT summaries `gates_lib.fit_dose_viable` needs."""
    from MechInterp.intervention import get_decoder_layer

    hook, controller = steer_lib.build_hook_and_controller(direction_vec, sigma_c)
    layer_module = get_decoder_layer(model, mrows.decoder_block_index(layer))
    handle = layer_module.register_forward_hook(controller)
    results = []
    try:
        for mult in DOSE_MULTIPLIERS:
            dose_abs = round(mult * sigma_c, 6)
            gain = float(mult)
            tag = f"hs{layer}__gated__dose{mult}"
            log = _run_log(family, tag, {"family": family, "layer": layer, "mult": mult, "seed": SEED})
            all_rows = fired_confab_rows + known_rows
            gains = {r["row_key"]: gain for r in all_rows}
            steer_lib.run_rows(
                model, tokenizer, device, controller, "gen_stream", all_rows, gains,
                MAX_NEW, batch_size, log, lambda r: r["row_key"],
            )
            log.finalize({"n_rows": len(all_rows), "dose_abs": dose_abs, "gain": gain})
            log.close()
            recs = {r["row_key"]: r for r in load_jsonl(runlog_path(family, tag))}
            confab_recs = [recs[r["row_key"]] for r in fired_confab_rows]
            known_recs = [recs[r["row_key"]] for r in known_rows]
            confab_refused = gates_lib.rate_wilson(confab_recs, "refused")
            confab_well_formed = gates_lib.rate_wilson(confab_recs, "well_formed")
            known_false_refusal = gates_lib.rate_wilson(known_recs, "refused")
            viable = gates_lib.fit_dose_viable(confab_refused, confab_well_formed, known_false_refusal)
            results.append({
                "layer": layer, "dose_mult": mult, "dose_abs": dose_abs, "gain": gain,
                "n_fired_confab": len(fired_confab_rows), "n_known": len(known_rows),
                "confab_refused": confab_refused, "confab_well_formed": confab_well_formed,
                "known_false_refusal": known_false_refusal, "viable": viable,
            })
    finally:
        handle.remove()
        controller.reset()
    return results


def _run_log(family: str, tag: str, run_config: dict[str, Any]):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(family, tag), run_config=run_config)


def cmd_run(args: argparse.Namespace) -> int:
    fcell = mrows.family_cell(args.family)
    revision = mrows.resolve_revision(args.family)
    pdir = ANALYSIS / args.family
    joined_path = pdir / "joined_rows_private.jsonl"
    if not joined_path.is_file():
        raise SystemExit(
            f"missing {joined_path}; run materialize_rows.py --family {args.family} first "
            "(requires staged private inputs -- see that module's docstring)."
        )
    rows = load_jsonl(joined_path)
    fit_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "fit"]
    fit_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "fit"]
    unknown = [r for r in rows if r["role"] == "unknown_refused"]
    fit_rows = fit_confab + fit_known + unknown

    anchor_path = pdir / "anchors_at_candidate_layers.json"
    if not anchor_path.is_file():
        raise SystemExit(
            f"missing {anchor_path}; this harness expects materialize_rows.py "
            "to have extracted anchors at the candidate layers into this file "
            "(GPU capture step, deferred -- see NOTEBOOK.md)."
        )
    raw_anchors = json.loads(anchor_path.read_text())
    anchors = {rk: {int(l): np.asarray(v, dtype=np.float64) for l, v in per.items()} for rk, per in raw_anchors.items()}

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    hidden_dim = model.config.hidden_size if hasattr(model.config, "hidden_size") else model.config.text_config.hidden_size

    fits = fit_all_layers(args.family, fit_rows, anchors, fcell["candidate_layers"], hidden_dim)

    all_candidates: list[dict[str, Any]] = []
    for layer in fcell["candidate_layers"]:
        fit = fits[layer]["fit"]
        gate = fits[layer]["gate"]
        H_for_gate = {rk: anchors[rk][layer] for rk in anchors if layer in anchors[rk]}
        confab_scored = direction_fit.score_and_fire([r for r in fit_confab], H_for_gate, fit, gate["tau_frozen"])
        fired_confab = [r for r in confab_scored if r["fire"]]

        import torch
        direction_vec = torch.tensor(fit["c_hat"], dtype=torch.float32)
        sigma_c = fit["stats"]["sigma_c"]
        results = sweep_layer_doses(
            model, tokenizer, device, layer, sigma_c, direction_vec,
            fired_confab, fit_known, {}, args.batch_size, args.family,
        )
        all_candidates.extend(results)
        write_json(COMMITTED / args.family / f"hs{layer}_fit_build_manifest.json", {**gate, **fit["stats"], "layer": layer})

    selected = gates_lib.select_fit_operating_point(all_candidates)
    report = {
        "family": args.family, "candidates": all_candidates,
        "selected_operating_point": selected,
        "outcome_shape_if_no_heldout_run": None if selected else "F",
    }
    write_json(COMMITTED / args.family / "fit_dose_ladder_report.json", report)
    print(json.dumps(report, indent=2, default=str), flush=True)
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
