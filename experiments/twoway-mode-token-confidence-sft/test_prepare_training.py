from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

MODULE_PATH = Path(__file__).with_name("prepare_training.py")
spec = importlib.util.spec_from_file_location("twoway_prepare_training", MODULE_PATH)
prep = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prep
assert spec.loader is not None
spec.loader.exec_module(prep)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, n: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps({"i": i}) + "\n" for i in range(n)), encoding="utf-8")


TEMPLATE = {
    "name": "pending_render",
    "target": "local",
    "method": "sft",
    "provider": "local_docker",
    "run": {"method": "sft", "trainer": "Trainers/sft/train_sft.py", "dry_run": True},
    "model": {"load_in_4bit": True, "dtype": None},
    "dataset": {},
    "training": {"batch_size": 2, "num_epochs": 1},
    "lora": {"r": 32, "alpha": 64},
    "artifacts": {},
}


def _fixture(tmp_path: Path, *, train_rows: int = 18197, dev_rows: int = 602,
             pin_train_sha: bool = False) -> Path:
    repo = tmp_path / "repo"
    experiment_dir = repo / "experiments" / "twoway-mode-token-confidence-sft"
    dataset_dir = experiment_dir / "analysis" / "dataset"
    _write_jsonl(dataset_dir / "train.jsonl", train_rows)
    _write_jsonl(dataset_dir / "dev.jsonl", dev_rows)

    frozen_heldout = repo / "experiments" / "fresh-sft-epistemic-mode-token-grpo" / "analysis" / "dataset" / "heldout.jsonl"
    _write_jsonl(frozen_heldout, 1201)

    (experiment_dir / "sft_recipe.yaml").write_text(yaml.safe_dump(TEMPLATE), encoding="utf-8")

    config = {
        "schema_version": 1,
        "experiment": "twoway-mode-token-confidence-sft",
        "launch_authorized": False,
        "private_dataset": {
            "directory": "analysis/dataset",
            "splits": {
                "train": {"file": "train.jsonl", "rows": train_rows},
                "dev": {"file": "dev.jsonl", "rows": dev_rows, "role": "qualification_only"},
            },
            "heldout": {
                "source": "experiments/fresh-sft-epistemic-mode-token-grpo/analysis/dataset/heldout.jsonl",
                "sha256": _sha(frozen_heldout),
                "access": "forbidden_sealed_carried_forward_untouched",
            },
        },
        "model": {
            "repo": "unsloth/Qwen3-4B-bnb-4bit",
            "revision": "cad0bedfdd862093a12af478cb974ab2addd0e0a",
            "load_in_4bit": True,
            "dtype": None,
            "required_snapshot_files": {},
            "tokenizer": {
                "additional_special_tokens": ["<ANSWER>", "<ABSTAIN>"],
                "train_new_embedding_rows": True,
                "train_new_lm_head_rows": True,
                "merged_model_save_method": "merged_4bit_forced",
            },
        },
        "canonical_output": {"artifact": "adapter_plus_tokenizer", "retain_merged_model": False},
        "lane": {"compute": "local_rtx_3090", "gpu": "RTX_3090"},
        "tuner": {
            "expected_commit": "f6f1229",
            "require_clean_worktree": True,
            "recipe_template": "sft_recipe.yaml",
        },
    }
    if pin_train_sha:
        config["private_dataset"]["splits"]["train"]["sha256"] = _sha(dataset_dir / "train.jsonl")
    config_path = experiment_dir / "training.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_preflight_happy_path_no_launch(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    report = prep.preflight(config_path, staging_root=tmp_path / "staging")
    assert report["launch_authorized"] is False
    assert report["lane"] == "local_rtx_3090"
    assert report["dataset"]["splits"]["train"]["rows"] == 18197
    assert report["dataset"]["splits"]["dev"]["rows"] == 602
    assert report["heldout_seal"]["rows_parsed"] == 0
    assert report["rendered_recipe"]["run"]["dry_run"] is True
    assert report["rendered_recipe"]["model"]["additional_special_tokens"] == ["<ANSWER>", "<ABSTAIN>"]
    # train + dev staged; held-out never staged.
    assert set(report["staged"]) == {"train", "dev"}
    assert not (tmp_path / "staging" / "heldout.jsonl").exists()


def test_heldout_seal_is_hash_only_and_mismatch_fails(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text())
    seal = prep.seal_heldout(config, config_path.parents[2])
    assert seal["rows_parsed"] == 0 and len(seal["sha256"]) == 64
    config["private_dataset"]["heldout"]["sha256"] = "0" * 64
    with pytest.raises(prep.PreparationError, match="held-out SHA-256 mismatch"):
        prep.seal_heldout(config, config_path.parents[2])


def test_train_row_count_mismatch_fails_closed(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path, train_rows=18196)
    config = yaml.safe_load(config_path.read_text())
    config["private_dataset"]["splits"]["train"]["rows"] = 18197  # config lies about count
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(prep.PreparationError, match="row-count mismatch"):
        prep.verify_dataset(config, config_path.parent)


def test_pinned_train_sha_mismatch_fails(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path, pin_train_sha=True)
    config = yaml.safe_load(config_path.read_text())
    config["private_dataset"]["splits"]["train"]["sha256"] = "f" * 64
    with pytest.raises(prep.PreparationError, match="SHA-256 mismatch"):
        prep.verify_dataset(config, config_path.parent)


def test_pending_sentinel_sha_is_not_enforced(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text())
    config["private_dataset"]["splits"]["train"]["sha256"] = prep.PENDING_SENTINEL
    report = prep.verify_dataset(config, config_path.parent)
    assert report["splits"]["train"]["sha256_pinned"] is False


def test_render_recipe_keeps_dry_run_and_two_tokens(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text())
    recipe = prep.render_recipe(
        config, TEMPLATE, run_id="r1", staged_train="/stage/train.jsonl",
        artifact_root="/stage/artifacts",
    )
    assert recipe["run"]["dry_run"] is True
    assert recipe["name"] == "twoway-mode-token-confidence-sft--r1"
    assert recipe["dataset"]["train_path"] == "/stage/train.jsonl"
    assert recipe["model"]["revision"] == "cad0bedfdd862093a12af478cb974ab2addd0e0a"


def test_render_recipe_rejects_three_tokens(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text())
    config["model"]["tokenizer"]["additional_special_tokens"] = ["<ANSWER>", "<ABSTAIN>", "<QUALIFY>"]
    with pytest.raises(prep.PreparationError, match="exactly two unique special tokens"):
        prep.render_recipe(
            config, TEMPLATE, run_id="r1", staged_train="/s/train.jsonl", artifact_root="/s/art",
        )


def test_render_recipe_refuses_live_template(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text())
    live_template = json.loads(json.dumps(TEMPLATE))
    live_template["run"]["dry_run"] = False
    with pytest.raises(prep.PreparationError, match="dry_run: true"):
        prep.render_recipe(
            config, live_template, run_id="r1", staged_train="/s/train.jsonl", artifact_root="/s/art",
        )


def test_config_must_declare_launch_unauthorized(tmp_path: Path) -> None:
    config_path = _fixture(tmp_path)
    config = yaml.safe_load(config_path.read_text())
    config["launch_authorized"] = True
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(prep.PreparationError, match="launch_authorized: false"):
        prep.load_config(config_path)
