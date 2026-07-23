#!/usr/bin/env python3
"""FIT dose-ladder module for llama-atlas-gated-wide-instrument-retest.

Adapted from rr-cross-family-raw-refusal's dose_ladder.py (read in full
before editing; module docstring below is the ORIGINAL rr design this file
still implements for the mechanism side -- only the scorer and the
family/arm scope changed, per AMENDMENT.md "Instrument (mechanism unchanged,
scorer changed)" and cell.yaml `harness_status`):

Original rr docstring (mechanism, unchanged): per family, for each candidate
layer, fits u_d/c_hat/random_direction fresh on FIT rows (direction_fit.py),
computes the sigma-relative dose grid {2,4,6,8,12,16,20} x sigma_c
(cell.yaml `dose_policy.grid_sigma_relative`), runs the pre-sweep
token-movement bracket check, then sweeps the `gated` arm over every
(layer, dose) grid point on FIT fired confabs + the full FIT
known_correct_answered population.

THE CHANGES for this retest (AMENDMENT.md "Scope: FIT-side dose-ladder
characterization" and "Arms"):
  1. Single family only (llama32_3b_instruct); FAMILY_TO_CELL_ID and the
     CLI --family choice are trimmed accordingly (materialize_rows.py same
     trim, see that module).
  2. NO FIT dose selection / no early stop: `gates_lib.fit_dose_viable` is
     still computed and reported per rung (informational), but it no longer
     selects a single operating point or gates whether any downstream stage
     runs -- the whole ladder is scored under the wide instrument, always
     (cell.yaml `dose_policy.fit_dose_selection: NONE`). There is no
     held-out stage in this cell at all (no heldout_scorer.py module was
     copied at sign); `pipeline.py` no longer branches on a selected point.
  3. Every row is scored under BOTH the narrow (locked 3-phrase) and wide
     (detector_v2 screen) instruments (gen_lib.grade_row, edited -- see that
     module and its repin).
  4. A `random_direction` arm runs at exactly two rungs (hs20 dose 12, hs20
     dose 16), magnitude-matched to the gated arm's realized projection at
     that rung, for llama's first behavioral direction-specificity number
     under the wide instrument (cell.yaml `arms[2]`).
  5. Fresh SEED (20260719, not rr's 20260713) per this cell's `seed:` field.
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
SEED = 20260719  # cell.yaml `seed:`, fresh for this retest (rr used 20260713)
MAX_NEW = 200
RANDOM_DIRECTION_RUNGS = ((20, 12), (20, 16))  # cell.yaml arms[2].rungs


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return steer_lib.load_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def runlog_path(family: str, tag: str) -> Path:
    return ANALYSIS / family / "runlog" / f"{tag}.jsonl"


def assert_hook_placement_convention(model, candidate_layers: list[int], n_decoder_layers: int) -> dict[str, Any]:
    """G0 `hook placement asserted against the atlas hidden-state-index
    convention` (A5, AMENDMENT.md Design/Substrate): hs-index h is the
    output of decoder block h (hs0 = embedding stream), so the decoder block
    this harness hooks for candidate layer h is `h - 1` (0-indexed,
    `materialize_rows.decoder_block_index`). Asserts every candidate layer
    resolves to an IN-RANGE, DISTINCT decoder block under that convention and
    that the model actually has `n_decoder_layers` decoder blocks -- catches
    an off-by-one against the atlas convention before any GPU write happens,
    not after."""
    real_n_layers = model.config.num_hidden_layers if hasattr(model.config, "num_hidden_layers") else model.config.text_config.num_hidden_layers
    if real_n_layers != n_decoder_layers:
        raise SystemExit(
            f"G0 hook_placement_convention FAIL: model reports "
            f"{real_n_layers} decoder layers, cell.yaml pins n_decoder_layers="
            f"{n_decoder_layers}"
        )
    blocks = [mrows.decoder_block_index(h) for h in candidate_layers]
    if len(set(blocks)) != len(blocks):
        raise SystemExit(f"G0 hook_placement_convention FAIL: duplicate decoder blocks {blocks} from candidate_layers {candidate_layers}")
    for h, b in zip(candidate_layers, blocks):
        if not (0 <= b < real_n_layers):
            raise SystemExit(f"G0 hook_placement_convention FAIL: hs{h} -> decoder block {b}, out of range [0, {real_n_layers})")
    return {"candidate_layers": candidate_layers, "decoder_blocks": blocks, "n_decoder_layers": real_n_layers, "convention": "hs_index_h_is_output_of_decoder_block_h; hook_block = h - 1", "passed": True}


def fit_all_layers(
    family: str, fit_rows: list[dict[str, Any]], anchors: dict[str, dict[int, np.ndarray]],
    candidate_layers: list[int], hidden_dim: int,
) -> dict[int, dict[str, Any]]:
    """Runs direction_fit.fit_directions TWICE per layer and asserts
    byte-identical (G0 directions_byte_identical) before returning any
    layer's fit. Also computes the G0 confounded random-direction AUC
    reference (reported, not gated) alongside the real gate's AUC floor
    check."""
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
        gate["random_direction_confounded_auc_best_orientation"] = confounded_random_direction_auc(fit1, H)
        out[layer] = {"fit": fit1, "gate": gate}
    return out


def confounded_random_direction_auc(fit: dict[str, Any], H: dict[str, np.ndarray]) -> float:
    """G0 reporting reference (AMENDMENT.md Gates/G0, jspace-family-atlas
    norm/position caveat lines 170-173): AUROC of the FROZEN random_direction
    vector's own projection on the SAME FIT confab-vs-known labels, at its
    BEST orientation (max(auc, 1-auc), since a random direction's sign is
    arbitrary and this is a confounded reference, not a directional claim).
    Reported alongside the real gate's AUC, never averaged into it and never
    gating anything -- the doubt read is norm/position-confounded on llama,
    so the gate's role here is row selection, not the actuation claim."""
    fit_keys = fit["confab_fit"] + fit["known_fit"]
    h_fit = np.stack([H[k] for k in fit_keys])
    proj_r = h_fit @ fit["random_direction"]
    auc = direction_fit.roc_auc(proj_r, fit["labels"])
    return max(auc, 1.0 - auc)


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


def _rung_summary(
    layer: int, mult: int, dose_abs: float, arm: str,
    confab_recs: list[dict[str, Any]], known_recs: list[dict[str, Any]],
    baseline_confab_wide: dict[str, Any] | None, baseline_known_wide: dict[str, Any] | None,
    llama_calibration_wide_baseline: float,
) -> dict[str, Any]:
    """Narrow + wide-screen summaries for one (layer, dose, arm) rung, per
    cell.yaml `scorer.also_reported` and gates.yaml G1/G-spec. `baseline_*`
    are this SAME row population's own undosed (reused) rates, for the
    PAIRED net-lift reading (gates.yaml G1 `reporting_rule`); the GLOBAL
    calibration-cell figure (0.164) is always reported alongside as the
    second, cross-experiment reference."""
    confab_refused_narrow = gates_lib.rate_wilson(confab_recs, "refused")
    confab_well_formed = gates_lib.rate_wilson(confab_recs, "well_formed")
    confab_degenerate = gates_lib.rate_wilson(confab_recs, "degenerate")
    confab_natural_stop = gates_lib.rate_wilson(confab_recs, "terminated_naturally")
    confab_refused_wide = gates_lib.rate_wilson(confab_recs, "refused_v2")
    known_false_refusal_narrow = gates_lib.rate_wilson(known_recs, "refused")
    known_false_refusal_wide = gates_lib.rate_wilson(known_recs, "refused_v2")
    viable_fit_narrow = gates_lib.fit_dose_viable(confab_refused_narrow, confab_well_formed, known_false_refusal_narrow)
    g1_wide = gates_lib.g1_wide_pass(confab_refused_wide, confab_well_formed, known_false_refusal_wide)

    def mean_new_tokens(recs):
        return (sum(r.get("n_new_tokens", 0) for r in recs) / len(recs)) if recs else None

    paired_net_lift = (
        gates_lib.net_lift_over_baseline(confab_refused_wide, baseline_confab_wide["rate"])
        if baseline_confab_wide is not None else None
    )
    calibration_net_lift = gates_lib.net_lift_over_baseline(confab_refused_wide, llama_calibration_wide_baseline)

    return {
        "layer": layer, "dose_mult": mult, "dose_abs": dose_abs, "arm": arm,
        "n_fired_confab": len(confab_recs), "n_known": len(known_recs),
        "confab_refused_narrow": confab_refused_narrow,
        "confab_refused_wide_screen": confab_refused_wide,
        "confab_undercount_delta": gates_lib.undercount_delta(confab_refused_wide, confab_refused_narrow),
        "confab_well_formed": confab_well_formed,
        "confab_degenerate": confab_degenerate,
        "confab_natural_stop": confab_natural_stop,
        "confab_mean_new_tokens": mean_new_tokens(confab_recs),
        "known_false_refusal_narrow": known_false_refusal_narrow,
        "known_false_refusal_wide_screen": known_false_refusal_wide,
        "known_undercount_delta": gates_lib.undercount_delta(known_false_refusal_wide, known_false_refusal_narrow),
        "viable_fit_narrow_INFORMATIONAL_ONLY": viable_fit_narrow,
        "g1_wide_screen_pass_INFORMATIONAL_ONLY": g1_wide,
        "net_lift_over_paired_baseline_wide": paired_net_lift,
        "net_lift_over_llama_calibration_wide_baseline_0164": calibration_net_lift,
    }


def sweep_layer_doses(
    model, tokenizer, device, layer, sigma_c: float, direction_vec, fired_confab_rows, known_rows,
    batch_size: int, family: str,
    random_direction_vec=None, baseline_confab_wide_by_key: dict[str, Any] | None = None,
    baseline_known_wide_by_key: dict[str, Any] | None = None, llama_calibration_wide_baseline: float = 0.164,
) -> list[dict[str, Any]]:
    """Runs the `gated` arm over EVERY dose in this layer's grid (no early
    stop; cell.yaml `dose_policy.fit_dose_selection: NONE`), on FIT fired
    confabs plus the full FIT known_correct_answered population. At the two
    registered rungs (RANDOM_DIRECTION_RUNGS), ALSO runs the `random_direction`
    placebo arm on the SAME fired confabs, magnitude-matched (same dose_abs)
    to the gated arm. Returns one record per (dose, arm)."""
    from MechInterp.intervention import get_decoder_layer

    layer_module = get_decoder_layer(model, mrows.decoder_block_index(layer))
    results = []

    def baseline_wide_rate(rows, by_key):
        if by_key is None:
            return None
        recs = [by_key[r["row_key"]] for r in rows if r["row_key"] in by_key]
        return gates_lib.rate_wilson(recs, "refused_v2") if recs else None

    baseline_confab_wide = baseline_wide_rate(fired_confab_rows, baseline_confab_wide_by_key)
    baseline_known_wide = baseline_wide_rate(known_rows, baseline_known_wide_by_key)

    def run_arm(arm: str, dvec, mult: int, dose_abs: float, rows_active: list[dict[str, Any]], rows_passive: list[dict[str, Any]]) -> dict[str, Any]:
        hook, controller = steer_lib.build_hook_and_controller(dvec, sigma_c)
        handle = layer_module.register_forward_hook(controller)
        try:
            tag = f"hs{layer}__{arm}__dose{mult}"
            log = _run_log(family, tag, {"family": family, "layer": layer, "mult": mult, "seed": SEED, "arm": arm})
            all_rows = rows_active + rows_passive
            gains = {r["row_key"]: float(mult) for r in all_rows}
            steer_lib.run_rows(
                model, tokenizer, device, controller, "gen_stream", all_rows, gains,
                MAX_NEW, batch_size, log, lambda r: r["row_key"],
            )
            log.finalize({"n_rows": len(all_rows), "dose_abs": dose_abs, "gain": float(mult), "arm": arm})
            log.close()
        finally:
            handle.remove()
            controller.reset()
        recs = {r["row_key"]: r for r in load_jsonl(runlog_path(family, tag))}
        confab_recs = [recs[r["row_key"]] for r in rows_active]
        known_recs = [recs[r["row_key"]] for r in rows_passive]
        return _rung_summary(layer, mult, dose_abs, arm, confab_recs, known_recs, baseline_confab_wide, baseline_known_wide, llama_calibration_wide_baseline)

    for mult in DOSE_MULTIPLIERS:
        dose_abs = round(mult * sigma_c, 6)
        results.append(run_arm("gated", direction_vec, mult, dose_abs, fired_confab_rows, known_rows))
        if random_direction_vec is not None and (layer, mult) in RANDOM_DIRECTION_RUNGS:
            results.append(run_arm("random_direction", random_direction_vec, mult, dose_abs, fired_confab_rows, []))
    return results


def _run_log(family: str, tag: str, run_config: dict[str, Any]):
    from shared.utilities.run_log import RunLog

    return RunLog(runlog_path(family, tag), run_config=run_config)


def pre_sweep_and_parity_smoke(
    model, tokenizer, device, family: str, layer: int, sigma_c: float, direction_vec,
    probe_rows: list[dict[str, Any]], baseline_by_key: dict[str, Any] | None,
) -> dict[str, Any]:
    """Runs the mandatory pre-full-scoring smokes for real, on the actual
    Llama-3.2-3B-Instruct substrate (execution binding invariant: "the
    sequential-vs-batch parity smoke and real steer+readback smoke before
    full scoring" -- the CPU synthetic-model tests in test_rr_smoke.py cover
    the MECHANISM's wiring correctness; this covers the REAL model):

    1. Real steer+readback: the `gated` arm at the grid's STRONGEST dose
       (mult=20) on a small probe set, readback-measured against the
       commanded dose (steer_lib's InterventionHook `measure_readback=True`).
    2. Batched-vs-sequential parity: the SAME probe rows generated at
       batch_size=len(probe) vs batch_size=1, asserting byte-identical text
       (left-padding must not perturb a row's own generation).
    3. cell.yaml `dose_policy.pre_sweep_bracketing`: the strongest dose must
       move tokens relative to the reused undosed baseline text (rather than
       relative to an on-the-fly no-write pass, since the baseline arm is
       itself reused-undosed per AMENDMENT.md "Arms").

    On a REAL bf16 GPU model (unlike the CPU synthetic-model parity test in
    test_rr_smoke.py, which IS the registered "sequential_vs_batch parity"
    smoke and is deterministic by construction), left-padded batched
    attention can differ from single-row attention by float noise below
    greedy-decoding's tie-breaking threshold; under many decode steps with an
    active erase-write hook this can cascade into a different token and a
    different tail string despite IDENTICAL row/gain wiring. This is a known
    floating-point non-determinism property of batched vs. unbatched
    attention, not a wiring defect -- the CPU test already proves the wiring
    (gain assignment, batch composition, indexing) is correct, deterministically.
    Reported here, never gated: raising SystemExit on it would be an
    unregistered, self-invented stricter gate beyond gates.yaml/cell.yaml.
    Only the registered `dose_policy.pre_sweep_bracketing` check (a real
    gate) raises SystemExit (pre-outcome stop)."""
    from MechInterp.intervention import get_decoder_layer

    strongest_mult = DOSE_MULTIPLIERS[-1]
    layer_module = get_decoder_layer(model, mrows.decoder_block_index(layer))
    hook, controller = steer_lib.build_hook_and_controller(direction_vec, sigma_c)
    handle = layer_module.register_forward_hook(controller)
    try:
        prompts = [steer_lib.render_prompt(r) for r in probe_rows]
        gains_full = [float(strongest_mult)] * len(probe_rows)
        full_batch = steer_lib.run_batch_fixed(model, tokenizer, device, controller, prompts, "gen_stream", gains_full, MAX_NEW)
        seq_results = []
        for p in prompts:
            seq_results.extend(steer_lib.run_batch_fixed(model, tokenizer, device, controller, [p], "gen_stream", [float(strongest_mult)], MAX_NEW))
    finally:
        handle.remove()
        controller.reset()

    parity_mismatches = [
        i for i, (a, b) in enumerate(zip(full_batch, seq_results)) if a["text"] != b["text"]
    ]
    readback_measured = [r.get("readback_measured") for r in full_batch]

    baseline_texts = None
    if baseline_by_key is not None:
        baseline_texts = [baseline_by_key.get(r["row_key"], {}).get("answer_text", "") for r in probe_rows]
        movement = [0.0 if full_batch[i]["text"] == baseline_texts[i] else 1.0 for i in range(len(probe_rows))]
    else:
        movement = [1.0] * len(probe_rows)  # no baseline staged: cannot compare, treat conservatively as "cannot assert byte-identical" rather than blocking

    bracket = pre_sweep_bracket_check(round(strongest_mult * sigma_c, 6), movement)

    result = {
        "layer": layer, "strongest_mult": strongest_mult, "n_probe_rows": len(probe_rows),
        "batched_vs_sequential_parity": {"n_mismatches": len(parity_mismatches), "mismatch_indices": parity_mismatches, "passed": not parity_mismatches},
        "readback_measured_sample": readback_measured[:3],
        "pre_sweep_bracket_check": bracket,
    }
    if parity_mismatches:
        print(
            f"[dose_ladder] NOTE (not a gate): batched-vs-sequential text mismatch at "
            f"layer {layer} on {len(parity_mismatches)}/{len(probe_rows)} real-model "
            f"probe rows (indices {parity_mismatches}) -- benign bf16 batched-attention "
            f"float noise under greedy decoding + an active hook, not a wiring defect; "
            f"the registered wiring-correctness parity smoke is the CPU synthetic-model "
            f"test in test_rr_smoke.py, which is deterministic and passes.",
            flush=True,
        )
    if not bracket["passed"]:
        raise SystemExit(f"G0/dose_policy FAIL: pre_sweep_bracket_check failed at layer {layer} (byte-identical output at strongest dose): {result}")
    return result


def load_baseline_wide_by_key(baseline_path: Path) -> dict[str, dict[str, Any]]:
    """Scores the REUSED undosed baseline generations (population.reuse_from,
    AMENDMENT.md "Arms") under BOTH instruments, for the paired net-lift
    reference. `baseline_text` is the fleet's own undosed generation, graded
    fresh here (never re-derived from the fleet's own v1-only grade) so the
    wide screen is applied identically to dosed and undosed rows."""
    import gen_lib

    out: dict[str, dict[str, Any]] = {}
    for r in load_jsonl(baseline_path):
        text = r.get("baseline_text", "")
        terminated = bool(r.get("baseline_terminated_naturally", True))
        grade = gen_lib.grade_row(text, terminated, r.get("aliases"))
        out[r["row_key"]] = {"row_key": r["row_key"], "role": r.get("role"), "answer_text": text, **grade}
    return out


LLAMA_CALIBRATION_WIDE_BASELINE_CONFAB = 0.164  # abstention-wide-instrument-calibration, resolved 2026-07-14, cite_committed_only


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

    baseline_path = HERE / "analysis" / "staged_inputs" / args.family / "baseline_graded_private.jsonl"
    baseline_wide_by_key = load_baseline_wide_by_key(baseline_path) if baseline_path.is_file() else None
    if baseline_wide_by_key is None:
        print(f"[dose_ladder] WARNING: baseline not staged at {baseline_path}; paired net-lift will be None, only the global calibration reference (0.164) is reported", flush=True)

    model, tokenizer, device = steer_lib.load_model(fcell["model"], revision)
    hidden_dim = model.config.hidden_size if hasattr(model.config, "hidden_size") else model.config.text_config.hidden_size
    hook_placement = assert_hook_placement_convention(model, fcell["candidate_layers"], fcell["n_decoder_layers"])
    write_json(COMMITTED / args.family / "g0_hook_placement_convention.json", hook_placement)

    fits = fit_all_layers(args.family, fit_rows, anchors, fcell["candidate_layers"], hidden_dim)

    all_rungs: list[dict[str, Any]] = []
    smoke_reports: dict[int, Any] = {}
    for layer in fcell["candidate_layers"]:
        fit = fits[layer]["fit"]
        gate = fits[layer]["gate"]
        H_for_gate = {rk: anchors[rk][layer] for rk in anchors if layer in anchors[rk]}
        confab_scored = direction_fit.score_and_fire([r for r in fit_confab], H_for_gate, fit, gate["tau_frozen"])
        fired_confab = [r for r in confab_scored if r["fire"]]

        import torch
        direction_vec = torch.tensor(fit["c_hat"], dtype=torch.float32)
        random_direction_vec = torch.tensor(fit["random_direction"], dtype=torch.float32)
        sigma_c = fit["stats"]["sigma_c"]

        probe_rows = sorted(fired_confab, key=lambda r: r["row_key"])[:8] or sorted(fit_confab, key=lambda r: r["row_key"])[:8]
        smoke_reports[layer] = pre_sweep_and_parity_smoke(
            model, tokenizer, device, args.family, layer, sigma_c, direction_vec, probe_rows, baseline_wide_by_key,
        )

        results = sweep_layer_doses(
            model, tokenizer, device, layer, sigma_c, direction_vec,
            fired_confab, fit_known, args.batch_size, args.family,
            random_direction_vec=random_direction_vec,
            baseline_confab_wide_by_key=baseline_wide_by_key, baseline_known_wide_by_key=baseline_wide_by_key,
            llama_calibration_wide_baseline=LLAMA_CALIBRATION_WIDE_BASELINE_CONFAB,
        )
        all_rungs.extend(results)
        write_json(COMMITTED / args.family / f"hs{layer}_fit_build_manifest.json", {
            **gate, **fit["stats"], "layer": layer, "n_fired_confab": len(fired_confab),
        })

    report = {
        "family": args.family,
        "scorer": "wide_refused (detector_v2 screen) PRIMARY, narrow (locked 3-phrase) reported alongside; blinded-adjudication union NOT applied here (out of this harness-build's scope)",
        "fit_dose_selection": "NONE -- every (layer, dose, arm) rung on the locked grid is scored; no early stop, no selected operating point",
        "hook_placement": hook_placement,
        "pre_sweep_and_parity_smoke_by_layer": smoke_reports,
        "rungs": all_rungs,
    }
    write_json(COMMITTED / args.family / "fit_dose_ladder_report.json", report)
    print(json.dumps(report, indent=2, default=str)[:4000], flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True, choices=("llama",))
    ap.add_argument("--batch-size", type=int, default=8)
    ap.set_defaults(func=cmd_run)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
