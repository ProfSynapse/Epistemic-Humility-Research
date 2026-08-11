#!/usr/bin/env python3
"""Stage 8 (GPU, bespoke -- see gap note below): two-site pairs, three,
magnitude-matched (AMENDMENT.md Run plan row 8; cell.yaml `multi_site`, Axis
4; gates.yaml G3 companion reporting only -- no gate is scored on pairs
directly, they are recorded).

CAPABILITY GAP (documented, not a workaround-by-editing-the-submodule):
`MechInterp.config.SteerCellConfig.law` declares exactly ONE readout/layer
per run, and `run_steer` builds exactly one `InterventionHook` +
`GenerationInterventionController` registered on one decoder layer (read in
full: `cli.py::run_steer`, `cell.py`). AMENDMENT.md's Run-plan preamble says
"Stages are `mechinterp` verbs driven by recipe YAML... no bespoke runner",
but a simultaneous two-site write has no such recipe verb to drive: it needs
TWO InterventionHook instances (one per site's own c_hat, own layer, own
sigma) registered on two different decoder-layer modules at once. PyTorch
forward hooks on different modules compose naturally within one
model.generate() call (each layer's hook fires as the model's own forward
pass reaches that layer), so this is mechanically simple -- the gap is purely
that the CLI/config layer has no schema for "two simultaneous readouts". This
script is therefore the one genuinely bespoke driver in this harness,
reusing `MechInterp.cell.row_key_of` / `pending_rows`-equivalent resume logic
and `MechInterp.intervention.{InterventionHook,get_decoder_layer}` directly
(no submodule edits), mirroring `cli.py::_run_one_pass`'s begin/generate/
reset shape for two controllers instead of one.

AMBIGUITY (flagged, not silently resolved -- confirm with lead before the
real run):
  1. cell.yaml `multi_site.magnitude_match`: "split the best single site's
     calibrated dose across the two members so total commanded displacement
     matches" does not say HOW to split. This script splits the total setpoint
     EQUALLY (setpoint_A = setpoint_B = total_setpoint / 2, each converted to
     that site's own gain via gain = setpoint / sigma_site), the simplest
     reading, but an unequal split (e.g. proportional to each site's own
     single-site calibrated setpoint) is equally consistent with the prose.
  2. Pair-selection rules reference "best in-band" / "best out-of-band" /
     "lowest eligible" / "highest eligible" without defining the ranking key
     or the in-band/out-of-band partition explicitly as a formula. This
     script reads: eligible = site has >=1 dose-viable (SELECTED) (site,
     position) cell; rank key = that cell's `fit_confab_clean_tighten`
     (the same key `dose_calibrate.py`'s own selection_rule uses, for
     consistency); in-band = site.status containing "in_band" (only
     hs13/hs16/hs19 in the current registered site table); "lowest"/"highest"
     = by `relative_depth`. A different partition (e.g. treating
     `anchor_band_upper_edge` as in-band) changes which 3 pairs are drawn.

Output: `analysis/pairs_<substrate>_<pair_name>_<position>/output.jsonl`
(resumable checkpoint) and `analysis-committed/<substrate>/pairs_summary.json`
(pair definitions, split setpoints, per-pair confab_held_out clean_tighten
rate + Wilson CI, no row text). Recorded per
`multi_site.insufficient_sites_disposition` as NOT_RUN if fewer than two
eligible sites exist.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    DIRECTIONS_DIR,
    POSITION_TO_GENERATION_MODE,
    POSITIONS,
    base_repo_and_revision,
    install_pinned_loader,
    load_cell,
    load_jsonl,
    load_split_manifest,
    rows_with_text_path,
    split_manifest_path,
    all_sites,
    substrate_config,
    wilson_ci_point,
    write_json,
    write_jsonl_row,
)
from materialize_configs import generation_contract  # noqa: E402
from gate_scoring import gate_score_for_rows  # noqa: E402
import grader_sweep  # noqa: E402


def eligible_sites(substrate: str, cell: dict) -> dict:
    """site.name -> {site, best_cell_key, fit_confab_clean_tighten, gain, setpoint, sigma}."""
    disp_path = COMMITTED / substrate / "dose_disposition.json"
    if not disp_path.exists():
        return {}
    disp = json.loads(disp_path.read_text())["cells"]
    sites = all_sites(cell)
    out = {}
    for key, c in disp.items():
        if c.get("status") != "SELECTED":
            continue
        site_name = key.split(":")[0]
        rung = c["selected_rung"]
        best = out.get(site_name)
        if best is None or rung["fit_confab_clean_tighten"] > best["fit_confab_clean_tighten"]:
            out[site_name] = {
                "site": sites[site_name], "cell_key": key,
                "fit_confab_clean_tighten": rung["fit_confab_clean_tighten"],
                "setpoint": rung["setpoint"], "sigma": c["sigma"],
            }
    return out


def select_pairs(eligible: dict) -> list[tuple[str, str, str]]:
    """Returns [(pair_name, site_a, site_b), ...] per cell.yaml selection_rules."""
    names = list(eligible)
    in_band = sorted((n for n in names if "in_band" in eligible[n]["site"].status),
                      key=lambda n: -eligible[n]["fit_confab_clean_tighten"])
    out_band = sorted((n for n in names if "in_band" not in eligible[n]["site"].status),
                       key=lambda n: -eligible[n]["fit_confab_clean_tighten"])
    by_depth = sorted(names, key=lambda n: eligible[n]["site"].relative_depth)

    pairs = []
    if len(in_band) >= 2:
        pairs.append(("best_in_band_x_second_best_in_band", in_band[0], in_band[1]))
    if in_band and out_band:
        pairs.append(("best_in_band_x_best_out_of_band", in_band[0], out_band[0]))
    if len(by_depth) >= 2:
        pairs.append(("lowest_eligible_x_highest_eligible", by_depth[0], by_depth[-1]))
    return pairs


def run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("Refusing to run a GPU verb without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    import os
    os.environ["SWEEP_SUBSTRATE"] = args.substrate

    cell = load_cell()
    sub_cfg = substrate_config(args.substrate, cell)
    eligible = eligible_sites(args.substrate, cell)
    if len(eligible) < 2:
        out_path = COMMITTED / args.substrate / "pairs_summary.json"
        write_json(out_path, {"substrate": args.substrate,
                               "status": "NOT_RUN_insufficient_eligible_sites",
                               "n_eligible": len(eligible)})
        print(f"[pairs:{args.substrate}] NOT_RUN: only {len(eligible)} eligible site(s).", flush=True)
        return 0

    pairs = select_pairs(eligible)
    install_pinned_loader(sub_cfg.get("adapter_revision"))
    import torch
    from MechInterp.cli import _generation_kwargs
    from MechInterp.config import GenerationContract
    from MechInterp.intervention import InterventionHook, GenerationInterventionController, get_decoder_layer
    from render_sweep import render as render_fn
    from sweep_lib import pinned_load_model_and_tokenizer

    base_repo, base_revision = base_repo_and_revision(args.substrate, cell)
    model, tokenizer = pinned_load_model_and_tokenizer(
        base_repo, sub_cfg.get("adapter_repo"), base_revision, sub_cfg.get("adapter_revision"))

    # F15 fix: generation_contract()/GenerationContract + MechInterp.cli's own
    # _generation_kwargs is the SAME shared generation contract every other
    # path in this cell uses (materialize_configs.steer_config_dict /
    # dose_config_dict feed it to SteerCellConfig/DoseCalibrationConfig,
    # which run_steer/run_dose_calibration pass through it internally) --
    # previously this script called model.generate() directly with no
    # eos_token_id/pad_token_id, so clean_tighten's terminated_naturally/
    # trailing_clean signals (both EOS-sensitive) were not measured under the
    # same instrument as the rest of the cell.
    generation_cfg = GenerationContract(**generation_contract(cell, cell["seed"]))
    gen_kwargs = _generation_kwargs(tokenizer, generation_cfg)

    # F4/F8 fix: per-substrate rows/split paths, read via load_split_manifest
    # (json.loads), not load_jsonl.
    rows = {r["row_key"]: r for r in load_jsonl(rows_with_text_path(args.substrate))}
    split_manifest = load_split_manifest(args.substrate)
    split = split_manifest.get("rows", [])
    held_out_keys = [s["row_key"] for s in split
                      if s["split"] == "held_out" and s["role"] in ("confab", "known_correct_answered")]
    held_out_rows = [rows[k] for k in held_out_keys if k in rows]
    if not held_out_rows:
        print(f"[pairs:{args.substrate}] ERROR: no held-out rows "
              f"({rows_with_text_path(args.substrate)} / {split_manifest_path(args.substrate)}). "
              "Run split_fit_heldout.py first.", file=sys.stderr)
        return 1

    # F14 fix: same registered readback tolerance dose_calibrate.py uses
    # (cell.yaml `dose_ladder.readback_tolerance`) -- AMENDMENT.md's
    # multi_site.magnitude_match requires readback verified at BOTH members
    # "against the same tolerance, so that a pair result cannot be additional
    # dose under another name".
    rb_tol = cell["dose_ladder"]["readback_tolerance"]

    def _within_tol(commanded, measured):
        if commanded is None or measured is None:
            return False
        return abs(measured - commanded) <= max(rb_tol["rel"] * abs(commanded), rb_tol["abs_floor"])

    summary = {"substrate": args.substrate, "eligible_sites": sorted(eligible), "pairs": {}}

    for pair_name, site_a_name, site_b_name in pairs:
        ea, eb = eligible[site_a_name], eligible[site_b_name]
        total_setpoint = max(ea["setpoint"], eb["setpoint"])  # "best single site's calibrated dose"
        setpoint_a = setpoint_b = total_setpoint / 2.0  # AMBIGUITY note 1: equal split
        gain_a = setpoint_a / (ea["sigma"] or 1.0)
        gain_b = setpoint_b / (eb["sigma"] or 1.0)

        c_hat_a = json.loads((DIRECTIONS_DIR / args.substrate / site_a_name / f"c_hat_{site_a_name}.json").read_text())
        c_hat_b = json.loads((DIRECTIONS_DIR / args.substrate / site_b_name / f"c_hat_{site_b_name}.json").read_text())
        dir_a = torch.tensor(c_hat_a["vector"], dtype=torch.float32)
        dir_b = torch.tensor(c_hat_b["vector"], dtype=torch.float32)

        scores_a = gate_score_for_rows(args.substrate, site_a_name, held_out_keys)
        gated_keys = {k for k, s in scores_a.items() if s["gate_fire"]}
        pair_rows = [r for r in held_out_rows if r["row_key"] in gated_keys]

        pair_result = {"site_a": site_a_name, "site_b": site_b_name,
                        "total_setpoint": total_setpoint, "setpoint_a": setpoint_a, "setpoint_b": setpoint_b,
                        "gain_a": gain_a, "gain_b": gain_b, "n_fired": len(pair_rows), "positions": {}}

        for position in POSITIONS:
            gen_mode = POSITION_TO_GENERATION_MODE[position]
            hook_a = InterventionHook(law="erase_write", direction=dir_a, sigma=ea["sigma"] or 1.0,
                                       position="anchor", measure_readback=True)
            hook_b = InterventionHook(law="erase_write", direction=dir_b, sigma=eb["sigma"] or 1.0,
                                       position="anchor", measure_readback=True)
            ctrl_a = GenerationInterventionController(hook_a)
            ctrl_b = GenerationInterventionController(hook_b)
            layer_a = get_decoder_layer(model, ea["site"].decoder_block)
            layer_b = get_decoder_layer(model, eb["site"].decoder_block)
            handle_a = layer_a.register_forward_hook(ctrl_a)
            handle_b = layer_b.register_forward_hook(ctrl_b)

            out_dir = ANALYSIS / f"pairs_{args.substrate}_{pair_name}_{position}"
            out_path = out_dir / "output.jsonl"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            done = {json.loads(line)["row_key"] for line in out_path.open()} if out_path.exists() else set()

            try:
                for row in pair_rows:
                    rk = row["row_key"]
                    if rk in done:
                        continue
                    prompt = render_fn(row)
                    enc = tokenizer(prompt, return_tensors="pt").to(next(model.parameters()).device)
                    ctrl_a.begin_pass(gen_mode, gain_a, attention_mask=enc["attention_mask"], force_active=True)
                    ctrl_b.begin_pass(gen_mode, gain_b, attention_mask=enc["attention_mask"], force_active=True)
                    with torch.no_grad():
                        gen = model.generate(**enc, **gen_kwargs)
                    ctrl_a.reset()
                    ctrl_b.reset()
                    prompt_len = enc["input_ids"].shape[1]
                    full = gen.sequences[0]
                    text = tokenizer.decode(full[prompt_len:], skip_special_tokens=True)
                    terminated_naturally = bool(full.shape[0] - prompt_len < int(cell["surface"]["generation"]["max_new_tokens"]))

                    # F14 fix: verify readback at BOTH members against the
                    # registered tolerance, not just record it. A single row
                    # (batch=1, force_active=True) yields active_rows == [0],
                    # so commanded/measured are single-element lists.
                    rb_a, rb_b = hook_a.last_readback or {}, hook_b.last_readback or {}
                    commanded_a = (rb_a.get("commanded") or [None])[0]
                    measured_a = (rb_a.get("measured") or [None])[0]
                    commanded_b = (rb_b.get("commanded") or [None])[0]
                    measured_b = (rb_b.get("measured") or [None])[0]
                    readback_a_within_tol = _within_tol(commanded_a, measured_a)
                    readback_b_within_tol = _within_tol(commanded_b, measured_b)

                    rec = {"row_key": rk, "role": row.get("role"), "pair": pair_name, "position": position,
                           "site_a": site_a_name, "site_b": site_b_name,
                           "gain_a": gain_a, "gain_b": gain_b,
                           "readback_a": rb_a, "readback_b": rb_b,
                           "readback_a_commanded": commanded_a, "readback_a_measured": measured_a,
                           "readback_a_within_tol": readback_a_within_tol,
                           "readback_b_commanded": commanded_b, "readback_b_measured": measured_b,
                           "readback_b_within_tol": readback_b_within_tol,
                           "answer_text": text, "terminated_naturally": terminated_naturally}
                    rec.update(grader_sweep.grader(rec))
                    write_jsonl_row(out_path, rec)
            finally:
                handle_a.remove()
                handle_b.remove()

            records = load_jsonl(out_path)
            confab_recs = [r for r in records if r.get("role") == "confab"]
            n_tighten = sum(1 for r in confab_recs if r.get("clean_tighten"))
            # F14 fix: both members' readback must be within tolerance for a
            # record to count; frac_readback_within_tol is the fraction of
            # records satisfying both, recorded per position alongside the
            # existing confab_held_out rate.
            n_both_within_tol = sum(
                1 for r in records
                if r.get("readback_a_within_tol") and r.get("readback_b_within_tol")
            )
            frac_readback_within_tol = (n_both_within_tol / len(records)) if records else 0.0
            pair_result["positions"][position] = {
                "n_records": len(records), "confab_held_out": wilson_ci_point(n_tighten, len(confab_recs)),
                "frac_readback_within_tol": frac_readback_within_tol,
            }
            print(f"[pairs:{args.substrate}] {pair_name}:{position} n_records={len(records)}", flush=True)

        summary["pairs"][pair_name] = pair_result

    out_path = COMMITTED / args.substrate / "pairs_summary.json"
    write_json(out_path, summary)
    print(f"[pairs:{args.substrate}] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
