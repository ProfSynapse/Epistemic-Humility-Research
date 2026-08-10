#!/usr/bin/env python3
"""Stage 4 (GPU, `mechinterp steer`-equivalent): write smoke and readback at
every site and position, G0e (AMENDMENT.md Run plan row 4; gates.yaml
g0e_write_readback == 1.0).

`MechInterp.cli.run_steer` already runs an internal forward-only smoke check
(n_rows from `SteerCellConfig.smoke`) before its first real arm, and records
the verdict into the SAME output path's manifest (`cell_mod.record_smoke`,
keyed by config_sha) -- there is no separate tuner verb for "smoke only".
This script therefore builds one minimal SteerCellConfig per (site, position)
whose rows_path is a tiny, deterministic 8-row probe slice (never the real
held-out population, matching the Run-plan budget line "144 = 8 rows x 7
trained sites x 2 positions + 2 raw-base sites x 2"), with a single synthetic
`write_probe` arm, and calls `run_steer` so its built-in smoke gate fires and
is recorded; the probe arm's own tiny output is discarded (not part of any
held-out gate) since its only job is to trigger the smoke check.

AMBIGUITY (flagged, not silently resolved): cell.yaml's `smoke` block (n_rows,
tolerances) is independent of the dose ladder, but the smoke arm still needs
SOME gain to write at, and Stage 4 registration-order-precedes Stage 5 (dose
calibration) -- no calibrated dose exists yet at this point. This script uses
gain = 1.0 (one full sigma unit under c_hat, i.e. setpoint = sigma) as the
write-mechanism probe value. This is an arbitrary but documented placeholder,
not a registered number; confirm with the lead it is an acceptable smoke
probe magnitude before the real run (cell.yaml `smoke.note`: "A passing smoke
proves write accuracy only, never behavioral effect").

Output: `analysis/write_smoke_<substrate>_<site>_<position>/` (output.jsonl +
manifest.json, containing the recorded smoke block) and
`analysis-committed/<substrate>/write_smoke_report.json` (site x position ->
passed / frac_readback_within_tol, no row text).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    ANALYSIS,
    COMMITTED,
    DIRECTIONS_DIR,
    POSITIONS,
    install_pinned_loader,
    load_cell,
    load_jsonl,
    rows_with_text_path,
    sites_for,
    substrate_config,
    write_jsonl_row,
    write_json,
)
from materialize_configs import steer_config_dict  # noqa: E402

PROBE_GAIN = 1.0
N_PROBE_ROWS = 8


def probe_rows(substrate: str, n: int) -> list[dict]:
    # F8-class fix: this previously always read the trained-substrate's
    # rows_with_text.jsonl regardless of --substrate, so a raw_base smoke run
    # would silently probe against trained-substrate rows. Same bug class as
    # F8 in mine_pool.py/dose_calibrate.py/etc.; fixed the same way via
    # sweep_lib.rows_with_text_path.
    rows = load_jsonl(rows_with_text_path(substrate))
    confab = sorted((r for r in rows if r["role"] == "confab"), key=lambda r: r["row_key"])
    return confab[:n]


def run(args: argparse.Namespace) -> int:
    if not args.i_know_this_runs_on_gpu:
        print("Refusing to run a GPU verb without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    import os
    os.environ["SWEEP_SUBSTRATE"] = args.substrate

    cell = load_cell()
    sub_cfg = substrate_config(args.substrate, cell)
    sites = sites_for(args.substrate, cell)
    install_pinned_loader(sub_cfg.get("adapter_revision"))
    from MechInterp.config import SteerCellConfig
    from MechInterp.cli import run_steer

    from render_sweep import render as _render  # noqa: F401 (spec resolved by string below)

    probe = probe_rows(args.substrate, N_PROBE_ROWS)
    if not probe:
        print("[write-smoke] ERROR: no confab rows found; run mine_pool.py first.", file=sys.stderr)
        return 1
    probe_path = ANALYSIS / f"write_smoke_probe_rows_{args.substrate}.jsonl"
    probe_path.parent.mkdir(parents=True, exist_ok=True)
    probe_path.write_text("\n".join(json.dumps(r) for r in probe) + "\n")

    from sweep_lib import base_repo_and_revision
    base_repo, base_revision = base_repo_and_revision(args.substrate, cell)
    adapter = sub_cfg.get("adapter_repo")

    report = {"substrate": args.substrate, "probe_gain": PROBE_GAIN, "n_probe_rows": len(probe), "cells": {}}
    overall = True

    for site in sites:
        c_hat_path = DIRECTIONS_DIR / args.substrate / site.name / f"c_hat_{site.name}.json"
        if not c_hat_path.exists():
            print(f"[write-smoke] {site.name}: missing c_hat (run build_directions.py first); skipping.",
                  file=sys.stderr)
            overall = False
            continue
        for position in POSITIONS:
            out_dir = ANALYSIS / f"write_smoke_{args.substrate}_{site.name}_{position}"
            cfg_dict = steer_config_dict(
                cell, str(probe_path), "c_hat", str(c_hat_path), position,
                arms=[{"name": "write_probe", "strength": PROBE_GAIN}],
                output_path=str(out_dir / "output.jsonl"),
                layer=site.decoder_block,
                smoke_n_rows=N_PROBE_ROWS,
            )
            config = SteerCellConfig(**cfg_dict)
            rc = run_steer(config, base_repo, base_revision, adapter,
                            render_fn_spec="render_sweep:render", gpu_ack=True)
            # Smoke verdict lives at <output_path>.smoke_ok.json
            # (MechInterp.cell.smoke_state_path / record_smoke), keyed by
            # config_sha -- NOT in the arm-run manifest (write_manifest has no
            # "smoke" key). gates.yaml's g0e quantity is worded as a fraction
            # ("frac_readback_within_tol == 1.0"); the tuner's own smoke
            # readback only records an all-or-nothing write_ok, so this script
            # derives the per-commanded-row fraction itself from the
            # readback's commanded/measured lists.
            from MechInterp.cell import smoke_state_path
            smoke_path = smoke_state_path(out_dir / "output.jsonl")
            passed, frac_within_tol = None, None
            if smoke_path.exists():
                state = json.loads(smoke_path.read_text())
                passed = state.get("passed")
                rb = state.get("readback", {})
                commanded = [c for c in rb.get("commanded", []) if c is not None]
                measured = rb.get("measured", [])
                tol_each = [
                    abs(m - c) <= max(cell["smoke"]["write_rel_tol"] * abs(c), cell["smoke"]["write_abs_floor"])
                    for m, c in zip(measured, commanded)
                ]
                frac_within_tol = (sum(tol_each) / len(tol_each)) if tol_each else None
            # F23 fix: gates.yaml g0e_write_readback pass_if is
            # "== 1.0" on frac_readback_within_tol, not just the tuner's own
            # internal `passed` boolean -- a cell could pass the tuner's
            # coarser all-or-nothing check while this script's own derived
            # fraction is < 1.0 (or unmeasurable, i.e. None). Both must hold.
            cell_ok = bool(passed) and rc == 0 and frac_within_tol == 1.0
            overall = overall and cell_ok
            report["cells"][f"{site.name}:{position}"] = {
                "rc": rc, "passed": passed, "frac_readback_within_tol": frac_within_tol,
            }
            print(f"[write-smoke:{args.substrate}] {site.name}:{position} rc={rc} passed={passed}", flush=True)

    report["g0e_pass"] = overall
    out_path = COMMITTED / args.substrate / "write_smoke_report.json"
    write_json(out_path, report)
    print(f"[write-smoke:{args.substrate}] wrote {out_path}", flush=True)
    return 0 if overall else 1


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
