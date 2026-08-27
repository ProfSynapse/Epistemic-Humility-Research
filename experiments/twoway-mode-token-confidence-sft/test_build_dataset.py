from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

MODULE_PATH = Path(__file__).with_name("build_dataset.py")
spec = importlib.util.spec_from_file_location("twoway_build_dataset", MODULE_PATH)
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
assert spec.loader is not None
spec.loader.exec_module(builder)

QUALIFY_PREFIX = "My best answer is "
QUALIFY_SUFFIX = ", but I am not certain."


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jeffreys(k: int, n: int = 32) -> float:
    return (k + 0.5) / (n + 1)


def _frozen_row(row_key: str, k: int, source_mode: str, answer: str) -> dict:
    if source_mode == "ABSTAIN":
        assistant = f'<ABSTAIN>{{"answer":"I don\'t know reliably.","answer_confidence":{_jeffreys(k)}}}'
    elif source_mode == "QUALIFY":
        wrapped = f"{QUALIFY_PREFIX}{answer}{QUALIFY_SUFFIX}"
        assistant = json.dumps(
            {"answer": wrapped, "answer_confidence": _jeffreys(k)}, separators=(",", ":")
        )
        assistant = "<QUALIFY>" + assistant
    else:
        assistant = "<ANSWER>" + json.dumps(
            {"answer": answer, "answer_confidence": _jeffreys(k)}, separators=(",", ":")
        )
    return {
        "conversations": [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": f"q-{row_key}"},
            {"role": "assistant", "content": assistant},
        ],
        "metadata": {
            "row_key": row_key,
            "question_id": f"qid-{row_key}",
            "correct_count": k,
            "n_samples": 32,
            "answer_confidence": _jeffreys(k),
            "mode_label": source_mode,
            "entity_group_id": f"grp-{row_key}",
            "split": "unused",
            "gold_aliases": [answer.lower()],
        },
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in rows),
        encoding="utf-8",
    )


def _split_rows(prefix: str, n_abstain: int, n_qualify: int, n_answer: int) -> list[dict]:
    rows = []
    for i in range(n_abstain):
        rows.append(_frozen_row(f"{prefix}-ab-{i}", 0, "ABSTAIN", ""))
    for i in range(n_qualify):
        rows.append(_frozen_row(f"{prefix}-q-{i}", 15, "QUALIFY", f"Godfather{i}"))
    for i in range(n_answer):
        rows.append(_frozen_row(f"{prefix}-an-{i}", 30, "ANSWER", f"Morocco{i}"))
    return rows


def _fixture(tmp_path: Path) -> tuple[Path, dict]:
    repo = tmp_path / "repo"
    scorer = repo / "scoring.py"
    scorer.parent.mkdir(parents=True, exist_ok=True)
    scorer.write_text("# canonical scorer stub\n", encoding="utf-8")

    frozen_dir = repo / "experiments" / "fresh" / "analysis" / "dataset"
    train_rows = _split_rows("tr", 4, 2, 3)
    dev_rows = _split_rows("dv", 2, 1, 1)
    heldout_rows = _split_rows("ho", 1, 1, 1)
    _write_jsonl(frozen_dir / "train.jsonl", train_rows)
    _write_jsonl(frozen_dir / "dev.jsonl", dev_rows)
    _write_jsonl(frozen_dir / "heldout.jsonl", heldout_rows)

    config = {
        "schema_version": 1,
        "mode": "relabel_in_place",
        "source": {
            "canonical_scorer": {"path": "scoring.py", "sha256": _sha(scorer)},
            "frozen_split": {
                "directory": "experiments/fresh/analysis/dataset",
                "train": {"file": "train.jsonl", "sha256": _sha(frozen_dir / "train.jsonl"), "rows": len(train_rows)},
                "dev": {"file": "dev.jsonl", "sha256": _sha(frozen_dir / "dev.jsonl"), "rows": len(dev_rows)},
                "heldout": {"file": "heldout.jsonl", "sha256": _sha(frozen_dir / "heldout.jsonl"), "rows": len(heldout_rows)},
            },
            "identity": {"model_name": "unsloth/Qwen3-4B-bnb-4bit", "n_samples": 32},
        },
        "labeling": {
            "chance_probability": 0.5,
            "one_sided_confidence": 0.95,
            "clopper_pearson_boundaries": {"abstain_max_correct": 10},
            "confidence_target": {"estimator": "jeffreys_posterior_mean", "alpha": 0.5, "beta": 0.5},
        },
        "relabel": {
            "qualify_source_template": {"prefix": QUALIFY_PREFIX, "suffix": QUALIFY_SUFFIX},
            "assert_frozen_abstain_equals_k_le_abstain_max": True,
            "assert_confidence_matches_jeffreys": True,
        },
        "mode_tokens": {"ANSWER": "<ANSWER>", "ABSTAIN": "<ABSTAIN>"},
        "render": {
            "system_message": "sys",
            "user_message_template": "$question",
            "answer_text_templates": {"ANSWER": "$gold_answer", "ABSTAIN": "I don't know reliably."},
            "assistant_output_template": "$mode_token$json_payload",
            "output_json": {"required_fields": ["answer", "answer_confidence"], "additional_fields_allowed": False},
        },
        "output": {
            "directory": "experiments/slug/analysis/dataset",
            "files": {"train": "train.jsonl", "dev": "dev.jsonl", "aggregate_manifest": "aggregate_manifest.json"},
        },
    }
    config_path = repo / "experiments" / "slug" / "dataset_builder.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path, config


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_abstain_boundary_derivation_is_ten() -> None:
    assert builder.derive_abstain_boundary(32, 0.5, 0.95) == 10


def test_qualify_gold_extraction_roundtrip_and_mismatch() -> None:
    template = {"prefix": QUALIFY_PREFIX, "suffix": QUALIFY_SUFFIX}
    got = builder._extract_qualify_gold(
        "My best answer is Paris, but I am not certain.", template
    )
    assert got == "Paris"
    with pytest.raises(builder.ContractError, match="qualify_template_mismatch"):
        builder._extract_qualify_gold("no template here", template)


def test_end_to_end_relabel_counts_and_content(tmp_path: Path) -> None:
    config_path, _ = _fixture(tmp_path)
    aggregate = builder.build_dataset(config_path)

    assert aggregate["mode_counts"]["train"] == {"ABSTAIN": 4, "ANSWER": 5}
    assert aggregate["mode_counts"]["dev"] == {"ABSTAIN": 2, "ANSWER": 2}
    assert aggregate["held_out"]["rows_parsed"] == 0
    assert aggregate["label_rule"]["abstain_max_correct"] == 10

    out_dir = config_path.parent / "analysis" / "dataset"
    assert not (out_dir / "heldout.jsonl").exists()  # held-out never re-emitted

    dev = _read_jsonl(out_dir / "dev.jsonl")
    for record in dev:
        assistant = record["conversations"][2]["content"]
        assert "<QUALIFY>" not in assistant
        assert assistant.startswith(("<ANSWER>", "<ABSTAIN>"))
    # former QUALIFY row is now ANSWER carrying the extracted supported answer
    former_q = [r for r in dev if r["metadata"]["source_mode_label"] == "QUALIFY"]
    assert former_q and all(r["metadata"]["mode_label"] == "ANSWER" for r in former_q)
    payload = json.loads(former_q[0]["conversations"][2]["content"][len("<ANSWER>"):])
    assert payload["answer"] == "Godfather0"
    assert payload["answer_confidence"] == pytest.approx(_jeffreys(15))


def test_frozen_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    config_path, config = _fixture(tmp_path)
    config["source"]["frozen_split"]["train"]["sha256"] = "0" * 64
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="sha256_mismatch"):
        builder.build_dataset(config_path)


def test_confidence_jeffreys_mismatch_fails(tmp_path: Path) -> None:
    config_path, config = _fixture(tmp_path)
    frozen_dir = config_path.parents[2] / "experiments" / "fresh" / "analysis" / "dataset"
    rows = _read_jsonl(frozen_dir / "dev.jsonl")
    rows[0]["metadata"]["answer_confidence"] = 0.123456
    _write_jsonl(frozen_dir / "dev.jsonl", rows)
    config["source"]["frozen_split"]["dev"]["sha256"] = _sha(frozen_dir / "dev.jsonl")
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="jeffreys"):
        builder.build_dataset(config_path)


def test_abstain_integrity_mismatch_fails(tmp_path: Path) -> None:
    # A frozen ABSTAIN row whose k exceeds the abstain boundary must fail closed.
    config_path, config = _fixture(tmp_path)
    frozen_dir = config_path.parents[2] / "experiments" / "fresh" / "analysis" / "dataset"
    rows = _read_jsonl(frozen_dir / "dev.jsonl")
    for r in rows:
        if r["metadata"]["mode_label"] == "ABSTAIN":
            r["metadata"]["correct_count"] = 20  # k>10 but still tagged ABSTAIN
            r["metadata"]["answer_confidence"] = _jeffreys(20)
            break
    _write_jsonl(frozen_dir / "dev.jsonl", rows)
    config["source"]["frozen_split"]["dev"]["sha256"] = _sha(frozen_dir / "dev.jsonl")
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="frozen_abstain_not_equal_k_le_abstain_max"):
        builder.build_dataset(config_path)


def test_prefix_free_token_collision_fails(tmp_path: Path) -> None:
    config_path, config = _fixture(tmp_path)
    config["mode_tokens"] = {"ANSWER": "<A>", "ABSTAIN": "<A>x"}
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(builder.ContractError, match="prefix-free"):
        builder.build_dataset(config_path)
