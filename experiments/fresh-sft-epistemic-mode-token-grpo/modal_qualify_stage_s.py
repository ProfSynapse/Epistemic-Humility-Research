#!/usr/bin/env python3
"""Modal A10G lane for one hash-bound Stage-S dev qualification."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import modal
import yaml


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "modal_qualification.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
RUN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")

runtime = CONFIG["runtime"]
volume_config = CONFIG["volumes"]
image = modal.Image.from_registry(runtime["image"]).entrypoint([]).pip_install(*runtime["pip"])
input_volume = modal.Volume.from_name(volume_config["input"]["name"], create_if_missing=False)
output_volume = modal.Volume.from_name(volume_config["output"]["name"], create_if_missing=False)
cache_volume = modal.Volume.from_name(volume_config["cache"]["name"], create_if_missing=False)
app = modal.App("eh-stage-s-dev-qualification")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _credential_free_repo_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("repository origin must be a credential-free HTTPS URL")
    if parsed.query or parsed.fragment:
        raise RuntimeError("repository origin must not contain query or fragment data")
    host = parsed.hostname + (f":{parsed.port}" if parsed.port else "")
    return urlunsplit((parsed.scheme, host, parsed.path.removesuffix(".git"), "", ""))


def _git(destination: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(destination), *args], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:2])} failed for {destination}")
    return result


def _clone_exact(repo_url: str, branch: str, commit: str, destination: Path) -> None:
    expected_origin = _credential_free_repo_url(repo_url)
    if destination.exists():
        if not destination.is_dir() or not (destination / ".git").is_dir():
            raise RuntimeError(f"existing workspace is not a git checkout: {destination}")
        actual_origin = _credential_free_repo_url(
            _git(destination, "remote", "get-url", "origin").stdout.strip()
        )
        if actual_origin != expected_origin:
            raise RuntimeError("existing workspace origin differs from expected credential-free URL")
        tracked = _git(destination, "status", "--porcelain", "--untracked-files=no")
        if tracked.stdout.strip():
            raise RuntimeError("existing workspace has tracked source drift")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--branch", branch, "--depth", "1", "--no-checkout", repo_url, str(destination)],
            check=True,
        )
        actual_origin = _credential_free_repo_url(
            _git(destination, "remote", "get-url", "origin").stdout.strip()
        )
        if actual_origin != expected_origin:
            raise RuntimeError("cold clone origin differs from expected credential-free URL")
    _git(destination, "fetch", "--depth", "1", "origin", commit)
    _git(destination, "checkout", "--detach", commit)
    head = _git(destination, "rev-parse", "HEAD").stdout.strip()
    if head.lower() != commit:
        raise RuntimeError(f"exact commit checkout failed: {destination}")


def _verify_file(path: Path, expected_sha: str, label: str) -> None:
    if not path.is_file() or _sha(path) != expected_sha:
        raise RuntimeError(f"{label} is missing or has the wrong SHA-256")


@app.function(
    image=image,
    gpu=runtime["gpu"],
    timeout=int(float(runtime["timeout_hours"]) * 3600),
    volumes={
        volume_config["input"]["mount"]: input_volume,
        volume_config["output"]["mount"]: output_volume,
        volume_config["cache"]["mount"]: cache_volume,
    },
)
def run_qualification(
    qualification_run_id: str,
    training_run_id: str,
    experiment_repo_url: str,
    experiment_branch: str,
    experiment_commit: str,
    experiment_module_sha256: str,
    modal_config_sha256: str,
    qualification_config_sha256: str,
    dev_sha256: str,
    tuner_repo_url: str,
    tuner_branch: str,
    tuner_commit: str,
    training_done_identity_json: str,
):
    """Verify the completed training artifact, then run the public batch CLI."""
    if not RUN_RE.fullmatch(qualification_run_id) or not RUN_RE.fullmatch(training_run_id):
        raise ValueError("run ids must be path-safe and at most 64 characters")
    if not COMMIT_RE.fullmatch(experiment_commit) or not COMMIT_RE.fullmatch(tuner_commit):
        raise ValueError("source commits must be exact lowercase 40-character SHAs")
    if tuner_commit != CONFIG["tuner"]["commit"]:
        raise ValueError("tuner commit differs from the governed qualification config")
    if experiment_repo_url != CONFIG["source"]["repo_url"] or experiment_branch != CONFIG["source"]["branch"]:
        raise ValueError("experiment source differs from the governed qualification config")
    if tuner_repo_url != CONFIG["tuner"]["repo_url"] or tuner_branch != CONFIG["tuner"]["branch"]:
        raise ValueError("tuner source differs from the governed qualification config")
    try:
        expected_training_identity = json.loads(training_done_identity_json)
    except json.JSONDecodeError as exc:
        raise ValueError("training DONE identity argument is not valid JSON") from exc
    if not isinstance(expected_training_identity, dict):
        raise ValueError("training DONE identity argument must be a JSON object")

    input_root = Path(volume_config["input"]["mount"]) / qualification_run_id
    staged_config = input_root / "qualification.yaml"
    staged_dev = input_root / "dev.jsonl"
    _verify_file(staged_config, qualification_config_sha256, "staged qualification config")
    _verify_file(staged_dev, dev_sha256, "staged dev split")
    if any((input_root / name).exists() for name in CONFIG["qualification"]["forbidden_files"]):
        raise RuntimeError("qualification input namespace contains forbidden train/heldout bytes")

    training_root = (
        Path(volume_config["output"]["mount"])
        / "outputs/runs/modal/sft"
        / f"{training_run_id}-{tuner_commit[:8]}"
    )
    training_done = _json(training_root / CONFIG["training_artifact"]["done_marker"])
    identity = training_done.get("identity", {})
    if training_done.get("status") != "completed" or identity != expected_training_identity:
        raise RuntimeError("training DONE marker exact identity mismatch")
    model_root = training_root / CONFIG["training_artifact"]["final_model_directory"]
    lineage = training_root / CONFIG["training_artifact"]["lineage_file"]
    if not model_root.is_dir() or not lineage.is_file():
        raise RuntimeError("completed training artifact lacks final_model or special-token lineage")

    run_root = (
        Path(volume_config["output"]["mount"])
        / "outputs/runs/modal/qualification"
        / f"{qualification_run_id}-{experiment_commit[:8]}"
    )
    run_root.mkdir(parents=True, exist_ok=True)
    provenance_path = run_root / "provenance.json"
    provenance = {
        "schema_version": 1,
        "qualification_run_id": qualification_run_id,
        "training_run_id": training_run_id,
        "experiment_commit": experiment_commit,
        "tuner_commit": tuner_commit,
        "training_done_identity": expected_training_identity,
        "qualification_config_sha256": qualification_config_sha256,
        "dev_sha256": dev_sha256,
        "training_done_sha256": _sha(training_root / CONFIG["training_artifact"]["done_marker"]),
        "special_token_lineage_sha256": _sha(lineage),
    }
    if provenance_path.exists() and _json(provenance_path) != provenance:
        raise RuntimeError("qualification resume provenance mismatch")
    done_path = run_root / CONFIG["qualification"]["done_marker"]
    if done_path.exists():
        done = _json(done_path)
        if done.get("status") != "completed" or done.get("provenance") != provenance:
            raise RuntimeError("qualification DONE marker identity mismatch")
        return {"status": "completed", "no_op": True, "artifact_root": str(run_root)}

    experiment_root = run_root / "workspace/experiment"
    tuner_root = run_root / "workspace/tuner"
    _clone_exact(experiment_repo_url, experiment_branch, experiment_commit, experiment_root)
    _clone_exact(tuner_repo_url, tuner_branch, tuner_commit, tuner_root)
    experiment_dir = experiment_root / "experiments" / CONFIG["experiment"]
    _verify_file(experiment_dir / "modal_qualify_stage_s.py", experiment_module_sha256, "experiment Modal module")
    _verify_file(experiment_dir / "modal_qualification.yaml", modal_config_sha256, "Modal qualification config")
    _verify_file(experiment_dir / "qualification.yaml", qualification_config_sha256, "qualification config in source")
    dev_target = experiment_dir / "analysis/dataset/dev.jsonl"
    dev_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(staged_dev, dev_target)
    _verify_file(dev_target, dev_sha256, "materialized dev split")
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_volume.commit()

    os.environ["HF_HOME"] = str(Path(volume_config["cache"]["mount"]) / "huggingface")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        "python3",
        str(experiment_dir / "qualify_stage_s.py"),
        "run",
        "--config",
        str(experiment_dir / "qualification.yaml"),
        "--run-id",
        qualification_run_id,
        "--stage-s-model",
        str(model_root),
        "--special-token-lineage",
        str(lineage),
        "--tuner-worktree",
        str(tuner_root),
    ]
    local_run_manifest = experiment_dir / "analysis/qualification" / qualification_run_id / "run_manifest.json"
    if local_run_manifest.exists():
        command.append("--resume")
    stopped = threading.Event()

    def commit_loop() -> None:
        while not stopped.wait(float(runtime["periodic_volume_commit_seconds"])):
            output_volume.commit()

    thread = threading.Thread(target=commit_loop, daemon=True)
    thread.start()
    try:
        subprocess.run(command, cwd=experiment_root, check=True)
    finally:
        stopped.set()
        thread.join(timeout=5)
        output_volume.commit()
    summary = experiment_dir / "analysis/qualification" / qualification_run_id / "summary.json"
    if not summary.is_file():
        raise RuntimeError("qualification runner returned without a summary")
    run_manifest = _json(local_run_manifest)
    generation_rows = sum(
        int(value.get("rows", -1))
        for value in run_manifest.get("generation_outputs", {}).values()
    )
    if run_manifest.get("status") != "qualification_complete" or generation_rows != int(
        CONFIG["qualification"]["expected_generation_rows"]
    ):
        raise RuntimeError("qualification runner did not complete the exact registered generation count")
    done = {
        "schema_version": 1,
        "status": "completed",
        "provenance": provenance,
        "summary_sha256": _sha(summary),
    }
    done_path.write_text(json.dumps(done, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_volume.commit()
    return {"status": "completed", "no_op": False, "artifact_root": str(run_root), "summary_sha256": done["summary_sha256"]}
