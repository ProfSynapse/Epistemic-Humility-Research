#!/usr/bin/env python3
"""Cross-family doubt-snap pipeline entrypoint.

This file is intentionally thin at draft time: it validates the registered
matrix and provides the stable CLI that the Modal wrapper will call. The heavy
GPU implementation fills in the stage handlers behind this interface before
signing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent


def load_yaml(name: str) -> dict[str, Any]:
    with (ROOT / name).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{name} did not parse to a mapping")
    return data


def cells() -> list[dict[str, Any]]:
    matrix = load_yaml("model_matrix.yaml")
    value = matrix.get("cells")
    if not isinstance(value, list) or not value:
        raise ValueError("model_matrix.yaml has no cells")
    return value


def selected_cells(cell_ids: list[str] | None) -> list[dict[str, Any]]:
    all_cells = cells()
    if not cell_ids:
        return all_cells
    wanted = set(cell_ids)
    got = [c for c in all_cells if c.get("cell_id") in wanted]
    missing = wanted - {c.get("cell_id") for c in got}
    if missing:
        raise SystemExit(f"unknown cell_id(s): {', '.join(sorted(missing))}")
    return got


def plan(cell_ids: list[str] | None, *, json_out: bool) -> None:
    cell_yaml = load_yaml("cell.yaml")
    gates_yaml = load_yaml("gates.yaml")
    rows = []
    for cell in selected_cells(cell_ids):
        rows.append(
            {
                "cell_id": cell["cell_id"],
                "family": cell["family"],
                "scale_tier": cell["scale_tier"],
                "repo": cell["repo"],
                "revision": cell["revision"],
                "gated_access": cell["gated_access"],
                "layer_rule": cell_yaml["modeling"]["anchor"]["layer_rule"],
                "dose_grid": cell_yaml["snap"]["dose_selection"][
                    "candidate_realized_projection_targets"
                ],
                "batching": cell_yaml["execution"]["batching"],
                "per_cell_gates": [g["name"] for g in gates_yaml["per_cell_gates"]],
            }
        )
    if json_out:
        print(json.dumps(rows, indent=2, sort_keys=True))
        return
    for row in rows:
        gated = f" gated={row['gated_access']}"
        print(
            f"{row['cell_id']}: {row['repo']}@{row['revision']}"
            f" tier={row['scale_tier']}{gated}"
        )
        print(f"  layer_rule: {row['layer_rule']}")
        print(f"  dose_grid: {row['dose_grid']}")
        print("  batching: baseline_generation, hidden_state_extraction, grouped intervention")


def validate_access(cell_ids: list[str] | None) -> None:
    from huggingface_hub import repo_info

    failures: list[str] = []
    for cell in selected_cells(cell_ids):
        try:
            info = repo_info(cell["repo"], revision=cell["revision"])
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{cell['cell_id']}: {exc}")
            continue
        print(
            f"{cell['cell_id']}: ok repo={cell['repo']} "
            f"sha={info.sha} gated={info.gated}"
        )
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        raise SystemExit(1)


def run_cell(cell_id: str, stage: str, dry_run: bool) -> None:
    cell = selected_cells([cell_id])[0]
    if dry_run:
        plan([cell_id], json_out=True)
        return
    raise SystemExit(
        "GPU stage handlers are not implemented yet. This draft pins the CLI "
        f"for Modal; implement stage={stage!r} before signing or launching."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--cell-id", action="append")
    p_plan.add_argument("--json", action="store_true")

    p_access = sub.add_parser("validate-access")
    p_access.add_argument("--cell-id", action="append")

    p_run = sub.add_parser("run-cell")
    p_run.add_argument("--cell-id", required=True)
    p_run.add_argument(
        "--stage",
        choices=["mine", "extract", "fit", "smoke", "heldout", "full"],
        default="full",
    )
    p_run.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if args.cmd == "plan":
        plan(args.cell_id, json_out=args.json)
    elif args.cmd == "validate-access":
        validate_access(args.cell_id)
    elif args.cmd == "run-cell":
        run_cell(args.cell_id, args.stage, args.dry_run)


if __name__ == "__main__":
    main()
