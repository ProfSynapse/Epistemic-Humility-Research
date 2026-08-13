#!/usr/bin/env python3
"""Stage 7 (GPU, `mechinterp steer`): placebo draws, permuted gate,
orthogonalization control (AMENDMENT.md Run plan row 7; gates.yaml G3, whose
`companion_arms_reported_separately` are permuted_gate and raw_write_pos_ctrl).

Only runs on (site, position) cells `run_held_out.py` recorded status ==
"RAN" (a real dose exists). Three separate steer-cell invocations per cell,
because each writes along a DIFFERENT readout (see `materialize_configs.py`'s
docstring: one `LawConfig.readout` per steer-cell run):

  permuted_gate      readout=c_hat (same as `gated`), arms=[permuted_gate
                     (permuted_control_of="gated", control_seed=cell.yaml
                     seed, strength=selected gain), baseline_undosed]. Row
                     population: the SAME held-out rows_scored file
                     `run_held_out.py` wrote (reused, not regenerated, so the
                     `gated` fire set `permuted_control_of` references is
                     defined over the identical population).
  random_direction   readout = each of K>=3 accepted draws from
                     `build_random_directions.py` (`directions/<substrate>/
                     <site>/random_direction_draw_<k>_<site>.json`), one run
                     per draw. arms=[gated-equivalent at the SAME fired rows
                     and gain as the real `gated` arm, but along the draw's
                     direction instead of c_hat -- realized via a `flag_field`
                     selector precomputed from the real gated arm's fired-row
                     set, matched-magnitude by using the SAME gain value].
  raw_write_pos_ctrl readout=pos_ctrl (`source_directions/pos_ctrl_<site>.json`;
                     for raw_base this is the SOURCE amendment's committed
                     artifact under `MIDBAND_LAYERS_DIR`, imported unchanged
                     per BLOCKER #8 -- raw_base never fits pos_ctrl locally),
                     arms=[raw_write_pos_ctrl (flag_field, same fired rows,
                     same gain), baseline_undosed].

Output: `analysis/controls_<substrate>_<site>_<position>_<control>/` per
control run, plus `analysis-committed/<substrate>/controls_summary.json`
(rates + Wilson CI per control x cell, no row text).
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
    MIDBAND_LAYERS_DIR,
    POSITIONS,
    base_repo_and_revision,
    install_pinned_loader,
    load_cell,
    load_jsonl,
    sites_for,
    substrate_config,
    wilson_ci_point,
    write_json,
)
from materialize_configs import steer_config_dict  # noqa: E402


def summarize(records: list[dict], arm: str) -> dict:
    arm_recs = [r for r in records if r.get("arm") == arm]
    confab = [r for r in arm_recs if r.get("role") == "confab"]
    n_tighten = sum(1 for r in confab if r.get("clean_tighten"))
    return {"n_active": sum(1 for r in arm_recs if r.get("active")),
            "confab_held_out": wilson_ci_point(n_tighten, len(confab))}


def run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("Refusing to run a GPU verb without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    import os
    os.environ["SWEEP_SUBSTRATE"] = args.substrate

    cell = load_cell()
    sub_cfg = substrate_config(args.substrate, cell)
    sites = sites_for(args.substrate, cell)
    seed = int(cell["seed"])
    k_min = int(cell["placebo"]["k_draws_min"])

    held_out_summary_path = COMMITTED / args.substrate / "held_out_summary.json"
    if not held_out_summary_path.exists():
        print(f"[controls:{args.substrate}] ERROR: run run_held_out.py first.", file=sys.stderr)
        return 1
    held_out = json.loads(held_out_summary_path.read_text())["cells"]

    install_pinned_loader(sub_cfg.get("adapter_revision"))
    from MechInterp.config import SteerCellConfig
    from MechInterp.cli import run_steer

    base_repo, base_revision = base_repo_and_revision(args.substrate, cell)
    adapter = sub_cfg.get("adapter_repo")

    summary = {"substrate": args.substrate, "cells": {}}

    for site in sites:
        c_hat_path = DIRECTIONS_DIR / args.substrate / site.name / f"c_hat_{site.name}.json"
        if args.substrate == "raw_base":
            # BLOCKER #8 import posture: raw_base never fits pos_ctrl (no
            # local source_directions/ -- see build_directions.py). The
            # readout comes unchanged from the source amendment's committed,
            # already-gated artifact, same as the c_hat/u_d import.
            pos_ctrl_path = MIDBAND_LAYERS_DIR / site.name / "source_directions" / f"pos_ctrl_{site.name}.json"
        else:
            pos_ctrl_path = DIRECTIONS_DIR / args.substrate / site.name / "source_directions" / f"pos_ctrl_{site.name}.json"
        for position in POSITIONS:
            key = f"{site.name}:{position}"
            cell_disp = held_out.get(key, {})
            if cell_disp.get("status") != "RAN":
                summary["cells"][key] = {"status": "NOT_RUN_no_held_out_run"}
                continue
            gain = float(cell_disp["gain"])
            rows_path = ANALYSIS / f"held_out_rows_{args.substrate}_{site.name}_{position}.jsonl"
            gated_rows = load_jsonl(rows_path)
            fired_keys = {r["row_key"] for r in gated_rows if r.get("gate_fire")}
            for r in gated_rows:
                r["_gated_fire_flag"] = r["row_key"] in fired_keys
            flagged_rows_path = ANALYSIS / f"controls_rows_{args.substrate}_{site.name}_{position}.jsonl"
            flagged_rows_path.write_text("\n".join(json.dumps(r) for r in gated_rows) + "\n")

            cell_result = {"status": "RAN", "permuted_gate": None, "raw_write_pos_ctrl": None, "random_direction": []}

            # -- permuted_gate: readout=c_hat, same fired-count population, seeded permutation
            out_dir = ANALYSIS / f"controls_{args.substrate}_{site.name}_{position}_permuted_gate"
            cfg = steer_config_dict(
                cell, str(rows_path), "c_hat", str(c_hat_path), position,
                arms=[
                    {"name": "gated", "strength": gain, "score_field": "gate_score",
                     "threshold": next((r["gate_tau"] for r in gated_rows if "gate_tau" in r), 0.0)},
                    {"name": "permuted_gate", "permuted_control_of": "gated", "control_seed": seed, "strength": gain},
                ],
                output_path=str(out_dir / "output.jsonl"), layer=site.decoder_block,
            )
            rc = run_steer(SteerCellConfig(**cfg), base_repo, base_revision, adapter,
                            render_fn_spec="render_sweep:render", gpu_ack=True)
            recs = load_jsonl(out_dir / "output.jsonl")
            cell_result["permuted_gate"] = {"rc": rc, **summarize(recs, "permuted_gate")}

            # -- raw_write_pos_ctrl: readout=pos_ctrl, same fired rows (flag_field), same gain
            out_dir = ANALYSIS / f"controls_{args.substrate}_{site.name}_{position}_raw_write_pos_ctrl"
            cfg = steer_config_dict(
                cell, str(flagged_rows_path), "pos_ctrl", str(pos_ctrl_path), position,
                arms=[
                    {"name": "raw_write_pos_ctrl", "strength": gain, "flag_field": "_gated_fire_flag"},
                    {"name": "baseline_undosed", "strength": 0.0},
                ],
                output_path=str(out_dir / "output.jsonl"), layer=site.decoder_block,
            )
            rc = run_steer(SteerCellConfig(**cfg), base_repo, base_revision, adapter,
                            render_fn_spec="render_sweep:render", gpu_ack=True)
            recs = load_jsonl(out_dir / "output.jsonl")
            cell_result["raw_write_pos_ctrl"] = {"rc": rc, **summarize(recs, "raw_write_pos_ctrl")}

            # -- random_direction: K>=3 accepted draws, each its own readout
            site_dir = DIRECTIONS_DIR / args.substrate / site.name
            draw_paths = sorted(site_dir.glob(f"random_direction_draw_*_{site.name}.json"))
            if len(draw_paths) < k_min:
                print(f"[controls:{args.substrate}] {key}: only {len(draw_paths)} accepted draws "
                      f"(< k_draws_min={k_min}); run build_random_directions.py first.", file=sys.stderr)
            for draw_path in draw_paths:
                draw_idx = draw_path.stem.split("_")[3]
                out_dir = ANALYSIS / f"controls_{args.substrate}_{site.name}_{position}_random_{draw_idx}"
                cfg = steer_config_dict(
                    cell, str(flagged_rows_path), f"random_{draw_idx}", str(draw_path), position,
                    arms=[
                        {"name": "random_direction", "strength": gain, "flag_field": "_gated_fire_flag"},
                        {"name": "baseline_undosed", "strength": 0.0},
                    ],
                    output_path=str(out_dir / "output.jsonl"), layer=site.decoder_block,
                )
                rc = run_steer(SteerCellConfig(**cfg), base_repo, base_revision, adapter,
                                render_fn_spec="render_sweep:render", gpu_ack=True)
                recs = load_jsonl(out_dir / "output.jsonl")
                # F1/F13 groundwork: the registered G3 math is a LIFT ratio
                # (rate minus that draw's own undosed baseline), not a raw
                # rate ratio. baseline_undosed is already run alongside each
                # random_direction draw (arms= above) but was previously
                # discarded here -- only the random_direction arm's summary
                # was kept. Both are now recorded so adjudicate_gates.py can
                # compute per-draw lift = random_direction_rate -
                # baseline_undosed_rate without a second GPU pass.
                cell_result["random_direction"].append({
                    "draw": draw_idx, "rc": rc,
                    "random_direction": summarize(recs, "random_direction"),
                    "baseline_undosed": summarize(recs, "baseline_undosed"),
                })

            summary["cells"][key] = cell_result
            print(f"[controls:{args.substrate}] {key}: done "
                  f"({len(cell_result['random_direction'])} random draws)", flush=True)

    out_path = COMMITTED / args.substrate / "controls_summary.json"
    write_json(out_path, summary)
    print(f"[controls:{args.substrate}] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
