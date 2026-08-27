#!/usr/bin/env python3
"""Local-lane preflight, recipe render, and staging for the two-way SFT run.

Copy-and-simplify of ``fresh-sft-epistemic-mode-token-grpo/prepare_stage_s.py``.
The Stage-S preparer carried a Modal launch/plan path; this successor is pinned to
the LOCAL RTX 3090 lane (training.yaml sec ``lane``, LOCKED 2026-07-24), so all
Modal planning/launch machinery is dropped. What remains is the deterministic,
no-launch spine:

- verify the relabeled train/dev dataset (sha256 + row counts) produced by the
  builder;
- treat the frozen held-out file as SEALED: hash its bytes only, never parse a
  row, and record ``rows_parsed == 0``;
- verify the pinned repaired tuner (commit f6f1229+, PEFT-aware adapter loader)
  on a clean worktree;
- render the no-launch SFT recipe (dry_run stays true, launch stays unauthorized);
- stage train + dev only.

This module never launches training and never authorizes a launch; a GPU run is a
separate, human-approved step after sign.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

TRAIN_FILE = "train.jsonl"
DEV_FILE = "dev.jsonl"
PENDING_SENTINEL = "PENDING_BUILDER_OUTPUT"


class PreparationError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_jsonl_rows(path: Path) -> int:
    rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows += 1
    return rows


def load_config(config_path: Path) -> tuple[dict[str, Any], Path, Path]:
    config_path = config_path.resolve()
    experiment_dir = config_path.parent
    repo_root = experiment_dir.parents[1]
    value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PreparationError(f"expected YAML mapping: {config_path}")
    if value.get("schema_version") != 1:
        raise PreparationError("training config schema_version must equal 1")
    if value.get("experiment") != experiment_dir.name:
        raise PreparationError("training config experiment does not match directory")
    if value.get("launch_authorized") is not False:
        raise PreparationError("training config must declare launch_authorized: false")
    return value, experiment_dir, repo_root


def _resolve_within(root: Path, relative: str, label: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PreparationError(f"{label} escapes its allowed root") from exc
    return path


def seal_heldout(config: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    """Verify the sealed held-out file by BYTES ONLY. Never parse a row.

    Returns a record asserting zero rows were parsed. This is the sole contact
    this preparer has with the held-out file, and it is a hash comparison only.
    """
    heldout = config["private_dataset"]["heldout"]
    if str(heldout.get("access")) != "forbidden_sealed_carried_forward_untouched":
        raise PreparationError("held-out access flag is not the sealed-carry-forward value")
    path = _resolve_within(repo_root, str(heldout["source"]), "heldout.source")
    if not path.is_file():
        raise PreparationError(f"sealed held-out file is missing: {path}")
    actual = sha256_file(path)  # bytes only; the file is never opened as text/JSON
    if actual != str(heldout["sha256"]):
        raise PreparationError("sealed held-out SHA-256 mismatch")
    return {"path": str(path), "sha256": actual, "rows_parsed": 0}


def verify_dataset(config: Mapping[str, Any], experiment_dir: Path) -> dict[str, Any]:
    """Verify the relabeled train/dev split. sha256 checked when pinned (post-sign)."""
    dataset = config["private_dataset"]
    directory = _resolve_within(experiment_dir, str(dataset["directory"]), "private_dataset.directory")
    report: dict[str, Any] = {"directory": str(directory), "splits": {}}
    for split_name, filename in (("train", TRAIN_FILE), ("dev", DEV_FILE)):
        spec = dataset["splits"][split_name]
        path = directory / str(spec["file"])
        if str(spec["file"]) != filename:
            raise PreparationError(f"{split_name} filename is not the expected {filename}")
        if not path.is_file():
            raise PreparationError(f"{split_name} split is missing: {path}")
        actual_sha = sha256_file(path)
        actual_rows = _count_jsonl_rows(path)
        if actual_rows != int(spec["rows"]):
            raise PreparationError(
                f"{split_name} row-count mismatch: expected {spec['rows']}, got {actual_rows}"
            )
        pinned = spec.get("sha256")
        if pinned is not None and str(pinned) != PENDING_SENTINEL and str(pinned) != actual_sha:
            raise PreparationError(f"{split_name} SHA-256 mismatch")
        report["splits"][split_name] = {
            "path": str(path),
            "sha256": actual_sha,
            "rows": actual_rows,
            "sha256_pinned": pinned is not None and str(pinned) != PENDING_SENTINEL,
        }
    return report


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )


def verify_tuner(config: Mapping[str, Any], tuner_root: Path) -> str:
    tuner = config["tuner"]
    tuner_root = tuner_root.resolve()
    top = _git(tuner_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != tuner_root:
        raise PreparationError("tuner worktree is not an exact repository root")
    head = _git(tuner_root, "rev-parse", "HEAD")
    actual = head.stdout.strip().lower() if head.returncode == 0 else ""
    expected = str(tuner["expected_commit"]).lower()
    if not (actual == expected or actual.startswith(expected)):
        raise PreparationError(f"tuner commit mismatch: expected {expected}, got {actual}")
    if tuner.get("require_clean_worktree") is not True:
        raise PreparationError("training requires tuner.require_clean_worktree=true")
    status = _git(tuner_root, "status", "--porcelain", "--untracked-files=all")
    if status.returncode != 0 or status.stdout.strip():
        raise PreparationError("training requires an exactly clean pinned tuner worktree")
    return actual


def verify_base_snapshot(config: Mapping[str, Any], snapshot_dir: Path) -> dict[str, Any]:
    required = config["model"]["required_snapshot_files"]
    verified: dict[str, str] = {}
    for filename, expected_sha in required.items():
        path = snapshot_dir / str(filename)
        if not path.is_file():
            raise PreparationError(f"base-model snapshot file missing: {filename}")
        actual = sha256_file(path)
        if actual != str(expected_sha):
            raise PreparationError(f"base-model snapshot SHA-256 mismatch: {filename}")
        verified[str(filename)] = actual
    return verified


def render_recipe(
    config: Mapping[str, Any],
    template: Mapping[str, Any],
    *,
    run_id: str,
    staged_train: str,
    artifact_root: str,
) -> dict[str, Any]:
    """Pure render of the no-launch SFT recipe. dry_run and no-launch are invariant."""
    if template.get("run", {}).get("dry_run") is not True:
        raise PreparationError("recipe template must keep run.dry_run: true")
    recipe = json.loads(json.dumps(template))  # deep copy without shared references
    recipe["name"] = f"{config['experiment']}--{run_id}"
    recipe["run"]["dry_run"] = True
    model = config["model"]
    recipe["model"]["repo"] = model["repo"]
    recipe["model"]["revision"] = model["revision"]
    recipe["model"]["load_in_4bit"] = bool(model["load_in_4bit"])
    tokens = list(model["tokenizer"]["additional_special_tokens"])
    if len(tokens) != 2 or len(set(tokens)) != 2:
        raise PreparationError("recipe render requires exactly two unique special tokens")
    recipe["model"]["additional_special_tokens"] = tokens
    recipe["model"]["train_new_embedding_rows"] = bool(model["tokenizer"]["train_new_embedding_rows"])
    recipe["model"]["train_new_lm_head_rows"] = bool(model["tokenizer"]["train_new_lm_head_rows"])
    recipe["dataset"] = {"format": "chat_jsonl", "train_path": staged_train}
    recipe["artifacts"] = {
        "output_root": artifact_root,
        "artifact": config["canonical_output"]["artifact"],
        "retain_merged_model": bool(config["canonical_output"]["retain_merged_model"]),
        "merged_model_save_method": model["tokenizer"]["merged_model_save_method"],
    }
    if recipe["run"]["dry_run"] is not True:
        raise PreparationError("recipe render must not enable a live run")
    return recipe


def stage(config: Mapping[str, Any], experiment_dir: Path, staging_root: Path) -> dict[str, Any]:
    """Copy train + dev into the staging root. Held-out is never staged."""
    dataset = config["private_dataset"]
    directory = _resolve_within(experiment_dir, str(dataset["directory"]), "private_dataset.directory")
    staging_root = staging_root.resolve()
    staging_root.mkdir(parents=True, exist_ok=True)
    staged: dict[str, Any] = {}
    for split_name, filename in (("train", TRAIN_FILE), ("dev", DEV_FILE)):
        source = directory / filename
        if not source.is_file():
            raise PreparationError(f"cannot stage missing {split_name} split: {source}")
        destination = staging_root / filename
        shutil.copyfile(source, destination)
        if sha256_file(destination) != sha256_file(source):
            raise PreparationError(f"staged {split_name} copy hash mismatch")
        staged[split_name] = {"path": str(destination), "sha256": sha256_file(destination)}
    heldout_name = Path(str(dataset["heldout"]["source"])).name
    if (staging_root / heldout_name).exists():
        raise PreparationError("held-out file must never be staged")
    return staged


def preflight(
    config_path: Path,
    *,
    tuner_root: Path | None = None,
    snapshot_dir: Path | None = None,
    staging_root: Path | None = None,
) -> dict[str, Any]:
    config, experiment_dir, repo_root = load_config(config_path)
    template = yaml.safe_load(
        _resolve_within(experiment_dir, str(config["tuner"]["recipe_template"]), "recipe_template")
        .read_text(encoding="utf-8")
    )
    report: dict[str, Any] = {
        "experiment": config["experiment"],
        "lane": config["lane"]["compute"],
        "launch_authorized": False,
        "dataset": verify_dataset(config, experiment_dir),
        "heldout_seal": seal_heldout(config, repo_root),
    }
    if tuner_root is not None:
        report["tuner_commit"] = verify_tuner(config, tuner_root)
    if snapshot_dir is not None:
        report["base_snapshot"] = verify_base_snapshot(config, snapshot_dir)
    train_path = report["dataset"]["splits"]["train"]["path"]
    report["rendered_recipe"] = render_recipe(
        config, template, run_id="preflight",
        staged_train=train_path, artifact_root="scratch/eh_staging/artifacts",
    )
    if staging_root is not None:
        report["staged"] = stage(config, experiment_dir, staging_root)
    if report["heldout_seal"]["rows_parsed"] != 0 or report["launch_authorized"] is not False:
        raise PreparationError("preflight invariant violated (held-out parsed or launch authorized)")
    return report


def parse_args(argv: Any = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("training.yaml"))
    parser.add_argument("--tuner-worktree", type=Path)
    parser.add_argument("--snapshot-dir", type=Path)
    parser.add_argument("--staging-root", type=Path)
    return parser.parse_args(argv)


def main(argv: Any = None) -> int:
    args = parse_args(argv)
    try:
        report = preflight(
            args.config, tuner_root=args.tuner_worktree,
            snapshot_dir=args.snapshot_dir, staging_root=args.staging_root,
        )
    except PreparationError as exc:
        print(f"preparation failed: {exc}", file=sys.stderr)
        return 2
    print(canonical_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
