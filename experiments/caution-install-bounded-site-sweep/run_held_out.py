#!/usr/bin/env python3
"""Stage 6 (GPU, `mechinterp steer`): held-out ladder at selected doses, every
viable (site, position) cell, plus raw-base G4 anchors (AMENDMENT.md Run plan
row 6; gates.yaml G1, G2, G4).

Runs the two arms that share the c_hat readout AND belong to Stage 6 per the
registered Run plan table (row 6 = "held-out ladder... plus raw-base
anchors"; row 7 = "placebo draws, permuted gate, orthogonalization control" --
`permuted_gate` is therefore Stage 7's `run_controls.py`, not here, even
though it shares c_hat with `gated`; see that script's docstring):
  gated            score_field="gate_score", threshold=tau (from
                   `gate_scoring.py`, fitted by `build_directions.py` on FIT
                   only, applied here to HELD-OUT rows), strength=selected
                   gain from `dose_calibrate.py`'s disposition.
  baseline_undosed strength=0.0 (no selector: every row, no-op).

Only (site, position) cells with a `dose_disposition.json` status ==
"SELECTED" run; a NOT_RUN cell is skipped and recorded as NOT-RUN here too
(gates.yaml g_dose_viability.failure_disposition: "the cell leaves the
held-out stage").

Rows: HELD-OUT split confab + known_correct_answered (surface.split via
split_fit_heldout.py).

Output: `analysis/held_out_<substrate>_<site>_<position>/output.jsonl`
(checkpoint, resumable) and `analysis-committed/<substrate>/held_out_summary.json`
(per cell: arm -> n, n_active, clean_tighten rate + Wilson CI for
confab_held_out, not_well_formed_correct rate + Wilson CI for
known_correct_answered_held_out -- G1/G2's raw ingredients; adjudication
itself is `adjudicate_gates.py`, Stage 9).
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
    POSITIONS,
    base_repo_and_revision,
    install_pinned_loader,
    load_cell,
    load_jsonl,
    load_split_manifest,
    rows_with_text_path,
    split_manifest_path,
    sites_for,
    substrate_config,
    wilson_ci_point,
    write_json,
)
from materialize_configs import steer_config_dict  # noqa: E402
from gate_scoring import gate_score_for_rows  # noqa: E402
from extract_anchor import _raw_base_joined_rows  # noqa: E402


def held_out_rows(substrate: str) -> list[dict]:
    # F8 completion (third consumer, PI-approved repin 2026-08-11): raw_base
    # has no split manifest by design -- its registered population is rep2's
    # verified 221-row anchor pool, sourced exactly as extract_anchor.py and
    # dose_calibrate.py already do (all split="held_out", role "confab";
    # hard-fails on missing text or wrong roles). Trained path unchanged.
    if substrate == "raw_base":
        return _raw_base_joined_rows()
    rows = {r["row_key"]: r for r in load_jsonl(rows_with_text_path(substrate))}
    split_manifest = load_split_manifest(substrate)
    split = split_manifest.get("rows", [])
    keys = [s["row_key"] for s in split
            if s["split"] == "held_out" and s["role"] in ("confab", "known_correct_answered")]
    return [rows[k] for k in keys if k in rows]


def summarize_cell(records: list[dict]) -> dict:
    """F12 fix: gates.yaml G2 headline_rule requires BOTH the full held-out
    known-correct population rate AND the fired-only rate, with both
    numerators/denominators recorded ("if the fired-only rate exceeds the cap
    while the full-population number passes, the fired-only rate goes in the
    headline, not a table"). Previously only the full-population rate was
    computed; the fired-only rate was never materialized even though
    n_fired_known (its denominator) was already being counted."""
    out = {}
    for arm in sorted(set(r.get("arm") for r in records)):
        arm_recs = [r for r in records if r.get("arm") == arm]
        confab = [r for r in arm_recs if r.get("role") == "confab"]
        known = [r for r in arm_recs if r.get("role") == "known_correct_answered"]
        known_fired = [r for r in known if r.get("active")]
        n_tighten = sum(1 for r in confab if r.get("clean_tighten"))
        n_not_wfc = sum(1 for r in known if r.get("not_well_formed_correct"))
        n_not_wfc_fired = sum(1 for r in known_fired if r.get("not_well_formed_correct"))
        out[arm] = {
            "n_active": sum(1 for r in arm_recs if r.get("active")),
            "confab_held_out": {**wilson_ci_point(n_tighten, len(confab))},
            "known_correct_answered_held_out": {**wilson_ci_point(n_not_wfc, len(known))},
            "known_correct_answered_held_out_fired_only": {
                **wilson_ci_point(n_not_wfc_fired, len(known_fired))
            },
            "n_fired_known": len(known_fired),
        }
    return out


def run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("Refusing to run a GPU verb without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    import os
    os.environ["SWEEP_SUBSTRATE"] = args.substrate

    cell = load_cell()
    sub_cfg = substrate_config(args.substrate, cell)
    sites = sites_for(args.substrate, cell)

    dose_disp_path = COMMITTED / args.substrate / "dose_disposition.json"
    if not dose_disp_path.exists():
        print(f"[held-out:{args.substrate}] ERROR: no dose disposition; run dose_calibrate.py first.",
              file=sys.stderr)
        return 1
    dose_disp = json.loads(dose_disp_path.read_text())["cells"]

    rows = held_out_rows(args.substrate)
    if not rows:
        print(f"[held-out:{args.substrate}] ERROR: no held-out rows "
              f"({rows_with_text_path(args.substrate)} / {split_manifest_path(args.substrate)}). "
              + ("Run split_fit_heldout.py first." if args.substrate == "trained" else
                 "raw_base has no registered mining/split stage in this harness "
                 "(see harness remediation report, finding F8)."),
              file=sys.stderr)
        return 1

    install_pinned_loader(sub_cfg.get("adapter_revision"))
    from MechInterp.config import SteerCellConfig
    from MechInterp.cli import run_steer

    base_repo, base_revision = base_repo_and_revision(args.substrate, cell)
    adapter = sub_cfg.get("adapter_repo")

    summary = {"substrate": args.substrate, "cells": {}}

    for site in sites:
        c_hat_path = DIRECTIONS_DIR / args.substrate / site.name / f"c_hat_{site.name}.json"
        for position in POSITIONS:
            key = f"{site.name}:{position}"
            disp = dose_disp.get(key)
            if not disp or disp.get("status") != "SELECTED":
                summary["cells"][key] = {"status": "NOT_RUN_dose_not_selected"}
                print(f"[held-out:{args.substrate}] {key}: NOT_RUN (dose not selected)", flush=True)
                continue
            gain = float(disp["gain"])

            scores = gate_score_for_rows(args.substrate, site.name, [r["row_key"] for r in rows])
            if not scores:
                summary["cells"][key] = {"status": "NOT_RUN_no_gate_scores"}
                print(f"[held-out:{args.substrate}] {key}: NOT_RUN (no cached gate scores)", flush=True)
                continue
            rows_scored = [dict(r, **scores[r["row_key"]]) for r in rows if r["row_key"] in scores]
            # The tuner smoke gate probes the first rows of the file. Put
            # gate-active rows first so it probes real write rows, not the
            # natural baseline projection of inactive rows (which the smoke
            # mismeasures as off-target movement). Same fix as
            # aq-sycophancy-activation-actuator; repin audit 2026-08-11.
            rows_scored.sort(
                key=lambda r: (
                    not (float(r["gate_score"]) >= float(r["gate_tau"])),
                    str(r["row_key"]),
                )
            )
            rows_path = ANALYSIS / f"held_out_rows_{args.substrate}_{site.name}_{position}.jsonl"
            rows_path.write_text("\n".join(json.dumps(r) for r in rows_scored) + "\n")
            tau = next(iter(scores.values()))["gate_tau"]

            arms = [
                {"name": "gated", "strength": gain, "score_field": "gate_score", "threshold": tau},
                {"name": "baseline_undosed", "strength": 0.0},
            ]

            out_dir = ANALYSIS / f"held_out_{args.substrate}_{site.name}_{position}"
            cfg_dict = steer_config_dict(
                cell, str(rows_path), "c_hat", str(c_hat_path), position, arms=arms,
                output_path=str(out_dir / "output.jsonl"), layer=site.decoder_block,
            )
            config = SteerCellConfig(**cfg_dict)
            rc = run_steer(config, base_repo, base_revision, adapter,
                            render_fn_spec="render_sweep:render", gpu_ack=True)
            records = load_jsonl(out_dir / "output.jsonl")
            cell_summary = {"status": "RAN", "rc": rc, "gain": gain, "arms": summarize_cell(records)}
            summary["cells"][key] = cell_summary
            print(f"[held-out:{args.substrate}] {key}: rc={rc}", flush=True)

    out_path = COMMITTED / args.substrate / "held_out_summary.json"
    write_json(out_path, summary)
    print(f"[held-out:{args.substrate}] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
