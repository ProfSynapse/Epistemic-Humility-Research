from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


MODULE_PATH = Path(__file__).with_name("prepare_stage_s.py")
SPEC = importlib.util.spec_from_file_location("prepare_stage_s", MODULE_PATH)
assert SPEC and SPEC.loader
stager = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = stager
SPEC.loader.exec_module(stager)

EXPECTED_IMAGE = (
    "unsloth/unsloth@sha256:"
    "0e57d91e2d61539e9d144949fd0629d9f91e93c86a8bf46a2003f3a999cc3133"
)
EXPECTED_PIP = [
    "unsloth==2026.4.2",
    "unsloth_zoo==2026.4.2",
    "torch==2.9.0",
    "transformers==5.5.0",
    "peft==0.18.1",
    "trl==0.24.0",
    "bitsandbytes==0.49.2",
    "huggingface_hub==1.9.0",
    "safetensors==0.5.2",
    "datasets==4.3.0",
    "accelerate==1.4.0",
]
EXPECTED_TRAINING = {
    "batch_size": 2,
    "gradient_accumulation": 4,
    "learning_rate": 0.0002,
    "num_epochs": 1,
    "max_seq_length": 2048,
    "save_steps": 500,
    "save_total_limit": 2,
    "chat_template_kwargs": {"enable_thinking": False},
}
EXPECTED_LORA = {
    "r": 32,
    "alpha": 64,
    "dropout": 0.05,
    "target_modules": [
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
}
DIRECT_SFT_CONFIG = {
    "model": {
        "model_name": "example/Default",
        "max_seq_length": 1024,
        "dtype": None,
        "load_in_4bit": True,
    },
    "lora": {
        "r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.0,
        "bias": "none",
        "target_modules": ["q_proj"],
        "use_gradient_checkpointing": "unsloth",
        "random_state": 3407,
        "use_rslora": False,
        "use_dora": False,
    },
    "training": {
        "output_dir": "./sft_output",
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 1,
        "learning_rate": 0.001,
        "max_grad_norm": 1.0,
        "lr_scheduler_type": "linear",
        "max_seq_length": 1024,
        "packing": False,
        "completion_only_loss": True,
        "assistant_only_loss": False,
        "gradient_checkpointing": True,
        "optim": "adamw_8bit",
        "fp16": False,
        "bf16": True,
        "num_train_epochs": 1,
        "warmup_ratio": 0.0,
        "logging_steps": 1,
        "save_steps": 10,
        "save_total_limit": 1,
        "dataloader_num_workers": 0,
        "dataloader_pin_memory": False,
        "group_by_length": False,
        "eval_strategy": "no",
        "eval_steps": 10,
    },
    "dataset": {
        "dataset_name": "example/default",
        "dataset_file": "default.jsonl",
        "local_file": None,
        "num_proc": 1,
        "test_size": 0.1,
        "split_dataset": False,
        "filter_desirable": False,
    },
    "wandb": {"enabled": True, "project": "old", "run_name": "old", "entity": "old"},
    "seed": 42,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_tuner(path: Path) -> str:
    path.mkdir(parents=True)
    (path / ".gitignore").write_text("scratch/\n", encoding="utf-8")
    (path / "trainer.py").write_text("# synthetic tuner\n", encoding="utf-8")
    direct_config = path / "Trainers" / "sft" / "configs" / "config.yaml"
    direct_config.parent.mkdir(parents=True)
    direct_config.write_text(yaml.safe_dump(DIRECT_SFT_CONFIG, sort_keys=False), encoding="utf-8")
    modal_wrapper = path / "Trainers" / "cloud" / "train_modal.py"
    modal_wrapper.parent.mkdir(parents=True)
    modal_wrapper.write_text("# synthetic Modal wrapper\n", encoding="utf-8")
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "tests@example.invalid")
    _git(path, "config", "user.name", "Stage Tests")
    _git(path, "remote", "add", "origin", "https://example.invalid/synthetic.git")
    _git(
        path,
        "add",
        ".gitignore",
        "trainer.py",
        "Trainers/sft/configs/config.yaml",
        "Trainers/cloud/train_modal.py",
    )
    _git(path, "commit", "-q", "-m", "fixture")
    return _git(path, "rev-parse", "HEAD")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _fixture(tmp_path: Path) -> dict:
    project = tmp_path / "project"
    experiment = project / "experiments" / "synthetic-stage-s"
    dataset = experiment / "analysis" / "dataset"
    tuner = tmp_path / "tuner"
    tuner_commit = _init_tuner(tuner)
    raw_marker = "PRIVATE-ROW-MARKER-DO-NOT-LEAK"
    # Prefix-related strings are intentional: longest-match selection must
    # preserve arbitrary configured special tokens without banning them.
    renamed_tokens = ["<ROUTE>", "<ROUTE>_BLUE", "<ROUTE>_BLUE_DEEP"]
    renamed_modes = ["BLUE_ROUTE", "AMBER_ROUTE", "GRAY_ROUTE"]

    train_rows = []
    for within_mode_index in range(3):
        for mode, token in zip(renamed_modes, renamed_tokens, strict=True):
            row_index = len(train_rows)
            user_content = raw_marker if row_index == 0 else f"private train {row_index}"
            train_rows.append(
                {
                    "conversations": [
                        {"role": "system", "content": "synthetic"},
                        {"role": "user", "content": user_content},
                        {"role": "assistant", "content": token + '{"answer":"private"}'},
                    ],
                    "metadata": {
                        "row_key": f"private-row-{row_index:02d}",
                        "mode_label": mode,
                    },
                }
            )

    split_rows = {
        "train": train_rows,
        "dev": [{"conversations": [{"role": "user", "content": "private dev"}]}],
        "heldout": [{"conversations": [{"role": "user", "content": "private heldout"}]}],
    }
    split_config = {}
    aggregate_outputs = {}
    for split, rows in split_rows.items():
        path = dataset / f"{split}.jsonl"
        _write_jsonl(path, rows)
        split_config[split] = {"file": path.name, "rows": len(rows), "sha256": _sha(path)}
        aggregate_outputs[split] = {
            "file": path.name,
            "rows": len(rows),
            "sha256": _sha(path),
        }
    aggregate = dataset / "aggregate_manifest.json"
    aggregate.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "outputs": aggregate_outputs,
                "mode_counts": {mode: 3 for mode in renamed_modes},
                "identity_overlap_across_splits": 0,
                "normalized_question_overlap_across_splits": 0,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    hf_cache = tmp_path / "hf" / "hub"
    revision = "a" * 40
    snapshot = hf_cache / "models--example--Synthetic-4B" / "snapshots" / revision
    snapshot.mkdir(parents=True)
    (snapshot / "tokenizer.json").write_text("synthetic tokenizer", encoding="utf-8")
    (snapshot / "config.json").write_text("synthetic config", encoding="utf-8")

    template = {
        "name": "pending_render",
        "target": "local",
        "method": "sft",
        "provider": "local_docker",
        "job": {"image": EXPECTED_IMAGE, "pull_policy": "missing"},
        "setup": {"pip": EXPECTED_PIP},
        "run": {
            "method": "sft",
            "trainer": "Trainers/sft/train_sft.py",
            "dry_run": True,
            "dashboard": False,
        },
        "model": {"load_in_4bit": True, "dtype": None},
        "dataset": {},
        "training": EXPECTED_TRAINING,
        "lora": EXPECTED_LORA,
        "artifacts": {},
    }
    experiment.mkdir(parents=True, exist_ok=True)
    template_path = experiment / "stage_sft_recipe.yaml"
    template_path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")

    config = {
        "schema_version": 1,
        "experiment": "synthetic-stage-s",
        "launch_authorized": False,
        "private_dataset": {
            "directory": "analysis/dataset",
            "aggregate_manifest": {
                "file": aggregate.name,
                "sha256": _sha(aggregate),
            },
            "splits": split_config,
        },
        "model": {
            "repo": "example/Synthetic-4B",
            "revision": revision,
            "load_in_4bit": True,
            "dtype": None,
            "required_snapshot_files": {
                "tokenizer.json": _sha(snapshot / "tokenizer.json"),
                "config.json": _sha(snapshot / "config.json"),
            },
            "tokenizer": {
                "additional_special_tokens": renamed_tokens,
                "existing_token_policy": "error",
                "initialization": "mean_existing_rows",
                "train_new_embedding_rows": True,
                "train_new_lm_head_rows": True,
                "verify_tokenizer_roundtrip": True,
                "verify_adapter_roundtrip": True,
                "verify_merged_model_roundtrip": False,
                "merged_model_save_method": "merged_4bit_forced",
            },
        },
        "modal": {
            "input_volume": "synthetic-private-inputs",
            "input_mount": "/vol/inputs",
            "output_volume": "synthetic-artifacts",
            "output_mount": "/vol/artifacts",
            "cache_volume": "synthetic-cache",
            "gpu": "A10G",
            "timeout_hours": 2.0,
        },
        "tuner": {
            "expected_commit": tuner_commit,
            "staging_root": "scratch/eh_staging",
            "recipe_template": template_path.name,
            "rendered_recipe_file": "stage_sft_recipe.yaml",
            "require_clean_worktree": True,
        },
    }
    config_path = experiment / "stage_s.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return {
        "project": project,
        "experiment": experiment,
        "dataset": dataset,
        "tuner": tuner,
        "tuner_commit": tuner_commit,
        "hf_cache": hf_cache,
        "config": config,
        "config_path": config_path,
        "raw_marker": raw_marker,
        "renamed_tokens": renamed_tokens,
        "renamed_modes": renamed_modes,
    }


def _synthetic_modal_plan(context: dict, run_id: str, config_path: Path, dataset_path: Path) -> dict:
    recipe = context["recipe"]
    modal = context["config"]["modal"]
    config_mount = f"/vol/inputs/{run_id}/{config_path.name}"
    dataset_mount = f"/vol/inputs/{run_id}/{dataset_path.name}"
    return {
        "schema_version": 1,
        "inspection_only": True,
        "source": {
            "repo_url": context["tuner"]["repo_url"],
            "branch": context["tuner"]["branch"],
            "commit": context["tuner"]["commit"],
        },
        "runtime": {
            "image": recipe["job"]["image"],
            "pip_packages": list(recipe["setup"]["pip"]),
            "gpu": modal["gpu"],
            "timeout_hours": modal["timeout_hours"],
        },
        "inputs": {
            "volume_name": modal["input_volume"],
            "mount_path": modal["input_mount"],
            "config": {
                "volume_path": f"{run_id}/{config_path.name}",
                "mounted_path": config_mount,
                "sha256": _sha(config_path),
                "bytes": config_path.stat().st_size,
            },
            "dataset": {
                "volume_path": f"{run_id}/{dataset_path.name}",
                "mounted_path": dataset_mount,
                "sha256": _sha(dataset_path),
                "bytes": dataset_path.stat().st_size,
            },
        },
        "artifacts": {
            "backend": "modal_volume",
            "volume_name": modal["output_volume"],
            "mount_path": modal["output_mount"],
            "canonical_root": "/vol/artifacts/outputs/runs/modal/sft",
            "publish_final_model": False,
        },
        "launch": {
            "environment": {
                "MODAL_TRAINING_IMAGE": recipe["job"]["image"],
                "MODAL_TRAINING_PIP_PACKAGES_JSON": json.dumps(
                    recipe["setup"]["pip"], separators=(",", ":")
                ),
                "MODAL_GPU": modal["gpu"],
                "MODAL_TIMEOUT_SECONDS": str(int(modal["timeout_hours"] * 3600)),
                "MODAL_INPUT_VOLUME_NAME": modal["input_volume"],
                "MODAL_INPUT_MOUNT_PATH": modal["input_mount"],
                "MODAL_CACHE_VOLUME_NAME": modal["cache_volume"],
                "MODAL_OUTPUT_VOLUME_NAME": modal["output_volume"],
                "MODAL_OUTPUT_MOUNT_PATH": modal["output_mount"],
            },
            "argv": [
                "modal",
                "run",
                "--detach",
                f"{context['tuner']['root'] / 'Trainers' / 'cloud' / 'train_modal.py'}::run_training",
                "--trainer-type",
                "sft",
                "--repo-url",
                context["tuner"]["repo_url"],
                "--repo-branch",
                context["tuner"]["branch"],
                "--repo-commit",
                context["tuner"]["commit"],
                "--config-path",
                config_mount,
                "--config-sha256",
                _sha(config_path),
                "--dataset-sha256",
                _sha(dataset_path),
            ],
            "verification": {
                "require_nonempty_app_id_from_submission": True,
                "require_remote_function": "run_training",
                "require_running_or_completed_task": True,
                "commands": [
                    ["modal", "app", "list", "--json"],
                    ["modal", "app", "logs", "<app-id>"],
                ],
            },
        },
    }


def _source_snapshot(experiment: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(experiment)): path.read_bytes()
        for path in sorted(experiment.rglob("*"))
        if path.is_file() and "analysis" not in path.relative_to(experiment).parts
    }


def _block_codes(report: dict) -> set[str]:
    return {blocker["code"] for blocker in report["blockers"]}


def test_stage_uses_arbitrary_tokens_and_never_writes_private_rows_to_source(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    before = _source_snapshot(fixture["experiment"])
    report, context = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
        run_id="renamed-tokens",
    )
    assert report["ready_to_stage"] is True
    assert context["recipe"]["model"]["tokenizer"]["additional_special_tokens"] == fixture["renamed_tokens"]
    assert context["recipe"]["model"]["revision"] == fixture["config"]["model"]["revision"]
    result = stager.stage(context, "renamed-tokens")
    assert result["launch_authorized"] is False
    staged = fixture["tuner"] / result["relative_directory"]
    rendered = yaml.safe_load((staged / "stage_sft_recipe.yaml").read_text(encoding="utf-8"))
    assert rendered["model"]["tokenizer"]["additional_special_tokens"] == fixture["renamed_tokens"]
    assert rendered["model"]["tokenizer"]["verify_merged_model_roundtrip"] is False
    assert rendered["model"]["tokenizer"]["merged_model_save_method"] == "merged_4bit_forced"
    assert rendered["model"]["load_in_4bit"] is True
    assert rendered["model"]["dtype"] is None
    assert rendered["job"]["image"] == EXPECTED_IMAGE
    assert rendered["setup"]["pip"] == EXPECTED_PIP
    assert rendered["training"] == EXPECTED_TRAINING
    assert rendered["lora"] == EXPECTED_LORA
    assert rendered["run"]["dry_run"] is True
    assert "pending_pre_sign" not in yaml.safe_dump(rendered)
    assert fixture["raw_marker"] in (staged / "train.jsonl").read_text(encoding="utf-8")
    assert _source_snapshot(fixture["experiment"]) == before
    for relative, content in before.items():
        assert fixture["raw_marker"].encode() not in content, relative
    assert _git(fixture["tuner"], "status", "--porcelain") == ""


def test_modal_smoke_package_is_balanced_deterministic_and_private(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    before = _source_snapshot(fixture["experiment"])
    report, context = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
        run_id="modal-smoke",
    )
    assert report["ready_to_stage"] is True
    assert fixture["renamed_tokens"][1].startswith(fixture["renamed_tokens"][0])
    assert fixture["renamed_tokens"][2].startswith(fixture["renamed_tokens"][1])

    first_rows, first_mapping, first_selection = stager.select_smoke_rows(
        context["dataset"]["splits"]["train"]["path"],
        context["dataset"]["splits"]["train"]["sha256"],
        fixture["renamed_tokens"],
        2,
        expected_modes=fixture["renamed_modes"],
    )
    second_rows, second_mapping, second_selection = stager.select_smoke_rows(
        context["dataset"]["splits"]["train"]["path"],
        context["dataset"]["splits"]["train"]["sha256"],
        fixture["renamed_tokens"],
        2,
        expected_modes=fixture["renamed_modes"],
    )
    assert first_rows == second_rows
    assert first_mapping == second_mapping
    assert first_selection == second_selection
    assert first_mapping == dict(zip(fixture["renamed_modes"], fixture["renamed_tokens"], strict=True))

    monkeypatch.setattr(stager, "inspect_modal_plan", _synthetic_modal_plan)
    result = stager.stage_smoke(context, "modal-smoke", rows_per_mode=2)
    assert result["launch_authorized"] is False
    staged = fixture["tuner"] / result["relative_directory"]
    assert {path.name for path in staged.iterdir()} == {
        "smoke_manifest.json",
        "smoke_sft.yaml",
        "smoke_train.jsonl",
    }

    smoke_rows = [
        json.loads(line)
        for line in (staged / "smoke_train.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    smoke_modes = [row["metadata"]["mode_label"] for row in smoke_rows]
    assert smoke_modes == fixture["renamed_modes"] * 2

    trainer = yaml.safe_load((staged / "smoke_sft.yaml").read_text(encoding="utf-8"))
    assert trainer["model"]["model_name"] == fixture["config"]["model"]["repo"]
    assert trainer["model"]["revision"] == fixture["config"]["model"]["revision"]
    expected_smoke_tokenizer = dict(fixture["config"]["model"]["tokenizer"])
    expected_smoke_tokenizer["verify_merged_model_roundtrip"] = True
    assert trainer["model"]["tokenizer"] == expected_smoke_tokenizer
    assert trainer["model"]["tokenizer"]["merged_model_save_method"] == "merged_4bit_forced"
    assert trainer["model"]["load_in_4bit"] is True
    assert trainer["model"]["dtype"] is None
    assert trainer["training"]["max_steps"] == 2
    assert trainer["training"]["output_dir"] == "/vol/artifacts/outputs"
    assert trainer["dataset"]["local_file"] == "/vol/inputs/modal-smoke/smoke_train.jsonl"
    assert trainer["wandb"] == {
        "enabled": False,
        "project": None,
        "run_name": None,
        "entity": None,
    }

    manifest_text = (staged / "smoke_manifest.json").read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    assert fixture["raw_marker"] not in manifest_text
    assert manifest["source_train"] == {
        "sha256": context["dataset"]["splits"]["train"]["sha256"],
        "rows": 9,
    }
    assert manifest["tuner_commit"] == fixture["tuner_commit"]
    assert manifest["trainer_config_sha256"] == _sha(staged / "smoke_sft.yaml")
    assert manifest["selection"]["row_count"] == 6
    assert [
        item["row_identifier"] for item in manifest["selection"]["selected_rows_in_file_order"]
    ] == [row["metadata"]["row_key"] for row in smoke_rows]
    assert manifest["runtime"]["input_mount"] == "/vol/inputs"
    assert manifest["runtime"]["output_root"] == "/vol/artifacts/outputs"
    assert manifest["runtime"]["max_steps"] == 2
    assert manifest["runtime"]["wandb_enabled"] is False
    assert manifest["runtime"]["hub_publication_enabled"] is False
    assert manifest["stage_sft_recipe"] == {
        "file": "stage_sft_recipe.yaml",
        "sha256": _sha(fixture["experiment"] / "stage_sft_recipe.yaml"),
        "immutable_runtime_image": EXPECTED_IMAGE,
        "exact_dependency_pins": EXPECTED_PIP,
        "model": {"load_in_4bit": True, "dtype": None},
    }
    inspected = manifest["modal_inspected_plan_contract"]
    assert inspected["runtime"]["image"] == EXPECTED_IMAGE
    assert inspected["runtime"]["pip_packages"] == EXPECTED_PIP
    assert all(inspected["comparisons"].values())
    contract_without_sha = dict(inspected)
    contract_sha = contract_without_sha.pop("sha256")
    assert contract_sha == hashlib.sha256(
        stager.canonical_json(contract_without_sha).encode("utf-8")
    ).hexdigest()
    assert manifest["required_postconditions"] == [
        "configured_token_ids_stable_after_tokenizer_save_reload",
        "adapter_only_save_reload_matches_complete_adapter_state",
        "merge_save_reload_uses_pinned_base_revision",
        "adapter_artifact_contains_no_full_vocabulary_tensors",
    ]
    assert _source_snapshot(fixture["experiment"]) == before
    assert _git(fixture["tuner"], "status", "--porcelain") == ""


def test_modal_smoke_requires_train_rows_for_every_configured_mode(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    report, context = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
        run_id="missing-mode",
    )
    assert report["ready_to_stage"] is True
    train_path = context["dataset"]["splits"]["train"]["path"]
    retained = [
        json.loads(line)
        for line in train_path.read_text(encoding="utf-8").splitlines()
        if not json.loads(line)["conversations"][-1]["content"].startswith(
            fixture["renamed_tokens"][-1]
        )
    ]
    _write_jsonl(train_path, retained)
    try:
        stager.select_smoke_rows(
            train_path,
            _sha(train_path),
            fixture["renamed_tokens"],
            1,
            expected_modes=fixture["renamed_modes"],
        )
    except stager.PreflightError as exc:
        assert "every configured mode" in str(exc)
    else:
        raise AssertionError("missing configured mode did not fail closed")


def test_modal_smoke_rejects_inspected_runtime_contract_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _fixture(tmp_path)
    report, context = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
        run_id="runtime-drift",
    )
    assert report["ready_to_stage"] is True

    def mismatched_plan(context, run_id, config_path, dataset_path):
        plan = _synthetic_modal_plan(context, run_id, config_path, dataset_path)
        plan["runtime"]["pip_packages"] = ["different==1.0"]
        return plan

    monkeypatch.setattr(stager, "inspect_modal_plan", mismatched_plan)
    with pytest.raises(stager.PreflightError, match="dependency pins differ"):
        stager.stage_smoke(context, "runtime-drift", rows_per_mode=1)
    assert not (fixture["tuner"] / "scratch" / "eh_staging" / "runtime-drift").exists()


def _mutate_launch_contract(plan: dict, mutation: str) -> None:
    environment = plan["launch"]["environment"]
    argv = plan["launch"]["argv"]
    verification = plan["launch"]["verification"]
    if mutation == "schema_version":
        plan["schema_version"] = True
    elif mutation == "inspection_only":
        plan["inspection_only"] = False
    elif mutation == "runtime_gpu":
        plan["runtime"]["gpu"] = "L40S"
    elif mutation == "runtime_timeout":
        plan["runtime"]["timeout_hours"] = 3.0
    elif mutation == "source_repo_url":
        plan["source"]["repo_url"] = "https://example.invalid/other.git"
    elif mutation == "source_branch":
        plan["source"]["branch"] = "other"
    elif mutation == "source_commit":
        plan["source"]["commit"] = "b" * 40
    elif mutation == "input_volume":
        plan["inputs"]["volume_name"] = "other-inputs"
    elif mutation == "input_mount":
        plan["inputs"]["mount_path"] = "/other/inputs"
    elif mutation == "output_backend":
        plan["artifacts"]["backend"] = "local"
    elif mutation == "output_volume":
        plan["artifacts"]["volume_name"] = "other-outputs"
    elif mutation == "output_mount":
        plan["artifacts"]["mount_path"] = "/other/outputs"
    elif mutation == "output_root":
        plan["artifacts"]["canonical_root"] = "/other/root"
    elif mutation == "publication":
        plan["artifacts"]["publish_final_model"] = True
    elif mutation.startswith("environment:"):
        environment[mutation.partition(":")[2]] = "mutated"
    elif mutation == "argv_detach":
        argv[2] = "--interactive"
    elif mutation == "argv_target":
        argv[3] = "train_modal.py::other_function"
    elif mutation.startswith("argv:"):
        flag = mutation.partition(":")[2]
        argv[argv.index(flag) + 1] = "mutated"
    elif mutation == "verification_app_id":
        verification["require_nonempty_app_id_from_submission"] = False
    elif mutation == "verification_function":
        verification["require_remote_function"] = "other_function"
    elif mutation == "verification_task":
        verification["require_running_or_completed_task"] = False
    elif mutation == "verification_commands":
        verification["commands"] = [["modal", "app", "list"]]
    else:
        raise AssertionError(f"unknown test mutation: {mutation}")


@pytest.mark.parametrize(
    ("mutation", "expected_failure"),
    [
        ("schema_version", "schema_version_is_one"),
        ("inspection_only", "inspection_only_is_true"),
        ("runtime_gpu", "runtime_gpu_matches_stage_s"),
        ("runtime_timeout", "runtime_timeout_matches_stage_s"),
        ("source_repo_url", "source_repo_url_matches_tuner"),
        ("source_branch", "source_branch_matches_tuner"),
        ("source_commit", "tuner_commit_matches_package"),
        ("input_volume", "input_volume_matches_stage_s"),
        ("input_mount", "input_mount_matches_stage_s"),
        ("output_backend", "artifact_backend_is_modal_volume"),
        ("output_volume", "output_volume_matches_stage_s"),
        ("output_mount", "output_mount_matches_stage_s"),
        ("output_root", "artifact_root_matches_stage_s"),
        ("publication", "hub_publication_disabled"),
        ("environment:MODAL_TRAINING_IMAGE", "launch_environment_matches_expected"),
        (
            "environment:MODAL_TRAINING_PIP_PACKAGES_JSON",
            "launch_environment_matches_expected",
        ),
        ("environment:MODAL_GPU", "launch_environment_matches_expected"),
        ("environment:MODAL_TIMEOUT_SECONDS", "launch_environment_matches_expected"),
        ("environment:MODAL_INPUT_VOLUME_NAME", "launch_environment_matches_expected"),
        ("environment:MODAL_INPUT_MOUNT_PATH", "launch_environment_matches_expected"),
        ("environment:MODAL_CACHE_VOLUME_NAME", "launch_environment_matches_expected"),
        ("environment:MODAL_OUTPUT_VOLUME_NAME", "launch_environment_matches_expected"),
        ("environment:MODAL_OUTPUT_MOUNT_PATH", "launch_environment_matches_expected"),
        ("argv_detach", "direct_detached_launch_argv_matches_expected"),
        ("argv_target", "direct_detached_launch_argv_matches_expected"),
        ("argv:--repo-url", "direct_detached_launch_argv_matches_expected"),
        ("argv:--repo-branch", "direct_detached_launch_argv_matches_expected"),
        ("argv:--repo-commit", "direct_detached_launch_argv_matches_expected"),
        ("argv:--config-path", "direct_detached_launch_argv_matches_expected"),
        ("argv:--config-sha256", "direct_detached_launch_argv_matches_expected"),
        ("argv:--dataset-sha256", "direct_detached_launch_argv_matches_expected"),
        ("verification_app_id", "verification_contract_matches_expected"),
        ("verification_function", "verification_contract_matches_expected"),
        ("verification_task", "verification_contract_matches_expected"),
        ("verification_commands", "verification_contract_matches_expected"),
    ],
)
def test_modal_smoke_rejects_every_launch_critical_contract_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_failure: str,
) -> None:
    fixture = _fixture(tmp_path)
    run_id = "launch-contract"
    report, context = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
        run_id=run_id,
    )
    assert report["ready_to_stage"] is True

    def mismatched_plan(context, run_id, config_path, dataset_path):
        plan = _synthetic_modal_plan(context, run_id, config_path, dataset_path)
        _mutate_launch_contract(plan, mutation)
        return plan

    monkeypatch.setattr(stager, "inspect_modal_plan", mismatched_plan)
    with pytest.raises(stager.PreflightError, match=expected_failure):
        stager.stage_smoke(context, run_id, rows_per_mode=1)
    assert not (fixture["tuner"] / "scratch" / "eh_staging" / run_id).exists()


@pytest.mark.parametrize(
    "overlap_field",
    ["identity_overlap_across_splits", "normalized_question_overlap_across_splits"],
)
def test_aggregate_split_overlap_must_be_exact_zero(
    tmp_path: Path, overlap_field: str
) -> None:
    fixture = _fixture(tmp_path)
    aggregate_path = fixture["dataset"] / "aggregate_manifest.json"
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    aggregate[overlap_field] = 1
    aggregate_path.write_text(json.dumps(aggregate, sort_keys=True) + "\n", encoding="utf-8")
    fixture["config"]["private_dataset"]["aggregate_manifest"]["sha256"] = _sha(
        aggregate_path
    )
    fixture["config_path"].write_text(
        yaml.safe_dump(fixture["config"], sort_keys=False), encoding="utf-8"
    )
    report, _ = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
    )
    assert report["ready_to_stage"] is False
    overlap_blocks = [
        blocker
        for blocker in report["blockers"]
        if blocker["code"] == "aggregate_split_overlap_nonzero"
    ]
    assert overlap_blocks == [
        {"code": "aggregate_split_overlap_nonzero", "field": overlap_field, "expected": 0, "actual": 1}
    ]


def test_private_artifact_hash_mismatch_blocks_preflight(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    train = fixture["dataset"] / "train.jsonl"
    train.write_bytes(train.read_bytes() + b"\n")
    report, _ = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
    )
    assert report["ready_to_stage"] is False
    assert "train_artifact_sha256_mismatch" in _block_codes(report)


def test_dirty_and_mismatched_tuner_both_block(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    config = fixture["config"]
    config["tuner"]["expected_commit"] = "b" * 40
    fixture["config_path"].write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    (fixture["tuner"] / "dirty.txt").write_text("dirty", encoding="utf-8")
    report, _ = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
    )
    codes = _block_codes(report)
    assert "tuner_commit_mismatch" in codes
    assert "tuner_worktree_dirty" in codes
    assert not (fixture["tuner"] / "scratch" / "eh_staging").exists()


def test_unresolved_tuner_commit_and_recipe_fields_report_without_staging(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    config = fixture["config"]
    config["tuner"]["expected_commit"] = "pending_pre_sign"
    fixture["config_path"].write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    template_path = fixture["experiment"] / config["tuner"]["recipe_template"]
    template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    template["job"]["image"] = "pending_pre_sign_runtime_image"
    template_path.write_text(yaml.safe_dump(template, sort_keys=False), encoding="utf-8")
    report, _ = stager.preflight(
        fixture["config_path"],
        fixture["tuner"],
        hf_cache_root=fixture["hf_cache"],
    )
    codes = _block_codes(report)
    assert "tuner_expected_commit_unresolved" in codes
    assert "recipe_fields_unresolved" in codes
    assert not (fixture["tuner"] / "scratch" / "eh_staging").exists()


def test_checked_in_recipe_has_exact_candidate_pins_and_no_pending_fields() -> None:
    recipe = yaml.safe_load(MODULE_PATH.with_name("stage_sft_recipe.yaml").read_text(encoding="utf-8"))
    assert recipe["job"]["image"] == EXPECTED_IMAGE
    assert recipe["setup"]["pip"] == EXPECTED_PIP
    assert recipe["training"] == EXPECTED_TRAINING
    assert recipe["lora"] == EXPECTED_LORA
    assert recipe["model"] == {"load_in_4bit": True, "dtype": None}
    assert recipe["run"]["dry_run"] is True
    assert "pending_pre_sign" not in yaml.safe_dump(recipe)


def test_checked_in_stage_config_keeps_full_run_merge_check_separate() -> None:
    config = yaml.safe_load(MODULE_PATH.with_name("stage_s.yaml").read_text(encoding="utf-8"))
    assert config["model"]["load_in_4bit"] is True
    assert config["model"]["dtype"] is None
    assert config["model"]["tokenizer"]["verify_merged_model_roundtrip"] is False
    assert config["model"]["tokenizer"]["merged_model_save_method"] == "merged_4bit_forced"
    assert config["tuner"]["expected_commit"] == "b0b7c7f83f2c8f21a1b7fc127b81a85bf3baff0a"
