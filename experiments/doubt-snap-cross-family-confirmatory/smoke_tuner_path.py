#!/usr/bin/env python3
"""Two-row Modal harness smoke for the cross-family tuner path.

This is not an outcome path. It uses synthetic rows and a deterministic random
direction to verify that the Modal checkout, render, grader import, model load,
hook smoke, and `mechinterp steer` output path all work before launching the
registered cells.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"
SEED = 20260707


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not parse as a mapping")
    return data


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def cell_by_id(cell_id: str) -> dict[str, Any]:
    matrix = load_yaml(ROOT / "model_matrix.yaml")
    for cell in matrix["cells"]:
        if cell["cell_id"] == cell_id:
            return cell
    raise SystemExit(f"unknown cell_id: {cell_id}")


def model_shape(cell: dict[str, Any]) -> tuple[int, int, int]:
    from transformers import AutoConfig

    cfg = AutoConfig.from_pretrained(
        cell["repo"],
        revision=cell.get("revision"),
        token=os.environ.get("HF_TOKEN") or None,
        trust_remote_code=True,
    )
    text_cfg = getattr(cfg, "text_config", cfg)
    n_layers = int(getattr(text_cfg, "num_hidden_layers"))
    hidden_dim = int(getattr(text_cfg, "hidden_size"))
    layer_idx = int(round(0.94 * (n_layers - 1)))
    return n_layers, hidden_dim, layer_idx


def direction_record(cell: dict[str, Any], hidden_dim: int, layer_idx: int) -> dict[str, Any]:
    rng = np.random.default_rng(SEED + hidden_dim + layer_idx)
    vector = rng.normal(size=hidden_dim)
    vector = vector / float(np.linalg.norm(vector))
    return {
        "schema_version": "mechinterp-direction/v1",
        "layer": layer_idx,
        "hidden_dim": hidden_dim,
        "normalized": True,
        "vector": [float(x) for x in vector],
        "raw_norm": 1.0,
        "intercept": 0.0,
        "mu": [0.0] * hidden_dim,
        "sigma": 1.0,
        "calibration": {},
        "recipe": {"source": "doubt-snap-cross-family-confirmatory/smoke_tuner_path.py"},
        "provenance": {
            "role": "synthetic_modal_harness_smoke",
            "cell_id": cell["cell_id"],
            "base_model": cell["repo"],
            "revision": cell["revision"],
        },
    }


def run(cmd: list[str]) -> None:
    print(f"[smoke-tuner-path] $ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), env=os.environ.copy())
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell-id", default="llama32_3b_instruct")
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()

    cell = cell_by_id(args.cell_id)
    os.environ["DOUBT_SNAP_RENDER_MODEL"] = cell["repo"]
    os.environ["DOUBT_SNAP_RENDER_REVISION"] = cell["revision"]

    _, hidden_dim, layer_idx = model_shape(cell)
    out_dir = ROOT / "analysis" / args.cell_id / "modal_harness_smoke"
    rows_path = out_dir / "rows.jsonl"
    direction_path = out_dir / "smoke_direction.json"
    config_path = out_dir / "smoke_steer.yaml"
    output_path = out_dir / "rows_out.jsonl"

    rows = [
        {
            "row_key": "smoke:known:paris",
            "question": "What is the capital of France?",
            "aliases": ["Paris"],
            "role": "known_correct_answered",
            "split": "smoke",
            "source": "synthetic_smoke",
            "category_canon": "synthetic_smoke",
            "fire": True,
        },
        {
            "row_key": "smoke:known:arithmetic",
            "question": "What is 2 plus 2?",
            "aliases": ["4", "four"],
            "role": "known_correct_answered",
            "split": "smoke",
            "source": "synthetic_smoke",
            "category_canon": "synthetic_smoke",
            "fire": True,
        },
    ]
    write_jsonl(rows_path, rows)
    write_json(direction_path, direction_record(cell, hidden_dim, layer_idx))
    config = {
        "surface": {
            "rows_path": str(rows_path),
            "seed": SEED,
            "generation": {
                "max_new_tokens": 24,
                "min_new_tokens": 1,
                "do_sample": False,
                "extra_eos_tokens": ["<|im_end|>"],
            },
        },
        "readouts": [{"name": "smoke_direction", "path": str(direction_path)}],
        "law": {
            "kind": "erase_write",
            "readout": "smoke_direction",
            "position": "anchor_onward",
            "generation_mode": "gen_stream",
        },
        "arms": [
            {"name": "baseline", "strength": 0.0},
            {"name": "smoke_write", "strength": 1.0, "flag_field": "fire"},
        ],
        "execution": {
            "output_path": str(output_path),
            "resume": True,
            "render_fn": "render:render",
            "grader": "grader:grade",
            "batch_size": args.batch_size,
        },
        "smoke": {
            "n_rows": 2,
            "write_rel_tol": 0.05,
            "write_abs_floor": 0.5,
            "offtarget_tol": 0.001,
            "gen_stream_probe_strength": 250.0,
        },
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    run(
        [
            sys.executable,
            str(TUNER),
            "mechinterp",
            "steer",
            "--mi-config",
            str(config_path),
            "--model",
            cell["repo"],
            "--model-revision",
            cell["revision"],
            "--i-know-this-runs-on-gpu",
        ]
    )
    if not output_path.is_file():
        raise SystemExit(f"smoke output missing: {output_path}")
    n_rows = sum(1 for line in output_path.read_text(encoding="utf-8").splitlines() if line.strip())
    if n_rows < 4:
        raise SystemExit(f"smoke output too short: expected >=4 rows, saw {n_rows}")
    smoke_ok = output_path.with_suffix(output_path.suffix + ".smoke_ok.json")
    if not smoke_ok.is_file():
        raise SystemExit(f"smoke readback record missing: {smoke_ok}")
    print(
        json.dumps(
            {
                "status": "passed",
                "cell_id": args.cell_id,
                "model": cell["repo"],
                "layer_idx": layer_idx,
                "hidden_dim": hidden_dim,
                "output_rows": n_rows,
                "output_path": str(output_path),
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
