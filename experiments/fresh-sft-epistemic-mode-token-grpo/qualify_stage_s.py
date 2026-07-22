#!/usr/bin/env python3
"""Prepare, generate, resume, and adjudicate the Stage-S dev qualification.

Model execution crosses only the pinned Synaptic-Tuner public ``batch-generate``
CLI. This module owns experiment-specific prompt construction and scoring; it
never imports tuner internals and never opens the sealed held-out row file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

COMPLETIONS_FILE = "completions.jsonl"
CHECKPOINT_FILE = "checkpoint.json"
MODE_NAMES = ("ANSWER", "QUALIFY", "ABSTAIN")


class QualificationError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return "".join(canonical_json(dict(row)) + "\n" for row in rows).encode("utf-8")


def hash_artifact_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise QualificationError(f"Stage-S artifact tree is missing: {root}")
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise QualificationError(f"Stage-S artifact tree contains a symlink: {path}")
        if path.is_file():
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    if not entries:
        raise QualificationError("Stage-S artifact tree contains no files")
    return {
        "root": str(root),
        "files": entries,
        "sha256": sha256_bytes(canonical_json(entries).encode("utf-8")),
    }


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )


def verify_tuner(config: Mapping[str, Any], tuner_root: Path) -> str:
    tuner_root = tuner_root.resolve()
    top = _git(tuner_root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != tuner_root:
        raise QualificationError("tuner worktree is not an exact repository root")
    head = _git(tuner_root, "rev-parse", "HEAD")
    actual = head.stdout.strip().lower() if head.returncode == 0 else ""
    expected = str(config["tuner"]["expected_commit"]).lower()
    if actual != expected:
        raise QualificationError(f"tuner commit mismatch: expected {expected}, got {actual}")
    status = _git(tuner_root, "status", "--porcelain", "--untracked-files=all")
    if status.returncode != 0:
        raise QualificationError("could not inspect tuner worktree status")
    if config["tuner"].get("require_clean_worktree") is not True:
        raise QualificationError("qualification requires tuner.require_clean_worktree=true")
    if status.stdout.strip():
        raise QualificationError("qualification requires an exactly clean pinned tuner worktree")
    if not (tuner_root / "tuner.py").is_file():
        raise QualificationError("tuner worktree lacks the public tuner.py entrypoint")
    return actual


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise QualificationError(f"expected YAML mapping: {path}")
    return value


def _resolve_within(root: Path, relative: str, label: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise QualificationError(f"{label} escapes its allowed root") from exc
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise QualificationError(f"invalid JSONL at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise QualificationError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(row)
    return rows


def _write_jsonl_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        for row in rows:
            handle.write(canonical_json(dict(row)) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(json.dumps(dict(value), indent=2, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def load_contract(config_path: Path) -> tuple[dict[str, Any], Path, Path]:
    config_path = config_path.resolve()
    experiment_dir = config_path.parent
    repo_root = experiment_dir.parents[1]
    config = _load_yaml(config_path)
    if config.get("schema_version") != 1:
        raise QualificationError("qualification schema_version must equal 1")
    if config.get("experiment") != experiment_dir.name:
        raise QualificationError("qualification experiment does not match directory")
    if "heldout" in str(config["dev"]["path"]).lower():
        raise QualificationError("qualification dev path must not reference heldout")
    forbidden = str(config["heldout"]["path_forbidden_in_runner"])
    if forbidden == str(config["dev"]["path"]):
        raise QualificationError("qualification dev path aliases the forbidden heldout path")
    if "remaining_pre_sign" in yaml.safe_dump(config):
        raise QualificationError("qualification config contains an unresolved pre-sign field")
    return config, experiment_dir, repo_root


def load_dev_rows(
    config: Mapping[str, Any], experiment_dir: Path, repo_root: Path
) -> list[dict[str, Any]]:
    dev_path = _resolve_within(experiment_dir, str(config["dev"]["path"]), "dev.path")
    forbidden = _resolve_within(
        experiment_dir, str(config["heldout"]["path_forbidden_in_runner"]), "heldout path"
    )
    if dev_path == forbidden:
        raise QualificationError("dev path resolves to the sealed heldout file")
    if not dev_path.is_file():
        raise QualificationError(f"dev file is missing: {dev_path}")
    actual_sha = sha256_file(dev_path)
    if actual_sha != config["dev"]["sha256"]:
        raise QualificationError("dev SHA-256 mismatch")
    rows = _read_jsonl(dev_path)
    if len(rows) != int(config["dev"]["rows"]):
        raise QualificationError("dev row count mismatch")
    counts = Counter(str(row.get("metadata", {}).get("mode_label")) for row in rows)
    expected = Counter({str(k): int(v) for k, v in config["dev"]["rows_by_mode"].items()})
    if counts != expected:
        raise QualificationError("dev mode-count mismatch")
    for row in rows:
        conversations = row.get("conversations")
        metadata = row.get("metadata")
        if not isinstance(conversations, list) or len(conversations) != 3:
            raise QualificationError("dev rows must have system, user, and target assistant turns")
        if [turn.get("role") for turn in conversations] != ["system", "user", "assistant"]:
            raise QualificationError("dev conversation role order is invalid")
        if not isinstance(metadata, dict) or metadata.get("split") != "dev":
            raise QualificationError("qualification received a non-dev row")
    return rows


def load_runtime_tokens(
    config: Mapping[str, Any], experiment_dir: Path, lineage_path: Path, tokenizer: Any
) -> tuple[list[str], dict[str, int], dict[str, Any]]:
    stage_config = _load_yaml(_resolve_within(experiment_dir, config["stage_s_config"], "stage_s"))
    configured = list(stage_config["model"]["tokenizer"]["additional_special_tokens"])
    if len(configured) != len(MODE_NAMES) or len(set(configured)) != len(configured):
        raise QualificationError("Stage-S configured token strings must be three unique values")
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    entries = lineage.get("configured_tokens")
    if not isinstance(entries, list):
        raise QualificationError("special-token lineage lacks configured_tokens")
    lineage_tokens = [entry.get("token") for entry in entries]
    if lineage_tokens != configured:
        raise QualificationError("runtime token strings/order differ from stage_s.yaml")
    ids = [entry.get("token_id") for entry in entries]
    if any(isinstance(value, bool) or not isinstance(value, int) for value in ids):
        raise QualificationError("runtime token IDs must be integers")
    if len(set(ids)) != len(ids):
        raise QualificationError("runtime token IDs are not unique")
    provenance = lineage.get("base_model_provenance")
    base = config["models"]["base"]
    if not isinstance(provenance, dict) or (
        provenance.get("requested_repo") != base["repo"]
        or provenance.get("requested_revision") != base["revision"]
        or provenance.get("resolved_commit") != str(base["revision"]).lower()
    ):
        raise QualificationError("adapter base-model lineage does not match qualification config")
    special_tokens = list(getattr(tokenizer, "all_special_tokens", ()))
    special_ids = list(getattr(tokenizer, "all_special_ids", ()))
    if not callable(getattr(tokenizer, "convert_tokens_to_ids", None)) or not callable(
        getattr(tokenizer, "encode", None)
    ):
        raise QualificationError("saved tokenizer lacks required special-token inspection APIs")
    for token, expected_id in zip(configured, ids, strict=True):
        actual_id = tokenizer.convert_tokens_to_ids(token)
        encoded = list(tokenizer.encode(token, add_special_tokens=False))
        if token not in special_tokens or expected_id not in special_ids:
            raise QualificationError(f"configured token is not registered special: {token!r}")
        if actual_id != expected_id or encoded != [expected_id]:
            raise QualificationError(
                f"saved tokenizer runtime ID/atomic encoding differs from lineage for {token!r}"
            )
    return configured, dict(zip(MODE_NAMES, ids)), lineage


def _row_id(row: Mapping[str, Any]) -> str:
    value = row["metadata"].get("row_key")
    if not isinstance(value, str) or not value:
        raise QualificationError("dev row lacks a stable row_key")
    return value


def prepare_run(
    config_path: Path,
    run_id: str,
    stage_s_model: Path,
    lineage_path: Path,
    *,
    tokenizer: Any | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    config, experiment_dir, repo_root = load_contract(config_path)
    rows = load_dev_rows(config, experiment_dir, repo_root)
    stage_s_model = stage_s_model.resolve()
    lineage_path = lineage_path.resolve()
    try:
        lineage_relative = lineage_path.relative_to(stage_s_model)
    except ValueError as exc:
        raise QualificationError("special-token lineage must be inside the Stage-S artifact tree") from exc
    if lineage_relative.as_posix() != "special_tokens_lineage.json":
        raise QualificationError("special-token lineage must be the canonical artifact-root file")
    if tokenizer is None:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(str(stage_s_model), local_files_only=True)
    tokens, token_ids, lineage = load_runtime_tokens(
        config, experiment_dir, lineage_path, tokenizer
    )
    artifact_tree = hash_artifact_tree(stage_s_model)
    output_root = _resolve_within(experiment_dir, str(config["output"]["root"]), "output.root")
    run_dir = output_root / run_id
    manifest_path = run_dir / config["output"]["run_manifest"]

    base_rows: list[dict[str, Any]] = []
    native_rows: list[dict[str, Any]] = []
    forced_rows: list[dict[str, Any]] = []
    for row in rows:
        messages = [dict(turn) for turn in row["conversations"][:2]]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=bool(config["generation"]["enable_thinking"]),
        )
        identifier = _row_id(row)
        base_rows.append({"id": identifier, "prompt": prompt})
        native_rows.append({"id": identifier, "prompt": prompt})
        for mode, token in zip(MODE_NAMES, tokens):
            forced_rows.append({"id": f"{identifier}::forced::{mode}", "prompt": prompt + token})

    prompt_records = (
        ("base_native", base_rows),
        ("stage_s_native", native_rows),
        ("stage_s_forced", forced_rows),
    )
    prompt_paths = {
        key: run_dir / config["output"]["prompt_files"][key] for key, _ in prompt_records
    }
    prompt_manifest = {
        key: {
            "file": prompt_paths[key].name,
            "sha256": sha256_bytes(_jsonl_bytes(records)),
            "rows": len(records),
        }
        for key, records in prompt_records
    }

    manifest = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "run_id": run_id,
        "status": "prepared_no_generation",
        "launch_authorized": False,
        "config_sha256": sha256_file(config_path),
        "dev_sha256": config["dev"]["sha256"],
        "dev_rows": len(rows),
        "heldout_rows_accessed": 0,
        "stage_s_model": str(stage_s_model),
        "stage_s_artifact_tree": artifact_tree,
        "special_token_lineage_path": str(lineage_path),
        "special_token_lineage_sha256": sha256_file(lineage_path),
        "configured_tokens": [
            {"name": mode, "token": token, "runtime_token_id": token_ids[mode]}
            for mode, token in zip(MODE_NAMES, tokens)
        ],
        "base_model_provenance": lineage["base_model_provenance"],
        "prompt_files": prompt_manifest,
        "expected_generation_invocations": {
            "base_native": {
                "model": str(config["models"]["base"]["repo"]),
                "revision": str(config["models"]["base"]["revision"]),
            },
            "stage_s_native": {"model": str(stage_s_model), "revision": None},
            "stage_s_forced": {"model": str(stage_s_model), "revision": None},
        },
    }
    invariant_keys = (
        "schema_version",
        "experiment",
        "run_id",
        "config_sha256",
        "dev_sha256",
        "dev_rows",
        "heldout_rows_accessed",
        "stage_s_model",
        "stage_s_artifact_tree",
        "special_token_lineage_path",
        "special_token_lineage_sha256",
        "configured_tokens",
        "base_model_provenance",
        "prompt_files",
        "expected_generation_invocations",
    )
    if resume:
        if not manifest_path.is_file():
            raise QualificationError("resume requires an existing run manifest")
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if any(previous.get(key) != manifest.get(key) for key in invariant_keys):
            raise QualificationError("resume manifest differs from prepared run")
        for key, details in previous["prompt_files"].items():
            path = run_dir / details["file"]
            if not path.is_file() or sha256_file(path) != details["sha256"]:
                raise QualificationError(f"resume prompt file drifted: {key}")
            if len(_read_jsonl(path)) != details["rows"]:
                raise QualificationError(f"resume prompt row count drifted: {key}")
        return previous
    if run_dir.exists():
        raise QualificationError(f"qualification run already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    for key, records in prompt_records:
        _write_jsonl_atomic(prompt_paths[key], records)
        if sha256_file(prompt_paths[key]) != prompt_manifest[key]["sha256"]:
            raise QualificationError(f"prompt write hash mismatch: {key}")
    _write_json_atomic(manifest_path, manifest)
    return manifest


def _generation_command(
    tuner_root: Path,
    prompts: Path,
    out_dir: Path,
    model: str,
    config: Mapping[str, Any],
    *,
    revision: str | None,
    resume: bool,
) -> list[str]:
    generation = config["generation"]
    command = [
        sys.executable,
        str(tuner_root / "tuner.py"),
        str(generation["public_tuner_verb"]),
        "--prompts",
        str(prompts),
        "--model",
        model,
        "--out-dir",
        str(out_dir),
        "--engine",
        str(generation["engine"]),
        "--batch-size",
        str(generation["batch_size"]),
        "--max-new-tokens",
        str(generation["max_new_tokens"]),
        "--min-new-tokens",
        str(generation["min_new_tokens"]),
        "--seed",
        str(generation["seed"]),
    ]
    if revision:
        command.extend(["--model-revision", revision])
    if resume:
        command.append("--resume")
    return command


def _verify_prompt_files(run_dir: Path, manifest: Mapping[str, Any]) -> None:
    for key, details in manifest["prompt_files"].items():
        path = run_dir / details["file"]
        if not path.is_file() or sha256_file(path) != details["sha256"]:
            raise QualificationError(f"prompt hash mismatch before generation/scoring: {key}")
        if len(_read_jsonl(path)) != int(details["rows"]):
            raise QualificationError(f"prompt row-count mismatch: {key}")


def _verify_completed_generation(
    run_dir: Path, key: str, details: Mapping[str, Any], expected_rows: int
) -> Path:
    if details.get("status") != "complete":
        raise QualificationError(f"generation job is not complete: {key}")
    path = run_dir / str(details.get("file", ""))
    if not path.is_file() or sha256_file(path) != details.get("sha256"):
        raise QualificationError(f"generation output hash mismatch: {key}")
    rows = _read_jsonl(path)
    if len(rows) != expected_rows or details.get("rows") != expected_rows:
        raise QualificationError(f"generation output row-count mismatch: {key}")
    checkpoint = path.parent / CHECKPOINT_FILE
    if not checkpoint.is_file():
        raise QualificationError(f"generation checkpoint is missing: {key}")
    checkpoint_value = json.loads(checkpoint.read_text(encoding="utf-8"))
    ids = [str(row.get("id")) for row in rows]
    if (
        checkpoint_value.get("count") != expected_rows
        or set(map(str, checkpoint_value.get("done_ids", []))) != set(ids)
    ):
        raise QualificationError(f"generation checkpoint is incomplete/inconsistent: {key}")
    if details.get("checkpoint_sha256") != sha256_file(checkpoint):
        raise QualificationError(f"generation checkpoint hash mismatch: {key}")
    return path


def generate(
    config_path: Path,
    run_id: str,
    stage_s_model: Path,
    tuner_root: Path,
    *,
    resume: bool,
) -> dict[str, Any]:
    config, experiment_dir, _ = load_contract(config_path)
    run_dir = _resolve_within(experiment_dir, str(config["output"]["root"]), "output.root") / run_id
    manifest_path = run_dir / config["output"]["run_manifest"]
    if not manifest_path.is_file():
        raise QualificationError("prepare must complete before generation")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("config_sha256") != sha256_file(config_path):
        raise QualificationError("qualification config changed after prepare")
    tuner_commit = verify_tuner(config, tuner_root)
    if str(stage_s_model.resolve()) != manifest.get("stage_s_model"):
        raise QualificationError("generation Stage-S model path differs from prepared manifest")
    if hash_artifact_tree(stage_s_model) != manifest.get("stage_s_artifact_tree"):
        raise QualificationError("Stage-S artifact tree changed after prepare")
    _verify_prompt_files(run_dir, manifest)
    jobs = (
        (
            "base_native",
            str(config["models"]["base"]["repo"]),
            str(config["models"]["base"]["revision"]),
        ),
        ("stage_s_native", str(stage_s_model.resolve()), None),
        ("stage_s_forced", str(stage_s_model.resolve()), None),
    )
    expected_invocations = manifest.get("expected_generation_invocations", {})
    completed: dict[str, Any] = dict(manifest.get("generation_outputs", {}))
    manifest["status"] = "generation_in_progress"
    manifest["tuner_commit"] = tuner_commit
    _write_json_atomic(manifest_path, manifest)
    for key, model, revision in jobs:
        invocation = {"model": model, "revision": revision}
        if invocation != expected_invocations.get(key):
            raise QualificationError(f"generation invocation differs from prepared manifest: {key}")
        prompt_details = manifest["prompt_files"][key]
        prompts = run_dir / prompt_details["file"]
        if sha256_file(prompts) != prompt_details["sha256"]:
            raise QualificationError(f"prompt changed immediately before invocation: {key}")
        out_dir = run_dir / config["output"]["generation_directories"][key]
        job_resume = resume and out_dir.exists()
        command = _generation_command(
            tuner_root, prompts, out_dir, model, config, revision=revision, resume=job_resume
        )
        result = subprocess.run(command, cwd=tuner_root, check=False)
        if result.returncode != 0:
            raise QualificationError(f"public tuner batch-generate failed for {key}")
        completions = out_dir / COMPLETIONS_FILE
        completion_rows = _read_jsonl(completions)
        expected_rows = int(prompt_details["rows"])
        if len(completion_rows) != expected_rows:
            raise QualificationError(f"public tuner returned incomplete row count for {key}")
        checkpoint = out_dir / CHECKPOINT_FILE
        if not checkpoint.is_file():
            raise QualificationError(f"public tuner omitted checkpoint for {key}")
        checkpoint_value = json.loads(checkpoint.read_text(encoding="utf-8"))
        if checkpoint_value.get("count") != expected_rows:
            raise QualificationError(f"public tuner checkpoint incomplete for {key}")
        completed[key] = {
            "status": "complete",
            "file": str(completions.relative_to(run_dir)),
            "sha256": sha256_file(completions),
            "rows": len(completion_rows),
            "checkpoint_file": str(checkpoint.relative_to(run_dir)),
            "checkpoint_sha256": sha256_file(checkpoint),
            "model": model,
            "revision": revision,
            "prompt_sha256": prompt_details["sha256"],
            "public_tuner_argv": command,
        }
        manifest["generation_outputs"] = completed
        _write_json_atomic(manifest_path, manifest)
    manifest["status"] = "generation_complete"
    manifest["generation_outputs"] = completed
    _write_json_atomic(manifest_path, manifest)
    return manifest


def wilson_lower(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 0.0
    p = successes / n
    denominator = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    radius = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n)
    return (centre - radius) / denominator


def paired_bootstrap_ci(deltas: Sequence[int], seed: int, resamples: int) -> tuple[float, float]:
    if not deltas:
        raise QualificationError("paired bootstrap requires non-empty deltas")
    rng = random.Random(seed)
    n = len(deltas)
    values = sorted(sum(deltas[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    low = values[max(0, math.floor(0.025 * resamples))]
    high = values[min(resamples - 1, math.ceil(0.975 * resamples) - 1)]
    return low, high


def _load_scorer(config: Mapping[str, Any], repo_root: Path):
    path = _resolve_within(repo_root, config["canonical_scorer"]["path"], "canonical scorer")
    if sha256_file(path) != config["canonical_scorer"]["sha256"]:
        raise QualificationError("canonical scorer SHA-256 mismatch")
    spec = importlib.util.spec_from_file_location("stage_s_canonical_scorer", path)
    if spec is None or spec.loader is None:
        raise QualificationError("cannot import canonical scorer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completion_map(path: Path) -> dict[str, dict[str, Any]]:
    rows = _read_jsonl(path)
    result = {str(row.get("id")): row for row in rows}
    if len(result) != len(rows):
        raise QualificationError(f"duplicate completion ids: {path}")
    return result


def _parse_payload(text: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    subgrade = {"json_parse": False, "exact_fields": False, "confidence_valid": False}
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, subgrade
    if not isinstance(payload, dict):
        return None, subgrade
    subgrade["json_parse"] = True
    subgrade["exact_fields"] = set(payload) == {"answer", "answer_confidence"}
    confidence = payload.get("answer_confidence")
    subgrade["confidence_valid"] = (
        not isinstance(confidence, bool)
        and isinstance(confidence, (int, float))
        and math.isfinite(float(confidence))
        and 0.0 <= float(confidence) <= 1.0
    )
    return payload, subgrade


def _posture_ok(
    mode: str,
    payload: dict[str, Any] | None,
    parse_subgrade: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    answer = payload.get("answer") if isinstance(payload, dict) else None
    answer_is_string = isinstance(answer, str)
    rule = contract[mode]
    checks: dict[str, bool] = {
        "json_parse": bool(parse_subgrade.get("json_parse")),
        "exact_fields": bool(parse_subgrade.get("exact_fields")),
        "confidence_valid": bool(parse_subgrade.get("confidence_valid")),
        "answer_is_string": answer_is_string,
    }
    required_checks = list(checks.values())
    if not answer_is_string:
        return False, checks
    substantive = bool(answer.strip()) and any(character.isalnum() for character in answer)
    if rule.get("require_nonempty_substantive_answer"):
        checks["nonempty_substantive_answer"] = substantive
        required_checks.append(substantive)
    forbidden_phrases = rule.get("forbidden_phrases_casefold", [])
    if forbidden_phrases:
        folded = answer.casefold()
        checks["forbidden_phrases_absent"] = all(
            str(phrase).casefold() not in folded for phrase in forbidden_phrases
        )
        required_checks.append(checks["forbidden_phrases_absent"])
    exact_shape = rule.get("exact_shape")
    if exact_shape is not None:
        if not isinstance(exact_shape, dict):
            raise QualificationError(f"posture_contract.{mode}.exact_shape must be a mapping")
        prefix = str(exact_shape.get("prefix", ""))
        suffix = str(exact_shape.get("suffix", ""))
        shape_match = answer.startswith(prefix) and answer.endswith(suffix)
        candidate = answer[len(prefix) : len(answer) - len(suffix)] if shape_match else ""
        candidate_substantive = bool(candidate.strip()) and any(
            character.isalnum() for character in candidate
        )
        checks["exact_shape"] = shape_match
        required_checks.append(shape_match)
        if exact_shape.get("require_nonempty_substantive_candidate"):
            checks["nonempty_substantive_candidate"] = candidate_substantive
            required_checks.append(candidate_substantive)
    if "exact_answers" in rule:
        checks["exact_answer"] = answer in rule["exact_answers"]
        required_checks.append(checks["exact_answer"])
    if "forbidden_exact_answers" in rule:
        checks["forbidden_exact_answer"] = answer not in rule["forbidden_exact_answers"]
        required_checks.append(checks["forbidden_exact_answer"])
    for index, substring in enumerate(rule.get("required_substrings", [])):
        checks[f"required_substring_{index}"] = substring in answer
        required_checks.append(checks[f"required_substring_{index}"])
    for index, substring in enumerate(rule.get("forbidden_substrings", [])):
        checks[f"forbidden_substring_{index}"] = substring not in answer
        required_checks.append(checks[f"forbidden_substring_{index}"])
    return all(required_checks), checks


def _native_visible_text(
    completion_text: Any, predicted_mode: str | None, tokens_by_mode: Mapping[str, str]
) -> tuple[str, bool, bool]:
    text = completion_text if isinstance(completion_text, str) else ""
    token = tokens_by_mode.get(predicted_mode or "")
    prefix_match = isinstance(token, str) and text.startswith(token)
    visible = text[len(token) :] if prefix_match and token is not None else text
    no_visible_tokens = all(value not in visible for value in tokens_by_mode.values())
    return visible, prefix_match, no_visible_tokens


def _forced_visible_text(
    completion_text: Any, tokens_by_mode: Mapping[str, str]
) -> tuple[str, bool]:
    visible = completion_text if isinstance(completion_text, str) else ""
    return visible, all(value not in visible for value in tokens_by_mode.values())


def score(config_path: Path, run_id: str, *, resume: bool) -> dict[str, Any]:
    config, experiment_dir, repo_root = load_contract(config_path)
    rows = load_dev_rows(config, experiment_dir, repo_root)
    scorer = _load_scorer(config, repo_root)
    run_dir = _resolve_within(experiment_dir, str(config["output"]["root"]), "output.root") / run_id
    manifest_path = run_dir / config["output"]["run_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    allowed_statuses = {"generation_complete"}
    if resume:
        allowed_statuses.add("qualification_complete")
    if manifest.get("status") not in allowed_statuses:
        raise QualificationError("scoring requires a completed generation manifest")
    if manifest.get("config_sha256") != sha256_file(config_path):
        raise QualificationError("qualification config changed before scoring")
    if hash_artifact_tree(Path(manifest["stage_s_model"])) != manifest.get(
        "stage_s_artifact_tree"
    ):
        raise QualificationError("Stage-S artifact tree changed before scoring")
    lineage_path = Path(manifest["special_token_lineage_path"])
    if sha256_file(lineage_path) != manifest.get("special_token_lineage_sha256"):
        raise QualificationError("special-token lineage changed before scoring")
    _verify_prompt_files(run_dir, manifest)
    token_entries = manifest["configured_tokens"]
    id_to_mode = {int(entry["runtime_token_id"]): str(entry["name"]) for entry in token_entries}
    tokens_by_mode = {str(entry["name"]): str(entry["token"]) for entry in token_entries}
    outputs = config["output"]["generation_directories"]
    generation_outputs = manifest.get("generation_outputs", {})
    verified_paths = {
        key: _verify_completed_generation(
            run_dir, key, generation_outputs.get(key, {}), int(manifest["prompt_files"][key]["rows"])
        )
        for key in ("base_native", "stage_s_native", "stage_s_forced")
    }
    for key, expected in manifest["expected_generation_invocations"].items():
        actual = generation_outputs[key]
        if actual.get("model") != expected["model"] or actual.get("revision") != expected["revision"]:
            raise QualificationError(f"recorded generation invocation drifted: {key}")
        if actual.get("prompt_sha256") != manifest["prompt_files"][key]["sha256"]:
            raise QualificationError(f"recorded generation prompt hash drifted: {key}")
    base = _completion_map(verified_paths["base_native"])
    native = _completion_map(verified_paths["stage_s_native"])
    forced = _completion_map(verified_paths["stage_s_forced"])
    expected_ids = {_row_id(row) for row in rows}
    if set(base) != expected_ids or set(native) != expected_ids:
        raise QualificationError("native completion ids do not exactly match dev rows")
    expected_forced = {f"{identifier}::forced::{mode}" for identifier in expected_ids for mode in MODE_NAMES}
    if set(forced) != expected_forced:
        raise QualificationError("forced completion ids do not exactly match dev rows x modes")

    scored_path = run_dir / config["output"]["scored_rows"]
    existing_rows = _read_jsonl(scored_path) if resume and scored_path.exists() else []
    if existing_rows and scored_path.read_bytes() != _jsonl_bytes(existing_rows):
        raise QualificationError("existing scored row log is not canonical byte-for-byte JSONL")
    existing_by_id = {str(row.get("id")): row for row in existing_rows}
    if len(existing_by_id) != len(existing_rows):
        raise QualificationError("existing scored row log contains duplicate IDs")
    if set(existing_by_id) - expected_ids:
        raise QualificationError("existing scored row log contains IDs outside the dev split")
    if scored_path.exists() and not resume:
        raise QualificationError("scored row log exists; pass --resume")
    scored_path.parent.mkdir(parents=True, exist_ok=True)
    with scored_path.open("a", encoding="utf-8") as handle:
        for row in rows:
            identifier = _row_id(row)
            metadata = row["metadata"]
            aliases = list(metadata["gold_aliases"])
            native_row = native[identifier]
            first_ids = native_row.get("completion_token_ids")
            first_id = first_ids[0] if isinstance(first_ids, list) and first_ids else None
            predicted_mode = id_to_mode.get(first_id)
            native_visible, native_prefix_match, native_tokens_stripped = _native_visible_text(
                native_row.get("completion_text", ""), predicted_mode, tokens_by_mode
            )
            payload, native_subgrade = _parse_payload(native_visible)
            answer = payload.get("answer") if isinstance(payload, dict) else ""
            stage_correct = isinstance(answer, str) and scorer.is_correct(answer, aliases)
            base_correct = scorer.is_correct(str(base[identifier].get("completion_text", "")), aliases)
            forced_exhaust: dict[str, Any] = {}
            for mode in MODE_NAMES:
                forced_row = forced[f"{identifier}::forced::{mode}"]
                forced_visible, forced_tokens_stripped = _forced_visible_text(
                    forced_row.get("completion_text", ""), tokens_by_mode
                )
                forced_payload, forced_parse = _parse_payload(forced_visible)
                posture_ok, posture_checks = _posture_ok(
                    mode, forced_payload, forced_parse, config["posture_contract"]
                )
                forced_answer = (
                    forced_payload.get("answer") if isinstance(forced_payload, dict) else ""
                )
                posture_checks["correct_descriptive"] = bool(
                    isinstance(forced_answer, str) and scorer.is_correct(forced_answer, aliases)
                )
                posture_ok = posture_ok and forced_tokens_stripped
                forced_exhaust[mode] = {
                    "completion_text": forced_row.get("completion_text"),
                    "visible_text": forced_visible,
                    "visible_special_tokens_stripped": forced_tokens_stripped,
                    "completion_token_ids": forced_row.get("completion_token_ids"),
                    "finish_reason": forced_row.get("finish_reason"),
                    "payload": forced_payload,
                    "parse_subgrade": forced_parse,
                    "posture_subgrade": posture_checks,
                    "posture_compliant": posture_ok,
                }
            scored = {
                "id": identifier,
                "source_mode": metadata["mode_label"],
                "gold_aliases": aliases,
                "base": {
                    "completion_text": base[identifier].get("completion_text"),
                    "completion_token_ids": base[identifier].get("completion_token_ids"),
                    "finish_reason": base[identifier].get("finish_reason"),
                    "correct": bool(base_correct),
                },
                "stage_s_native": {
                    "completion_text": native_row.get("completion_text"),
                    "visible_text": native_visible,
                    "completion_token_ids": first_ids,
                    "finish_reason": native_row.get("finish_reason"),
                    "first_token_id": first_id,
                    "predicted_mode": predicted_mode,
                    "configured_first_token": predicted_mode is not None,
                    "textual_mode_prefix_match": native_prefix_match,
                    "visible_special_tokens_stripped": native_tokens_stripped,
                    "payload": payload,
                    "subgrade": native_subgrade,
                    "correct": bool(stage_correct),
                },
                "stage_s_forced": forced_exhaust,
            }
            if identifier in existing_by_id:
                if canonical_json(existing_by_id[identifier]) != canonical_json(scored):
                    raise QualificationError(
                        f"existing scored row differs from hash-bound recomputation: {identifier}"
                    )
                continue
            handle.write(canonical_json(scored) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    scored_rows = _read_jsonl(scored_path)
    if len(scored_rows) != len(rows):
        raise QualificationError("scored row log is incomplete")
    thresholds = config["gates"]
    n = len(scored_rows)
    configured = sum(row["stage_s_native"]["configured_first_token"] for row in scored_rows)
    json_valid = sum(row["stage_s_native"]["subgrade"]["json_parse"] for row in scored_rows)
    exact_fields = sum(row["stage_s_native"]["subgrade"]["exact_fields"] for row in scored_rows)
    confidence_valid = sum(row["stage_s_native"]["subgrade"]["confidence_valid"] for row in scored_rows)
    confidence_values = [
        float(row["stage_s_native"]["payload"]["answer_confidence"])
        for row in scored_rows
        if row["stage_s_native"]["subgrade"]["confidence_valid"]
    ]
    confidence_sd = statistics.pstdev(confidence_values) if len(confidence_values) >= 2 else 0.0
    forced_flags = [
        forced_row["posture_compliant"]
        for row in scored_rows
        for forced_row in row["stage_s_forced"].values()
    ]
    native_strip_flags = [
        row["stage_s_native"]["visible_special_tokens_stripped"] for row in scored_rows
    ]
    forced_strip_flags = [
        forced_row["visible_special_tokens_stripped"]
        for row in scored_rows
        for forced_row in row["stage_s_forced"].values()
    ]
    predicted_counts = Counter(row["stage_s_native"]["predicted_mode"] for row in scored_rows)
    per_mode: dict[str, Any] = {}
    for mode in MODE_NAMES:
        subset = [row for row in scored_rows if row["source_mode"] == mode]
        successes = sum(row["stage_s_native"]["predicted_mode"] == mode for row in subset)
        lower = wilson_lower(successes, len(subset))
        per_mode[mode] = {
            "successes": successes,
            "n": len(subset),
            "recall": successes / len(subset),
            "wilson_lower": lower,
            "pass": lower > float(thresholds["per_mode_recall"]["lower_bound_gt"]),
        }
    deltas = [
        int(row["stage_s_native"]["correct"]) - int(row["base"]["correct"])
        for row in scored_rows
    ]
    noninferiority = thresholds["answer_quality_noninferiority"]
    ci_low, ci_high = paired_bootstrap_ci(
        deltas, int(noninferiority["seed"]), int(noninferiority["resamples"])
    )
    rates = {
        "configured_first_token": configured / n,
        "valid_json": json_valid / n,
        "exact_required_fields": exact_fields / n,
        "confidence_parse_and_range": confidence_valid / n,
        "forced_posture_compliance": sum(forced_flags) / len(forced_flags),
        "native_visible_special_token_stripping": sum(native_strip_flags) / len(native_strip_flags),
        "forced_visible_special_token_stripping": sum(forced_strip_flags) / len(forced_strip_flags),
    }
    gate_results = {
        "configured_first_token": rates["configured_first_token"] >= thresholds["configured_first_token_rate_min"],
        "valid_json": rates["valid_json"] >= thresholds["valid_json_after_mode_token_rate_min"],
        "exact_required_fields": rates["exact_required_fields"] >= thresholds["exact_required_fields_rate_min"],
        "confidence_parse_and_range": rates["confidence_parse_and_range"] >= thresholds["confidence_parse_and_range_rate_min"],
        "confidence_population_sd": confidence_sd >= thresholds["confidence_population_sd_min"],
        "forced_posture_compliance": rates["forced_posture_compliance"] >= thresholds["deterministic_forced_token_posture_compliance_min"],
        "native_visible_special_token_stripping": rates["native_visible_special_token_stripping"] >= thresholds["visible_special_token_stripping_rate_min"],
        "forced_visible_special_token_stripping": rates["forced_visible_special_token_stripping"] >= thresholds["visible_special_token_stripping_rate_min"],
        "per_mode_wilson_majority": all(value["pass"] for value in per_mode.values()),
        "max_single_mode_share": max(predicted_counts.values(), default=0) <= int(thresholds["max_single_mode_share"]["numerator_max"]),
        "answer_quality_noninferiority": ci_low > float(noninferiority["lower_bound_gt"]),
    }
    summary = {
        "schema_version": 1,
        "experiment": config["experiment"],
        "run_id": run_id,
        "status": "completed",
        "dev_rows": n,
        "heldout_rows_accessed": 0,
        "rates": rates,
        "confidence_population_sd": confidence_sd,
        "predicted_mode_counts": dict(sorted((str(k), v) for k, v in predicted_counts.items())),
        "per_mode_recall": per_mode,
        "answer_quality": {
            "metric": noninferiority["metric"],
            "point_difference": sum(deltas) / n,
            "ci": noninferiority["ci"],
            "seed": noninferiority["seed"],
            "resamples": noninferiority["resamples"],
            "ci_lower": ci_low,
            "ci_upper": ci_high,
        },
        "gates": gate_results,
        "all_pass": all(gate_results.values()),
        "data_exhaust": {
            "scored_rows": scored_path.name,
            "scored_rows_sha256": sha256_file(scored_path),
            "generation_outputs": manifest.get("generation_outputs"),
        },
    }
    _write_json_atomic(run_dir / config["output"]["summary"], summary)
    manifest["status"] = "qualification_complete"
    manifest["summary_sha256"] = sha256_file(run_dir / config["output"]["summary"])
    manifest["scored_rows_sha256"] = sha256_file(scored_path)
    _write_json_atomic(run_dir / config["output"]["run_manifest"], manifest)
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "generate", "score", "run"))
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("qualification.yaml"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--stage-s-model", type=Path, required=True)
    parser.add_argument("--special-token-lineage", type=Path)
    parser.add_argument("--tuner-worktree", type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result: Mapping[str, Any]
        if args.command in {"prepare", "run"}:
            if args.special_token_lineage is None:
                raise QualificationError("prepare requires --special-token-lineage")
            result = prepare_run(
                args.config,
                args.run_id,
                args.stage_s_model,
                args.special_token_lineage,
                resume=args.resume,
            )
        if args.command in {"generate", "run"}:
            if args.tuner_worktree is None:
                raise QualificationError("generate requires --tuner-worktree")
            result = generate(
                args.config,
                args.run_id,
                args.stage_s_model,
                args.tuner_worktree.resolve(),
                resume=args.resume,
            )
        if args.command in {"score", "run"}:
            result = score(args.config, args.run_id, resume=args.resume)
        print(canonical_json(result))
        return 0
    except (QualificationError, OSError, ValueError, yaml.YAMLError) as exc:
        print(f"stage-s qualification failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
