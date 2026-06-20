#!/usr/bin/env python3
"""Plan or execute Phase 3 local causal-pilot sweeps.

This wrapper is intentionally non-GPU by default. It builds deterministic calls
to `phase3_causal_pilot_runner.py` across configured candidates and modes, and
only invokes the runner when `--execute` is passed with the relevant allow flag.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROBE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROBE_DIR.parents[2]
RUNNER = PROBE_DIR / "phase3_causal_pilot_runner.py"
DOCKER_CONFIG_PATH_KEYS = {
    "adapter_path",
    "direction_csv",
    "direction_file",
    "direction_manifest",
    "extraction_dir",
    "extraction_manifest",
    "probe_results",
    "root",
}


class SweepError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SweepError(f"{path} did not load to a YAML mapping")
    return payload


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False)


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def _csv(values: list[Any]) -> str:
    return ",".join(str(value) for value in values)


def container_repo_path(path: Path, *, repo_mount: str) -> str:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise SweepError(f"path is outside repo and cannot be mounted into Docker: {resolved}") from exc
    return f"{repo_mount.rstrip('/')}/{rel.as_posix()}"


def docker_config_path(value: str | Path, *, repo_mount: str) -> str:
    text = str(value)
    normalized = text.replace("\\", "/")
    mount = repo_mount.rstrip("/")
    if normalized == mount or normalized.startswith(f"{mount}/"):
        return normalized

    path = Path(text)
    if path.is_absolute():
        return container_repo_path(path, repo_mount=repo_mount)

    return f"{mount}/{normalized.lstrip('/')}"


def _rewrite_docker_config_paths(value: Any, *, repo_mount: str, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            item_key: _rewrite_docker_config_paths(
                item_value,
                repo_mount=repo_mount,
                key=item_key,
            )
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [
            _rewrite_docker_config_paths(item, repo_mount=repo_mount, key=key)
            for item in value
        ]
    if key in DOCKER_CONFIG_PATH_KEYS and isinstance(value, str) and value:
        return docker_config_path(value, repo_mount=repo_mount)
    return value


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def execution_config(sweep: dict[str, Any]) -> dict[str, Any]:
    execution = sweep.get("execution", {})
    if execution is None:
        execution = {}
    if not isinstance(execution, dict):
        raise SweepError("sweep.execution must be a mapping")
    backend = execution.get("backend", "host")
    if backend not in {"host", "docker"}:
        raise SweepError("sweep.execution.backend must be 'host' or 'docker'")
    docker = execution.get("docker", {})
    if docker is None:
        docker = {}
    if not isinstance(docker, dict):
        raise SweepError("sweep.execution.docker must be a mapping")
    return {
        "backend": backend,
        "docker": {
            "image": docker.get("image", "unsloth/unsloth:latest"),
            "repo_mount": docker.get("repo_mount", "/workspace/repo"),
            "workdir": docker.get("workdir", docker.get("repo_mount", "/workspace/repo")),
            "hf_home": docker.get("hf_home", "/workspace/repo/.cache/hf"),
            "huggingface_hub_cache": docker.get(
                "huggingface_hub_cache",
                "/workspace/repo/.cache/hf/hub",
            ),
        },
    }


def runner_args(
    *,
    mode: dict[str, Any],
    materialized_config: Path,
    label: str,
    backend: str,
    docker: dict[str, Any],
) -> list[str]:
    if backend == "docker":
        runner_path = container_repo_path(RUNNER, repo_mount=docker["repo_mount"])
        config_path = container_repo_path(materialized_config, repo_mount=docker["repo_mount"])
    else:
        runner_path = str(RUNNER)
        config_path = str(materialized_config)
    args = [
        runner_path,
        "--mode",
        mode["name"],
        "--config",
        config_path,
        "--candidate",
        label,
        "--coefficients",
        _csv(mode["coefficients"]),
        "--controls",
        _csv(mode["controls"]),
        "--max-rows",
        str(mode["max_rows"]),
    ]
    if mode["name"] == "generation":
        args.extend(["--max-new-tokens", str(mode["max_new_tokens"])])
        args.append("--allow-generation")
    else:
        args.append("--allow-logit-diagnostic")
    return args


def build_command(
    *,
    mode: dict[str, Any],
    materialized_config: Path,
    label: str,
    execution: dict[str, Any],
) -> list[str]:
    backend = execution["backend"]
    docker = execution["docker"]
    args = runner_args(
        mode=mode,
        materialized_config=materialized_config,
        label=label,
        backend=backend,
        docker=docker,
    )
    if backend == "host":
        return [sys.executable, *args]
    return [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "--entrypoint",
        "python",
        "-e",
        f"HF_HOME={docker['hf_home']}",
        "-e",
        f"HUGGINGFACE_HUB_CACHE={docker['huggingface_hub_cache']}",
        "-v",
        f"{REPO_ROOT}:{docker['repo_mount']}",
        "-w",
        docker["workdir"],
        docker["image"],
        *args,
    ]


def _selected_candidates(
    source_config: dict[str, Any],
    selection: list[str] | str,
) -> list[dict[str, Any]]:
    candidates = source_config.get("candidate_directions", [])
    if not isinstance(candidates, list) or not candidates:
        raise SweepError("candidate source config has no candidate_directions")
    by_label = {candidate.get("label"): candidate for candidate in candidates}
    if selection == "all":
        return list(candidates)
    if not isinstance(selection, list) or not selection:
        raise SweepError("sweep.candidates must be 'all' or a non-empty list")
    missing = [label for label in selection if label not in by_label]
    if missing:
        raise SweepError(f"candidate label(s) not found in source config: {missing}")
    return [by_label[label] for label in selection]


def split_executable_candidates(
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    executable: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("skip_by_default") is True:
            skipped.append({
                "label": candidate.get("label"),
                "reason": candidate.get("skip_reason", "candidate is marked skip_by_default"),
                "requires_adapterless_runner": bool(candidate.get("requires_adapterless_runner")),
            })
        else:
            executable.append(candidate)
    return executable, skipped


def _mode_plan(raw_mode: dict[str, Any]) -> dict[str, Any]:
    name = raw_mode.get("name")
    if name not in {"generation", "logit_diagnostic"}:
        raise SweepError(f"unsupported mode {name!r}")
    coefficients = raw_mode.get("coefficients")
    controls = raw_mode.get("controls")
    if not isinstance(coefficients, list) or not coefficients:
        raise SweepError(f"mode {name} requires a non-empty coefficients list")
    if not isinstance(controls, list) or not controls:
        raise SweepError(f"mode {name} requires a non-empty controls list")
    if name == "logit_diagnostic" and controls[0] != "no_vector_baseline":
        raise SweepError("logit_diagnostic controls must start with no_vector_baseline")
    return {
        "name": name,
        "coefficients": coefficients,
        "controls": controls,
        "max_rows": int(raw_mode.get("max_rows", 16)),
        "max_new_tokens": int(raw_mode.get("max_new_tokens", 64)),
    }


def parse_mode_filter(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    modes = {
        part.strip()
        for value in values
        for part in value.split(",")
        if part.strip()
    }
    if not modes:
        raise SweepError("--mode-filter must include at least one non-empty mode")
    unsupported = modes - {"generation", "logit_diagnostic"}
    if unsupported:
        raise SweepError(f"unsupported --mode-filter value(s): {sorted(unsupported)}")
    return modes


def filter_modes(
    modes: list[dict[str, Any]],
    mode_filter: set[str] | None,
) -> list[dict[str, Any]]:
    if mode_filter is None:
        return modes
    filtered = [mode for mode in modes if mode["name"] in mode_filter]
    if not filtered:
        configured = sorted({mode["name"] for mode in modes})
        raise SweepError(
            f"--mode-filter matched no configured modes; filter={sorted(mode_filter)} "
            f"configured={configured}"
        )
    return filtered


def build_runner_config(
    *,
    template_config: dict[str, Any],
    candidate: dict[str, Any],
    output_root: Path,
    sweep_name: str,
    mode: str,
    execution: dict[str, Any],
    runner_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a generation-enabled runner config scoped to one candidate."""
    config = copy.deepcopy(template_config)
    if runner_overrides:
        config = deep_merge(config, runner_overrides)
    config["candidate_directions"] = [copy.deepcopy(candidate)]
    config.setdefault("spec", {})["name"] = f"{sweep_name}__{candidate['label']}__{mode}"
    config.setdefault("output", {})["root"] = str(output_root / candidate["label"] / mode)
    config["output"]["intervention_results_allowed_by_this_spec"] = True
    config.setdefault("first_smoke", {}).setdefault("initial_scope", {})[
        "generation_allowed_by_this_spec"
    ] = True
    config.setdefault("spec", {})["status"] = "generation_smoke"
    config.setdefault("model", {})["enable_thinking"] = False
    if execution["backend"] == "docker":
        config = _rewrite_docker_config_paths(
            config,
            repo_mount=execution["docker"]["repo_mount"],
        )
    return config


def execution_log_dir(plan: dict[str, Any]) -> Path:
    return Path(plan["output_root"]) / "_execution_logs"


def _job_slug(job: dict[str, Any], index: int) -> str:
    raw = f"{index:03d}__{job['candidate']}__{job['mode']}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _execution_log_paths(plan: dict[str, Any], job: dict[str, Any], index: int) -> dict[str, Path]:
    log_dir = execution_log_dir(plan)
    slug = _job_slug(job, index)
    return {
        "stdout": log_dir / f"{slug}.stdout.log",
        "stderr": log_dir / f"{slug}.stderr.log",
        "results": log_dir / "execution_results.jsonl",
    }


def _write_execution_result(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_jobs(config_path: Path, mode_filter: set[str] | None = None) -> dict[str, Any]:
    sweep_config = load_yaml(config_path)
    sweep = sweep_config.get("sweep", {})
    if not isinstance(sweep, dict):
        raise SweepError("sweep config must contain a 'sweep' mapping")
    sweep_name = sweep.get("name")
    if not isinstance(sweep_name, str) or not sweep_name:
        raise SweepError("sweep.name is required")
    output_root = resolve_path(sweep.get("output_root", "experiment/phase1/probe/phase3_sweep"))
    runner_config_path = resolve_path(sweep["runner_config"])
    candidate_source_path = resolve_path(sweep.get("candidate_source_config", runner_config_path))
    execution = execution_config(sweep)
    runner_template = load_yaml(runner_config_path)
    candidate_source = load_yaml(candidate_source_path)
    runner_overrides = sweep.get("runner_overrides", {})
    if runner_overrides is None:
        runner_overrides = {}
    if not isinstance(runner_overrides, dict):
        raise SweepError("sweep.runner_overrides must be a mapping")
    candidates = _selected_candidates(candidate_source, sweep.get("candidates", "all"))
    executable_candidates, skipped_candidates = split_executable_candidates(candidates)
    modes = [_mode_plan(mode) for mode in sweep.get("modes", [])]
    if not modes:
        raise SweepError("sweep.modes must contain at least one mode")
    modes = filter_modes(modes, mode_filter)

    jobs: list[dict[str, Any]] = []
    config_dir = output_root / "_sweep_configs"
    for candidate in executable_candidates:
        label = candidate["label"]
        for mode in modes:
            materialized_config = config_dir / f"{label}__{mode['name']}.yaml"
            command = build_command(
                mode=mode,
                materialized_config=materialized_config,
                label=label,
                execution=execution,
            )
            jobs.append({
                "candidate": label,
                "mode": mode["name"],
                "execution_backend": execution["backend"],
                "coefficients": mode["coefficients"],
                "controls": mode["controls"],
                "max_rows": mode["max_rows"],
                "max_new_tokens": mode["max_new_tokens"],
                "materialized_config": str(materialized_config),
                "command": command,
                "runner_config_payload": build_runner_config(
                    template_config=runner_template,
                    candidate=candidate,
                    output_root=output_root,
                    sweep_name=sweep_name,
                    mode=mode["name"],
                    execution=execution,
                    runner_overrides=runner_overrides,
                ),
            })
    return {
        "sweep_name": sweep_name,
        "config": str(config_path.resolve()),
        "runner_config": str(runner_config_path),
        "candidate_source_config": str(candidate_source_path),
        "output_root": str(output_root),
        "execution_backend": execution["backend"],
        "execution": execution,
        "mode_filter": sorted(mode_filter) if mode_filter is not None else None,
        "inventory_candidate_count": len(candidates),
        "executable_candidate_count": len(executable_candidates),
        "skipped_candidate_count": len(skipped_candidates),
        "skipped_candidates": skipped_candidates,
        "job_count": len(jobs),
        "jobs": jobs,
    }


def write_plan(plan: dict[str, Any]) -> list[Path]:
    output_root = Path(plan["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "sweep_name": plan["sweep_name"],
        "config": plan["config"],
        "runner_config": plan["runner_config"],
        "candidate_source_config": plan["candidate_source_config"],
        "output_root": plan["output_root"],
        "execution_backend": plan["execution_backend"],
        "mode_filter": plan["mode_filter"],
        "inventory_candidate_count": plan["inventory_candidate_count"],
        "executable_candidate_count": plan["executable_candidate_count"],
        "skipped_candidate_count": plan["skipped_candidate_count"],
        "skipped_candidates": plan["skipped_candidates"],
        "job_count": plan["job_count"],
        "generation_executed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = output_root / "sweep_manifest.json"
    commands_path = output_root / "planned_commands.jsonl"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with commands_path.open("w", encoding="utf-8") as fh:
        for job in plan["jobs"]:
            row = {key: job[key] for key in (
                "candidate",
                "mode",
                "execution_backend",
                "coefficients",
                "controls",
                "max_rows",
                "max_new_tokens",
                "materialized_config",
                "command",
            )}
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return [manifest_path, commands_path]


def materialize_configs(plan: dict[str, Any]) -> list[Path]:
    written: list[Path] = []
    for job in plan["jobs"]:
        path = Path(job["materialized_config"])
        write_yaml(path, job["runner_config_payload"])
        written.append(path)
    return written


def execute_jobs(plan: dict[str, Any], *, allow_generation: bool, allow_logit_diagnostic: bool) -> list[dict[str, Any]]:
    needs_generation = any(job["mode"] == "generation" for job in plan["jobs"])
    needs_logit = any(job["mode"] == "logit_diagnostic" for job in plan["jobs"])
    if needs_generation and not allow_generation:
        raise SweepError("Refusing generation sweep execution without --allow-generation")
    if needs_logit and not allow_logit_diagnostic:
        raise SweepError("Refusing logit diagnostic sweep execution without --allow-logit-diagnostic")
    materialize_configs(plan)
    results: list[dict[str, Any]] = []
    log_dir = execution_log_dir(plan)
    log_dir.mkdir(parents=True, exist_ok=True)
    for index, job in enumerate(plan["jobs"]):
        log_paths = _execution_log_paths(plan, job, index)
        result = subprocess.run(
            job["command"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        log_paths["stdout"].write_text(result.stdout or "", encoding="utf-8")
        log_paths["stderr"].write_text(result.stderr or "", encoding="utf-8")
        row = {
            "candidate": job["candidate"],
            "mode": job["mode"],
            "execution_backend": job["execution_backend"],
            "materialized_config": job["materialized_config"],
            "command": job["command"],
            "returncode": result.returncode,
            "stdout_log_path": str(log_paths["stdout"]),
            "stderr_log_path": str(log_paths["stderr"]),
            "execution_results_path": str(log_paths["results"]),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_execution_result(log_paths["results"], row)
        results.append(row)
        if result.returncode != 0:
            raise SweepError(
                f"runner failed for candidate={job['candidate']} mode={job['mode']} "
                f"with exit {result.returncode}; stdout={log_paths['stdout']} "
                f"stderr={log_paths['stderr']}: {result.stderr.strip()}"
            )
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--write-plan", action="store_true")
    parser.add_argument("--materialize-configs", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode-filter",
        action="append",
        help=(
            "only plan/materialize/execute matching runner modes; may be repeated "
            "or comma-separated, e.g. --mode-filter logit_diagnostic"
        ),
    )
    parser.add_argument("--allow-generation", action="store_true")
    parser.add_argument("--allow-logit-diagnostic", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        mode_filter = parse_mode_filter(args.mode_filter)
        plan = build_jobs(args.config, mode_filter=mode_filter)
        written: list[Path] = []
        if args.write_plan:
            written.extend(write_plan(plan))
        if args.materialize_configs:
            written.extend(materialize_configs(plan))
        execution_results: list[dict[str, Any]] = []
        if args.execute:
            execution_results = execute_jobs(
                plan,
                allow_generation=args.allow_generation,
                allow_logit_diagnostic=args.allow_logit_diagnostic,
            )
        public_plan = {
            key: plan[key]
            for key in (
                "sweep_name",
                "config",
                "runner_config",
                "candidate_source_config",
                "output_root",
                "execution_backend",
                "mode_filter",
                "inventory_candidate_count",
                "executable_candidate_count",
                "skipped_candidate_count",
                "skipped_candidates",
                "job_count",
            )
        }
        public_plan["jobs"] = [
            {key: job[key] for key in (
                "candidate",
                "mode",
                "coefficients",
                "controls",
                "max_rows",
                "max_new_tokens",
                "materialized_config",
                "command",
            )}
            for job in plan["jobs"]
        ]
        public_plan["written"] = [str(path) for path in written]
        public_plan["executed"] = bool(args.execute)
        public_plan["execution_results"] = execution_results
        print(json.dumps(public_plan, indent=2, sort_keys=True))
    except SweepError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
