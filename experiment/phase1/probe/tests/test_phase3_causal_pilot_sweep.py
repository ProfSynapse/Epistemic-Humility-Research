from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_causal_pilot_aggregate as aggregate  # noqa: E402
import phase3_causal_pilot_sweep as sweep  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_build_jobs_uses_all_source_candidates_and_is_non_executing(tmp_path):
    runner_config = tmp_path / "runner.yaml"
    source_config = tmp_path / "source.yaml"
    sweep_config = tmp_path / "sweep.yaml"
    _write_yaml(runner_config, {
        "spec": {"name": "template", "status": "generation_smoke"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "output": {"root": "old", "intervention_results_allowed_by_this_spec": True},
        "candidate_directions": [{"label": "old"}],
    })
    _write_yaml(source_config, {
        "candidate_directions": [
            {
                "label": "cand_a",
                "direction_id": "direction__a",
                "direction_file": "a.safetensors",
                "layer": 35,
                "role": "delta",
            },
            {
                "label": "cand_b",
                "direction_id": "direction__b",
                "direction_file": "b.safetensors",
                "layer": 36,
                "role": "h_lora",
            },
        ],
    })
    _write_yaml(sweep_config, {
        "sweep": {
            "name": "unit_sweep",
            "runner_config": str(runner_config),
            "candidate_source_config": str(source_config),
            "output_root": str(tmp_path / "out"),
            "candidates": "all",
            "modes": [{
                "name": "logit_diagnostic",
                "max_rows": 2,
                "coefficients": [1.0, 50.0],
                "controls": [
                    "no_vector_baseline",
                    "activation_addition",
                    "activation_subtraction",
                ],
            }],
        },
    })

    plan = sweep.build_jobs(sweep_config)

    assert plan["job_count"] == 2
    assert [job["candidate"] for job in plan["jobs"]] == ["cand_a", "cand_b"]
    assert all(job["mode"] == "logit_diagnostic" for job in plan["jobs"])
    assert not (tmp_path / "out").exists()
    first_payload = plan["jobs"][0]["runner_config_payload"]
    assert first_payload["candidate_directions"][0]["label"] == "cand_a"
    assert first_payload["output"]["root"].endswith("cand_a\\logit_diagnostic") or (
        first_payload["output"]["root"].endswith("cand_a/logit_diagnostic")
    )


def test_build_jobs_applies_runner_overrides_before_materializing(tmp_path):
    runner_config = tmp_path / "runner.yaml"
    source_config = tmp_path / "source.yaml"
    sweep_config = tmp_path / "sweep.yaml"
    _write_yaml(runner_config, {
        "spec": {"name": "template", "status": "generation_smoke"},
        "model": {"enable_thinking": True},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "selection": {"max_rows_default": 16},
        "output": {"root": "old", "intervention_results_allowed_by_this_spec": True},
        "candidate_directions": [{"label": "old"}],
    })
    _write_yaml(source_config, {
        "candidate_directions": [{
            "label": "cand_a",
            "direction_id": "direction__a",
            "direction_file": "a.safetensors",
            "layer": 35,
            "role": "delta",
        }],
    })
    _write_yaml(sweep_config, {
        "sweep": {
            "name": "unit_sweep",
            "runner_config": str(runner_config),
            "candidate_source_config": str(source_config),
            "output_root": str(tmp_path / "out"),
            "candidates": "all",
            "runner_overrides": {
                "model": {"enable_thinking": False},
                "selection": {
                    "max_rows_default": 2,
                    "row_keys": ["row-a", "row-b"],
                },
            },
            "modes": [{
                "name": "logit_diagnostic",
                "max_rows": 2,
                "coefficients": [1.0],
                "controls": ["no_vector_baseline"],
            }],
        },
    })

    plan = sweep.build_jobs(sweep_config)

    payload = plan["jobs"][0]["runner_config_payload"]
    assert payload["model"]["enable_thinking"] is False
    assert payload["selection"]["max_rows_default"] == 2
    assert payload["selection"]["row_keys"] == ["row-a", "row-b"]
    assert payload["candidate_directions"][0]["label"] == "cand_a"


def test_runner_overrides_replace_label_counts_atomically(tmp_path):
    runner_config = tmp_path / "runner.yaml"
    source_config = tmp_path / "source.yaml"
    sweep_config = tmp_path / "sweep.yaml"
    _write_yaml(runner_config, {
        "spec": {"name": "template", "status": "generation_smoke"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "output": {"root": "old", "intervention_results_allowed_by_this_spec": True},
        "readiness_checks": {
            "require_extraction_manifest": {
                "status": "ok",
                "verified": True,
                "row_count": 256,
                "label_counts": {"known": 128, "unknown": 128},
            },
        },
        "candidate_directions": [{"label": "old"}],
    })
    _write_yaml(source_config, {
        "candidate_directions": [{
            "label": "cand_a",
            "direction_id": "direction__a",
            "direction_file": "a.safetensors",
            "layer": 35,
            "role": "delta",
        }],
    })
    _write_yaml(sweep_config, {
        "sweep": {
            "name": "unit_sweep",
            "runner_config": str(runner_config),
            "candidate_source_config": str(source_config),
            "output_root": str(tmp_path / "out"),
            "candidates": "all",
            "runner_overrides": {
                "readiness_checks": {
                    "require_extraction_manifest": {
                        "row_count": 32,
                        "label_counts": {"known": 32},
                    },
                },
            },
            "modes": [{
                "name": "logit_diagnostic",
                "max_rows": 2,
                "coefficients": [1.0],
                "controls": ["no_vector_baseline"],
            }],
        },
    })

    plan = sweep.build_jobs(sweep_config)

    manifest_check = plan["jobs"][0]["runner_config_payload"]["readiness_checks"][
        "require_extraction_manifest"
    ]
    assert manifest_check["status"] == "ok"
    assert manifest_check["verified"] is True
    assert manifest_check["row_count"] == 32
    assert manifest_check["label_counts"] == {"known": 32}


def test_build_jobs_reports_skipped_candidates(tmp_path):
    runner_config = tmp_path / "runner.yaml"
    source_config = tmp_path / "source.yaml"
    sweep_config = tmp_path / "sweep.yaml"
    _write_yaml(runner_config, {
        "spec": {"name": "template", "status": "generation_smoke"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "output": {"root": "old", "intervention_results_allowed_by_this_spec": True},
        "candidate_directions": [{"label": "old"}],
    })
    _write_yaml(source_config, {
        "candidate_directions": [
            {
                "label": "base",
                "direction_id": "direction__base",
                "direction_file": "base.safetensors",
                "layer": 25,
                "role": "h_base",
                "requires_adapterless_runner": True,
                "skip_by_default": True,
                "skip_reason": "adapterless base is not implemented",
            },
            {
                "label": "sft",
                "direction_id": "direction__sft",
                "direction_file": "sft.safetensors",
                "layer": 36,
                "role": "h_lora",
            },
        ],
    })
    _write_yaml(sweep_config, {
        "sweep": {
            "name": "unit_sweep",
            "runner_config": str(runner_config),
            "candidate_source_config": str(source_config),
            "output_root": str(tmp_path / "out"),
            "candidates": "all",
            "modes": [{
                "name": "generation",
                "max_rows": 2,
                "coefficients": [1.0],
                "controls": ["no_vector_baseline", "activation_addition"],
            }],
        },
    })

    plan = sweep.build_jobs(sweep_config)

    assert plan["inventory_candidate_count"] == 2
    assert plan["executable_candidate_count"] == 1
    assert plan["skipped_candidate_count"] == 1
    assert plan["skipped_candidates"] == [{
        "label": "base",
        "reason": "adapterless base is not implemented",
        "requires_adapterless_runner": True,
    }]
    assert plan["job_count"] == 1
    assert plan["jobs"][0]["candidate"] == "sft"


def test_checked_in_full_sweep_inventory_counts():
    config_path = (
        sweep.REPO_ROOT
        / "archive"
        / "experiment"
        / "phase1"
        / "probe"
        / "config"
        / "causal-pilot-core"
        / "phase3_causal_pilot_local_sweep.yaml"
    )

    plan = sweep.build_jobs(config_path)

    assert plan["inventory_candidate_count"] == 9
    assert plan["executable_candidate_count"] == 8
    assert plan["skipped_candidate_count"] == 1
    assert plan["skipped_candidates"][0]["label"] == "base_original_h_base_l25"
    assert plan["job_count"] == 16
    assert plan["execution_backend"] == "docker"
    assert {job["candidate"] for job in plan["jobs"]} == {
        "sft_h_lora_l36",
        "sft_delta_l35",
        "dpo_cold_h_lora_l35",
        "kto_cold_h_lora_l36",
        "sft_dpo_h_lora_l34",
        "sft_dpo_delta_l35",
        "sft_kto_h_lora_l35",
        "sft_kto_delta_l36",
    }
    candidate_payloads = {
        job["candidate"]: job["runner_config_payload"]["candidate_directions"][0]
        for job in plan["jobs"]
    }
    sft_dpo_delta = candidate_payloads["sft_dpo_delta_l35"]
    assert sft_dpo_delta["extraction_dir"].endswith("extraction__0d58c201ab3e")
    assert sft_dpo_delta["direction_id"] == "direction__966bd7f65768ab65"
    assert sft_dpo_delta["direction_csv"].endswith("hidden_state_candidate_directions.csv")
    assert sft_dpo_delta["direction_file"].endswith(
        "directions/direction__966bd7f65768ab65.safetensors"
    )
    assert sft_dpo_delta["role"] == "delta"
    assert sft_dpo_delta["layer"] == 35
    assert sft_dpo_delta["arm"] == "sft_dpo"
    assert sft_dpo_delta["linear_probe_balanced_accuracy"] == 0.859375


def test_checked_in_full_sweep_uses_docker_commands():
    config_path = (
        sweep.REPO_ROOT
        / "archive"
        / "experiment"
        / "phase1"
        / "probe"
        / "config"
        / "causal-pilot-core"
        / "phase3_causal_pilot_local_sweep.yaml"
    )

    plan = sweep.build_jobs(config_path)
    command = plan["jobs"][0]["command"]

    assert command[:8] == [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "--entrypoint",
        "python",
    ]
    assert "-e" in command
    assert "HF_HOME=/workspace/repo/.cache/hf" in command
    assert "HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub" in command
    assert "-v" in command
    assert any(part.endswith(":/workspace/repo") for part in command)
    assert "-w" in command
    assert "/workspace/repo" in command
    assert "unsloth/unsloth:latest" in command
    image_index = command.index("unsloth/unsloth:latest")
    runner_args = command[image_index + 1:]
    assert runner_args[0] == (
        "/workspace/repo/experiment/phase1/probe/phase3_causal_pilot_runner.py"
    )
    assert "--config" in runner_args
    config_arg = runner_args[runner_args.index("--config") + 1]
    assert config_arg.startswith(
        "/workspace/repo/experiment/phase1/probe/qwen3-4b-instruct/"
    )
    assert "\\" not in config_arg
    assert "--allow-logit-diagnostic" in runner_args
    assert all("C:\\Users" not in part for part in command)


def test_docker_runner_config_rewrites_repo_paths_for_container():
    repo_root = sweep.REPO_ROOT
    config = sweep.build_runner_config(
        template_config={
            "spec": {"name": "template"},
            "runtime_model": {
                "adapter_path": str(repo_root / "experiment" / "phase1" / "runs" / "adapter"),
            },
            "selection": {
                "probe_results": str(
                    repo_root / "experiment" / "phase1" / "probe" / "qwen3-4b-instruct" / "probe_results.jsonl"
                ),
            },
            "output": {"root": "old"},
        },
        candidate={
            "label": "cand_a",
            "direction_id": "direction__a",
            "direction_file": str(
                repo_root / "experiment" / "phase1" / "probe" / "qwen3-4b-instruct" / "hidden_states" / "dir.safetensors"
            ),
            "direction_csv": "experiment/phase1/probe/qwen3-4b-instruct/hidden_states/directions.csv",
            "direction_manifest": str(
                repo_root / "experiment" / "phase1" / "probe" / "qwen3-4b-instruct" / "hidden_states" / "manifest.json"
            ),
            "extraction_dir": str(
                repo_root / "experiment" / "phase1" / "probe" / "qwen3-4b-instruct" / "hidden_states"
            ),
            "extraction_manifest": "experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction_manifest.json",
        },
        output_root=repo_root / "experiment" / "phase1" / "probe" / "out",
        sweep_name="unit_sweep",
        mode="logit_diagnostic",
        execution={
            "backend": "docker",
            "docker": {"repo_mount": "/workspace/repo"},
        },
    )

    encoded = yaml.safe_dump(config, sort_keys=True)

    assert config["output"]["root"] == "/workspace/repo/experiment/phase1/probe/out/cand_a/logit_diagnostic"
    assert config["runtime_model"]["adapter_path"] == "/workspace/repo/experiment/phase1/runs/adapter"
    assert config["selection"]["probe_results"].startswith("/workspace/repo/experiment/")
    candidate = config["candidate_directions"][0]
    assert candidate["direction_file"].startswith("/workspace/repo/experiment/")
    assert candidate["direction_csv"].startswith("/workspace/repo/experiment/")
    assert candidate["direction_manifest"].startswith("/workspace/repo/experiment/")
    assert candidate["extraction_dir"].startswith("/workspace/repo/experiment/")
    assert candidate["extraction_manifest"].startswith("/workspace/repo/experiment/")
    assert str(repo_root) not in encoded
    assert f"/workspace/repo/{str(repo_root)}" not in encoded
    assert "\\" not in encoded


def test_checked_in_full_sweep_mode_filter_limits_to_logit_diagnostic():
    config_path = (
        sweep.REPO_ROOT
        / "archive"
        / "experiment"
        / "phase1"
        / "probe"
        / "config"
        / "causal-pilot-core"
        / "phase3_causal_pilot_local_sweep.yaml"
    )

    plan = sweep.build_jobs(config_path, mode_filter={"logit_diagnostic"})

    assert plan["mode_filter"] == ["logit_diagnostic"]
    assert plan["job_count"] == 8
    assert {job["mode"] for job in plan["jobs"]} == {"logit_diagnostic"}
    assert all("--allow-logit-diagnostic" in job["command"] for job in plan["jobs"])
    assert all("--allow-generation" not in job["command"] for job in plan["jobs"])
    assert all("__generation.yaml" not in job["materialized_config"] for job in plan["jobs"])


def test_mode_filter_parses_repeated_and_comma_separated_values():
    assert sweep.parse_mode_filter(["logit_diagnostic,generation"]) == {
        "logit_diagnostic",
        "generation",
    }
    assert sweep.parse_mode_filter(["logit_diagnostic", "generation"]) == {
        "logit_diagnostic",
        "generation",
    }


def test_mode_filter_fails_when_no_configured_mode_matches(tmp_path):
    runner_config = tmp_path / "runner.yaml"
    source_config = tmp_path / "source.yaml"
    sweep_config = tmp_path / "sweep.yaml"
    _write_yaml(runner_config, {
        "spec": {"name": "template", "status": "generation_smoke"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "output": {"root": "old", "intervention_results_allowed_by_this_spec": True},
        "candidate_directions": [{"label": "old"}],
    })
    _write_yaml(source_config, {
        "candidate_directions": [{
            "label": "cand_a",
            "direction_id": "direction__a",
            "direction_file": "a.safetensors",
            "layer": 35,
            "role": "delta",
        }],
    })
    _write_yaml(sweep_config, {
        "sweep": {
            "name": "unit_sweep",
            "runner_config": str(runner_config),
            "candidate_source_config": str(source_config),
            "output_root": str(tmp_path / "out"),
            "candidates": "all",
            "modes": [{
                "name": "generation",
                "max_rows": 2,
                "coefficients": [1.0],
                "controls": ["no_vector_baseline", "activation_addition"],
            }],
        },
    })

    with pytest.raises(sweep.SweepError, match="matched no configured modes"):
        sweep.build_jobs(sweep_config, mode_filter={"logit_diagnostic"})


def test_write_plan_and_materialize_configs_are_explicit(tmp_path):
    plan = {
        "sweep_name": "unit_sweep",
        "config": "sweep.yaml",
        "runner_config": "runner.yaml",
        "candidate_source_config": "source.yaml",
        "output_root": str(tmp_path / "out"),
        "execution_backend": "host",
        "mode_filter": None,
        "inventory_candidate_count": 1,
        "executable_candidate_count": 1,
        "skipped_candidate_count": 0,
        "skipped_candidates": [],
        "job_count": 1,
        "jobs": [{
            "candidate": "cand_a",
            "mode": "generation",
            "execution_backend": "host",
            "coefficients": [1.0],
            "controls": ["no_vector_baseline", "activation_addition"],
            "max_rows": 2,
            "max_new_tokens": 8,
            "materialized_config": str(tmp_path / "out" / "_sweep_configs" / "cand_a.yaml"),
            "command": ["python", "runner.py"],
            "runner_config_payload": {"candidate_directions": [{"label": "cand_a"}]},
        }],
    }

    written_plan = sweep.write_plan(plan)
    written_configs = sweep.materialize_configs(plan)

    assert [path.name for path in written_plan] == [
        "sweep_manifest.json",
        "planned_commands.jsonl",
    ]
    assert written_configs[0].is_file()
    row = json.loads((tmp_path / "out" / "planned_commands.jsonl").read_text(encoding="utf-8"))
    assert row["candidate"] == "cand_a"
    assert "runner_config_payload" not in row


def test_execute_jobs_persists_logs_and_results_on_success(tmp_path, monkeypatch):
    plan = {
        "output_root": str(tmp_path / "out"),
        "jobs": [
            {
                "candidate": "cand_a",
                "mode": "logit_diagnostic",
                "execution_backend": "host",
                "materialized_config": str(tmp_path / "out" / "_sweep_configs" / "cand_a.yaml"),
                "command": ["python", "runner.py", "--candidate", "cand_a"],
                "runner_config_payload": {"candidate_directions": [{"label": "cand_a"}]},
            },
            {
                "candidate": "cand_b",
                "mode": "generation",
                "execution_backend": "host",
                "materialized_config": str(tmp_path / "out" / "_sweep_configs" / "cand_b.yaml"),
                "command": ["python", "runner.py", "--candidate", "cand_b"],
                "runner_config_payload": {"candidate_directions": [{"label": "cand_b"}]},
            },
        ],
    }

    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        idx = len(calls)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=f"stdout {idx}\n",
            stderr=f"stderr {idx}\n",
        )

    monkeypatch.setattr(sweep.subprocess, "run", fake_run)

    results = sweep.execute_jobs(
        plan,
        allow_generation=True,
        allow_logit_diagnostic=True,
    )

    assert calls == [job["command"] for job in plan["jobs"]]
    assert len(results) == 2
    log_dir = tmp_path / "out" / "_execution_logs"
    assert (log_dir / "000__cand_a__logit_diagnostic.stdout.log").read_text(encoding="utf-8") == "stdout 1\n"
    assert (log_dir / "000__cand_a__logit_diagnostic.stderr.log").read_text(encoding="utf-8") == "stderr 1\n"
    assert (log_dir / "001__cand_b__generation.stdout.log").read_text(encoding="utf-8") == "stdout 2\n"
    rows = [
        json.loads(line)
        for line in (log_dir / "execution_results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [row["candidate"] for row in rows] == ["cand_a", "cand_b"]
    assert rows[0]["stdout_log_path"] == results[0]["stdout_log_path"]
    assert rows[0]["stderr_log_path"] == results[0]["stderr_log_path"]
    assert rows[0]["execution_results_path"] == results[0]["execution_results_path"]


def test_execute_jobs_persists_completed_and_failed_rows_then_stops(tmp_path, monkeypatch):
    plan = {
        "output_root": str(tmp_path / "out"),
        "jobs": [
            {
                "candidate": "cand_a",
                "mode": "logit_diagnostic",
                "execution_backend": "host",
                "materialized_config": str(tmp_path / "out" / "_sweep_configs" / "cand_a.yaml"),
                "command": ["python", "runner.py", "--candidate", "cand_a"],
                "runner_config_payload": {"candidate_directions": [{"label": "cand_a"}]},
            },
            {
                "candidate": "cand_b",
                "mode": "logit_diagnostic",
                "execution_backend": "host",
                "materialized_config": str(tmp_path / "out" / "_sweep_configs" / "cand_b.yaml"),
                "command": ["python", "runner.py", "--candidate", "cand_b"],
                "runner_config_payload": {"candidate_directions": [{"label": "cand_b"}]},
            },
            {
                "candidate": "cand_c",
                "mode": "logit_diagnostic",
                "execution_backend": "host",
                "materialized_config": str(tmp_path / "out" / "_sweep_configs" / "cand_c.yaml"),
                "command": ["python", "runner.py", "--candidate", "cand_c"],
                "runner_config_payload": {"candidate_directions": [{"label": "cand_c"}]},
            },
        ],
    }

    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if len(calls) == 2:
            return subprocess.CompletedProcess(
                command,
                9,
                stdout="second stdout\n",
                stderr="second stderr\n",
            )
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="first stdout\n",
            stderr="first stderr\n",
        )

    monkeypatch.setattr(sweep.subprocess, "run", fake_run)

    with pytest.raises(sweep.SweepError, match="runner failed for candidate=cand_b"):
        sweep.execute_jobs(
            plan,
            allow_generation=False,
            allow_logit_diagnostic=True,
        )

    assert calls == [job["command"] for job in plan["jobs"][:2]]
    log_dir = tmp_path / "out" / "_execution_logs"
    rows = [
        json.loads(line)
        for line in (log_dir / "execution_results.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [(row["candidate"], row["returncode"]) for row in rows] == [
        ("cand_a", 0),
        ("cand_b", 9),
    ]
    assert (log_dir / "001__cand_b__logit_diagnostic.stdout.log").read_text(encoding="utf-8") == "second stdout\n"
    assert (log_dir / "001__cand_b__logit_diagnostic.stderr.log").read_text(encoding="utf-8") == "second stderr\n"
    assert not (log_dir / "002__cand_c__logit_diagnostic.stdout.log").exists()


def test_aggregate_collects_generation_and_logit_metrics(tmp_path):
    run_a = tmp_path / "cand_a" / "generation" / "run_1"
    run_a.mkdir(parents=True)
    (run_a / "metrics.json").write_text(
        json.dumps({"arm_a": {"truthful_rate": 50.0}}),
        encoding="utf-8",
    )
    (run_a / "run_manifest.json").write_text(
        json.dumps({
            "candidate": {"label": "cand_a", "direction_id": "direction__a", "layer": 35},
            "row_count": 2,
            "arm_count": 1,
            "config_sha": "abc",
            "outputs": {"metrics": str(run_a / "metrics.json")},
        }),
        encoding="utf-8",
    )
    run_b = tmp_path / "cand_b" / "logit_diagnostic" / "run_1"
    run_b.mkdir(parents=True)
    (run_b / "logit_metrics.json").write_text(
        json.dumps({"arm_b": {"top1_changed_rate": 25.0}}),
        encoding="utf-8",
    )
    (run_b / "run_manifest.json").write_text(
        json.dumps({
            "logit_diagnostic_executed": True,
            "candidate": {"label": "cand_b", "direction_id": "direction__b", "layer": 36},
            "row_count": 4,
            "arm_count": 1,
            "config_sha": "def",
            "outputs": {"logit_metrics": str(run_b / "logit_metrics.json")},
        }),
        encoding="utf-8",
    )

    rows = aggregate.collect_rows(tmp_path)

    assert len(rows) == 2
    assert {row["mode"] for row in rows} == {"generation", "logit_diagnostic"}
    assert rows[0]["candidate_label"] == "cand_a"
    assert rows[1]["top1_changed_rate"] == 25.0


def test_aggregate_resolves_docker_manifest_output_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(aggregate, "REPO_ROOT", tmp_path)
    run_dir = tmp_path / "experiment" / "phase1" / "probe" / "out" / "cand_a" / "logit_diagnostic" / "run_1"
    run_dir.mkdir(parents=True)
    metrics_path = run_dir / "logit_metrics.json"
    metrics_path.write_text(
        json.dumps({"arm_a": {"top1_changed_rate": 12.5}}),
        encoding="utf-8",
    )
    container_metrics_path = (
        "/workspace/repo/"
        + metrics_path.relative_to(tmp_path).as_posix()
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps({
            "logit_diagnostic_executed": True,
            "candidate": {"label": "cand_a", "direction_id": "direction__a", "layer": 35},
            "row_count": 4,
            "arm_count": 1,
            "config_sha": "abc",
            "outputs": {"logit_metrics": container_metrics_path},
        }),
        encoding="utf-8",
    )

    rows = aggregate.collect_rows(tmp_path / "experiment" / "phase1" / "probe" / "out")

    assert len(rows) == 1
    assert rows[0]["candidate_label"] == "cand_a"
    assert rows[0]["mode"] == "logit_diagnostic"
    assert rows[0]["top1_changed_rate"] == 12.5
