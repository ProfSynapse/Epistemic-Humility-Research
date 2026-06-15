#!/usr/bin/env python3
"""Prepare one local Phase 1 matrix cell for tuner `local-run`.

This is the narrow launch-prep companion to run_matrix.py. It uses the same
expansion, gating, staging, materialization, and run-record helpers, but scopes
them to one explicit local run_id so an operator can smoke-test one cell without
touching cloud/8B work or hand-assembling paths.

Usage:
    python prepare_local_cell.py --run-id sft__4b__headline__seed1 --status launched
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import check_prereqs  # noqa: E402
import run_matrix as rm  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare one local Phase 1 cell.")
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--status",
        choices=["prepared", "launched"],
        default="prepared",
        help="Run-record status to write. Use launched immediately before starting local-run.",
    )
    parser.add_argument(
        "--matrix",
        default=str(SCRIPT_DIR.parent / "config" / "matrix.yaml"),
    )
    parser.add_argument(
        "--recipes-dir",
        default=str(rm._REPO_ROOT / "experiment" / "phase1" / "recipes"),
    )
    parser.add_argument(
        "--data-root",
        default=str(rm._REPO_ROOT / "experiment" / "phase1" / "data"),
    )
    parser.add_argument(
        "--run-records-dir",
        default=str(rm._REPO_ROOT / "experiment" / "phase1" / "run_records"),
    )
    parser.add_argument("--research-repo-root", default=str(rm._REPO_ROOT))
    parser.add_argument("--tuner-root", default=str(rm._REPO_ROOT / "synaptic-tuner"))
    return parser


def _find_cell(cells: list[rm.Cell], run_id: str) -> rm.Cell:
    for cell in cells:
        if cell.coordinate.run_id() == run_id:
            return cell
    known = ", ".join(c.coordinate.run_id() for c in cells)
    raise rm.MatrixError(f"unknown run_id {run_id!r}; known cells: {known}")


def _append_arg(parts: list[str], flag: str, value: object | None) -> None:
    if value is None:
        return
    parts.extend([flag, str(value)])


def _apply_kto_logging_workaround(materialized: dict, run_id: str) -> None:
    """Patch the copied KTO trainer in-container before execution.

    The current tuner KTO trainer completes training and writes artifacts, then
    crashes in best-effort run registration because it references `logging`
    without importing it. Keep the workaround outside the submodule by patching
    the copy-mode container file immediately before running the trainer.
    """
    if (materialized.get("run") or {}).get("method") != "kto":
        return

    model = materialized.get("model") or {}
    dataset = materialized.get("dataset") or {}
    training = materialized.get("training") or {}
    lora = materialized.get("lora") or {}
    artifacts = materialized.setdefault("artifacts", {})
    job = materialized.setdefault("job", {})

    output_root = str(artifacts["output_root"])
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_logging_patch"
    artifacts["run_timestamp"] = run_timestamp
    artifacts["host_path"] = f"{output_root}/{run_timestamp}"
    artifacts["container_path"] = f"/workspace/repo/{output_root}/{run_timestamp}"

    # Preserve the container for postmortem if another KTO-only issue appears.
    job["keep_container"] = True

    local_file = str(dataset["local_file"]).replace("\\", "/")
    trainer_parts = ["python", "train_kto.py"]
    _append_arg(trainer_parts, "--model-name", model.get("name") or model.get("model_name"))
    _append_arg(
        trainer_parts,
        "--max-seq-length",
        model.get("max_seq_length") or training.get("max_seq_length"),
    )
    _append_arg(trainer_parts, "--local-file", f"../../{local_file}")
    _append_arg(trainer_parts, "--batch-size", training.get("batch_size"))
    _append_arg(trainer_parts, "--gradient-accumulation", training.get("gradient_accumulation"))
    _append_arg(trainer_parts, "--learning-rate", training.get("learning_rate"))
    _append_arg(trainer_parts, "--seed", training.get("seed"))
    _append_arg(trainer_parts, "--num-epochs", training.get("num_epochs"))
    _append_arg(trainer_parts, "--max-steps", training.get("max_steps"))
    _append_arg(trainer_parts, "--beta", training.get("beta"))
    _append_arg(trainer_parts, "--lora-r", lora.get("r"))
    _append_arg(trainer_parts, "--lora-alpha", lora.get("alpha") or lora.get("lora_alpha"))
    _append_arg(trainer_parts, "--lora-dropout", lora.get("dropout") or lora.get("lora_dropout"))
    target_modules = lora.get("target_modules")
    if target_modules:
        _append_arg(trainer_parts, "--lora-target-modules", ",".join(target_modules))
    _append_arg(trainer_parts, "--init-lora-weights", lora.get("init_lora_weights"))
    if lora.get("use_dora"):
        trainer_parts.append("--use-dora")
    if lora.get("use_rslora"):
        trainer_parts.append("--use-rslora")
    trainer_parts.extend([
        "--output-root",
        f"../../{output_root}",
        "--run-timestamp",
        run_timestamp,
    ])

    patch_cmd = (
        "python -c \"from pathlib import Path; p=Path('train_kto.py'); "
        "s=p.read_text(); p.write_text(s.replace('import time\\n', "
        "'import time\\nimport logging\\n', 1))\""
    )
    materialized["run"] = {
        "command": ["bash", "-lc", f"{patch_cmd} && {' '.join(trainer_parts)}"],
        "workdir": "/workspace/repo/Trainers/kto",
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    matrix = rm.load_yaml(Path(args.matrix))
    cells = rm.expand_matrix(matrix)
    cell = _find_cell(cells, args.run_id)
    if cell.coordinate.size != "4b":
        raise rm.MatrixError(
            f"{args.run_id} is size={cell.coordinate.size}; prepare_local_cell is "
            "reserved for local 4B smoke/pilot cells."
        )

    recipes_dir = Path(args.recipes_dir)
    data_root = Path(args.data_root)
    research_repo_root = Path(args.research_repo_root)
    tuner_root = Path(args.tuner_root)
    run_records_dir = Path(args.run_records_dir)

    base = rm.load_yaml(recipes_dir / f"{cell.recipe}.yaml")
    materialized = rm.materialize_recipe(base, cell, lane="local")
    model_tag = rm.model_tag_from_recipe(base)
    train_file, dev_file = rm.dataset_basenames(base)

    gate = check_prereqs.check_cell(
        lane="local",
        method=cell.method,
        model_tag=model_tag,
        train_file=train_file,
        dev_file=dev_file,
        data_root=data_root,
        research_repo_root=research_repo_root,
        dataset_name=(base.get("dataset") or {}).get("hf_dataset_name"),
        is_bridge=cell.coordinate.is_bridge,
    )
    if gate.skip or not gate.ok:
        reason = gate.skip_reason or "gate did not pass"
        raise check_prereqs.PrereqError(f"{args.run_id}: {reason}")

    data_block = rm.stage_local_data(
        data_root=data_root,
        tuner_root=tuner_root,
        run_id=args.run_id,
        model_tag=model_tag,
        train_file=train_file,
        dev_file=dev_file,
    )
    data_block["hf_dataset_name"] = None
    data_block["hf_dataset_revision"] = None
    materialized["dataset"]["local_file"] = data_block["staged_data_file"]
    setup = materialized.setdefault("setup", {})
    setup["copy"] = [
        f"Trainers/{cell.method}",
        "Trainers/shared",
        "shared",
        "tuner",
        data_block["staged_data_file"],
    ]
    _apply_kto_logging_workaround(materialized, args.run_id)

    materialized_dir = run_records_dir / "materialized_recipes"
    materialized_dir.mkdir(parents=True, exist_ok=True)
    materialized_path = materialized_dir / f"{args.run_id}.yaml"
    materialized_text = yaml.safe_dump(materialized, sort_keys=False)
    materialized_path.write_text(materialized_text, encoding="utf-8")

    invocation = rm.local_invocation(materialized_path.resolve())
    record = rm.build_run_record(
        cell=cell,
        recipe=materialized,
        materialized_text=materialized_text,
        lane="local",
        research_repo_root=research_repo_root,
        data_block=data_block,
        status=args.status,
        tuner_invocation=invocation,
        prereq_details={"datasets_present": True, "leakage_guard_passed": True},
    )
    record["matrix_version"] = matrix["matrix_version"]
    record["materialized_recipe"] = str(materialized_path)
    record_path = rm.write_run_record(record, run_records_dir)

    print(json.dumps({
        "run_id": args.run_id,
        "status": args.status,
        "materialized_recipe": str(materialized_path),
        "run_record": str(record_path),
        "staged_data_file": data_block["staged_data_file"],
        "command": invocation,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
