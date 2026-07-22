from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import yaml


MODULE_PATH = Path(__file__).with_name("build_dataset.py")
SPEC = importlib.util.spec_from_file_location("mode_dataset_builder", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def _sample_vector(correct_count: int) -> list[bool]:
    return [True] * correct_count + [False] * (32 - correct_count)


def _row(index: int, correct_count: int, greedy_correct: bool) -> dict:
    question = f"Synthetic question {index}?"
    return {
        "probe_pool_row_key": f"row-{index:03d}",
        "probe_pool_source_index": index,
        "question_id": f"q-{index:03d}",
        "question": question,
        "question_norm": builder.normalize_question(question),
        "normalized_aliases": [f"synthetic alias {index}"],
        "answer_value": f"Synthetic answer {index}",
        "n_samples": 32,
        "greedy_correct": greedy_correct,
        "p_correct": correct_count / 32,
        "sampled_correct": _sample_vector(correct_count),
        "model_tag": "synthetic-model-tag",
        "probe_config_sha": "synthetic-probe-sha",
    }


def _rows() -> list[dict]:
    rows = []
    for index in range(10):
        rows.append(_row(index, index % 11, False))
    for index in range(10, 20):
        rows.append(_row(index, 11 + (index % 11), False))
    for index in range(20, 30):
        rows.append(_row(index, 22 + (index % 11), True))
    # A -> B -> C overlap is transitive, not merely pairwise duplicate grouping.
    rows[0]["normalized_aliases"].append("transitive alpha")
    rows[1]["answer_value"] = "Transitive alpha"
    rows[1]["normalized_aliases"].append("transitive beta")
    rows[2]["answer_value"] = "Transitive beta"
    # Duplicate source questions must also stay together even if aliases differ.
    rows[4]["question_id"] = rows[3]["question_id"]
    rows[6]["question"] = "  Shared   normalized question? "
    rows[6]["question_norm"] = builder.normalize_question(rows[6]["question"])
    rows[7]["question"] = "shared normalized question?"
    rows[7]["question_norm"] = builder.normalize_question(rows[7]["question"])
    # Mixed-mode components are ordinary eligible groups, never filtered out.
    rows[5]["normalized_aliases"].append("mixed component link")
    rows[10]["answer_value"] = "Mixed component link"
    return rows


def _manifest(row_count: int) -> dict:
    return {
        "model_tag": "synthetic-model-tag",
        "model_name": "example/Synthetic-4B",
        "enable_thinking": False,
        "sampling": {
            "n_samples": 32,
            "temperature": 1.0,
            "top_p": 0.9,
            "seed": 1234,
        },
        "probe_config_sha": "synthetic-probe-sha",
        "n_questions": row_count,
    }


def _config(results: Path, manifest: Path, output: Path, row_count: int) -> dict:
    return {
        "schema_version": 1,
        "source": {
            "canonical_scorer": {
                "path": str(builder.IMPORTED_SCORER_PATH),
                "sha256": _sha(builder.IMPORTED_SCORER_PATH),
            },
            "probe_results": {
                "path": str(results),
                "sha256": _sha(results),
                "expected_rows": row_count,
            },
            "probe_manifest": {"path": str(manifest), "sha256": _sha(manifest)},
            "identity": {
                "model_name": "example/Synthetic-4B",
                "model_tag": "synthetic-model-tag",
                "probe_config_sha": "synthetic-probe-sha",
                "n_samples": 32,
                "temperature": 1.0,
                "top_p": 0.9,
                "seed": 1234,
                "enable_thinking": False,
            },
            "required_row_schema": {
                "probe_pool_row_key": "string",
                "probe_pool_source_index": "integer",
                "question_id": "string",
                "question": "string",
                "question_norm": "string",
                "normalized_aliases": "list_string",
                "answer_value": "string",
                "n_samples": "integer",
                "greedy_correct": "boolean",
                "p_correct": "number",
                "sampled_correct": "list_boolean",
                "model_tag": "string",
                "probe_config_sha": "string",
            },
        },
        "labeling": {
            "chance_probability": 0.5,
            "one_sided_confidence": 0.95,
            "clopper_pearson_boundaries": {
                "abstain_max_correct": 10,
                "answer_min_correct": 22,
            },
            "confidence_target": {
                "estimator": "jeffreys_posterior_mean",
                "alpha": 0.5,
                "beta": 0.5,
            },
        },
        "mode_tokens": {
            "ANSWER": "<MODE_A>",
            "QUALIFY": "<MODE_Q>",
            "ABSTAIN": "<MODE_Z>",
        },
        "render": {
            "system_message": "Synthetic system instruction.",
            "user_message_template": "$question",
            "answer_text_templates": {
                "ANSWER": "$gold_answer",
                "QUALIFY": "Tentative: $gold_answer",
                "ABSTAIN": "No reliable synthetic answer.",
            },
            "assistant_output_template": "$mode_token$json_payload",
            "output_json": {
                "required_fields": ["answer", "answer_confidence"],
                "additional_fields_allowed": False,
            },
        },
        "splits": {
            "seed": 77,
            "evaluation_targets_per_mode": {
                "dev": {"ANSWER": 2, "QUALIFY": 2, "ABSTAIN": 2},
                "heldout": {"ANSWER": 2, "QUALIFY": 2, "ABSTAIN": 2},
            },
            "max_group_fraction": 0.25,
            "max_absolute_mode_count_deviation": 1,
            "wilson_confidence": 0.95,
        },
        "output": {
            "directory": str(output),
            "files": {
                "train": "train.jsonl",
                "dev": "dev.jsonl",
                "heldout": "heldout.jsonl",
                "aggregate_manifest": "aggregate_manifest.json",
            },
        },
    }


def _fixture(tmp_path: Path) -> tuple[Path, dict, Path, Path]:
    repo = tmp_path / "repo"
    experiment = repo / "experiments" / "synthetic"
    inputs = repo / "inputs"
    output = experiment / "analysis" / "dataset"
    results = inputs / "probe_results.jsonl"
    manifest = inputs / "probe_manifest.json"
    rows = _rows()
    _write_jsonl(results, rows)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(_manifest(len(rows)), sort_keys=True), encoding="utf-8")
    config = _config(results, manifest, output, len(rows))
    experiment.mkdir(parents=True, exist_ok=True)
    config_path = experiment / "dataset_builder.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return config_path, config, results, manifest


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_exact_boundaries_and_greedy_wrong_override() -> None:
    assert builder.derive_exact_boundaries(32, 0.5, 0.95) == (10, 22)
    assert builder.classify(10, True, 10, 22) == "ABSTAIN"
    assert builder.classify(11, False, 10, 22) == "QUALIFY"
    assert builder.classify(21, True, 10, 22) == "QUALIFY"
    assert builder.classify(22, True, 10, 22) == "ANSWER"
    assert builder.classify(22, False, 10, 22) == "QUALIFY"
    assert builder.normalize_answer("A_B—Café") == "a b caf"
    assert builder.normalize_question("  Mixed   CASE? ") == "mixed case?"
    assert builder.wilson_half_width_at_half(200, 0.95) == pytest.approx(0.068639, abs=1e-6)
    assert builder.wilson_half_width_at_half(400, 0.95) == pytest.approx(0.0487655, abs=1e-7)


def test_arbitrary_configured_tokens_and_output_contract(tmp_path: Path) -> None:
    config_path, config, _, _ = _fixture(tmp_path)
    aggregate = builder.build_dataset(config_path)
    output = Path(config["output"]["directory"])
    assert aggregate["mode_counts"] == {"ANSWER": 10, "QUALIFY": 10, "ABSTAIN": 10}
    assert aggregate["split_diagnostic"]["worst_evaluation_mode_count_deviation"] <= 1
    assert aggregate["split_diagnostic"]["mixed_group_count"] >= 1
    for split in ("train", "dev"):
        for record in _read_jsonl(output / f"{split}.jsonl"):
            mode = record["metadata"]["mode_label"]
            content = record["conversations"][-1]["content"]
            token = config["mode_tokens"][mode]
            assert content.startswith(token)
            assert json.loads(content[len(token) :])["answer_confidence"] == record["metadata"]["answer_confidence"]
    assert all(len(record["conversations"]) == 2 for record in _read_jsonl(output / "heldout.jsonl"))


@pytest.mark.parametrize(
    "tokens,match",
    [
        ({"ANSWER": "<X>", "QUALIFY": "<X>", "ABSTAIN": "<Z>"}, "unique"),
        ({"ANSWER": "<X>", "QUALIFY": "<X>Q", "ABSTAIN": "<Z>"}, "prefix-free"),
    ],
)
def test_duplicate_and_prefix_token_collisions_fail(
    tmp_path: Path, tokens: dict[str, str], match: str
) -> None:
    config_path, config, _, _ = _fixture(tmp_path)
    config["mode_tokens"] = tokens
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(builder.ContractError, match=match):
        builder.build_dataset(config_path)


def test_hash_and_schema_fail_closed(tmp_path: Path) -> None:
    config_path, config, results, _ = _fixture(tmp_path)
    results.write_text(results.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(builder.ContractError, match="sha256_mismatch"):
        builder.build_dataset(config_path)

    rows = _rows()
    del rows[0]["greedy_correct"]
    _write_jsonl(results, rows)
    config["source"]["probe_results"]["sha256"] = _sha(results)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="row_schema_mismatch"):
        builder.build_dataset(config_path)

    rows = _rows()
    rows[0]["question_norm"] = "not the canonical normalized question"
    _write_jsonl(results, rows)
    config["source"]["probe_results"]["sha256"] = _sha(results)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="question_norm_mismatch"):
        builder.build_dataset(config_path)


def test_entity_groups_are_transitive_disjoint_and_split_is_deterministic(tmp_path: Path) -> None:
    config_path, config, _, _ = _fixture(tmp_path)
    first = builder.build_dataset(config_path)
    output = Path(config["output"]["directory"])
    first_bytes = {path.name: path.read_bytes() for path in sorted(output.iterdir())}
    second = builder.build_dataset(config_path)
    second_bytes = {path.name: path.read_bytes() for path in sorted(output.iterdir())}
    assert first == second
    assert first_bytes == second_bytes
    assert first["identity_overlap_across_splits"] == 0
    assert first["normalized_question_overlap_across_splits"] == 0

    records = {
        record["metadata"]["row_key"]: record
        for split in ("train", "dev", "heldout")
        for record in _read_jsonl(output / f"{split}.jsonl")
    }
    linked_splits = {records[f"row-{index:03d}"]["metadata"]["split"] for index in range(3)}
    linked_groups = {
        records[f"row-{index:03d}"]["metadata"]["entity_group_id"] for index in range(3)
    }
    assert len(linked_splits) == 1
    assert len(linked_groups) == 1
    duplicate_question_splits = {
        records[f"row-{index:03d}"]["metadata"]["split"] for index in (3, 4)
    }
    duplicate_question_groups = {
        records[f"row-{index:03d}"]["metadata"]["entity_group_id"] for index in (3, 4)
    }
    assert len(duplicate_question_splits) == 1
    assert len(duplicate_question_groups) == 1
    normalized_question_splits = {
        records[f"row-{index:03d}"]["metadata"]["split"] for index in (6, 7)
    }
    normalized_question_groups = {
        records[f"row-{index:03d}"]["metadata"]["entity_group_id"] for index in (6, 7)
    }
    assert len(normalized_question_splits) == 1
    assert len(normalized_question_groups) == 1

    identities_by_split: dict[str, set[str]] = {}
    for split in ("train", "dev", "heldout"):
        identities_by_split[split] = {
            identity
            for record in _read_jsonl(output / f"{split}.jsonl")
            for identity in record["metadata"]["gold_aliases"]
        }
    assert identities_by_split["train"].isdisjoint(identities_by_split["dev"])
    assert identities_by_split["train"].isdisjoint(identities_by_split["heldout"])
    assert identities_by_split["dev"].isdisjoint(identities_by_split["heldout"])


def test_source_hash_contract_is_path_independent(tmp_path: Path) -> None:
    config_path, config, results, manifest = _fixture(tmp_path)
    alternate_root = tmp_path / "alternate"
    copied_results = alternate_root / "inputs" / results.name
    copied_manifest = alternate_root / "inputs" / manifest.name
    copied_results.parent.mkdir(parents=True)
    copied_results.write_bytes(results.read_bytes())
    copied_manifest.write_bytes(manifest.read_bytes())

    config["source"]["probe_results"]["path"] = "inputs/probe_results.jsonl"
    config["source"]["probe_manifest"]["path"] = "inputs/probe_manifest.json"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    aggregate = builder.build_dataset(config_path, source_root=alternate_root)
    assert aggregate["source"]["probe_results_sha256"] == _sha(results)
    assert aggregate["source"]["probe_manifest_sha256"] == _sha(manifest)


def test_canonical_scorer_hash_and_import_path_fail_closed(tmp_path: Path) -> None:
    scorer_copy = tmp_path / "scoring.py"
    scorer_copy.write_bytes(builder.IMPORTED_SCORER_PATH.read_bytes())
    expected_sha = _sha(scorer_copy)
    assert builder.verify_canonical_scorer(scorer_copy, expected_sha) == expected_sha
    with pytest.raises(builder.ContractError, match="canonical_scorer_import_path_mismatch"):
        builder.verify_canonical_scorer(
            scorer_copy,
            expected_sha,
            imported_path=builder.IMPORTED_SCORER_PATH,
        )
    scorer_copy.write_bytes(scorer_copy.read_bytes() + b"\n# synthetic mutation\n")
    with pytest.raises(builder.ContractError, match="sha256_mismatch"):
        builder.verify_canonical_scorer(scorer_copy, expected_sha)


def test_rendered_token_collision_in_answer_fails_without_row_text(tmp_path: Path) -> None:
    config_path, config, results, _ = _fixture(tmp_path)
    rows = _rows()
    rows[20]["answer_value"] = "Synthetic <MODE_Q> collision"
    rows[20]["normalized_aliases"] = ["synthetic collision alias"]
    _write_jsonl(results, rows)
    config["source"]["probe_results"]["sha256"] = _sha(results)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="rendered_mode_token_collision"):
        builder.build_dataset(config_path)


def test_precision_targets_fail_when_whole_groups_cannot_meet_tolerance(tmp_path: Path) -> None:
    config_path, config, results, _ = _fixture(tmp_path)
    rows = _rows()
    for index, row in enumerate(rows):
        mode_group = index // 10
        row["normalized_aliases"].append(f"indivisible mode group {mode_group}")
    _write_jsonl(results, rows)
    config["source"]["probe_results"]["sha256"] = _sha(results)
    config["splits"]["max_group_fraction"] = 0.9
    config["splits"]["max_absolute_mode_count_deviation"] = 0
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="entity_group_stratification_infeasible"):
        builder.build_dataset(config_path)
