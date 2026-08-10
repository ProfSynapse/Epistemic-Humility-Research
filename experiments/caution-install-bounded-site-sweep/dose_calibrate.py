#!/usr/bin/env python3
"""Stage 5 (GPU, `mechinterp dose-calibrate`): FIT-only ratio-ladder
calibration, 8 rungs per site and position (AMENDMENT.md Run plan row 5;
gates.yaml g_dose_viability).

cell.yaml `dose_ladder.dose_rule`: "dose = ratio x that site's own median
anchor L2 norm, computed under that arm's own condition". This script reads
each site's FIT-pool anchor activations (already cached by
`extract_anchor.py`), takes the median L2 norm over the calibration pool
(`dose_ladder.calibration_pool`: 24 confab + 24 known-correct FIT rows, reused
across sites per D1), multiplies by each of the 8 registered ratios to get 8
absolute setpoints, and runs `MechInterp.cli.run_dose_calibration` with
`dose_kind: setpoint` (the tuner then converts setpoint -> gain = dose/sigma
internally per `_strength_for_dose`) -- no selection rule (every FIT row in
the calibration pool is dosed unconditionally at each rung; the answerability
gate is not part of calibration, only of the held-out `gated` arm at Stage 6).

AMBIGUITY (flagged, not silently resolved): "that arm's own condition" in the
dose_rule is read here as "the undosed/baseline condition of the SAME rows
about to be dosed" (the anchor token is a prefill read, identical across
position/generation_mode, so there is only one anchor-norm distribution per
site x substrate to compute this from, not one per arm). If the intended
reading is instead a per-position or per-substrate-condition-specific
baseline norm, the setpoints below would need to be recomputed narrower;
confirm with the lead before the real run.

Selection rule (cell.yaml `dose_ladder.selection_rule`, gates.yaml
`g_dose_viability.selection_rule`): "highest FIT confab clean_tighten, then
lower known-correct cost, then lower ratio" among rungs passing
`usable_rule` (frac_readback_within_tol == 1.0 AND collapse_rate_on_dosed ==
0.0 AND FIT confab clean_tighten >= 0.50). Zero usable rungs is recorded
NOT-RUN per `no_usable_rung_disposition`, never a behavioral null.

Output: `analysis/dose_<substrate>_<site>_<position>/` (checkpoint JSONL +
tuner summary.json) and `analysis-committed/<substrate>/dose_disposition.json`
(site x position -> full eight-rung table, selected rung or NOT-RUN, no row
text).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    DIRECTIONS_DIR,
    POSITIONS,
    base_repo_and_revision,
    dose_ratios,
    install_pinned_loader,
    load_cell,
    load_jsonl,
    load_split_manifest,
    raw_base_anchor_pool,
    rows_with_text_path,
    sites_for,
    split_manifest_path,
    substrate_config,
    write_json,
)
from materialize_configs import dose_config_dict  # noqa: E402


def sanitize_key(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_").replace("/", "_")


def calibration_pool(substrate: str, cell: dict) -> list[dict]:
    """D1: n_confab_fit_rows=24 + n_known_correct_fit_rows=24, reused across
    sites, deterministic (row_key-sorted) selection from the FIT split.
    F4/F8 fix: per-substrate rows/split paths, read via load_split_manifest
    (json.loads), not load_jsonl (which mis-parses the pretty-printed
    manifest object).

    2026-08-10 wiring pass, raw_base DESIGN CALL (reported, not silently
    chosen -- flag to the lead if a different reading was intended): raw_base
    has no registered FIT/HELD-OUT split at all (its confab population is
    rep2's single 221-row evidential pool, per
    sweep_lib.raw_base_anchor_pool()'s docstring, and rep2's own
    full_summary.json evaluates that pool as ONE population with no internal
    split either). Rather than inventing a FIT subset that would overlap the
    same rows G4 evaluates at Stage 6 -- or blocking dose calibration on a
    split that isn't registered anywhere -- this draws the confab side of
    the calibration pool from the SAME rep2-registered 221 rows (deterministic
    row_key-sorted, first n_confab), matching rep2's own no-split
    methodology. known_correct_answered has no registered raw_base source at
    all (G4 does not gate on it), so the known-correct side is simply empty
    for raw_base: `known_correct_cost` in the rung table then reads a fixed
    1.0 for every rung (the code's existing `max(1, ...)` denominator guard),
    a harmless constant tiebreaker, not a crash."""
    n_confab = int(cell["dose_ladder"]["calibration_pool"]["n_confab_fit_rows"])
    n_known = int(cell["dose_ladder"]["calibration_pool"]["n_known_correct_fit_rows"])

    if substrate == "raw_base":
        pool = raw_base_anchor_pool()  # hard-fails on missing/mismatched rep2 artifacts
        text_by_key = {r["row_key"]: r for r in load_jsonl(rows_with_text_path("raw_base"))}
        missing = [r["row_key"] for r in pool["rows"] if r["row_key"] not in text_by_key]
        # ALSO(a) (2026-08-10 lead adjudication): a present row_key with the
        # wrong role would silently join in as "confab" here too.
        wrong_role = [
            r["row_key"] for r in pool["rows"]
            if r["row_key"] in text_by_key and text_by_key[r["row_key"]].get("role") != "confab"
        ]
        if missing or wrong_role:
            raise RuntimeError(
                f"{rows_with_text_path('raw_base')} is missing question text for "
                f"{len(missing)}/{pool['n_confab']} of rep2's registered raw_base "
                f"anchor pool row_keys (first 5: {missing[:5]}), and "
                f"{len(wrong_role)}/{pool['n_confab']} present row_keys carry a "
                f"role other than 'confab' (first 5: {wrong_role[:5]}); this file "
                "must carry role: \"confab\" for every one of those row_keys too. "
                "See sweep_lib.raw_base_anchor_pool()'s docstring."
            )
        confab_fit = sorted(r["row_key"] for r in pool["rows"])[:n_confab]
        return [{**text_by_key[k], "row_key": k} for k in confab_fit]

    rows = {r["row_key"]: r for r in load_jsonl(rows_with_text_path(substrate))}
    split_manifest = load_split_manifest(substrate)
    split = {r["row_key"]: r["split"] for r in split_manifest.get("rows", [])}
    confab_fit = sorted(k for k, r in rows.items() if r["role"] == "confab" and split.get(k) == "fit")
    known_fit = sorted(k for k, r in rows.items()
                        if r["role"] == "known_correct_answered" and split.get(k) == "fit")
    chosen = confab_fit[:n_confab] + known_fit[:n_known]
    return [rows[k] for k in chosen]


def median_anchor_norm(substrate: str, site_name: str, hs_index: int, row_keys: list[str]) -> float:
    from safetensors.numpy import load_file

    extract_dir = ANALYSIS / f"extract_{substrate}"
    norms = []
    for rk in row_keys:
        path = extract_dir / f"{sanitize_key(rk)}__anchor.safetensors"
        if not path.exists():
            continue
        tensors = load_file(str(path))
        key = f"L{hs_index}"
        if key in tensors:
            norms.append(float(np.linalg.norm(tensors[key][0])))
    if not norms:
        raise RuntimeError(f"{site_name}: no cached anchor activations for calibration pool rows")
    return float(np.median(norms))


def run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("Refusing to run a GPU verb without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    import os
    os.environ["SWEEP_SUBSTRATE"] = args.substrate

    cell = load_cell()
    sub_cfg = substrate_config(args.substrate, cell)
    sites = sites_for(args.substrate, cell)
    ratios = dose_ratios(cell)
    tol = cell["dose_ladder"]["readback_tolerance"]

    pool = calibration_pool(args.substrate, cell)
    if not pool:
        print(f"[dose:{args.substrate}] ERROR: empty calibration pool "
              f"({rows_with_text_path(args.substrate)} / {split_manifest_path(args.substrate)}). "
              + ("Run mine_pool.py + split_fit_heldout.py first." if args.substrate == "trained" else
                 "raw_base's confab pool is rep2's registered 221-row anchor pool "
                 "(sweep_lib.raw_base_anchor_pool()); rows_with_text_raw_base.jsonl "
                 "still needs question text populated for those row_keys."),
              file=sys.stderr)
        return 1
    pool_path = ANALYSIS / f"dose_calibration_pool_{args.substrate}.jsonl"
    pool_path.write_text("\n".join(json.dumps(r) for r in pool) + "\n")
    confab_fit_keys = [r["row_key"] for r in pool if r["role"] == "confab"]

    base_repo, base_revision = base_repo_and_revision(args.substrate, cell)
    adapter = sub_cfg.get("adapter_repo")
    # F6 fix: run_dose_calibration's public signature has no `revision`
    # parameter at all (unlike run_steer) and calls
    # `_load_model_and_tokenizer(model_name, adapter)` with two positionals,
    # so without binding base_revision here the base model loads at repo
    # HEAD instead of its pin. See sweep_lib.install_pinned_loader's
    # docstring for why this bind is safe ONLY for the run_dose_calibration
    # call path (two positionals), never for run_steer call sites (three
    # positionals, revision passed explicitly -- binding it again here would
    # collide).
    install_pinned_loader(sub_cfg.get("adapter_revision"), base_revision=base_revision)
    from MechInterp.config import DoseCalibrationConfig
    from MechInterp.cli import run_dose_calibration
    from MechInterp import cell as cell_mod

    disposition = {"substrate": args.substrate, "ratios": ratios, "cells": {}}

    for site in sites:
        c_hat_path = DIRECTIONS_DIR / args.substrate / site.name / f"c_hat_{site.name}.json"
        if not c_hat_path.exists():
            print(f"[dose:{args.substrate}] {site.name}: missing c_hat; skipping.", file=sys.stderr)
            continue
        c_hat_rec = json.loads(c_hat_path.read_text())
        sigma = float(c_hat_rec.get("sigma", 1.0))
        median_norm = median_anchor_norm(args.substrate, site.name, site.hs_index,
                                          [r["row_key"] for r in pool])
        setpoints = [ratio * median_norm for ratio in ratios]

        for position in POSITIONS:
            out_dir = ANALYSIS / f"dose_{args.substrate}_{site.name}_{position}"
            cfg_dict = dose_config_dict(
                cell, str(pool_path), "c_hat", str(c_hat_path), position,
                doses=setpoints,
                output_path=str(out_dir / "checkpoint.jsonl"),
                summary_path=str(out_dir / "summary.json"),
                layer=site.decoder_block,
            )
            config = DoseCalibrationConfig(**cfg_dict)
            rc = run_dose_calibration(config, base_repo, adapter,
                                       render_fn_spec="render_sweep:render", gpu_ack=True)

            checkpoint = load_jsonl(out_dir / "checkpoint.jsonl")
            rung_table = []
            for ratio, setpoint in zip(ratios, setpoints):
                recs = [r for r in checkpoint if abs(r.get("dose", 1e9) - setpoint) < 1e-6]
                confab_recs = [r for r in recs if r.get("role") == "confab"]
                # F7 fix: a missing readback_measured/readback_commanded (an
                # arm whose hook never fired -- MechInterp.cli.py returns {}
                # from _readback_for_record when hook.last_readback is None,
                # so those keys are simply absent from the row) used to make
                # the `or` short-circuit True, i.e. an unmeasured row read as
                # WITHIN tolerance. gates.yaml readback_within_tol pass_if
                # "== 1.0" -- a missing measurement must FAIL, not pass.
                readback_ok = bool(recs) and all(
                    r.get("readback_measured") is not None and r.get("readback_commanded") is not None and
                    abs(r["readback_measured"] - r["readback_commanded"]) <=
                    max(tol["rel"] * abs(r["readback_commanded"]), tol["abs_floor"])
                    for r in recs
                )
                collapse = [r for r in recs if r.get("degenerate")]
                n_tighten = sum(1 for r in confab_recs if r.get("clean_tighten"))
                fit_confab_clean_tighten = (n_tighten / len(confab_recs)) if confab_recs else 0.0
                known_cost = 1.0 - (
                    sum(1 for r in recs if r.get("role") == "known_correct_answered"
                        and r.get("well_formed_correct")) /
                    max(1, sum(1 for r in recs if r.get("role") == "known_correct_answered"))
                )
                usable = bool(
                    len(recs) > 0 and readback_ok and len(collapse) == 0
                    and fit_confab_clean_tighten >= 0.50
                )
                rung_table.append({
                    "ratio": ratio, "setpoint": setpoint,
                    "readback_within_tol": readback_ok, "collapse_rate_on_dosed": len(collapse) / max(1, len(recs)),
                    "fit_confab_clean_tighten": fit_confab_clean_tighten,
                    "known_correct_cost": known_cost, "n_records": len(recs), "usable": usable,
                })

            usable_rungs = [r for r in rung_table if r["usable"]]
            if usable_rungs:
                usable_rungs.sort(key=lambda r: (-r["fit_confab_clean_tighten"], r["known_correct_cost"], r["ratio"]))
                selected = usable_rungs[0]
                gain = selected["setpoint"] / sigma if sigma else 0.0
                cell_disp = {
                    "status": "SELECTED", "selected_rung": selected, "gain": gain,
                    "median_anchor_norm": median_norm, "sigma": sigma, "rung_table": rung_table, "rc": rc,
                }
            else:
                cell_disp = {
                    "status": "NOT_RUN_no_usable_rung", "median_anchor_norm": median_norm,
                    "sigma": sigma, "rung_table": rung_table, "rc": rc,
                }
            disposition["cells"][f"{site.name}:{position}"] = cell_disp
            print(f"[dose:{args.substrate}] {site.name}:{position} status={cell_disp['status']} "
                  f"(n_usable_rungs={len(usable_rungs)})", flush=True)

    out_path = COMMITTED / args.substrate / "dose_disposition.json"
    write_json(out_path, disposition)
    print(f"[dose:{args.substrate}] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
