#!/usr/bin/env python3
"""Preflight and privately stage Stage-S inputs without launching training."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

import yaml


TOKENIZER_KEYS = (
    "additional_special_tokens",
    "existing_token_policy",
    "initialization",
    "train_new_embedding_rows",
    "train_new_lm_head_rows",
    "verify_tokenizer_roundtrip",
    "verify_adapter_roundtrip",
    "verify_merged_model_roundtrip",
    "merged_model_save_method",
)
TOKENIZER_BOOLEAN_KEYS = (
    "train_new_embedding_rows",
    "train_new_lm_head_rows",
    "verify_tokenizer_roundtrip",
    "verify_adapter_roundtrip",
    "verify_merged_model_roundtrip",
)
MERGED_MODEL_SAVE_METHODS = {"merged_16bit", "merged_4bit_forced"}
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
OCI_IMAGE_PATTERN = re.compile(r".+@sha256:[0-9a-fA-F]{64}\Z")
MODAL_INPUT_ROOT = Path("/vol/inputs")
MODAL_OUTPUT_ROOT = Path("/vol/artifacts/outputs")
SMOKE_MAX_STEPS = 2
SMOKE_DATASET_FILE = "smoke_train.jsonl"
SMOKE_CONFIG_FILE = "smoke_sft.yaml"
FULL_DATASET_FILE = "stage_s_train.jsonl"
FULL_CONFIG_FILE = "stage_s_full.yaml"
FULL_RUN_ID_PATTERN = re.compile(r"stage-s-full-[A-Za-z0-9][A-Za-z0-9._-]{0,48}\Z")
QUALIFICATION_RUN_ID_PATTERN = re.compile(
    r"stage-s-qual-[A-Za-z0-9][A-Za-z0-9._-]{0,48}\Z"
)
QUALIFICATION_CONFIG_FILE = "qualification.yaml"
MODAL_QUALIFICATION_CONFIG_FILE = "modal_qualification.yaml"
QUALIFICATION_DEV_FILE = "dev.jsonl"
QUALIFICATION_MANIFEST_FILE = "qualification_launch_manifest.json"


class PreflightError(ValueError):
    """Raised for an invalid preflight definition or unsafe staging request."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise PreflightError(f"{name} must be a mapping")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise PreflightError(f"{path.name} must contain a YAML mapping")
    return value


def load_config(path: Path) -> dict[str, Any]:
    config = _load_yaml(path)
    if config.get("schema_version") != 1:
        raise PreflightError("stage_s config schema_version must equal 1")
    if config.get("launch_authorized") is not False:
        raise PreflightError("stage_s launch_authorized must remain false")
    for section in ("private_dataset", "model", "tuner", "modal"):
        _require_mapping(config.get(section), section)
    if not isinstance(config["model"].get("load_in_4bit"), bool):
        raise PreflightError("model.load_in_4bit must be an explicit YAML boolean")
    if config["model"].get("dtype") is not None:
        raise PreflightError("model.dtype must be null for explicit automatic dtype selection")
    modal = config["modal"]
    for key in ("input_volume", "output_volume", "cache_volume", "gpu"):
        if not isinstance(modal.get(key), str) or not modal[key].strip():
            raise PreflightError(f"modal.{key} must be a non-empty string")
    if modal["gpu"] != "A10G":
        raise PreflightError("modal.gpu must equal A10G for the Stage-S smoke")
    if modal.get("input_mount") != str(MODAL_INPUT_ROOT):
        raise PreflightError(f"modal.input_mount must equal {MODAL_INPUT_ROOT}")
    if modal.get("output_mount") != str(MODAL_OUTPUT_ROOT.parent):
        raise PreflightError(f"modal.output_mount must equal {MODAL_OUTPUT_ROOT.parent}")
    timeout_hours = modal.get("timeout_hours")
    if isinstance(timeout_hours, bool) or not isinstance(timeout_hours, (int, float)) or timeout_hours <= 0:
        raise PreflightError("modal.timeout_hours must be a positive number")
    tokenizer = _require_mapping(config["model"].get("tokenizer"), "model.tokenizer")
    if tuple(tokenizer) != TOKENIZER_KEYS:
        raise PreflightError(
            "model.tokenizer must declare exactly the expected generic tuner schema in order"
        )
    tokens = tokenizer["additional_special_tokens"]
    if not isinstance(tokens, list) or not tokens:
        raise PreflightError("additional_special_tokens must be a non-empty YAML list")
    if any(not isinstance(token, str) or not token for token in tokens):
        raise PreflightError("additional_special_tokens entries must be non-empty strings")
    if len(set(tokens)) != len(tokens):
        raise PreflightError("additional_special_tokens must not contain duplicates")
    for key in TOKENIZER_BOOLEAN_KEYS:
        if not isinstance(tokenizer[key], bool):
            raise PreflightError(f"model.tokenizer.{key} must be a YAML boolean")
    save_method = tokenizer["merged_model_save_method"]
    if save_method not in MERGED_MODEL_SAVE_METHODS:
        raise PreflightError(
            "model.tokenizer.merged_model_save_method must be a supported generic tuner value"
        )
    return config


def _block(blockers: list[dict[str, Any]], code: str, **details: Any) -> None:
    blockers.append({"code": code, **details})


def _resolve_within(root: Path, relative: str, name: str) -> Path:
    configured = Path(relative)
    if configured.is_absolute():
        raise PreflightError(f"{name} must be relative")
    resolved = (root / configured).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PreflightError(f"{name} escapes its allowed root") from exc
    return resolved


def _check_file(
    path: Path,
    expected_sha: str,
    blockers: list[dict[str, Any]],
    code_prefix: str,
) -> str | None:
    if not path.is_file():
        _block(blockers, f"{code_prefix}_missing", file=path.name)
        return None
    actual = sha256_file(path)
    if actual != expected_sha:
        _block(
            blockers,
            f"{code_prefix}_sha256_mismatch",
            file=path.name,
            expected_sha256=expected_sha,
            actual_sha256=actual,
        )
    return actual


def _count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def check_private_dataset(
    config: Mapping[str, Any],
    experiment_dir: Path,
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    private = config["private_dataset"]
    dataset_dir = _resolve_within(experiment_dir, private["directory"], "private_dataset.directory")
    analysis_root = (experiment_dir / "analysis").resolve()
    try:
        dataset_dir.relative_to(analysis_root)
    except ValueError as exc:
        raise PreflightError("private_dataset.directory must remain under experiment analysis/") from exc

    aggregate_config = private["aggregate_manifest"]
    aggregate_path = dataset_dir / aggregate_config["file"]
    aggregate_sha = _check_file(
        aggregate_path,
        aggregate_config["sha256"],
        blockers,
        "aggregate_manifest",
    )
    aggregate: dict[str, Any] | None = None
    if aggregate_path.is_file():
        try:
            with aggregate_path.open("r", encoding="utf-8") as handle:
                aggregate = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            _block(blockers, "aggregate_manifest_invalid_json", error_type=type(exc).__name__)
    if aggregate is not None:
        for field in (
            "identity_overlap_across_splits",
            "normalized_question_overlap_across_splits",
        ):
            value = aggregate.get(field)
            if value != 0:
                _block(
                    blockers,
                    "aggregate_split_overlap_nonzero",
                    field=field,
                    expected=0,
                    actual=value,
                )

    verified_splits: dict[str, Any] = {}
    for split in ("train", "dev", "heldout"):
        expected = private["splits"][split]
        path = dataset_dir / expected["file"]
        actual_sha = _check_file(path, expected["sha256"], blockers, f"{split}_artifact")
        actual_rows = _count_lines(path) if path.is_file() else None
        if actual_rows is not None and actual_rows != expected["rows"]:
            _block(
                blockers,
                f"{split}_artifact_row_count_mismatch",
                expected_rows=expected["rows"],
                actual_rows=actual_rows,
            )
        if aggregate is not None:
            manifest_entry = aggregate.get("outputs", {}).get(split)
            if not isinstance(manifest_entry, dict):
                _block(blockers, "aggregate_split_missing", split=split)
            else:
                if manifest_entry.get("sha256") != expected["sha256"]:
                    _block(blockers, "aggregate_split_sha256_mismatch", split=split)
                if manifest_entry.get("rows") != expected["rows"]:
                    _block(blockers, "aggregate_split_row_count_mismatch", split=split)
        verified_splits[split] = {
            "path": path,
            "sha256": actual_sha,
            "rows": actual_rows,
        }
    return {
        "directory": dataset_dir,
        "aggregate_path": aggregate_path,
        "aggregate_sha256": aggregate_sha,
        "mode_counts": aggregate.get("mode_counts") if isinstance(aggregate, dict) else None,
        "splits": verified_splits,
    }


def default_hf_cache_root() -> Path:
    hf_home = os.environ.get("HF_HOME")
    base = Path(hf_home).expanduser() if hf_home else Path.home() / ".cache" / "huggingface"
    return base / "hub"


def check_model_snapshot(
    config: Mapping[str, Any],
    hf_cache_root: Path,
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    model = config["model"]
    revision = model.get("revision")
    if not isinstance(revision, str) or not COMMIT_PATTERN.fullmatch(revision):
        _block(blockers, "model_revision_unresolved", configured_revision=revision)
        return {"snapshot": None, "revision": revision, "files": {}}
    repo = model.get("repo")
    if not isinstance(repo, str) or "/" not in repo:
        raise PreflightError("model.repo must be a Hugging Face owner/repository string")
    cache_dir = hf_cache_root / ("models--" + repo.replace("/", "--"))
    snapshot = cache_dir / "snapshots" / revision
    if not snapshot.is_dir():
        _block(blockers, "model_revision_snapshot_missing", revision=revision)
        return {"snapshot": snapshot, "revision": revision, "files": {}}
    verified_files: dict[str, str | None] = {}
    for filename, expected_sha in model["required_snapshot_files"].items():
        verified_files[filename] = _check_file(
            snapshot / filename,
            expected_sha,
            blockers,
            "model_snapshot_file",
        )
    return {"snapshot": snapshot, "revision": revision, "files": verified_files}


def _git(tuner_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(tuner_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def check_tuner(
    config: Mapping[str, Any],
    tuner_root: Path,
    blockers: list[dict[str, Any]],
) -> dict[str, Any]:
    tuner_root = tuner_root.resolve()
    top = _git(tuner_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != tuner_root:
        _block(blockers, "tuner_worktree_invalid")
        return {
            "root": tuner_root,
            "commit": None,
            "repo_url": None,
            "branch": None,
            "dirty_entry_count": None,
        }

    head_result = _git(tuner_root, "rev-parse", "HEAD")
    head = head_result.stdout.strip() if head_result.returncode == 0 else None
    remote_result = _git(tuner_root, "remote", "get-url", "origin")
    repo_url = remote_result.stdout.strip() if remote_result.returncode == 0 else None
    if not repo_url:
        _block(blockers, "tuner_origin_url_unresolved")
    branch_result = _git(tuner_root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    if not branch or branch == "HEAD":
        _block(blockers, "tuner_named_branch_unresolved")
    expected = config["tuner"].get("expected_commit")
    if not isinstance(expected, str) or not COMMIT_PATTERN.fullmatch(expected):
        _block(blockers, "tuner_expected_commit_unresolved", configured_commit=expected)
    elif head != expected:
        _block(blockers, "tuner_commit_mismatch", expected_commit=expected, actual_commit=head)

    status = _git(tuner_root, "status", "--porcelain", "--untracked-files=all")
    dirty_count = len([line for line in status.stdout.splitlines() if line.strip()])
    if status.returncode != 0:
        _block(blockers, "tuner_status_failed")
    elif config["tuner"].get("require_clean_worktree") is True and dirty_count:
        _block(blockers, "tuner_worktree_dirty", dirty_entry_count=dirty_count)

    staging_relative = Path(config["tuner"]["staging_root"])
    if staging_relative.parts[:2] != ("scratch", "eh_staging") or staging_relative.is_absolute():
        raise PreflightError("tuner.staging_root must be beneath scratch/eh_staging")
    staging_root = _resolve_within(tuner_root, str(staging_relative), "tuner.staging_root")
    ignore_probe = staging_relative / ".preflight_ignore_probe"
    ignored = _git(tuner_root, "check-ignore", "-q", "--no-index", str(ignore_probe))
    if ignored.returncode != 0:
        _block(blockers, "tuner_staging_root_not_ignored")
    return {
        "root": tuner_root,
        "commit": head,
        "repo_url": repo_url,
        "branch": branch,
        "dirty_entry_count": dirty_count,
        "staging_root": staging_root,
        "staging_relative": staging_relative,
    }


def _pending_paths(value: Any, prefix: str = "") -> list[str]:
    pending: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            pending.extend(_pending_paths(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            pending.extend(_pending_paths(child, f"{prefix}[{index}]"))
    elif isinstance(value, str) and "pending_pre_sign" in value:
        pending.append(prefix)
    return pending


def render_recipe(
    config: Mapping[str, Any],
    template: Mapping[str, Any],
    run_id: str,
    staged_relative: Path,
) -> dict[str, Any]:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise PreflightError("run_id must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")
    recipe = json.loads(json.dumps(template))
    recipe["name"] = f"eh-stage-s-{run_id}"
    model = recipe.setdefault("model", {})
    model["name"] = config["model"]["repo"]
    model["revision"] = config["model"]["revision"]
    model["load_in_4bit"] = config["model"]["load_in_4bit"]
    model["dtype"] = config["model"]["dtype"]
    model["tokenizer"] = dict(config["model"]["tokenizer"])
    recipe.setdefault("dataset", {})["local_file"] = str(staged_relative / "train.jsonl")
    recipe.setdefault("artifacts", {})["output_root"] = str(staged_relative / "artifacts")
    recipe["artifacts"]["run_timestamp"] = "{timestamp}"
    return recipe


def check_recipe(
    config: Mapping[str, Any],
    experiment_dir: Path,
    staged_relative: Path,
    run_id: str,
    blockers: list[dict[str, Any]],
) -> tuple[dict[str, Any], Path]:
    template_path = _resolve_within(
        experiment_dir,
        config["tuner"]["recipe_template"],
        "tuner.recipe_template",
    )
    if not template_path.is_file():
        _block(blockers, "recipe_template_missing", file=template_path.name)
        return {}, template_path
    template = _load_yaml(template_path)
    template_model = _require_mapping(template.get("model"), "recipe template model")
    if template_model.get("load_in_4bit") != config["model"]["load_in_4bit"]:
        _block(blockers, "recipe_model_load_in_4bit_mismatch")
    if "dtype" not in template_model or template_model.get("dtype") != config["model"]["dtype"]:
        _block(blockers, "recipe_model_dtype_mismatch")
    job = _require_mapping(template.get("job"), "recipe template job")
    runtime_image = job.get("image")
    if not isinstance(runtime_image, str) or not OCI_IMAGE_PATTERN.fullmatch(runtime_image):
        _block(blockers, "recipe_runtime_image_not_immutable", configured=runtime_image)
    setup = _require_mapping(template.get("setup"), "recipe template setup")
    dependency_pins = setup.get("pip")
    if not isinstance(dependency_pins, list) or not dependency_pins:
        _block(blockers, "recipe_dependency_pins_missing")
    elif any(
        not isinstance(requirement, str)
        or requirement.count("==") != 1
        or not all(part.strip() for part in requirement.split("==", 1))
        for requirement in dependency_pins
    ):
        _block(blockers, "recipe_dependency_pin_not_exact")
    recipe = render_recipe(config, template, run_id, staged_relative)
    tokenizer = recipe.get("model", {}).get("tokenizer")
    if not isinstance(tokenizer, dict) or tuple(tokenizer) != TOKENIZER_KEYS:
        _block(blockers, "rendered_tokenizer_schema_mismatch")
    if recipe.get("model", {}).get("revision") != config["model"]["revision"]:
        _block(blockers, "rendered_model_revision_mismatch")
    if recipe.get("model", {}).get("load_in_4bit") != config["model"]["load_in_4bit"]:
        _block(blockers, "rendered_model_load_in_4bit_mismatch")
    pending = _pending_paths(recipe)
    if pending:
        _block(blockers, "recipe_fields_unresolved", fields=pending)
    if recipe.get("run", {}).get("dry_run") is not True:
        _block(blockers, "no_launch_recipe_must_be_dry_run")
    return recipe, template_path


def preflight(
    config_path: Path,
    tuner_root: Path,
    *,
    hf_cache_root: Path | None = None,
    run_id: str = "preflight",
) -> tuple[dict[str, Any], dict[str, Any]]:
    config_path = config_path.resolve()
    experiment_dir = config_path.parent
    config = load_config(config_path)
    blockers: list[dict[str, Any]] = []
    dataset = check_private_dataset(config, experiment_dir, blockers)
    model = check_model_snapshot(config, (hf_cache_root or default_hf_cache_root()).resolve(), blockers)
    tuner = check_tuner(config, tuner_root, blockers)
    staged_relative = Path(config["tuner"]["staging_root"]) / run_id
    recipe, template_path = check_recipe(
        config,
        experiment_dir,
        staged_relative,
        run_id,
        blockers,
    )
    report = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "mode": "preflight_no_launch",
        "launch_authorized": False,
        "ready_to_stage": not blockers,
        "blockers": blockers,
        "verified": {
            "aggregate_manifest_sha256": dataset["aggregate_sha256"],
            "split_sha256": {
                split: details["sha256"] for split, details in dataset["splits"].items()
            },
            "split_rows": {
                split: details["rows"] for split, details in dataset["splits"].items()
            },
            "model_revision": model["revision"],
            "model_snapshot_files": model["files"],
            "tuner_commit": tuner["commit"],
            "tuner_dirty_entry_count": tuner["dirty_entry_count"],
            "configured_special_token_count": len(config["model"]["tokenizer"]["additional_special_tokens"]),
            "recipe_template_sha256": sha256_file(template_path) if template_path.is_file() else None,
        },
    }
    context = {
        "config_path": config_path,
        "config": config,
        "dataset": dataset,
        "model": model,
        "tuner": tuner,
        "recipe": recipe,
        "recipe_template_path": template_path,
        "staged_relative": staged_relative,
    }
    return report, context


def stage(context: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    tuner = context["tuner"]
    staging_root: Path = tuner["staging_root"]
    destination = staging_root / run_id
    if destination.exists():
        raise PreflightError(f"staging destination already exists: {destination}")
    staging_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=staging_root))
    try:
        dataset = context["dataset"]
        # Stage S may stage its training rows and dev-only qualification rows.
        # The held-out bytes remain sealed for a separately registered
        # downstream experiment and must never enter this staging package.
        for split in ("train", "dev"):
            details = dataset["splits"][split]
            copied_path = temporary / f"{split}.jsonl"
            shutil.copyfile(details["path"], copied_path)
            if sha256_file(copied_path) != details["sha256"]:
                raise PreflightError(f"staged {split} bytes changed during copy")
        copied_aggregate = temporary / "aggregate_manifest.json"
        shutil.copyfile(dataset["aggregate_path"], copied_aggregate)
        if sha256_file(copied_aggregate) != dataset["aggregate_sha256"]:
            raise PreflightError("staged aggregate manifest bytes changed during copy")
        recipe_path = temporary / context["config"]["tuner"]["rendered_recipe_file"]
        with recipe_path.open("w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(context["recipe"], handle, sort_keys=False)

        files = {
            path.name: sha256_file(path)
            for path in sorted(temporary.iterdir())
            if path.is_file()
        }
        manifest = {
            "schema_version": 1,
            "experiment": context["config"]["experiment"],
            "run_id": run_id,
            "launch_authorized": False,
            "tuner_commit": tuner["commit"],
            "model_repo": context["config"]["model"]["repo"],
            "model_revision": context["config"]["model"]["revision"],
            "staged_splits": ["train", "dev"],
            "heldout_staged": False,
            "files": files,
        }
        manifest_path = temporary / "staging_manifest.json"
        manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return {
        "schema_version": 1,
        "staged": True,
        "launch_authorized": False,
        "run_id": run_id,
        "relative_directory": str(context["staged_relative"]),
        "staging_manifest_sha256": sha256_file(destination / "staging_manifest.json"),
    }


def _smoke_candidate_rank(source_sha256: str, row_identifier: str) -> str:
    return hashlib.sha256(f"{source_sha256}|{row_identifier}".encode("utf-8")).hexdigest()


def select_smoke_rows(
    train_path: Path,
    source_sha256: str,
    configured_tokens: list[str],
    rows_per_mode: int,
    expected_modes: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    """Select a deterministic, balanced train-only subset without mode semantics."""
    if isinstance(rows_per_mode, bool) or not isinstance(rows_per_mode, int) or rows_per_mode < 1:
        raise PreflightError("smoke rows_per_mode must be a positive integer")

    candidates_by_mode: dict[str, list[dict[str, Any]]] = {}
    token_by_mode: dict[str, str] = {}
    mode_by_token: dict[str, str] = {}
    seen_identifiers: set[str] = set()
    with train_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PreflightError(f"train row {line_number} is not valid JSON") from exc
            if not isinstance(row, dict):
                raise PreflightError(f"train row {line_number} must be a JSON object")
            metadata = _require_mapping(row.get("metadata"), f"train row {line_number} metadata")
            mode = metadata.get("mode_label")
            row_identifier = metadata.get("row_key")
            if not isinstance(mode, str) or not mode:
                raise PreflightError(f"train row {line_number} has no non-empty metadata.mode_label")
            if not isinstance(row_identifier, str) or not row_identifier:
                raise PreflightError(f"train row {line_number} has no non-empty metadata.row_key")
            if row_identifier in seen_identifiers:
                raise PreflightError(f"train dataset contains duplicate row identifier {row_identifier!r}")
            seen_identifiers.add(row_identifier)

            conversations = row.get("conversations")
            if not isinstance(conversations, list) or not conversations:
                raise PreflightError(f"train row {line_number} has no conversations")
            assistant = conversations[-1]
            if not isinstance(assistant, dict) or assistant.get("role") != "assistant":
                raise PreflightError(f"train row {line_number} must end with an assistant message")
            content = assistant.get("content")
            if not isinstance(content, str):
                raise PreflightError(f"train row {line_number} assistant content must be a string")
            matches = sorted(
                (token for token in configured_tokens if content.startswith(token)),
                key=lambda token: (-len(token), configured_tokens.index(token)),
            )
            if not matches:
                raise PreflightError(
                    f"train row {line_number} must begin with a configured special token"
                )
            # Prefix-related strings are valid special tokens. The longest raw
            # prefix is the only candidate that can describe the first atomic
            # token; the data-derived mode/token bijection below catches any
            # inconsistent reuse across rows.
            token = matches[0]
            previous_token = token_by_mode.setdefault(mode, token)
            if previous_token != token:
                raise PreflightError(f"mode {mode!r} maps to multiple configured tokens")
            previous_mode = mode_by_token.setdefault(token, mode)
            if previous_mode != mode:
                raise PreflightError(f"configured token maps to multiple data modes: {token!r}")
            candidates_by_mode.setdefault(mode, []).append(
                {
                    "row": row,
                    "row_identifier": row_identifier,
                    "source_line_number": line_number,
                    "rank": _smoke_candidate_rank(source_sha256, row_identifier),
                }
            )

    expected_mode_set = set(expected_modes or candidates_by_mode)
    missing_modes = sorted(expected_mode_set - set(candidates_by_mode))
    if missing_modes:
        raise PreflightError(
            "train data does not contain rows for every configured mode: "
            + ", ".join(repr(mode) for mode in missing_modes)
        )
    unexpected_modes = sorted(set(candidates_by_mode) - expected_mode_set)
    if unexpected_modes:
        raise PreflightError(
            "train data contains modes absent from the aggregate manifest: "
            + ", ".join(repr(mode) for mode in unexpected_modes)
        )

    ordered_modes = [
        mode_by_token[token]
        for token in configured_tokens
        if token in mode_by_token and mode_by_token[token] in expected_mode_set
    ]
    selected_by_mode: dict[str, list[dict[str, Any]]] = {}
    for mode in ordered_modes:
        candidates = sorted(
            candidates_by_mode[mode],
            key=lambda item: (item["rank"], item["row_identifier"], item["source_line_number"]),
        )
        if len(candidates) < rows_per_mode:
            raise PreflightError(
                f"mode {mode!r} has {len(candidates)} train rows; {rows_per_mode} required"
            )
        selected_by_mode[mode] = candidates[:rows_per_mode]

    selected_rows: list[dict[str, Any]] = []
    selected_manifest: list[dict[str, Any]] = []
    for within_mode_index in range(rows_per_mode):
        for mode in ordered_modes:
            selected = selected_by_mode[mode][within_mode_index]
            position = len(selected_rows)
            selected_rows.append(selected["row"])
            selected_manifest.append(
                {
                    "position": position,
                    "row_identifier": selected["row_identifier"],
                    "mode_label": mode,
                    "configured_token": token_by_mode[mode],
                    "source_line_number": selected["source_line_number"],
                    "selection_rank_sha256": selected["rank"],
                }
            )
    return selected_rows, token_by_mode, selected_manifest


def render_smoke_trainer_config(
    context: Mapping[str, Any],
    run_id: str,
) -> tuple[dict[str, Any], Path]:
    """Overlay the Stage-S candidate onto the exact tuner's direct SFT schema."""
    tuner_config_path = context["tuner"]["root"] / "Trainers" / "sft" / "configs" / "config.yaml"
    if not tuner_config_path.is_file():
        raise PreflightError("tuner direct SFT config is missing")
    direct = json.loads(json.dumps(_load_yaml(tuner_config_path)))
    for section in ("model", "lora", "training", "dataset", "wandb"):
        _require_mapping(direct.get(section), f"tuner direct SFT config {section}")

    recipe = context["recipe"]
    recipe_model = _require_mapping(recipe.get("model"), "rendered recipe model")
    recipe_training = _require_mapping(recipe.get("training"), "rendered recipe training")
    recipe_lora = _require_mapping(recipe.get("lora"), "rendered recipe lora")
    smoke_tokenizer = dict(context["config"]["model"]["tokenizer"])
    smoke_tokenizer["verify_merged_model_roundtrip"] = True
    direct["model"].update(
        {
            "model_name": context["config"]["model"]["repo"],
            "revision": context["config"]["model"]["revision"],
            "max_seq_length": recipe_training["max_seq_length"],
            "load_in_4bit": recipe_model["load_in_4bit"],
            "dtype": recipe_model["dtype"],
            "tokenizer": smoke_tokenizer,
        }
    )
    direct["lora"].update(
        {
            "r": recipe_lora["r"],
            "lora_alpha": recipe_lora["alpha"],
            "lora_dropout": recipe_lora["dropout"],
            "target_modules": list(recipe_lora["target_modules"]),
        }
    )
    direct["training"].update(
        {
            "output_dir": str(MODAL_OUTPUT_ROOT),
            "per_device_train_batch_size": recipe_training["batch_size"],
            "gradient_accumulation_steps": recipe_training["gradient_accumulation"],
            "learning_rate": recipe_training["learning_rate"],
            "num_train_epochs": recipe_training["num_epochs"],
            "max_seq_length": recipe_training["max_seq_length"],
            "save_steps": recipe_training["save_steps"],
            "save_total_limit": recipe_training["save_total_limit"],
            "chat_template_kwargs": dict(recipe_training["chat_template_kwargs"]),
            "max_steps": SMOKE_MAX_STEPS,
            "eval_strategy": "no",
        }
    )
    direct["dataset"].update(
        {
            "dataset_name": None,
            "dataset_file": None,
            "local_file": str(MODAL_INPUT_ROOT / run_id / SMOKE_DATASET_FILE),
            "split_dataset": False,
            "test_size": 0.0,
        }
    )
    direct["wandb"] = {"enabled": False, "project": None, "run_name": None, "entity": None}
    if isinstance(direct.get("evolutionary"), dict):
        direct["evolutionary"]["enabled"] = False
    if isinstance(direct.get("aux_head"), dict):
        direct["aux_head"]["enabled"] = False
    return direct, tuner_config_path


def inspect_modal_plan(
    context: Mapping[str, Any],
    run_id: str,
    config_path: Path,
    dataset_path: Path,
) -> dict[str, Any]:
    """Call the tuner's public inspect-only Modal planner; mutate no provider state."""
    planner = context["tuner"]["root"] / "scripts" / "plan_modal_sft_job.py"
    if not planner.is_file():
        raise PreflightError("tuner public Modal SFT planner is missing")
    modal_config = context["config"]["modal"]
    recipe = context["recipe"]
    command = [
        sys.executable,
        str(planner),
        "--config",
        str(config_path),
        "--dataset",
        str(dataset_path),
        "--input-volume",
        str(modal_config["input_volume"]),
        "--input-prefix",
        run_id,
        "--runtime-image",
        str(recipe["job"]["image"]),
        "--gpu",
        str(modal_config["gpu"]),
        "--timeout-hours",
        str(modal_config["timeout_hours"]),
        "--output-volume",
        str(modal_config["output_volume"]),
        "--output-mount",
        str(modal_config["output_mount"]),
        "--input-mount",
        str(modal_config["input_mount"]),
        "--cache-volume",
        str(modal_config["cache_volume"]),
        "--run-id",
        run_id,
    ]
    for requirement in recipe["setup"]["pip"]:
        command.extend(["--pip-package", requirement])
    result = subprocess.run(
        command,
        cwd=context["tuner"]["root"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        final_line = detail[-1] if detail else "no planner diagnostic"
        raise PreflightError(f"Modal inspect plan failed: {final_line}")
    try:
        plan = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PreflightError("Modal inspect planner did not return JSON") from exc
    if not isinstance(plan, dict):
        raise PreflightError("Modal inspect planner returned a non-object plan")
    return plan


def validate_modal_plan_contract(
    context: Mapping[str, Any],
    run_id: str,
    plan: Mapping[str, Any],
    config_sha256: str,
    dataset_sha256: str,
    *,
    config_filename: str = SMOKE_CONFIG_FILE,
    dataset_filename: str = SMOKE_DATASET_FILE,
) -> dict[str, Any]:
    """Compare the inspected Modal plan to the hash-bound experiment recipe."""
    recipe = context["recipe"]
    modal_config = context["config"]["modal"]
    runtime = _require_mapping(plan.get("runtime"), "Modal inspected plan runtime")
    inputs = _require_mapping(plan.get("inputs"), "Modal inspected plan inputs")
    artifacts = _require_mapping(plan.get("artifacts"), "Modal inspected plan artifacts")
    source = _require_mapping(plan.get("source"), "Modal inspected plan source")
    launch = _require_mapping(plan.get("launch"), "Modal inspected plan launch")
    environment = _require_mapping(
        launch.get("environment"), "Modal inspected plan launch environment"
    )
    verification = _require_mapping(
        launch.get("verification"), "Modal inspected plan launch verification"
    )
    launch_argv = launch.get("argv")
    if not isinstance(launch_argv, list):
        raise PreflightError("Modal inspected plan launch argv must be a list")

    expected_image = recipe["job"]["image"]
    expected_pips = list(recipe["setup"]["pip"])
    if runtime.get("image") != expected_image:
        raise PreflightError("Modal inspected runtime image differs from stage_sft_recipe.yaml")
    if runtime.get("pip_packages") != expected_pips:
        raise PreflightError("Modal inspected dependency pins differ from stage_sft_recipe.yaml")
    if not OCI_IMAGE_PATTERN.fullmatch(expected_image):
        raise PreflightError("Modal inspected runtime image is not immutable")

    config_input = _require_mapping(inputs.get("config"), "Modal inspected config input")
    dataset_input = _require_mapping(inputs.get("dataset"), "Modal inspected dataset input")
    expected_config_path = str(MODAL_INPUT_ROOT / run_id / config_filename)
    expected_dataset_path = str(MODAL_INPUT_ROOT / run_id / dataset_filename)
    expected_config_volume_path = str(Path(run_id) / config_filename)
    expected_dataset_volume_path = str(Path(run_id) / dataset_filename)
    expected_commit = str(context["tuner"]["commit"]).lower()
    expected_repo_url = context["tuner"]["repo_url"]
    expected_branch = context["tuner"]["branch"]
    if not COMMIT_PATTERN.fullmatch(expected_commit):
        raise PreflightError("Modal launch contract requires a resolved tuner commit")
    if not isinstance(expected_repo_url, str) or not expected_repo_url.strip():
        raise PreflightError("Modal launch contract requires a resolved tuner origin URL")
    if not isinstance(expected_branch, str) or not expected_branch.strip():
        raise PreflightError("Modal launch contract requires a resolved named tuner branch")
    expected_wrapper = context["tuner"]["root"] / "Trainers" / "cloud" / "train_modal.py"
    if not expected_wrapper.is_file():
        raise PreflightError("Modal launch contract requires the direct training wrapper")
    expected_environment = {
        "MODAL_TRAINING_IMAGE": expected_image,
        "MODAL_TRAINING_PIP_PACKAGES_JSON": json.dumps(
            expected_pips, separators=(",", ":")
        ),
        "MODAL_GPU": modal_config["gpu"],
        "MODAL_TIMEOUT_SECONDS": str(int(modal_config["timeout_hours"] * 3600)),
        "MODAL_INPUT_VOLUME_NAME": modal_config["input_volume"],
        "MODAL_INPUT_MOUNT_PATH": modal_config["input_mount"],
        "MODAL_CACHE_VOLUME_NAME": modal_config["cache_volume"],
        "MODAL_OUTPUT_VOLUME_NAME": modal_config["output_volume"],
        "MODAL_OUTPUT_MOUNT_PATH": modal_config["output_mount"],
    }
    expected_argv = [
        "modal",
        "run",
        "--detach",
        f"{expected_wrapper}::run_stable_training",
        "--trainer-type",
        "sft",
        "--repo-url",
        expected_repo_url,
        "--repo-branch",
        expected_branch,
        "--repo-commit",
        expected_commit,
        "--config-path",
        expected_config_path,
        "--config-sha256",
        config_sha256,
        "--dataset-sha256",
        dataset_sha256,
        "--run-id",
        run_id,
    ]
    expected_verification = {
        "require_nonempty_app_id_from_submission": True,
        "require_remote_function": "run_stable_training",
        "require_running_or_completed_task": True,
        "commands": [
            ["modal", "app", "list", "--json"],
            ["modal", "app", "logs", "<app-id>"],
        ],
    }
    expected_artifact_root = f"{modal_config['output_mount']}/outputs/runs/modal/sft"
    comparisons = {
        "schema_version_is_one": type(plan.get("schema_version")) is int
        and plan.get("schema_version") == 1,
        "inspection_only_is_true": plan.get("inspection_only") is True,
        "runtime_image_matches_recipe": runtime.get("image") == expected_image,
        "dependency_pins_match_recipe": runtime.get("pip_packages") == expected_pips,
        "runtime_gpu_matches_stage_s": runtime.get("gpu") == modal_config["gpu"],
        "runtime_timeout_matches_stage_s": runtime.get("timeout_hours")
        == modal_config["timeout_hours"],
        "config_sha256_matches_package": config_input.get("sha256") == config_sha256,
        "dataset_sha256_matches_package": dataset_input.get("sha256") == dataset_sha256,
        "config_volume_path_matches_package": config_input.get("volume_path")
        == expected_config_volume_path,
        "dataset_volume_path_matches_package": dataset_input.get("volume_path")
        == expected_dataset_volume_path,
        "config_mount_matches_package": config_input.get("mounted_path") == expected_config_path,
        "dataset_mount_matches_package": dataset_input.get("mounted_path") == expected_dataset_path,
        "source_repo_url_matches_tuner": source.get("repo_url") == expected_repo_url,
        "source_branch_matches_tuner": source.get("branch") == expected_branch,
        "tuner_commit_matches_package": source.get("commit") == expected_commit,
        "input_volume_matches_stage_s": inputs.get("volume_name")
        == modal_config["input_volume"],
        "input_mount_matches_stage_s": inputs.get("mount_path") == modal_config["input_mount"],
        "artifact_backend_is_modal_volume": artifacts.get("backend") == "modal_volume",
        "output_volume_matches_stage_s": artifacts.get("volume_name")
        == modal_config["output_volume"],
        "output_mount_matches_stage_s": artifacts.get("mount_path")
        == modal_config["output_mount"],
        "artifact_root_matches_stage_s": artifacts.get("canonical_root")
        == expected_artifact_root,
        "hub_publication_disabled": artifacts.get("publish_final_model") is False,
        "launch_environment_matches_expected": dict(environment) == expected_environment,
        "direct_detached_launch_argv_matches_expected": launch_argv == expected_argv,
        "verification_contract_matches_expected": dict(verification)
        == expected_verification,
    }
    failed = sorted(name for name, passed in comparisons.items() if not passed)
    if failed:
        raise PreflightError("Modal inspected plan contract mismatch: " + ", ".join(failed))

    contract = {
        "schema_version": plan.get("schema_version"),
        "inspection_only": plan.get("inspection_only"),
        "source": dict(source),
        "runtime": dict(runtime),
        "inputs": {
            "volume_name": inputs.get("volume_name"),
            "mount_path": inputs.get("mount_path"),
            "config": {
                key: config_input.get(key)
                for key in ("volume_path", "mounted_path", "sha256", "bytes")
            },
            "dataset": {
                key: dataset_input.get(key)
                for key in ("volume_path", "mounted_path", "sha256", "bytes")
            },
        },
        "artifacts": dict(artifacts),
        "launch": {
            "environment": launch.get("environment"),
            "argv": launch.get("argv"),
            "verification": launch.get("verification"),
        },
        "comparisons": comparisons,
    }
    contract["sha256"] = hashlib.sha256(canonical_json(contract).encode("utf-8")).hexdigest()
    return contract


def render_full_trainer_config(
    context: Mapping[str, Any], run_id: str
) -> tuple[dict[str, Any], Path]:
    """Render the full Stage-S direct SFT config without launch or merge retention."""
    direct, tuner_config_path = render_smoke_trainer_config(context, run_id)
    recipe_training = context["recipe"]["training"]
    direct["model"]["tokenizer"]["verify_merged_model_roundtrip"] = False
    direct["training"].pop("max_steps", None)
    direct["training"]["num_train_epochs"] = recipe_training["num_epochs"]
    direct["dataset"]["local_file"] = str(MODAL_INPUT_ROOT / run_id / FULL_DATASET_FILE)
    return direct, tuner_config_path


def _authorization_token(run_id: str, spec_sha256: str) -> str:
    return f"AUTHORIZE_FULL_STAGE_S:{run_id}:{spec_sha256}"


def _canonical_spec_sha256(spec: Mapping[str, Any]) -> str:
    live = dict(spec)
    live.pop("sha256", None)
    return hashlib.sha256(canonical_json(live).encode("utf-8")).hexdigest()


def stage_full(context: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    """Build a hash-bound full Modal package and resolved spec; launch nothing."""
    if not FULL_RUN_ID_PATTERN.fullmatch(run_id):
        raise PreflightError("full run_id must match stage-s-full-<unique-id>")
    tuner = context["tuner"]
    destination = tuner["staging_root"] / run_id
    if destination.exists():
        raise PreflightError(f"staging destination already exists: {destination}")
    train = context["dataset"]["splits"]["train"]
    trainer_config, tuner_config_path = render_full_trainer_config(context, run_id)
    tuner["staging_root"].mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=tuner["staging_root"]))
    try:
        dataset_path = temporary / FULL_DATASET_FILE
        shutil.copyfile(train["path"], dataset_path)
        if sha256_file(dataset_path) != train["sha256"]:
            raise PreflightError("full Stage-S train bytes changed during staging")
        config_path = temporary / FULL_CONFIG_FILE
        with config_path.open("w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(trainer_config, handle, sort_keys=False)
        config_sha = sha256_file(config_path)
        dataset_sha = sha256_file(dataset_path)
        plan = inspect_modal_plan(context, run_id, config_path, dataset_path)
        contract = validate_modal_plan_contract(
            context,
            run_id,
            plan,
            config_sha,
            dataset_sha,
            config_filename=FULL_CONFIG_FILE,
            dataset_filename=FULL_DATASET_FILE,
        )
        upload_commands = [
            [
                "modal", "volume", "put", "-f", context["config"]["modal"]["input_volume"],
                FULL_CONFIG_FILE, f"/{run_id}/{FULL_CONFIG_FILE}",
            ],
            [
                "modal", "volume", "put", "-f", context["config"]["modal"]["input_volume"],
                FULL_DATASET_FILE, f"/{run_id}/{FULL_DATASET_FILE}",
            ],
        ]
        launch_spec = {
            "schema_version": 1,
            "experiment": context["config"]["experiment"],
            "run_id": run_id,
            "mode": "full_stage_s_modal",
            "launch_authorized_by_instrument": False,
            "input_namespace": f"/{run_id}/",
            "staged_splits": ["train"],
            "heldout_staged": False,
            "source_checkout": {
                "strategy": "fresh_ephemeral_clone_then_exact_commit_checkout",
                "repo_url": contract["source"]["repo_url"],
                "branch": contract["source"]["branch"],
                "commit": contract["source"]["commit"],
            },
            "runtime": contract["runtime"],
            "upload_commands": upload_commands,
            "launch_environment": contract["launch"]["environment"],
            "launch_argv": contract["launch"]["argv"],
            "verification": contract["launch"]["verification"],
            "artifact_namespace": contract["artifacts"]["canonical_root"],
            "checkpoint_policy": {
                "save_steps": trainer_config["training"]["save_steps"],
                "save_total_limit": trainer_config["training"]["save_total_limit"],
                "backend": "modal_volume",
            },
            "canonical_output": {
                "artifact": "adapter_plus_tokenizer",
                "retain_merged_model": False,
            },
            "input_sha256": {FULL_CONFIG_FILE: config_sha, FULL_DATASET_FILE: dataset_sha},
            "modal_plan_contract_sha256": contract["sha256"],
        }
        spec_sha = _canonical_spec_sha256(launch_spec)
        launch_spec["sha256"] = spec_sha
        token = _authorization_token(run_id, spec_sha)
        manifest = {
            "schema_version": 1,
            "experiment": context["config"]["experiment"],
            "run_id": run_id,
            "mode": "full_stage_s_modal_resolved_spec",
            "launch_authorized": False,
            "private": True,
            "heldout_staged": False,
            "tuner_commit": tuner["commit"],
            "tuner_direct_sft_config_sha256": sha256_file(tuner_config_path),
            "stage_s_config_sha256": sha256_file(context["config_path"]),
            "stage_sft_recipe_sha256": sha256_file(context["recipe_template_path"]),
            "launch_spec": launch_spec,
            "authorization": {
                "requires_explicit_user_authorization_flag": True,
                "token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
                "token_format": "AUTHORIZE_FULL_STAGE_S:<run-id>:<launch-spec-sha256>",
            },
        }
        manifest_path = temporary / "full_stage_s_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "schema_version": 1,
        "staged": True,
        "mode": "full_stage_s_modal_resolved_spec",
        "launch_authorized": False,
        "run_id": run_id,
        "relative_directory": str(context["staged_relative"]),
        "manifest_sha256": sha256_file(destination / "full_stage_s_manifest.json"),
        "launch_spec_sha256": spec_sha,
        "authorization_token_format": manifest["authorization"]["token_format"],
    }


def launch_full(
    context: Mapping[str, Any],
    run_id: str,
    *,
    explicit_user_authorization: bool,
    authorization_token: str,
) -> dict[str, Any]:
    """Upload and submit an existing full package only after two invocation gates."""
    package = context["tuner"]["staging_root"] / run_id
    manifest_path = package / "full_stage_s_manifest.json"
    if not manifest_path.is_file():
        raise PreflightError("stage-full must create the resolved package before launch-full")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not explicit_user_authorization:
        raise PreflightError("launch-full requires --explicit-user-authorization")
    spec = _require_mapping(manifest.get("launch_spec"), "full launch spec")
    live_spec_sha = _canonical_spec_sha256(spec)
    stored_spec_sha = spec.get("sha256")
    if not isinstance(stored_spec_sha, str) or not hmac.compare_digest(
        live_spec_sha, stored_spec_sha
    ):
        raise PreflightError("launch-full canonical live spec hash differs from stored sha256")
    expected_token = _authorization_token(run_id, live_spec_sha)
    if not hmac.compare_digest(authorization_token, expected_token):
        raise PreflightError("launch-full authorization token is not bound to the live spec")
    token_sha = hashlib.sha256(authorization_token.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(token_sha, manifest["authorization"]["token_sha256"]):
        raise PreflightError("launch-full authorization token does not match the resolved spec")
    for filename, expected in spec["input_sha256"].items():
        if sha256_file(package / filename) != expected:
            raise PreflightError(f"full package input drifted: {filename}")
    for command in spec["upload_commands"]:
        command = list(command)
        command[5] = str(package / command[5])
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            raise PreflightError("Modal input upload failed")
    environment = {**os.environ, **{str(k): str(v) for k, v in spec["launch_environment"].items()}}
    result = subprocess.run(spec["launch_argv"], check=False, capture_output=True, text=True, env=environment)
    if result.returncode != 0 or not result.stdout.strip():
        raise PreflightError("detached Modal submission failed or returned no submission id")
    return {
        "schema_version": 1,
        "submitted": True,
        "run_id": run_id,
        "launch_spec_sha256": spec["sha256"],
        "submission_output": result.stdout.strip(),
        "verification_commands": spec["verification"]["commands"],
    }


def _qualification_authorization_token(run_id: str, spec_sha256: str) -> str:
    return f"AUTHORIZE_STAGE_S_QUALIFICATION:{run_id}:{spec_sha256}"


def _git_text(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise PreflightError(f"git {' '.join(args)} failed for experiment source")
    return result.stdout.strip()


def _verify_pushed_experiment_source(
    experiment_root: Path, repo_url: str, branch: str, commit: str, paths: list[Path]
) -> dict[str, str]:
    experiment_root = experiment_root.resolve()
    if not COMMIT_PATTERN.fullmatch(commit):
        raise PreflightError("qualification experiment commit must be an exact lowercase SHA")
    if Path(_git_text(experiment_root, "rev-parse", "--show-toplevel")).resolve() != experiment_root:
        raise PreflightError("qualification experiment worktree must be a repository root")
    origin = _git_text(experiment_root, "remote", "get-url", "origin")
    if origin.removesuffix(".git") != repo_url.removesuffix(".git"):
        raise PreflightError("qualification experiment origin differs from governed source")
    remote_ref = f"refs/remotes/origin/{branch}"
    remote_commit = _git_text(experiment_root, "rev-parse", remote_ref).lower()
    ancestor = subprocess.run(
        ["git", "-C", str(experiment_root), "merge-base", "--is-ancestor", commit, remote_ref],
        check=False,
    )
    if ancestor.returncode != 0 or remote_commit != commit:
        raise PreflightError("qualification experiment commit is not the exact pushed branch tip")
    hashes: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(experiment_root).as_posix()
        except ValueError as exc:
            raise PreflightError("qualification source file escapes experiment worktree") from exc
        blob = subprocess.run(
            ["git", "-C", str(experiment_root), "show", f"{commit}:{relative}"],
            check=False,
            capture_output=True,
        )
        if blob.returncode != 0 or blob.stdout != resolved.read_bytes():
            raise PreflightError(f"working qualification source differs from pushed commit: {relative}")
        hashes[relative] = hashlib.sha256(blob.stdout).hexdigest()
    return hashes


def _training_done_identity_from_resolved_manifest(
    context: Mapping[str, Any], training_run_id: str
) -> tuple[dict[str, Any], Path, str]:
    manifest_path = (
        context["tuner"]["staging_root"] / training_run_id / "full_stage_s_manifest.json"
    )
    if not manifest_path.is_file():
        raise PreflightError(
            "stage-qualification requires the resolved full-training manifest for its run id"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    spec = _require_mapping(manifest.get("launch_spec"), "resolved full-training launch spec")
    if manifest.get("run_id") != training_run_id or spec.get("run_id") != training_run_id:
        raise PreflightError("resolved full-training manifest run identity mismatch")
    if manifest.get("tuner_commit") != context["tuner"]["commit"]:
        raise PreflightError("resolved full-training manifest tuner commit mismatch")
    if _canonical_spec_sha256(spec) != spec.get("sha256"):
        raise PreflightError("resolved full-training manifest live spec hash mismatch")
    inputs = _require_mapping(spec.get("input_sha256"), "full-training input hashes")
    for filename in (FULL_CONFIG_FILE, FULL_DATASET_FILE):
        path = manifest_path.parent / filename
        if not path.is_file() or sha256_file(path) != inputs.get(filename):
            raise PreflightError(f"resolved full-training package input drifted: {filename}")
    runtime = _require_mapping(spec.get("runtime"), "full-training runtime")
    source = _require_mapping(spec.get("source_checkout"), "full-training source")
    modal_config = context["config"]["modal"]
    expected_identity = {
        "run": {"id": training_run_id, "stable": True},
        "source": {"branch": source["branch"], "commit": source["commit"]},
        "inputs": {
            "config": {
                "mounted_path": str(MODAL_INPUT_ROOT / training_run_id / FULL_CONFIG_FILE),
                "sha256": inputs[FULL_CONFIG_FILE],
            },
            "dataset": {
                "mounted_path": str(MODAL_INPUT_ROOT / training_run_id / FULL_DATASET_FILE),
                "sha256": inputs[FULL_DATASET_FILE],
            },
            "verified": True,
            "volume_name": modal_config["input_volume"],
            "mount_path": modal_config["input_mount"],
        },
        "runtime": {
            "image": runtime["image"],
            "pip_packages": list(runtime["pip_packages"]),
            "gpu": runtime["gpu"],
            "timeout_seconds": int(float(runtime["timeout_hours"]) * 3600),
        },
        "artifacts": {
            "volume_name": modal_config["output_volume"],
            "mount_path": modal_config["output_mount"],
        },
        "cache": {
            "volume_name": modal_config["cache_volume"],
            "mount_path": "/cache/huggingface",
        },
        "publish_final_model": False,
    }
    return expected_identity, manifest_path, sha256_file(manifest_path)


def stage_qualification(
    context: Mapping[str, Any],
    qualification_run_id: str,
    training_run_id: str,
    experiment_root: Path,
    experiment_commit: str,
) -> dict[str, Any]:
    """Resolve a dev-only Modal qualification package; upload and launch nothing."""
    if not QUALIFICATION_RUN_ID_PATTERN.fullmatch(qualification_run_id):
        raise PreflightError("qualification run id must match stage-s-qual-<unique-id>")
    if not FULL_RUN_ID_PATTERN.fullmatch(training_run_id):
        raise PreflightError("training run id must match stage-s-full-<unique-id>")
    experiment_dir = context["config_path"].parent
    modal_config_path = experiment_dir / MODAL_QUALIFICATION_CONFIG_FILE
    qualification_config_path = experiment_dir / QUALIFICATION_CONFIG_FILE
    modal_module_path = experiment_dir / "modal_qualify_stage_s.py"
    for path in (modal_config_path, qualification_config_path, modal_module_path):
        if not path.is_file():
            raise PreflightError(f"qualification instrument file is missing: {path.name}")
    modal_config = _load_yaml(modal_config_path)
    if modal_config.get("schema_version") != 1 or modal_config.get("launch_authorized") is not False:
        raise PreflightError("Modal qualification config must remain schema 1 and no-launch")
    source = _require_mapping(modal_config.get("source"), "Modal qualification source")
    tuner_config = _require_mapping(modal_config.get("tuner"), "Modal qualification tuner")
    if tuner_config.get("commit") != context["tuner"]["commit"]:
        raise PreflightError("Modal qualification tuner commit differs from Stage-S pin")
    training_identity, training_manifest_path, training_manifest_sha = (
        _training_done_identity_from_resolved_manifest(context, training_run_id)
    )
    source_hashes = _verify_pushed_experiment_source(
        experiment_root,
        str(source["repo_url"]),
        str(source["branch"]),
        experiment_commit,
        [modal_config_path, qualification_config_path, modal_module_path],
    )
    destination = context["tuner"]["staging_root"] / qualification_run_id
    if destination.exists():
        raise PreflightError(f"qualification staging destination already exists: {destination}")
    dev = context["dataset"]["splits"]["dev"]
    context["tuner"]["staging_root"].mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{qualification_run_id}.", dir=context["tuner"]["staging_root"])
    )
    try:
        staged_config = temporary / QUALIFICATION_CONFIG_FILE
        staged_modal_config = temporary / MODAL_QUALIFICATION_CONFIG_FILE
        staged_dev = temporary / QUALIFICATION_DEV_FILE
        shutil.copyfile(qualification_config_path, staged_config)
        shutil.copyfile(modal_config_path, staged_modal_config)
        shutil.copyfile(dev["path"], staged_dev)
        if sha256_file(staged_dev) != dev["sha256"]:
            raise PreflightError("qualification dev bytes changed during staging")
        input_hashes = {
            staged_config.name: sha256_file(staged_config),
            staged_modal_config.name: sha256_file(staged_modal_config),
            staged_dev.name: sha256_file(staged_dev),
        }
        training_artifact_root = (
            f"/vol/artifacts/outputs/runs/modal/sft/"
            f"{training_run_id}-{context['tuner']['commit'][:8]}"
        )
        remote_module = experiment_root / modal_module_path.relative_to(experiment_root)
        launch_argv = [
            "modal", "run", "--detach", f"{remote_module}::run_qualification",
            "--qualification-run-id", qualification_run_id,
            "--training-run-id", training_run_id,
            "--experiment-repo-url", str(source["repo_url"]),
            "--experiment-branch", str(source["branch"]),
            "--experiment-commit", experiment_commit,
            "--experiment-module-sha256", sha256_file(modal_module_path),
            "--modal-config-sha256", input_hashes[MODAL_QUALIFICATION_CONFIG_FILE],
            "--qualification-config-sha256", input_hashes[QUALIFICATION_CONFIG_FILE],
            "--dev-sha256", input_hashes[QUALIFICATION_DEV_FILE],
            "--tuner-repo-url", str(tuner_config["repo_url"]),
            "--tuner-branch", str(tuner_config["branch"]),
            "--tuner-commit", str(tuner_config["commit"]),
            "--training-done-identity-json", canonical_json(training_identity),
        ]
        upload_commands = [
            ["modal", "volume", "put", "-f", modal_config["volumes"]["input"]["name"],
             name, f"/{qualification_run_id}/{name}"]
            for name in (QUALIFICATION_CONFIG_FILE, MODAL_QUALIFICATION_CONFIG_FILE, QUALIFICATION_DEV_FILE)
        ]
        launch_spec = {
            "schema_version": 1,
            "experiment": context["config"]["experiment"],
            "mode": "stage_s_dev_modal_qualification",
            "qualification_run_id": qualification_run_id,
            "training_run_id": training_run_id,
            "training_artifact_root": training_artifact_root,
            "training_done_marker": f"{training_artifact_root}/DONE",
            "training_lineage": f"{training_artifact_root}/final_model/special_tokens_lineage.json",
            "training_resolved_manifest": {
                "path": str(training_manifest_path),
                "sha256": training_manifest_sha,
                "launch_spec_sha256": json.loads(
                    training_manifest_path.read_text(encoding="utf-8")
                )["launch_spec"]["sha256"],
            },
            "expected_training_done_identity": training_identity,
            "output_volume_name": modal_config["volumes"]["output"]["name"],
            "staged_splits": ["dev"],
            "heldout_staged": False,
            "train_staged": False,
            "source": {"repo_url": source["repo_url"], "branch": source["branch"], "commit": experiment_commit},
            "source_file_sha256": source_hashes,
            "local_modal_module": {
                "path": str(modal_module_path.resolve()),
                "sha256": sha256_file(modal_module_path),
            },
            "tuner": {"repo_url": tuner_config["repo_url"], "branch": tuner_config["branch"], "commit": tuner_config["commit"]},
            "runtime": modal_config["runtime"],
            "input_sha256": input_hashes,
            "upload_commands": upload_commands,
            "launch_argv": launch_argv,
            "verification_commands": [
                ["modal", "app", "list", "--json"],
                ["modal", "app", "logs", "<app-id>"],
                ["modal", "volume", "get", modal_config["volumes"]["output"]["name"],
                 f"/outputs/runs/modal/qualification/{qualification_run_id}-{experiment_commit[:8]}/DONE", "<local-DONE>"],
            ],
        }
        spec_sha = _canonical_spec_sha256(launch_spec)
        launch_spec["sha256"] = spec_sha
        token = _qualification_authorization_token(qualification_run_id, spec_sha)
        manifest = {
            "schema_version": 1,
            "launch_authorized": False,
            "private": True,
            "launch_spec": launch_spec,
            "authorization": {
                "requires_explicit_user_authorization_flag": True,
                "token_sha256": hashlib.sha256(token.encode("utf-8")).hexdigest(),
                "token_format": "AUTHORIZE_STAGE_S_QUALIFICATION:<run-id>:<launch-spec-sha256>",
            },
        }
        (temporary / QUALIFICATION_MANIFEST_FILE).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {
        "schema_version": 1,
        "staged": True,
        "launch_authorized": False,
        "run_id": qualification_run_id,
        "relative_directory": str(context["tuner"]["staging_relative"] / qualification_run_id),
        "manifest_sha256": sha256_file(destination / QUALIFICATION_MANIFEST_FILE),
        "launch_spec_sha256": spec_sha,
        "authorization_token_format": manifest["authorization"]["token_format"],
    }


def _verify_remote_training_ready(spec: Mapping[str, Any], package: Path) -> None:
    inspection = package / ".training-readiness"
    if inspection.exists():
        shutil.rmtree(inspection)
    inspection.mkdir()
    output_volume_name = str(spec["output_volume_name"])
    targets = ((spec["training_done_marker"], inspection / "DONE"), (spec["training_lineage"], inspection / "special_tokens_lineage.json"))
    try:
        for remote, local in targets:
            result = subprocess.run(
                ["modal", "volume", "get", output_volume_name, remote.removeprefix("/vol/artifacts"), str(local)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0 or not local.is_file():
                raise PreflightError("qualification launch requires training DONE and lineage on the output Volume")
        done = json.loads((inspection / "DONE").read_text(encoding="utf-8"))
        if (
            done.get("status") != "completed"
            or done.get("identity") != spec["expected_training_done_identity"]
        ):
            raise PreflightError("training DONE marker exact identity does not match qualification spec")
        lineage = json.loads((inspection / "special_tokens_lineage.json").read_text(encoding="utf-8"))
        if not isinstance(lineage.get("configured_tokens"), list):
            raise PreflightError("training special-token lineage is malformed")
    finally:
        shutil.rmtree(inspection, ignore_errors=True)


def launch_qualification(
    context: Mapping[str, Any],
    run_id: str,
    *,
    explicit_user_authorization: bool,
    authorization_token: str,
) -> dict[str, Any]:
    package = context["tuner"]["staging_root"] / run_id
    manifest_path = package / QUALIFICATION_MANIFEST_FILE
    if not manifest_path.is_file():
        raise PreflightError("stage-qualification must create the package first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not explicit_user_authorization:
        raise PreflightError("launch-qualification requires --explicit-user-authorization")
    spec = _require_mapping(manifest.get("launch_spec"), "qualification launch spec")
    live_sha = _canonical_spec_sha256(spec)
    if not hmac.compare_digest(live_sha, str(spec.get("sha256", ""))):
        raise PreflightError("qualification canonical live spec hash differs from stored sha256")
    expected_token = _qualification_authorization_token(run_id, live_sha)
    if not hmac.compare_digest(authorization_token, expected_token):
        raise PreflightError("qualification authorization token is not bound to the live spec")
    if not hmac.compare_digest(
        hashlib.sha256(authorization_token.encode("utf-8")).hexdigest(),
        manifest["authorization"]["token_sha256"],
    ):
        raise PreflightError("qualification authorization token hash mismatch")
    module_record = _require_mapping(spec.get("local_modal_module"), "local Modal module")
    module_path = Path(str(module_record.get("path", "")))
    if not module_path.is_file() or sha256_file(module_path) != module_record.get("sha256"):
        raise PreflightError("local Modal qualification module changed after staging")
    training_manifest = _require_mapping(
        spec.get("training_resolved_manifest"), "training resolved manifest"
    )
    training_manifest_path = Path(str(training_manifest.get("path", "")))
    if (
        not training_manifest_path.is_file()
        or sha256_file(training_manifest_path) != training_manifest.get("sha256")
    ):
        raise PreflightError("resolved full-training manifest changed after qualification staging")
    experiment_root = context["config_path"].parent.parents[1]
    source = spec["source"]
    source_paths = [experiment_root / relative for relative in spec["source_file_sha256"]]
    launch_source_hashes = _verify_pushed_experiment_source(
        experiment_root,
        str(source["repo_url"]),
        str(source["branch"]),
        str(source["commit"]),
        source_paths,
    )
    if launch_source_hashes != spec["source_file_sha256"]:
        raise PreflightError("qualification pushed source hashes changed after staging")
    for filename, expected in spec["input_sha256"].items():
        if sha256_file(package / filename) != expected:
            raise PreflightError(f"qualification package input drifted: {filename}")
    _verify_remote_training_ready(spec, package)
    for command in spec["upload_commands"]:
        live = list(command)
        live[5] = str(package / live[5])
        if subprocess.run(live, check=False).returncode != 0:
            raise PreflightError("Modal qualification input upload failed")
    result = subprocess.run(spec["launch_argv"], check=False, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise PreflightError("detached Modal qualification submission failed")
    return {
        "schema_version": 1,
        "submitted": True,
        "run_id": run_id,
        "launch_spec_sha256": live_sha,
        "submission_output": result.stdout.strip(),
        "verification_commands": spec["verification_commands"],
    }


def stage_smoke(
    context: Mapping[str, Any],
    run_id: str,
    *,
    rows_per_mode: int = 2,
    inspected_plan: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a private Modal input package without uploading or launching it."""
    tuner = context["tuner"]
    staging_root: Path = tuner["staging_root"]
    destination = staging_root / run_id
    if destination.exists():
        raise PreflightError(f"staging destination already exists: {destination}")

    configured_tokens = list(context["config"]["model"]["tokenizer"]["additional_special_tokens"])
    train = context["dataset"]["splits"]["train"]
    mode_counts = context["dataset"].get("mode_counts")
    if not isinstance(mode_counts, dict) or not mode_counts:
        raise PreflightError("aggregate manifest must declare non-empty mode_counts for smoke staging")
    if any(not isinstance(mode, str) or not mode for mode in mode_counts):
        raise PreflightError("aggregate manifest mode_counts keys must be non-empty strings")
    selected_rows, token_by_mode, selected_manifest = select_smoke_rows(
        train["path"],
        train["sha256"],
        configured_tokens,
        rows_per_mode,
        expected_modes=sorted(mode_counts),
    )
    trainer_config, tuner_config_path = render_smoke_trainer_config(context, run_id)

    staging_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{run_id}.", dir=staging_root))
    try:
        dataset_path = temporary / SMOKE_DATASET_FILE
        with dataset_path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in selected_rows:
                handle.write(canonical_json(row) + "\n")

        config_path = temporary / SMOKE_CONFIG_FILE
        with config_path.open("w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(trainer_config, handle, sort_keys=False)

        files = {
            dataset_path.name: sha256_file(dataset_path),
            config_path.name: sha256_file(config_path),
        }
        plan = dict(inspected_plan) if inspected_plan is not None else inspect_modal_plan(
            context, run_id, config_path, dataset_path
        )
        inspected_contract = validate_modal_plan_contract(
            context,
            run_id,
            plan,
            files[SMOKE_CONFIG_FILE],
            files[SMOKE_DATASET_FILE],
        )
        recipe_path = context["recipe_template_path"]
        manifest = {
            "schema_version": 1,
            "experiment": context["config"]["experiment"],
            "run_id": run_id,
            "mode": "modal_pre_sign_smoke_input",
            "launch_authorized": False,
            "private": True,
            "commit_allowed": False,
            "tuner_commit": tuner["commit"],
            "tuner_direct_sft_config_sha256": sha256_file(tuner_config_path),
            "stage_s_config_sha256": sha256_file(context["config_path"]),
            "stage_sft_recipe": {
                "file": recipe_path.name,
                "sha256": sha256_file(recipe_path),
                "immutable_runtime_image": context["recipe"]["job"]["image"],
                "exact_dependency_pins": list(context["recipe"]["setup"]["pip"]),
                "model": {
                    "load_in_4bit": context["recipe"]["model"]["load_in_4bit"],
                    "dtype": context["recipe"]["model"]["dtype"],
                },
            },
            "modal_inspected_plan_contract": inspected_contract,
            "source_train": {
                "sha256": train["sha256"],
                "rows": train["rows"],
            },
            "selection": {
                "rows_per_mode": rows_per_mode,
                "mode_count": len(token_by_mode),
                "row_count": len(selected_rows),
                "token_by_mode": token_by_mode,
                "selected_rows_in_file_order": selected_manifest,
            },
            "runtime": {
                "input_mount": str(MODAL_INPUT_ROOT),
                "output_root": str(MODAL_OUTPUT_ROOT),
                "trainer_entrypoint": "Trainers/sft/train_sft.py",
                "trainer_config": str(MODAL_INPUT_ROOT / run_id / SMOKE_CONFIG_FILE),
                "max_steps": SMOKE_MAX_STEPS,
                "wandb_enabled": False,
                "hub_publication_enabled": False,
                "forbidden_flags": ["--wandb", "--publish-final-model", "--publish-target-repo"],
            },
            "required_postconditions": [
                "configured_token_ids_stable_after_tokenizer_save_reload",
                "adapter_only_save_reload_matches_complete_adapter_state",
                "merge_save_reload_uses_pinned_base_revision",
                "adapter_artifact_contains_no_full_vocabulary_tensors",
            ],
            "files": files,
            "trainer_config_sha256": files[SMOKE_CONFIG_FILE],
        }
        manifest_path = temporary / "smoke_manifest.json"
        manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
        temporary.rename(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return {
        "schema_version": 1,
        "staged": True,
        "mode": "modal_pre_sign_smoke_input",
        "launch_authorized": False,
        "run_id": run_id,
        "relative_directory": str(context["staged_relative"]),
        "smoke_manifest_sha256": sha256_file(destination / "smoke_manifest.json"),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "preflight",
            "stage",
            "stage-smoke",
            "stage-full",
            "launch-full",
            "stage-qualification",
            "launch-qualification",
        ),
    )
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("stage_s.yaml"))
    parser.add_argument("--tuner-worktree", type=Path, required=True)
    parser.add_argument("--hf-cache-root", type=Path, default=None)
    parser.add_argument("--run-id", default="preflight")
    parser.add_argument("--smoke-rows-per-mode", type=int, default=2)
    parser.add_argument("--explicit-user-authorization", action="store_true")
    parser.add_argument("--authorization-token", default="")
    parser.add_argument("--training-run-id", default="")
    parser.add_argument("--experiment-worktree", type=Path)
    parser.add_argument("--experiment-commit", default="")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Return a blocker report with exit zero; never stage",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report, context = preflight(
            args.config,
            args.tuner_worktree,
            hf_cache_root=args.hf_cache_root,
            run_id=args.run_id,
        )
        if args.report or args.command == "preflight":
            print(canonical_json(report))
            return 0 if args.report or report["ready_to_stage"] else 2
        if report["blockers"]:
            print(canonical_json(report), file=sys.stderr)
            return 2
        if args.command == "stage-smoke":
            print(
                canonical_json(
                    stage_smoke(
                        context,
                        args.run_id,
                        rows_per_mode=args.smoke_rows_per_mode,
                    )
                )
            )
            return 0
        if args.command == "stage-full":
            print(canonical_json(stage_full(context, args.run_id)))
            return 0
        if args.command == "launch-full":
            print(
                canonical_json(
                    launch_full(
                        context,
                        args.run_id,
                        explicit_user_authorization=args.explicit_user_authorization,
                        authorization_token=args.authorization_token,
                    )
                )
            )
            return 0
        if args.command == "stage-qualification":
            if args.experiment_worktree is None:
                raise PreflightError("stage-qualification requires --experiment-worktree")
            print(
                canonical_json(
                    stage_qualification(
                        context,
                        args.run_id,
                        args.training_run_id,
                        args.experiment_worktree,
                        args.experiment_commit,
                    )
                )
            )
            return 0
        if args.command == "launch-qualification":
            print(
                canonical_json(
                    launch_qualification(
                        context,
                        args.run_id,
                        explicit_user_authorization=args.explicit_user_authorization,
                        authorization_token=args.authorization_token,
                    )
                )
            )
            return 0
        print(canonical_json(stage(context, args.run_id)))
        return 0
    except (PreflightError, OSError, yaml.YAMLError) as exc:
        print(f"stage-s preflight failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
