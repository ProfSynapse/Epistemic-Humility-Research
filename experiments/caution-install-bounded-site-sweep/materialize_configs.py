#!/usr/bin/env python3
"""Library (not a registered stage): builds tuner-native `SteerCellConfig` /
`DoseCalibrationConfig` YAML dicts for this cell's GPU stages, matching
`synaptic-tuner/MechInterp/config.py` schemas exactly (read in full before
writing this module).

Design note carried from `sweep_lib.py`'s module docstring: `LawConfig.readout`
is ONE name per steer-cell run, and `run_steer` builds exactly one
`InterventionHook` from it -- every arm in a given `SteerCellConfig` writes
along the SAME direction. cell.yaml's flat `arms` list therefore does not
map to one steer-cell run per (site, position): arms that share a readout
(`gated` + `baseline_undosed` + `permuted_gate`, all c_hat) can run together;
arms with a DIFFERENT readout (`random_direction` -- one per K draw,
`raw_write_pos_ctrl` -- pos_ctrl) each need their OWN run. This module's
`steer_config_dict` takes an explicit `readout_name`/`readout_path` pair per
call for exactly this reason; the calling stage script (`run_held_out.py`,
`run_controls.py`) decides how many separate runs a site/position needs.

Generated YAMLs are written under `generated/` (gitignored, per
`sweep_lib.GENERATED_DIR`) purely for provenance/inspection; the stage
scripts also hold the equivalent config dict in memory and pass it straight
to `MechInterp.config.SteerCellConfig(**dict)` / `DoseCalibrationConfig`
without round-tripping through disk, so a missing `generated/` file is never
a hard dependency at run time.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import GENERATED_DIR, POSITION_TO_GENERATION_MODE  # noqa: E402


def generation_contract(cell: dict, seed: int) -> dict:
    g = cell["surface"]["generation"]
    return {
        "max_new_tokens": int(g["max_new_tokens"]),
        "min_new_tokens": int(g["min_new_tokens"]),
        "do_sample": bool(g["do_sample"]),
        "temperature": float(g["temperature"]),
        "top_p": float(g["top_p"]),
        "seed": seed,
    }


def steer_config_dict(
    cell: dict,
    rows_path: str,
    readout_name: str,
    readout_path: str,
    position_name: str,
    arms: list[dict],
    output_path: str,
    grader_spec: str = "grader_sweep:grader",
    layer: Optional[int] = None,
    smoke_n_rows: Optional[int] = None,
    resume: bool = True,
) -> dict:
    smoke = cell["smoke"]
    return {
        "surface": {
            "rows_path": rows_path,
            "generation": generation_contract(cell, cell["seed"]),
            "seed": cell["seed"],
        },
        "readouts": [{"name": readout_name, "path": readout_path}],
        "law": {
            "kind": cell["law"]["kind"],
            "readout": readout_name,
            "layer": layer,
            "position": "anchor",
            "generation_mode": POSITION_TO_GENERATION_MODE[position_name],
        },
        "arms": arms,
        "execution": {
            "output_path": output_path,
            "resume": resume,
            "grader": grader_spec,
        },
        "smoke": {
            "n_rows": smoke_n_rows if smoke_n_rows is not None else int(smoke["n_rows"]),
            "write_rel_tol": float(smoke["write_rel_tol"]),
            "write_abs_floor": float(smoke["write_abs_floor"]),
        },
    }


def dose_config_dict(
    cell: dict,
    rows_path: str,
    readout_name: str,
    readout_path: str,
    position_name: str,
    doses: list[float],
    output_path: str,
    summary_path: str,
    grader_spec: str = "grader_sweep:grader",
    layer: Optional[int] = None,
    resume: bool = True,
) -> dict:
    return {
        "surface": {
            "rows_path": rows_path,
            "generation": generation_contract(cell, cell["seed"]),
            "seed": cell["seed"],
        },
        "readouts": [{"name": readout_name, "path": readout_path}],
        "law": {
            "kind": cell["law"]["kind"],
            "readout": readout_name,
            "layer": layer,
            "position": "anchor",
            "generation_mode": POSITION_TO_GENERATION_MODE[position_name],
        },
        "calibration": {"doses": doses, "dose_kind": "setpoint"},
        "execution": {
            "output_path": output_path,
            "summary_path": summary_path,
            "resume": resume,
            "grader": grader_spec,
        },
    }


def write_config_yaml(cfg: dict, name: str) -> Path:
    path = GENERATED_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    return path
