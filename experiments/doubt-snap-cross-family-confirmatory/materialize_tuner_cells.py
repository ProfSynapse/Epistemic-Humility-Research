#!/usr/bin/env python3
"""Materialize tuner-backed steer recipes for one cross-family cell.

This is glue, not a model runner. It consumes FIT-frozen artifacts produced by
the prep stages:

  analysis-committed/<cell_id>/c_hat.json
  analysis-committed/<cell_id>/random_direction.json
  analysis-committed/<cell_id>/dose_fit.json
  analysis/<cell_id>/heldout_rows_for_steer.jsonl

and writes two `mechinterp steer` configs under analysis/<cell_id>/:

  steer_c_hat.yaml       baseline + gated + permuted_gate
  steer_random_dir.yaml  random_direction placebo

The configs are resumable and can be launched independently; a failed model or
arm can be spun back up without rerunning the full family matrix.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a mapping")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a JSON object")
    return data


def cell_by_id(cell_id: str) -> dict[str, Any]:
    matrix = load_yaml(ROOT / "model_matrix.yaml")
    for cell in matrix.get("cells", []):
        if cell.get("cell_id") == cell_id:
            return cell
    raise SystemExit(f"unknown cell_id: {cell_id}")


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    tmp.replace(path)


def selected_dose(committed_dir: Path) -> float:
    payload = load_json(committed_dir / "dose_fit.json")
    dose = payload.get("selected_dose")
    if dose is None:
        raise SystemExit(f"{committed_dir / 'dose_fit.json'} has no selected_dose")
    return float(dose)


def direction_sigma(path: Path) -> float:
    payload = load_json(path)
    sigma = payload.get("sigma", 1.0)
    return float(sigma if sigma else 1.0)


def steer_config(
    *,
    rows_path: Path,
    direction_path: Path,
    readout_name: str,
    output_path: Path,
    arms: list[dict[str, Any]],
    batch_size: int,
    seed: int,
    max_new_tokens: int,
) -> dict[str, Any]:
    return {
        "surface": {
            "rows_path": str(rows_path),
            "seed": seed,
            "generation": {
                "max_new_tokens": max_new_tokens,
                "min_new_tokens": 1,
                "do_sample": False,
                "extra_eos_tokens": ["<|im_end|>"],
            },
        },
        "readouts": [{"name": readout_name, "path": str(direction_path)}],
        "law": {
            "kind": "erase_write",
            "readout": readout_name,
            "position": "anchor_onward",
            "generation_mode": "gen_stream",
        },
        "arms": arms,
        "execution": {
            "output_path": str(output_path),
            "resume": True,
            "render_fn": "render:render",
            "grader": "grader:grade",
            "batch_size": batch_size,
        },
        "smoke": {
            "n_rows": 8,
            "write_rel_tol": 0.05,
            "write_abs_floor": 0.5,
            "offtarget_tol": 0.001,
            "gen_stream_probe_strength": max(100.0, max(abs(float(a.get("strength", 0.0))) for a in arms)),
        },
    }


def materialize(cell_id: str, batch_size: int) -> dict[str, str]:
    cell = cell_by_id(cell_id)
    cfg = load_yaml(ROOT / "cell.yaml")
    seed = int(cfg.get("seed", 20260707))
    max_new = int(cfg["modeling"]["generation"]["max_new_tokens"])

    private_dir = ROOT / "analysis" / cell_id
    committed_dir = ROOT / "analysis-committed" / cell_id
    rows_path = private_dir / "heldout_rows_for_steer.jsonl"
    if not rows_path.is_file():
        raise SystemExit(f"missing held-out steer rows: {rows_path}")

    dose = selected_dose(committed_dir)
    c_hat = committed_dir / "c_hat.json"
    random_dir = committed_dir / "random_direction.json"
    for path in (c_hat, random_dir):
        if not path.is_file():
            raise SystemExit(f"missing direction artifact: {path}")

    c_gain = dose / direction_sigma(c_hat)
    random_gain = dose / direction_sigma(random_dir)

    c_hat_yaml = private_dir / "steer_c_hat.yaml"
    random_yaml = private_dir / "steer_random_dir.yaml"
    write_yaml(
        c_hat_yaml,
        steer_config(
            rows_path=rows_path,
            direction_path=c_hat,
            readout_name="c_hat",
            output_path=private_dir / "rows_out_c_hat.jsonl",
            arms=[
                {"name": "baseline", "strength": 0.0},
                {"name": "gated", "strength": c_gain, "flag_field": "fire"},
                {
                    "name": "permuted_gate",
                    "strength": c_gain,
                    "permuted_control_of": "gated",
                    "control_seed": seed,
                },
            ],
            batch_size=batch_size,
            seed=seed,
            max_new_tokens=max_new,
        ),
    )
    write_yaml(
        random_yaml,
        steer_config(
            rows_path=rows_path,
            direction_path=random_dir,
            readout_name="random_direction",
            output_path=private_dir / "rows_out_random_dir.jsonl",
            arms=[
                {"name": "random_direction", "strength": random_gain, "flag_field": "fire"}
            ],
            batch_size=batch_size,
            seed=seed,
            max_new_tokens=max_new,
        ),
    )

    pipeline = private_dir / "pipeline.yaml"
    write_yaml(
        pipeline,
        {
            "schema_version": "mechinterp-pipeline/v1",
            "name": f"doubt-snap-{cell_id}",
            "model": cell["repo"],
            "model_revision": cell.get("revision"),
            "runtime": {
                "provider": "local",
                "python": "python",
                "workdir": ".",
                "pythonpath": [str(ROOT)],
                "env": {"DOUBT_SNAP_RENDER_MODEL": cell["repo"]},
            },
            "modal": {
                "app_name": f"eh-doubt-snap-{cell_id}",
                "image": "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update",
                "gpu": "A10G",
                "timeout_hours": 8,
                "checkpoint_interval_sec": 120,
                "volume_name": "eh-doubt-snap-cross-family",
                "mount_path": "/vol/doubt_snap_cross_family",
                "pip": ["pyyaml", "pydantic", "safetensors", "scikit-learn", "accelerate"],
                "apt": ["git"],
            },
            "artifacts": {
                "checkpoint_paths": [
                    str(private_dir / "rows_out_c_hat.jsonl"),
                    str(private_dir / "rows_out_c_hat.jsonl.smoke_ok.json"),
                    str(private_dir / "rows_out_random_dir.jsonl"),
                    str(private_dir / "rows_out_random_dir.jsonl.smoke_ok.json"),
                ]
            },
            "stages": [
                {"name": "steer_c_hat", "kind": "mechinterp.steer", "config": str(c_hat_yaml)},
                {"name": "steer_random_dir", "kind": "mechinterp.steer", "config": str(random_yaml)},
            ],
        },
    )
    return {
        "cell_id": cell_id,
        "model": cell["repo"],
        "pipeline": str(pipeline),
        "steer_c_hat": str(c_hat_yaml),
        "steer_random_dir": str(random_yaml),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell-id", required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    print(json.dumps(materialize(args.cell_id, args.batch_size), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
